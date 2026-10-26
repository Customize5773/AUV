"""Run a complete visual ARENA mission, recording independent physical task proof."""
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
from sauvc_sim.runtime import STATUS_QOS


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--gui',action='store_true')
    parser.add_argument('--edition',choices=['2026','2027'],default='2027')
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--extended',action='store_true')
    parser.add_argument('--pinger-drum',type=int,choices=[0,1,2,3,4],default=0)
    parser.add_argument('--order',default='B-R-Y')
    parser.add_argument('--scene-variant',type=int,choices=[0,1],default=0)
    parser.add_argument('--blue-drum',type=int,choices=[1,2,3,4],default=1)
    parser.add_argument('--fault',default='none',choices=['none','camera_loss','command_loss','odom_loss','contact_loss','clock_loss'])
    args=parser.parse_args();args.output.parent.mkdir(parents=True,exist_ok=True)
    rclpy.init();node=rclpy.create_node('arena_check')
    observed={'state':'','result':{},'trajectory':[],'physics':[],'commands':[]}
    tracks={}
    acoustic={'samples':0,'contract_valid':True}
    def ping(m):
        p=json.loads(m.data);acoustic['samples']+=1
        acoustic['contract_valid'] &= set(p)=={'time','frequency_hz','tdoa_s'} and len(p['tdoa_s'])==4
    node.create_subscription(String,'/sauvc/acoustics',ping,10)
    def result(m): observed['result']=json.loads(m.data)
    def state(m): observed['state']=m.data
    def physics(m): observed['physics'].append(json.loads(m.data))
    def odom(m):
        p,q=m.pose.pose.position,m.pose.pose.orientation
        observed['trajectory'].append([m.header.stamp.sec+m.header.stamp.nanosec*1e-9,p.x,p.y,p.z,2*math.atan2(q.z,q.w)])
    def command(m): observed['commands'].append([time.monotonic(),m.linear.x,m.linear.y,m.linear.z,m.angular.z])
    def perception(m):
        packet=json.loads(m.data)
        for obj in packet.get('detections',[]):
            if not obj.get('confirmed'): continue
            row=tracks.setdefault(obj['label'],dict(confirmed_frames=0,max_hits=0,ids=[]))
            row['confirmed_frames']+=1
            row['max_hits']=max(row['max_hits'],obj['track_hits'])
            if obj['track_id'] not in row['ids']: row['ids'].append(obj['track_id'])
    node.create_subscription(String,'/sauvc/arena/result',result,STATUS_QOS)
    node.create_subscription(String,'/sauvc/arena/state',state,STATUS_QOS)
    node.create_subscription(String,'/sauvc/arena/physics',physics,10)
    node.create_subscription(Odometry,'/sauvc/odom',odom,qos_profile_sensor_data)
    node.create_subscription(Twist,'/sauvc/cmd_vel',command,10)
    for camera in ('front','bottom'):
        node.create_subscription(String,'/sauvc/perception/'+camera,perception,10)
    report={'passed':False,'edition':args.edition,'order':args.order,'fault':args.fault,
            'scene_variant':args.scene_variant,'blue_drum':args.blue_drum,
            'extended':args.extended,'pinger_drum':args.pinger_drum}
    with args.output.with_suffix('.log').open('w') as log:
        process=subprocess.Popen(['bash','tools/ros.sh','launch','sauvc_sim','arena.launch.py',
            'arena:=finals',f'edition:={args.edition}','autonomous:=true',f'headless:={str(not args.gui).lower()}',f'flare_order:={args.order}',
            f'scene_variant:={args.scene_variant}',f'blue_drum:={args.blue_drum}',
            f'extended:={str(args.extended).lower()}',f'pinger_drum:={args.pinger_drum}',
            f'fault:={args.fault}',f'output:={args.output.with_suffix("")}'],
            stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
        try:
            deadline=time.monotonic()+1000
            terminal_since=None
            last_state=None
            while time.monotonic()<deadline:
                rclpy.spin_once(node,timeout_sec=.1)
                if last_state!=observed['state']:
                    last_state=observed['state']
                    print(last_state,observed['trajectory'][-1] if observed['trajectory'] else '',flush=True)
                terminal=last_state in ('DONE','ABORT') or observed['result'].get('phase')=='FAILED'
                if terminal and terminal_since is None: terminal_since=time.monotonic()
                if terminal_since is not None and time.monotonic()-terminal_since>2: break
                if process.poll() is not None: raise RuntimeError('launch exited before completion')
            else: raise TimeoutError('ARENA did not finish in 1000 wall seconds')
            recent=observed['commands'][-10:]
            zero=len(recent)==10 and all(all(abs(v)<1e-6 for v in row[1:]) for row in recent)
            stationary=len(observed['trajectory'])>20 and math.dist(observed['trajectory'][-1][1:4],observed['trajectory'][-20][1:4])<.01
            success=last_state=='DONE' and observed['result'].get('passed',False)
            fault_verified=False
            if args.fault!='none':
                controller=Path(str(args.output.with_suffix(''))+'-controller.json')
                info=json.loads(controller.read_text()) if controller.exists() else {}
                key={'camera_loss':'front','contact_loss':'contacts'}.get(args.fault,args.fault.removesuffix('_loss'))
                fault_verified=('stale_'+key in (info.get('reason','')+' '+observed['result'].get('reason',''))
                                and bool(observed['trajectory']) and observed['trajectory'][-1][0]>=8)
            report.update(zero_command=zero,stationary=stationary,fault_verified=fault_verified,
                passed=zero and stationary and (success if args.fault=='none' else fault_verified and not success))
        except Exception as exc: report['error']=str(exc)
        finally:
            if process.poll() is None:
                try:
                    pause=subprocess.run(['ign','service','-s','/world/sauvc_finals/control',
                        '--reqtype','ignition.msgs.WorldControl','--reptype','ignition.msgs.Boolean',
                        '--timeout','3000','--req','pause: true'],capture_output=True,text=True,timeout=5)
                    report['paused_before_shutdown']='data: true' in pause.stdout
                    drain=time.monotonic()+.15
                    while time.monotonic()<drain:rclpy.spin_once(node,timeout_sec=.02)
                    stop=subprocess.run(['ign','service','-s','/server_control',
                        '--reqtype','ignition.msgs.ServerControl','--reptype','ignition.msgs.Boolean',
                        '--timeout','3000','--req','stop: true'],capture_output=True,text=True,timeout=5)
                    report['shutdown_via_service']='data: true' in stop.stdout
                    if report['shutdown_via_service']: process.wait(timeout=8)
                except (subprocess.TimeoutExpired,OSError): report['shutdown_via_service']=False
            if process.poll() is None: process.send_signal(signal.SIGINT)
            try:
                process.wait(timeout=12);report['shutdown_forced']=False
            except subprocess.TimeoutExpired:
                os.killpg(process.pid,signal.SIGKILL);process.wait();report['shutdown_forced']=True
            node.destroy_node();rclpy.try_shutdown()
    log_text=args.output.with_suffix('.log').read_text()
    report['shutdown_clean']=not report.get('shutdown_forced') and not any(s in log_text for s in ('Traceback','process has died','Errno::ESRCH'))
    report['passed']=report['passed'] and report['shutdown_clean']
    report['tracking']=tracks
    if args.fault=='none':
        required={'navigation_gate','orange_flare','blue_flare','red_flare','yellow_flare'} | (set() if args.extended else {'blue_drum'})
        report['confirmed_all_targets']=required<=tracks.keys()
        report['passed']=report['passed'] and report['confirmed_all_targets']
    if args.extended and args.fault=='none':
        report['acoustics']=acoustic
        report['physical_retention']=bool(observed['physics']) and observed['physics'][-1].get('payload_attached',False)
        score=observed['result'].get('score',{})
        report['extended_proof']=report['physical_retention'] and acoustic['samples']>20 and acoustic['contract_valid'] and score.get('target_acquisition')==50 and score.get('target_reacquisition')==60 and (args.edition!='2027' or observed['result'].get('target_zone_exited'))
        report['passed']=report['passed'] and report['extended_proof']
    if args.edition=='2027' and args.fault=='none':
        report['surfacing_square_verified']=observed['result'].get('score',{}).get('surfacing_square_bonus')==20 and 'surfacing_square' in tracks
        report['passed']=report['passed'] and report['surfacing_square_verified']
    report.update(observed)
    args.output.write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({k:v for k,v in report.items() if k not in ('trajectory','commands','physics')},indent=2))
    raise SystemExit(0 if report['passed'] else 1)


if __name__=='__main__': main()
