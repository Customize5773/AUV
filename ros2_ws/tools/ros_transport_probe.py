"""ROS observer independent of mission/checker, with one-second host samples."""
import argparse
import json
from pathlib import Path
import signal
import time
import rclpy
from rclpy.signals import SignalHandlerOptions
from std_msgs.msg import String
from sensor_msgs.msg import Image
from rclpy.qos import qos_profile_sensor_data


def image_record(camera,msg,now):
    return dict(kind='ros_image',camera=camera,wall_s=now,
                sim_s=msg.header.stamp.sec+msg.header.stamp.nanosec*1e-9,
                width=msg.width,height=msg.height,bytes=len(msg.data))


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True)
    p.add_argument('--images',action='store_true',help='Opt-in raw camera metadata; no pixels are logged')
    args=p.parse_args()
    stopping=False
    def stop(*_):
        nonlocal stopping
        stopping=True
    signal.signal(signal.SIGINT,stop);signal.signal(signal.SIGTERM,stop)
    rclpy.init(signal_handler_options=SignalHandlerOptions.NO);node=rclpy.create_node('sauvc_transport_probe')
    with args.output.open('w') as out:
        def write(value):out.write(json.dumps(value)+'\n')
        def receive(topic):
            def callback(msg):
                packet=json.loads(msg.data);record=dict(kind='ros',topic=topic,wall_s=time.monotonic(),sim_s=packet['time'])
                for key in ('sensor_sequence','producer_wall_s','sensor_publish_duration_s','sensor_age_wall_s','valid','reason'):
                    if key in packet:record[key]=packet[key]
                write(record)
            return callback
        for topic in ('sensors','dynamics/telemetry','state/health'):
            node.create_subscription(String,'/sauvc/'+topic,receive(topic),10)
        def camera_receive(camera):
            def callback(msg):
                packet=json.loads(msg.data);stamp=packet.get('stamp',{})
                write(dict(kind='camera',topic='perception/'+camera,wall_s=time.monotonic(),
                           sim_s=stamp.get('sec',0)+stamp.get('nanosec',0)*1e-9,
                           fresh=packet.get('fresh',False),valid_image=packet.get('valid_image',False)))
            return callback
        for camera in ('front','bottom'):
            node.create_subscription(String,'/sauvc/perception/'+camera,camera_receive(camera),10)
            if args.images:
                node.create_subscription(Image,'/sauvc/camera_'+camera+'/image_raw',
                    lambda msg,c=camera:write(image_record(c,msg,time.monotonic())),qos_profile_sensor_data)
        def heartbeat():
            write(dict(kind='heartbeat',wall_s=time.monotonic()));out.flush()
        def host():
            record=dict(kind='host',wall_s=time.monotonic())
            for name in ('/proc/loadavg','/proc/pressure/cpu','/proc/pressure/memory','/proc/pressure/io','/sys/fs/cgroup/cpu.stat'):
                try:record[name]=Path(name).read_text()
                except OSError:pass
            record['processes']=[]
            for entry in Path('/proc').iterdir():
                if not entry.name.isdigit():continue
                try:
                    words=(entry/'cmdline').read_bytes().split(b'\0')
                    names={Path(w.decode()).name for w in words if w}
                    if names & {'state_estimator','propulsion','parameter_bridge','perception','qualification'}:
                        record['processes'].append(dict(pid=entry.name,names=sorted(names & {'state_estimator','propulsion','parameter_bridge','perception','qualification'}),stat=(entry/'stat').read_text()))
                except (OSError,UnicodeError):pass
            write(record)
        node.create_timer(.1,heartbeat);node.create_timer(1.,host)
        try:
            while not stopping:rclpy.spin_once(node,timeout_sec=.05)
        finally:node.destroy_node();rclpy.try_shutdown()


if __name__=='__main__':main()
