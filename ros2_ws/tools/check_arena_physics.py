"""Isolated physical ball test; teleports belong to this harness, never the mission."""
import argparse
import json
import os
from pathlib import Path
import signal
import subprocess
import time
import rclpy
from std_msgs.msg import String,Bool


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--output',type=Path,required=True)
    args=p.parse_args();args.output.parent.mkdir(parents=True,exist_ok=True)
    rclpy.init();node=rclpy.create_node('arena_physics_check')
    samples=[]
    node.create_subscription(String,'/sauvc/arena/physics',lambda m:samples.append(json.loads(m.data)),10)
    release=node.create_publisher(Bool,'/sauvc/payload/release',10)
    report={'passed':False}
    def until(condition,seconds):
        end=time.monotonic()+seconds
        while time.monotonic()<end:
            rclpy.spin_once(node,timeout_sec=.05)
            if condition(): return True
            if process.poll() is not None: raise RuntimeError('launch exited')
        return False
    def move(x,y,z):
        r=subprocess.run(['ign','service','-s','/world/sauvc_finals/set_pose','--reqtype','ignition.msgs.Pose',
            '--reptype','ignition.msgs.Boolean','--timeout','3000','--req',
            f'name:"sauvc_auv",position:{{x:{x},y:{y},z:{z}}},orientation:{{w:1}}'],capture_output=True,text=True,timeout=5)
        if 'data: true' not in r.stdout: raise RuntimeError(r.stdout+r.stderr)
    with args.output.with_suffix('.log').open('w') as log:
        process=subprocess.Popen(['bash','tools/ros.sh','launch','sauvc_sim','arena.launch.py',
                                 'arena:=finals','headless:=true','cameras:=false'],
                                 stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
        try:
            if not until(lambda: samples and samples[-1]['time']>3,30): raise RuntimeError('no physics stream')
            balls=samples[-1]['balls']
            report['held_balls_stable']=abs(balls['blue_flare']['position'][2]+.73065)<.005 and abs(balls['payload']['position'][2]+.23)<.005
            move(10.71,11.,-1.)
            report['flare_ball_physically_fell']=until(lambda: samples[-1]['balls']['blue_flare']['released'] and samples[-1]['balls']['blue_flare']['position'][2]<-1.,5)
            move(23.8,12.5,-.3)
            until(lambda: abs(samples[-1]['balls']['payload']['position'][0]-24)<.01,3)
            release.publish(Bool(data=True))
            def settled():
                recent=[s for s in samples if s['time']>=samples[-1]['time']-.6]
                return (len(recent)>8 and recent[-1]['time']-recent[0]['time']>.5 and
                        all(s['balls']['payload']['released'] and
                            abs(s['balls']['payload']['position'][0]-24)<.05 and
                            abs(s['balls']['payload']['position'][1]-12.5)<.05 and
                            -1.2<s['balls']['payload']['position'][2]<-1.15 for s in recent))
            report['payload_physically_settled']=until(settled,7)
            before=samples[-1]['balls']['payload']['position']
            move(22.,12.5,-.3)
            release.publish(Bool(data=True))
            start=samples[-1]['time']
            until(lambda:samples[-1]['time']>start+1,4)
            report['repeated_release_does_not_rearm']=all(abs(a-b)<.01 for a,b in zip(before,samples[-1]['balls']['payload']['position']))
            report['passed']=all(report[k] for k in ('held_balls_stable','flare_ball_physically_fell','payload_physically_settled','repeated_release_does_not_rearm'))
        except Exception as exc: report['error']=str(exc)
        finally:
            if process.poll() is None:
                try:
                    subprocess.run(['ign','service','-s','/world/sauvc_finals/control',
                        '--reqtype','ignition.msgs.WorldControl','--reptype','ignition.msgs.Boolean',
                        '--timeout','3000','--req','pause: true'],capture_output=True,text=True,timeout=5)
                    stop=subprocess.run(['ign','service','-s','/server_control',
                        '--reqtype','ignition.msgs.ServerControl','--reptype','ignition.msgs.Boolean',
                        '--timeout','3000','--req','stop: true'],capture_output=True,text=True,timeout=5)
                    report['shutdown_via_service']='data: true' in stop.stdout
                    if report['shutdown_via_service']: process.wait(timeout=8)
                except (subprocess.TimeoutExpired,OSError): report['shutdown_via_service']=False
            if process.poll() is None: process.send_signal(signal.SIGINT)
            try: process.wait(timeout=12);report['shutdown_forced']=False
            except subprocess.TimeoutExpired:
                os.killpg(process.pid,signal.SIGKILL);process.wait();report['shutdown_forced']=True
            node.destroy_node();rclpy.try_shutdown()
    report['shutdown_clean']=not report['shutdown_forced'] and 'Traceback' not in args.output.with_suffix('.log').read_text()
    report['passed']=report['passed'] and report['shutdown_clean']
    report['samples']=samples
    args.output.write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({k:v for k,v in report.items() if k!='samples'},indent=2))
    raise SystemExit(0 if report['passed'] else 1)


if __name__=='__main__': main()
