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
from sauvc_sim.conditions import load_conditions


def stop_viewers(viewers):
    """Stop our viewer groups, including Qt children left after ros2 run exits."""
    forced=[]
    for viewer in viewers:
        try:os.killpg(viewer.pid,signal.SIGTERM)
        except ProcessLookupError:pass
    for viewer in viewers:
        try:viewer.wait(timeout=3)
        except subprocess.TimeoutExpired:pass
        try:
            os.killpg(viewer.pid,0)
            os.killpg(viewer.pid,signal.SIGKILL)
            forced.append(viewer.pid)
        except ProcessLookupError:pass
        viewer.wait()
    return forced


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--vehicle-model',choices=['auto','ideal','dynamic'],default='auto')
    parser.add_argument('--gui',action='store_true')
    parser.add_argument('--pov',action='store_true',help='Open and verify both annotated camera viewers (requires --gui)')
    parser.add_argument('--edition',choices=['2026','2027'],default='2027')
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--conditions',type=Path,help='JSON: sensor seed, world current, initial XY prior error, light scale')
    parser.add_argument('--extended',action='store_true')
    parser.add_argument('--pinger-drum',type=int,choices=[0,1,2,3,4],default=0)
    parser.add_argument('--order',default='B-R-Y')
    parser.add_argument('--scene-variant',type=int,choices=[0,1],default=0)
    parser.add_argument('--blue-drum',type=int,choices=[1,2,3,4],default=1)
    parser.add_argument('--fault',default='none',choices=['none','camera_loss','command_loss','odom_loss','contact_loss','clock_loss','imu_loss','pressure_loss','dvl_loss','actuator_loss'])
    args=parser.parse_args();args.output.parent.mkdir(parents=True,exist_ok=True)
    test_conditions=load_conditions(args.conditions)
    if args.pov and not args.gui:parser.error('--pov requires --gui')
    rclpy.init();node=rclpy.create_node('arena_check')
    observed={'state':'','result':{},'trajectory':[],'physics':[],'commands':[],'estimates':[],'sensors':[],'dynamics':[],'health':[]}
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
        observed['trajectory'].append([m.header.stamp.sec+m.header.stamp.nanosec*1e-9,p.x,p.y,p.z,math.atan2(2*(q.w*q.z+q.x*q.y),1-2*(q.y*q.y+q.z*q.z))])
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
    def estimate(m):
        p,q=m.pose.pose.position,m.pose.pose.orientation
        observed['estimates'].append([m.header.stamp.sec+m.header.stamp.nanosec*1e-9,p.x,p.y,p.z,math.atan2(2*(q.w*q.z+q.x*q.y),1-2*(q.y*q.y+q.z*q.z))])
    node.create_subscription(Odometry,'/sauvc/state/odom',estimate,qos_profile_sensor_data)
    node.create_subscription(String,'/sauvc/state/health',lambda m:observed['health'].append(json.loads(m.data)),10)
    node.create_subscription(String,'/sauvc/sensors',lambda m:observed['sensors'].append(json.loads(m.data)),10)
    node.create_subscription(String,'/sauvc/dynamics/telemetry',lambda m:observed['dynamics'].append(json.loads(m.data)),10)
    report={'vehicle_model':args.vehicle_model,'passed':False,'edition':args.edition,'order':args.order,'fault':args.fault,
            'scene_variant':args.scene_variant,'blue_drum':args.blue_drum,
            'extended':args.extended,'pinger_drum':args.pinger_drum,'conditions':test_conditions}
    viewers=[];viewer_logs=[]
    with args.output.with_suffix('.log').open('w') as log:
        process=subprocess.Popen(['bash','tools/ros.sh','launch','sauvc_sim','arena.launch.py',
            'arena:=finals',f'vehicle_model:={args.vehicle_model}',f'edition:={args.edition}','autonomous:=true',f'headless:={str(not args.gui).lower()}',f'flare_order:={args.order}',
            f'scene_variant:={args.scene_variant}',f'blue_drum:={args.blue_drum}',
            f'extended:={str(args.extended).lower()}',f'pinger_drum:={args.pinger_drum}',
            f'conditions_file:={args.conditions.resolve() if args.conditions else ""}',
            f'fault:={args.fault}',f'output:={args.output.with_suffix("")}'],
            stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
        try:
            if args.pov:
                for camera in ('front','bottom'):
                    viewer_log=args.output.with_name(args.output.stem+'-pov-'+camera+'.log').open('w')
                    viewer_logs.append(viewer_log)
                    viewers.append(subprocess.Popen(['bash','tools/ros.sh','run','rqt_image_view','rqt_image_view',
                        f'/sauvc/perception/{camera}/image_annotated'],stdout=viewer_log,
                        stderr=subprocess.STDOUT,start_new_session=True))
            deadline=time.monotonic()+1000
            terminal_since=None
            last_state=None
            while time.monotonic()<deadline:
                if any(v.poll() is not None for v in viewers):raise RuntimeError('POV viewer exited during mission')
                rclpy.spin_once(node,timeout_sec=.1)
                if last_state!=observed['state']:
                    last_state=observed['state']
                    print(last_state,observed['trajectory'][-1] if observed['trajectory'] else '',flush=True)
                terminal=last_state in ('DONE','ABORT') or observed['result'].get('phase')=='FAILED'
                if terminal and terminal_since is None: terminal_since=time.monotonic()
                if terminal_since is not None and time.monotonic()-terminal_since>2:
                    stable=len(observed['trajectory'])>20 and math.dist(observed['trajectory'][-1][1:4],observed['trajectory'][-20][1:4])<.01
                    if args.vehicle_model=='ideal' or stable or time.monotonic()-terminal_since>40:break
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
                key={'camera_loss':'front','contact_loss':'contacts','imu_loss':'gyro','pressure_loss':'pressure_pa'}.get(args.fault,args.fault.removesuffix('_loss'))
                fault_verified=('stale_'+key in (info.get('reason','')+' '+observed['result'].get('reason',''))
                                and bool(observed['trajectory']) and observed['trajectory'][-1][0]>=8)
            if args.vehicle_model!='ideal':
                from check_qualification import estimation_errors
                truth=[s.node_name for s in node.get_subscriptions_info_by_topic('/sauvc/odom')]
                report['truth_subscribers']=truth
                consumers={s.node_name for s in node.get_subscriptions_info_by_topic('/sauvc/arena/result')}
                report['referee_pose_isolated']=not bool({'sauvc_arena','sauvc_propulsion','sauvc_state_estimator','sauvc_command_guard'}&consumers)
                report['sensor_only_control']=not bool({'sauvc_arena','sauvc_propulsion','sauvc_state_estimator','sauvc_command_guard'}&set(truth))
                report['sensor_contract_valid']=bool(observed['sensors']) and all(set(p)<={'time','deployment_held','actuator_timeout','gyro','accel','mag','dvl','pressure_pa'} for p in observed['sensors'])
                report['estimation_error']=estimation_errors(observed['trajectory'],observed['estimates'])
                report['estimation_error']['qualification_reference_passed']=report['estimation_error'].pop('passed')
                report['estimation_error']['reference_limits']={'max_xy_m':.2,'max_depth_m':.03,'max_yaw_rad':.03}
                report['estimated_state_available']=report['estimation_error']['samples']>50
                health=observed['health'][-1] if observed['health'] else {}
                report['dvl_calibration']={k:health.get(k) for k in ('dvl_bias_xy_mps','dvl_bias_samples','dvl_calibrating')}
                report['dvl_calibration_valid']=health.get('dvl_bias_samples',0)>=20 and health.get('dvl_calibrating') is False
                report['seven_thrusters']=bool(observed['dynamics']) and all(len(p['force_n'])==7 for p in observed['dynamics'])
                report['thrusters_zero']=bool(observed['dynamics']) and all(abs(f)<.05 for f in observed['dynamics'][-1]['force_n'])
            report.update(zero_command=zero,stationary=stationary,fault_verified=fault_verified,
                passed=zero and stationary and (success if args.fault=='none' else fault_verified and not success))
            if args.pov:
                report['pov_subscribers']={c:[s.node_name for s in node.get_subscriptions_info_by_topic(
                    f'/sauvc/perception/{c}/image_annotated') if s.node_name.startswith('rqt_gui_cpp_node_')]
                    for c in ('front','bottom')}
                report['pov_verified']=all(report['pov_subscribers'].values()) and all(v.poll() is None for v in viewers)
                report['passed']=report['passed'] and report['pov_verified']
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
            report['pov_cleanup_forced_groups']=stop_viewers(viewers)
            for viewer_log in viewer_logs:viewer_log.close()
            node.destroy_node();rclpy.try_shutdown()
    log_text=args.output.with_suffix('.log').read_text()
    report['shutdown_clean']=not report.get('shutdown_forced') and not any(s in log_text for s in ('Traceback','process has died','Errno::ESRCH'))
    report['passed']=report['passed'] and report['shutdown_clean']
    if args.vehicle_model!='ideal':report['passed']=report['passed'] and all(report.get(k,False) for k in ('sensor_only_control','referee_pose_isolated','sensor_contract_valid','estimated_state_available','dvl_calibration_valid','seven_thrusters','thrusters_zero'))
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
    print(json.dumps({k:v for k,v in report.items() if k not in ('trajectory','commands','physics','estimates','sensors','dynamics','health')},indent=2))
    raise SystemExit(0 if report['passed'] else 1)


if __name__=='__main__': main()
