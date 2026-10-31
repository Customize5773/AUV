"""Run one bounded qualification and save observed trajectory, state and judge result."""
from sauvc_sim.rules2027 import VERSION
import argparse
import json
import math
import os
from pathlib import Path
import signal
import subprocess
import time
import bisect
from datetime import datetime
from zoneinfo import ZoneInfo

import rclpy
from rclpy.qos import qos_profile_sensor_data, QoSProfile, DurabilityPolicy
from geometry_msgs.msg import Twist
from nav_msgs.msg import Odometry
from std_msgs.msg import String
from sauvc_sim.qualification import MAX_SPEED_SCALE
from sauvc_sim.conditions import load_conditions


def estimation_errors(truth,estimates):
    times=[p[0] for p in truth];errors=[]
    for e in estimates:
        j=bisect.bisect_left(times,e[0])
        if not 0<j<len(truth):continue
        a,b=truth[j-1],truth[j]
        if b[0]<=a[0] or b[0]-a[0]>.1:continue
        f=(e[0]-a[0])/(b[0]-a[0])
        position=[a[k]+f*(b[k]-a[k]) for k in (1,2,3)]
        yaw=a[4]+f*math.atan2(math.sin(b[4]-a[4]),math.cos(b[4]-a[4]))
        errors.append((math.dist(e[1:3],position[:2]),abs(e[3]-position[2]),
                       abs(math.atan2(math.sin(e[4]-yaw),math.cos(e[4]-yaw)))))
    if not errors:return {'samples':0,'passed':False}
    maximum=[max(row[i] for row in errors) for i in range(3)]
    return dict(samples=len(errors),max_xy_m=maximum[0],max_depth_m=maximum[1],
                max_yaw_rad=maximum[2],rms=[math.sqrt(sum(row[i]**2 for row in errors)/len(errors)) for i in range(3)],
                passed=len(errors)>50 and all(a<b for a,b in zip(maximum,(.2,.03,.03))))


def calibration_evidence(observed):
    thrust=next((p['time'] for p in observed['dynamics'] if any(abs(f)>.05 for f in p['force_n'])),None)
    before=[p for p in observed['health'] if thrust is not None and p['time']<=thrust]
    start=before[-1] if before else {};end=observed['health'][-1] if observed['health'] else {}
    uncertainty=start.get('dvl_bias_uncertainty_mps')
    ready=(start.get('valid') is True and start.get('dvl_calibration_ready') is True
           and start.get('dvl_bias_samples',0)>=200 and isinstance(uncertainty,(int,float))
           and math.isfinite(uncertainty) and 0<=uncertainty<=.0004)
    poses=[p for p in observed['trajectory'] if thrust is not None and p[0]<thrust-.1]
    held_motion=max((math.dist(p[1:4],poses[0][1:4]) for p in poses),default=None)
    frozen=end.get('dvl_calibrating') is False and end.get('dvl_calibration_ready') is True
    return dict(first_thrust_s=thrust,ready_before_thrust=ready,preflight_motion_m=held_motion,
                pre_thrust_health=start,final_health=end,
                passed=ready and frozen and len(poses)>50 and held_motion<.001)



NATIVE_FAULTS = ('imu_loss', 'pressure_loss', 'dvl_loss', 'actuator_loss')


def native_fault_evidence(observed, fault):
    thrust = next((p['time'] for p in observed['dynamics'] if any(abs(f)>.05 for f in p['force_n'])), None)
    injected = next((p['time'] for p in observed['dynamics'] if p.get('injected_fault')==fault), None)
    elapsed = injected-thrust if thrust is not None and injected is not None else None
    # The first force sample follows the command that releases the restraint.
    return dict(first_thrust_s=thrust, injected_s=injected, elapsed_since_thrust_s=elapsed,
                passed=elapsed is not None and 11.9<=elapsed<=12.1)



def runtime_fault_evidence(log_text, fault, dynamics, delay):
    events=[json.loads(line.split('FAULT_INJECTED ',1)[1]) for line in log_text.splitlines() if 'FAULT_INJECTED ' in line]
    events=[p for p in events if p['fault']==fault]
    thrust=next((p['time'] for p in dynamics if any(abs(f)>.05 for f in p['force_n'])),None)
    return dict(events=events,first_thrust_s=thrust,passed=bool(events) and thrust is not None and all(
        abs(p['started_s']-thrust)<.2 and delay<=p['injected_s']-p['started_s']<=delay+.3 for p in events))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--bridge-layout',choices=['single','isolated'],default=None,help='Override bridge process isolation; omit to use launch default')
    parser.add_argument('--mode', choices=['vision', 'odom'], default='vision')
    parser.add_argument('--vehicle-model',choices=['auto','ideal','dynamic'],default='auto')
    parser.add_argument('--speed-scale', type=float, default=MAX_SPEED_SCALE)
    parser.add_argument('--lane', type=int, choices=[1, 2,3], default=1)
    parser.add_argument('--lateral-offset', type=float, default=0.)
    parser.add_argument('--yaw', type=float, default=0.)
    parser.add_argument('--fault', choices=['', 'camera_loss', 'command_loss',
                                          'odom_loss', 'contact_loss', 'clock_loss',
                                          'controller_freeze','imu_loss','pressure_loss','dvl_loss','actuator_loss'], default='')
    parser.add_argument('--gui', action='store_true')
    parser.add_argument('--pov',action='store_true',help='Open both annotated camera viewers; requires --gui')
    parser.add_argument('--edition',choices=['2026','2027'],default='2027')
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--surface-hold',action='store_true')
    parser.add_argument('--hold-duration',type=float,default=30.,help='Hold measurement window in simulation seconds (at least 30)')
    parser.add_argument('--conditions',type=Path,help='JSON: sensor seed, world current, initial XY prior error, light scale')
    args = parser.parse_args()
    if args.surface_hold and (args.vehicle_model=='ideal' or args.fault not in ('','none')):parser.error('surface hold test requires dynamic vehicle and no early fault')
    if not math.isfinite(args.hold_duration) or args.hold_duration<30:parser.error('--hold-duration must be finite and at least 30')
    if not args.surface_hold and args.hold_duration!=30:parser.error('--hold-duration requires --surface-hold')
    if args.pov and not args.gui:parser.error('--pov requires --gui')
    test_conditions=load_conditions(args.conditions)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    rclpy.init()
    node = rclpy.create_node('qualification_check')
    qos = QoSProfile(depth=1, durability=DurabilityPolicy.TRANSIENT_LOCAL)
    observed = {'state': '', 'result': {}, 'trajectory': [], 'commands': [],'estimates':[],
                'sensors':[],'dynamics':[],'health':[],'hold_status':[]}
    def result(msg):
        observed['result'] = json.loads(msg.data)
    def state(msg):
        observed['state'] = msg.data
    def odom(msg):
        p, q = msg.pose.pose.position, msg.pose.pose.orientation
        observed['trajectory'].append([msg.header.stamp.sec+msg.header.stamp.nanosec*1e-9,
                                       p.x, p.y, p.z, math.atan2(2*(q.w*q.z+q.x*q.y),1-2*(q.y*q.y+q.z*q.z))])
    def command(msg):
        observed['commands'].append([time.monotonic(), msg.linear.x, msg.linear.y,
                                     msg.linear.z, msg.angular.z])
    def estimate(msg):
        p,q=msg.pose.pose.position,msg.pose.pose.orientation
        observed['estimates'].append([msg.header.stamp.sec+msg.header.stamp.nanosec*1e-9,
                                     p.x,p.y,p.z,math.atan2(2*(q.w*q.z+q.x*q.y),1-2*(q.y*q.y+q.z*q.z))])
    # Record callback timing separately: simulator stamps alone cannot locate a stall.
    from reception_monitor import ReceptionMonitor
    reception = ReceptionMonitor()
    def timed(topic, callback, stamp):
        def receive(msg):
            reception.record(topic, time.monotonic(), stamp(msg))
            callback(msg)
        return receive
    stamp = lambda m: m.header.stamp.sec + m.header.stamp.nanosec * 1e-9
    odom = timed('truth', odom, stamp)
    estimate = timed('estimate', estimate, stamp)
    def packet(topic):
        def receive(msg):
            value = json.loads(msg.data)
            reception.record(topic, time.monotonic(), value.get('time'))
            observed[topic].append(value)
        return receive
    subscriptions = [node.create_subscription(String, '/sauvc/qualification/result', result, qos),
                     node.create_subscription(String, '/sauvc/qualification/state', state, qos),
                     node.create_subscription(Odometry, '/sauvc/odom', odom, qos_profile_sensor_data),
                     node.create_subscription(Twist, '/sauvc/cmd_vel', command, 10)]
    subscriptions += [node.create_subscription(Odometry,'/sauvc/state/odom',estimate,qos_profile_sensor_data),
        node.create_subscription(String,'/sauvc/sensors',packet('sensors'),10),
        node.create_subscription(String,'/sauvc/dynamics/telemetry',packet('dynamics'),10)]
    node.create_subscription(String,'/sauvc/state/health',packet('health'),10)
    node.create_subscription(String,'/sauvc/surface_hold/status',lambda m:observed['hold_status'].append(json.loads(m.data)),10)
    report = {'passed': False, 'mode': args.mode, 'lane': args.lane,
              'speed_scale': args.speed_scale,
              'vehicle_model':args.vehicle_model,'conditions':test_conditions,'surface_hold':args.surface_hold,
              'lateral_offset': args.lateral_offset, 'yaw': args.yaw, 'fault': args.fault,
              'bridge_layout':args.bridge_layout,'rulebook': VERSION if args.edition=='2027' else '2026 v6.1.0', 'checked_on': datetime.now(ZoneInfo('Asia/Jakarta')).date().isoformat()}
    frozen_pid = None
    viewers=[];viewer_logs=[];pov_windows=[]
    with args.output.with_suffix('.log').open('w') as log:
        process = subprocess.Popen(['bash', 'tools/ros.sh', 'launch', 'sauvc_sim', 'arena.launch.py',
            'autonomous:=true',f'edition:={args.edition}', f'mode:={args.mode}', f'lane:={args.lane}',
            f'vehicle_model:={args.vehicle_model}',
            f'surface_hold:={str(args.surface_hold).lower()}',
            *([f'conditions_file:={args.conditions.resolve()}'] if args.conditions else []),
            *([f'bridge_layout:={args.bridge_layout}'] if args.bridge_layout else []),
            f'speed_scale:={args.speed_scale}',
            f'lateral_offset:={args.lateral_offset}', f'yaw:={args.yaw}',
            f'headless:={str(not args.gui).lower()}', f'output:={args.output.with_suffix("")}',
            f'fault:={"none" if args.fault == "controller_freeze" else args.fault or "none"}'],
            stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
        try:
            if args.pov:
                for camera in ('front','bottom'):
                    viewer_log=args.output.with_name(args.output.stem+'-pov-'+camera+'.log').open('w')
                    viewer_logs.append(viewer_log)
                    viewers.append(subprocess.Popen(['bash','tools/ros.sh','run','rqt_image_view','rqt_image_view',
                        f'/sauvc/perception/{camera}/image_annotated'],stdout=viewer_log,stderr=subprocess.STDOUT,start_new_session=True))
            deadline = time.monotonic()+220+(3*args.hold_duration if args.surface_hold else 0)
            terminal_since = None
            terminal_sim = None
            motion_started = None
            while time.monotonic() < deadline:
                if any(v.poll() is not None for v in viewers):raise RuntimeError('POV viewer exited during mission')
                if args.pov and not pov_windows and observed['state'] not in ('','WAIT','WAIT_READY'):
                    from pov_windows import arrange
                    pov_windows=arrange(viewers)
                rclpy.spin_once(node, timeout_sec=.1)
                if process.poll() is not None:
                    raise RuntimeError('launch exited before completion')
                if motion_started is None and observed['dynamics'] and any(abs(f)>.05 for f in observed['dynamics'][-1]['force_n']):
                    motion_started=observed['dynamics'][-1]['time']
                if motion_started is None and (args.vehicle_model=='ideal' or (args.vehicle_model=='auto' and args.mode=='odom')) and observed['commands'] and observed['trajectory'] and any(abs(v)>1e-6 for v in observed['commands'][-1][1:]):
                    motion_started=observed['trajectory'][-1][0]
                if args.fault == 'controller_freeze' and frozen_pid is None and motion_started is not None and observed['trajectory'] and observed['trajectory'][-1][0]-motion_started>8:
                    children = subprocess.check_output(['ps', '--ppid', str(process.pid), '-o', 'pid=,args='], text=True)
                    for line in children.splitlines():
                        pid, *command_words = line.split()
                        if any(Path(word).name == 'qualification' for word in command_words):
                            frozen_pid = int(pid)
                            os.kill(frozen_pid, signal.SIGSTOP)
                            report['controller_frozen'] = True
                            elapsed=observed['trajectory'][-1][0]-motion_started
                            report['fault_injection']=dict(first_thrust_s=motion_started,elapsed_since_thrust_s=elapsed,passed=8<=elapsed<=8.2)
                            break
                    if frozen_pid is None:
                        raise RuntimeError('controller process not found for freeze test')
                terminal = observed['state'] in ('DONE', 'ABORT') or observed['result'].get('phase') == 'FAILED'
                if terminal and terminal_since is None:
                    terminal_since = time.monotonic()
                if terminal_since is not None and time.monotonic()-terminal_since > 2:
                    if args.surface_hold and observed['state']=='DONE':
                        if not observed['trajectory']:continue
                        if terminal_sim is None:terminal_sim=observed['trajectory'][-1][0]
                        if observed['trajectory'][-1][0]-terminal_sim<args.hold_duration+5:continue
                    stable=len(observed['trajectory'])>20 and math.dist(
                        observed['trajectory'][-1][1:4],observed['trajectory'][-20][1:4])<.01
                    if not observed['sensors'] or stable or time.monotonic()-terminal_since>40:
                        break
            else:
                raise TimeoutError('qualification mission/hold exceeded wall-time deadline')
            recent = observed['commands'][-10:]
            zero = len(recent) == 10 and all(all(abs(v) < 1e-6 for v in c[1:]) for c in recent)
            stopped = len(observed['trajectory']) > 20 and math.dist(
                observed['trajectory'][-1][1:4], observed['trajectory'][-20][1:4]) < .01
            mission_passed = observed['state'] == 'DONE' and observed['result'].get('passed', False)
            fault_verified = False
            if args.fault:
                controller_path = args.output.with_suffix('').with_name(args.output.stem+'-controller.json')
                controller = json.loads(controller_path.read_text()) if controller_path.exists() else {}
                expected = 'stale_' + {'contact_loss': 'contacts', 'controller_freeze': 'command',
                    'imu_loss':'gyro','pressure_loss':'pressure_pa'}.get(args.fault, args.fault.removesuffix('_loss'))
                reason = observed['result'].get('reason', '') if frozen_pid else controller.get('reason', '')
                fault_verified = expected in reason and bool(observed['trajectory']) and observed['trajectory'][-1][0] >= 8
                if args.fault in NATIVE_FAULTS:
                    report['fault_injection']=native_fault_evidence(observed,args.fault)
                    report['calibration_verification']=calibration_evidence(observed)
                    fault_verified=fault_verified and report['fault_injection']['passed'] and report['calibration_verification']['passed']
                elif args.fault=='controller_freeze':
                    fault_verified=fault_verified and report.get('fault_injection',{}).get('passed',False)
                elif observed['dynamics']:
                    report['fault_injection']=runtime_fault_evidence(args.output.with_suffix('.log').read_text(),args.fault,observed['dynamics'],8)
                    fault_verified=fault_verified and report['fault_injection']['passed']
            report.update(mission_passed=mission_passed, zero_command=zero, stationary=stopped,
                          fault_verified=fault_verified if args.fault else None,
                          passed=zero and stopped and ((not mission_passed and fault_verified) if args.fault else mission_passed))
            if observed['sensors']:
                truth_subscribers=[s.node_name for s in node.get_subscriptions_info_by_topic('/sauvc/odom')]
                report['truth_subscribers']=truth_subscribers
                report['result_subscribers']=[s.node_name for s in node.get_subscriptions_info_by_topic('/sauvc/qualification/result')]
                forbidden={'sauvc_qualification','sauvc_propulsion','sauvc_state_estimator','sauvc_command_guard'}
                report['sensor_only_control']=not bool(forbidden&set(truth_subscribers))
                report['referee_pose_isolated']=not bool(forbidden&set(report['result_subscribers']))
                allowed={'time','deployment_held','actuator_timeout','gyro','accel','mag','dvl','pressure_pa'}
                report['sensor_contract_valid']=all(set(p)<=allowed for p in observed['sensors'])
                report['passed']=report['passed'] and report['sensor_only_control'] and bool(observed['estimates'])
                report['passed']=report['passed'] and report['sensor_contract_valid']
                report['passed']=report['passed'] and report['referee_pose_isolated']
                report['thrusters_zero']=len(observed['dynamics'])>=20 and all(
                    abs(f)<.05 for row in observed['dynamics'][-20:] for f in row['force_n'])
                report['passed']=report['passed'] and (args.surface_hold or report['thrusters_zero'])
                if not args.fault:
                    report['calibration_verification']=calibration_evidence(observed)
                    report['passed']=report['passed'] and report['calibration_verification']['passed']
                    report['estimation_error']=estimation_errors(observed['trajectory'],observed['estimates'])
                    report['passed']=report['passed'] and report['estimation_error']['passed']
            if args.surface_hold and mission_passed:
                from surface_hold_check import verify_hold
                report['hold_verification']=verify_hold(node,observed,args.hold_duration)
                report['passed']=report['passed'] and report['hold_verification']['passed']
            if args.pov:
                report['pov_subscribers']={c:[s.node_name for s in node.get_subscriptions_info_by_topic(
                    f'/sauvc/perception/{c}/image_annotated') if s.node_name.startswith('rqt_gui_cpp_node_')] for c in ('front','bottom')}
                report['pov_windows']=pov_windows
                report['pov_verified']=len(pov_windows)==2 and all(report['pov_subscribers'].values()) and all(v.poll() is None for v in viewers)
                report['passed']=report['passed'] and report['pov_verified']
            report['bridge_publishers']={topic:[p.node_name for p in node.get_publishers_info_by_topic(topic)]
                                         for topic in ('/clock','/sauvc/sensors','/sauvc/camera_front/image_raw')}
            report['bridge_qos']={topic:[dict(node=p.node_name,reliability=p.qos_profile.reliability.name,depth=p.qos_profile.depth) for p in node.get_publishers_info_by_topic(topic)] for topic in report['bridge_publishers']}
            report['bridge_publishers_unique']=all(len(v)==1 for v in report['bridge_publishers'].values())
            report['passed']=report['passed'] and report['bridge_publishers_unique']
        except Exception as exc:
            report['passed']=False
            report['error'] = str(exc)
        finally:
            report['reception'] = reception.summary()
            if frozen_pid is not None:
                try:
                    os.kill(frozen_pid, signal.SIGCONT)
                except ProcessLookupError:
                    pass
            if process.poll() is None:
                # Stop the render server through its API before tearing down ROS.
                try:
                    pause=subprocess.run(['ign','service','-s','/world/sauvc_qualification/control',
                        '--reqtype','ignition.msgs.WorldControl','--reptype','ignition.msgs.Boolean',
                        '--timeout','3000','--req','pause: true'],stdout=log,stderr=subprocess.STDOUT,timeout=5)
                    report['paused_before_shutdown']=pause.returncode==0
                    drain=time.monotonic()+.15
                    while time.monotonic()<drain:rclpy.spin_once(node,timeout_sec=.02)
                    stop = subprocess.run(['ign', 'service', '-s', '/server_control',
                        '--reqtype', 'ignition.msgs.ServerControl', '--reptype', 'ignition.msgs.Boolean',
                        '--timeout', '3000', '--req', 'stop: true'], stdout=log,
                        stderr=subprocess.STDOUT, timeout=5)
                    report['shutdown_via_service'] = stop.returncode == 0
                    if stop.returncode == 0:
                        process.wait(timeout=8)
                except (subprocess.TimeoutExpired, OSError):
                    report['shutdown_via_service'] = False
            if process.poll() is None:
                process.send_signal(signal.SIGINT)
            try:
                process.wait(timeout=12)
                report['shutdown_forced'] = False
            except subprocess.TimeoutExpired:
                os.killpg(process.pid, signal.SIGKILL)
                process.wait()
                report['shutdown_forced'] = True
                report['passed'] = False
            from check_arena import stop_viewers
            report['pov_cleanup_forced_groups']=stop_viewers(viewers)
            for viewer_log in viewer_logs:viewer_log.close()
            node.destroy_node()
            rclpy.try_shutdown()
    report.update(observed)
    log_text = args.output.with_suffix('.log').read_text()
    report['shutdown_clean'] = not report.get('shutdown_forced', False) and not any(
        marker in log_text for marker in ('Traceback', 'Errno::ESRCH', 'process has died'))
    report['passed'] = report['passed'] and report['shutdown_clean']
    args.output.write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps({k: v for k, v in report.items() if k not in ('trajectory', 'commands','estimates','sensors','dynamics','health','hold_status')}, indent=2))
    raise SystemExit(0 if report['passed'] else 1)

if __name__ == '__main__':
    main()
