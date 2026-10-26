"""Physical pulse, active brake, passive drag and buoyancy tests; no pose injection."""
import argparse
import json
import math
import os
from pathlib import Path
import signal
import subprocess
import time
import rclpy
from rclpy.qos import qos_profile_sensor_data
from geometry_msgs.msg import Twist
from nav_msgs.msg import Odometry
from std_msgs.msg import String


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args();args.output.parent.mkdir(parents=True,exist_ok=True)
    rclpy.init();node=rclpy.create_node('dynamics_check')
    samples=[];forces=[];stages=[]
    def odom(m):
        p=m.pose.pose.position;v=m.twist.twist.linear
        samples.append([m.header.stamp.sec+m.header.stamp.nanosec*1e-9,p.x,p.y,p.z,v.x,v.y,v.z])
    node.create_subscription(Odometry,'/sauvc/odom',odom,qos_profile_sensor_data)
    node.create_subscription(String,'/sauvc/dynamics/telemetry',lambda m:forces.append(json.loads(m.data)),10)
    pub=node.create_publisher(Twist,'/sauvc/cmd_vel',10)
    state=node.create_publisher(String,'/sauvc/qualification/state',10)
    report={'passed':False}
    def drive(name,velocity,seconds):
        start=samples[-1][0];wall=time.monotonic()+seconds*3+10
        stages.append(dict(name=name,time=start,velocity=velocity))
        msg=Twist();msg.linear.x,msg.linear.y,msg.linear.z=velocity
        last=0.
        while samples[-1][0]-start<seconds:
            if time.monotonic()>wall:raise TimeoutError(name)
            if time.monotonic()-last>.04:pub.publish(msg);last=time.monotonic()
            rclpy.spin_once(node,timeout_sec=.01)
    with args.output.with_suffix('.log').open('w') as log:
        process=subprocess.Popen(['bash','tools/ros.sh','launch','sauvc_sim','arena.launch.py',
            'vehicle_model:=dynamic','headless:=true','cameras:=false'],stdout=log,
            stderr=subprocess.STDOUT,start_new_session=True)
        try:
            end=time.monotonic()+30
            while not samples or samples[-1][0]<2:
                rclpy.spin_once(node,timeout_sec=.05)
                if time.monotonic()>end:raise TimeoutError('startup')
            drive('dive',[0.,0.,-.2],3.)
            drive('hold',[0.,0.,0.],1.)
            drive('forward',[.6,0.,0.],5.)
            drive('brake',[0.,0.,0.],2.5)
            drive('reverse',[-.4,0.,0.],2.5)
            at_release=samples[-1]
            state.publish(String(data='STOP'))
            drive('passive_float',[0.,0.,0.],5.)
            times={s['name']:s['time'] for s in stages}
            ramp=[s for s in samples if times['forward']<=s[0]<times['forward']+.15]
            cruise=[s for s in samples if times['brake']-.5<s[0]<times['brake']]
            brake=[s for s in samples if times['reverse']-.4<s[0]<times['reverse']]
            braking_forces=[math.sqrt(.5)*sum(row['force_n'][:4]) for row in forces
                            if times['brake']+.2<row['time']<times['brake']+1.]
            passive=[s for s in samples if s[0]>times['passive_float']+4]
            checks=dict(finite_acceleration=bool(ramp) and max(abs(s[4]) for s in ramp)<.3,
                seven_thruster_telemetry=bool(forces) and all(len(r["force_n"])==7 for r in forces),
                speed_tracks=bool(cruise) and abs(sum(s[4] for s in cruise)/len(cruise)-.6)<.1,
                reverse_thrust_braking=bool(braking_forces) and min(braking_forces)<-1,
                actively_stopped=bool(brake) and max(abs(s[4]) for s in brake)<.03,
                passive_drag=bool(passive) and abs(passive[-1][4])<abs(at_release[4])*.6,
                unpowered_buoyancy=samples[-1][3]-at_release[3]>.15,
                thrusters_off=bool(forces) and max(abs(f) for r in forces[-20:] for f in r['force_n'])<.05)
            report.update(checks=checks,passed=all(checks.values()))
        except Exception as exc:report['error']=str(exc)
        finally:
            pub.publish(Twist())
            if process.poll() is None:
                try:
                    subprocess.run(['ign','service','-s','/world/sauvc_qualification/control',
                        '--reqtype','ignition.msgs.WorldControl','--reptype','ignition.msgs.Boolean',
                        '--timeout','3000','--req','pause: true'],stdout=log,stderr=log,timeout=5)
                    drain=time.monotonic()+.15
                    while time.monotonic()<drain:rclpy.spin_once(node,timeout_sec=.02)
                    subprocess.run(['ign','service','-s','/server_control','--reqtype','ignition.msgs.ServerControl',
                        '--reptype','ignition.msgs.Boolean','--timeout','3000','--req','stop: true'],stdout=log,stderr=log,timeout=5)
                    process.wait(timeout=8)
                except subprocess.TimeoutExpired:process.send_signal(signal.SIGINT)
            try:process.wait(timeout=12);report['shutdown_forced']=False
            except subprocess.TimeoutExpired:
                os.killpg(process.pid,signal.SIGKILL);process.wait();report['shutdown_forced']=True
            node.destroy_node();rclpy.try_shutdown()
    text=args.output.with_suffix('.log').read_text()
    report['shutdown_clean']=not report['shutdown_forced'] and not any(s in text for s in ('Traceback','process has died','Errno::ESRCH'))
    report['passed']=report['passed'] and report['shutdown_clean']
    report.update(stages=stages,samples=samples,forces=forces)
    args.output.write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({k:v for k,v in report.items() if k not in ('stages','samples','forces')},indent=2))
    raise SystemExit(0 if report['passed'] else 1)


if __name__=='__main__':main()
