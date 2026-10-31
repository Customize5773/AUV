"""ROS observer independent of mission/checker, with one-second host samples."""
import argparse
import json
from pathlib import Path
import signal
import time
import rclpy
from rclpy.signals import SignalHandlerOptions
from std_msgs.msg import String


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);args=p.parse_args()
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
