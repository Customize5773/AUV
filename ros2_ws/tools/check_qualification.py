"""Run one bounded qualification and save observed trajectory, state and judge result."""
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


def main():
    parser = argparse.ArgumentParser(description=__doc__)
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
    parser.add_argument('--edition',choices=['2026','2027'],default='2027')
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--conditions',type=Path,help='JSON: sensor seed, world current, initial XY prior error, light scale')
    args = parser.parse_args()
    test_conditions=load_conditions(args.conditions)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    rclpy.init()
    node = rclpy.create_node('qualification_check')
    qos = QoSProfile(depth=1, durability=DurabilityPolicy.TRANSIENT_LOCAL)
    observed = {'state': '', 'result': {}, 'trajectory': [], 'commands': [],'estimates':[],
                'sensors':[],'dynamics':[]}
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
    subscriptions = [node.create_subscription(String, '/sauvc/qualification/result', result, qos),
                     node.create_subscription(String, '/sauvc/qualification/state', state, qos),
                     node.create_subscription(Odometry, '/sauvc/odom', odom, qos_profile_sensor_data),
                     node.create_subscription(Twist, '/sauvc/cmd_vel', command, 10)]
    subscriptions += [node.create_subscription(Odometry,'/sauvc/state/odom',estimate,qos_profile_sensor_data),
        node.create_subscription(String,'/sauvc/sensors',lambda m:observed['sensors'].append(json.loads(m.data)),10),
        node.create_subscription(String,'/sauvc/dynamics/telemetry',lambda m:observed['dynamics'].append(json.loads(m.data)),10)]
    report = {'passed': False, 'mode': args.mode, 'lane': args.lane,
              'speed_scale': args.speed_scale,
              'vehicle_model':args.vehicle_model,'conditions':test_conditions,
              'lateral_offset': args.lateral_offset, 'yaw': args.yaw, 'fault': args.fault,
              'rulebook': '2027.2.1' if args.edition=='2027' else '2026 v6.1.0', 'checked_on': datetime.now(ZoneInfo('Asia/Jakarta')).date().isoformat()}
    frozen_pid = None
    with args.output.with_suffix('.log').open('w') as log:
        process = subprocess.Popen(['bash', 'tools/ros.sh', 'launch', 'sauvc_sim', 'arena.launch.py',
            'autonomous:=true',f'edition:={args.edition}', f'mode:={args.mode}', f'lane:={args.lane}',
            f'vehicle_model:={args.vehicle_model}',
            f'conditions_file:={args.conditions.resolve() if args.conditions else ""}',
            f'speed_scale:={args.speed_scale}',
            f'lateral_offset:={args.lateral_offset}', f'yaw:={args.yaw}',
            f'headless:={str(not args.gui).lower()}', f'output:={args.output.with_suffix("")}',
            f'fault:={"none" if args.fault == "controller_freeze" else args.fault or "none"}'],
            stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
        try:
            deadline = time.monotonic()+220
            terminal_since = None
            while time.monotonic() < deadline:
                rclpy.spin_once(node, timeout_sec=.1)
                if args.fault == 'controller_freeze' and frozen_pid is None and observed['trajectory'] and observed['trajectory'][-1][0] > 8:
                    children = subprocess.check_output(['ps', '--ppid', str(process.pid), '-o', 'pid=,args='], text=True)
                    for line in children.splitlines():
                        pid, *command_words = line.split()
                        if any(Path(word).name == 'qualification' for word in command_words):
                            frozen_pid = int(pid)
                            os.kill(frozen_pid, signal.SIGSTOP)
                            report['controller_frozen'] = True
                            break
                    if frozen_pid is None:
                        raise RuntimeError('controller process not found for freeze test')
                terminal = observed['state'] in ('DONE', 'ABORT') or observed['result'].get('phase') == 'FAILED'
                if terminal and terminal_since is None:
                    terminal_since = time.monotonic()
                if terminal_since is not None and time.monotonic()-terminal_since > 2:
                    stable=len(observed['trajectory'])>20 and math.dist(
                        observed['trajectory'][-1][1:4],observed['trajectory'][-20][1:4])<.01
                    if not observed['sensors'] or stable or time.monotonic()-terminal_since>40:
                        break
                if process.poll() is not None:
                    raise RuntimeError('launch exited before completion')
            else:
                raise TimeoutError('qualification did not finish within 220 wall seconds')
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
                if not args.fault:
                    report['thrusters_zero']=bool(observed['dynamics']) and all(
                        abs(f)<.05 for row in observed['dynamics'][-20:] for f in row['force_n'])
                    report['passed']=report['passed'] and report['thrusters_zero']
                    report['estimation_error']=estimation_errors(observed['trajectory'],observed['estimates'])
                    report['passed']=report['passed'] and report['estimation_error']['passed']
        except Exception as exc:
            report['error'] = str(exc)
        finally:
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
            node.destroy_node()
            rclpy.try_shutdown()
    report.update(observed)
    log_text = args.output.with_suffix('.log').read_text()
    report['shutdown_clean'] = not report.get('shutdown_forced', False) and not any(
        marker in log_text for marker in ('Traceback', 'Errno::ESRCH', 'process has died'))
    report['passed'] = report['passed'] and report['shutdown_clean']
    args.output.write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps({k: v for k, v in report.items() if k not in ('trajectory', 'commands','estimates','sensors','dynamics')}, indent=2))
    raise SystemExit(0 if report['passed'] else 1)

if __name__ == '__main__':
    main()
