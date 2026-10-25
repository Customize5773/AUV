"""Run one bounded qualification and save observed trajectory, state and judge result."""
import argparse
import json
import math
import os
from pathlib import Path
import signal
import subprocess
import time

import rclpy
from rclpy.qos import qos_profile_sensor_data, QoSProfile, DurabilityPolicy
from geometry_msgs.msg import Twist
from nav_msgs.msg import Odometry
from std_msgs.msg import String
from sauvc_sim.qualification import MAX_SPEED_SCALE


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--mode', choices=['vision', 'odom'], default='vision')
    parser.add_argument('--speed-scale', type=float, default=MAX_SPEED_SCALE)
    parser.add_argument('--lane', type=int, choices=[1, 2], default=1)
    parser.add_argument('--lateral-offset', type=float, default=0.)
    parser.add_argument('--yaw', type=float, default=0.)
    parser.add_argument('--fault', choices=['', 'camera_loss', 'command_loss',
                                          'odom_loss', 'contact_loss', 'clock_loss',
                                          'controller_freeze'], default='')
    parser.add_argument('--gui', action='store_true')
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    rclpy.init()
    node = rclpy.create_node('qualification_check')
    qos = QoSProfile(depth=1, durability=DurabilityPolicy.TRANSIENT_LOCAL)
    observed = {'state': '', 'result': {}, 'trajectory': [], 'commands': []}
    def result(msg):
        observed['result'] = json.loads(msg.data)
    def state(msg):
        observed['state'] = msg.data
    def odom(msg):
        p, q = msg.pose.pose.position, msg.pose.pose.orientation
        observed['trajectory'].append([msg.header.stamp.sec+msg.header.stamp.nanosec*1e-9,
                                       p.x, p.y, p.z, 2*math.atan2(q.z, q.w)])
    def command(msg):
        observed['commands'].append([time.monotonic(), msg.linear.x, msg.linear.y,
                                     msg.linear.z, msg.angular.z])
    subscriptions = [node.create_subscription(String, '/sauvc/qualification/result', result, qos),
                     node.create_subscription(String, '/sauvc/qualification/state', state, qos),
                     node.create_subscription(Odometry, '/sauvc/odom', odom, qos_profile_sensor_data),
                     node.create_subscription(Twist, '/sauvc/cmd_vel', command, 10)]
    report = {'passed': False, 'mode': args.mode, 'lane': args.lane,
              'speed_scale': args.speed_scale,
              'lateral_offset': args.lateral_offset, 'yaw': args.yaw, 'fault': args.fault,
              'rulebook': '2026 v6.1.0', 'checked_on': '2026-10-25'}
    frozen_pid = None
    with args.output.with_suffix('.log').open('w') as log:
        process = subprocess.Popen(['bash', 'tools/ros.sh', 'launch', 'sauvc_sim', 'arena.launch.py',
            'autonomous:=true', f'mode:={args.mode}', f'lane:={args.lane}',
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
                expected = 'stale_' + {'contact_loss': 'contacts', 'controller_freeze': 'command'}.get(args.fault, args.fault.removesuffix('_loss'))
                reason = observed['result'].get('reason', '') if frozen_pid else controller.get('reason', '')
                fault_verified = expected in reason and bool(observed['trajectory']) and observed['trajectory'][-1][0] >= 8
            report.update(mission_passed=mission_passed, zero_command=zero, stationary=stopped,
                          fault_verified=fault_verified if args.fault else None,
                          passed=zero and stopped and ((not mission_passed and fault_verified) if args.fault else mission_passed))
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
    print(json.dumps({k: v for k, v in report.items() if k not in ('trajectory', 'commands')}, indent=2))
    raise SystemExit(0 if report['passed'] else 1)

if __name__ == '__main__':
    main()
