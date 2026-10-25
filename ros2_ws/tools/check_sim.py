"""Bounded ROS/Gazebo smoke test: transport, camera frames, dive, forward, turn, stop."""
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
from rosgraph_msgs.msg import Clock
from sensor_msgs.msg import Image


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--arena', choices=['qualification', 'finals'], required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--no-cameras', action='store_true')
    args = parser.parse_args()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    counts = dict(clock=0, odom=0, front=0, bottom=0)
    frames = {}
    pose = None
    yaw = None
    result = {'arena': args.arena, 'passed': False, 'counts': counts, 'camera_frames': frames}
    rclpy.init()
    node = rclpy.create_node('sauvc_sim_check')
    pub = node.create_publisher(Twist, '/sauvc/cmd_vel', 10)

    def clock(msg):
        counts['clock'] += 1

    def odom(msg):
        nonlocal pose, yaw
        counts['odom'] += 1
        p, q = msg.pose.pose.position, msg.pose.pose.orientation
        pose = (p.x, p.y, p.z)
        yaw = math.atan2(2 * (q.w * q.z + q.x * q.y), 1 - 2 * (q.y**2 + q.z**2))

    def camera(msg, name):
        counts[name] += 1
        frames[name] = {'width': msg.width, 'height': msg.height, 'encoding': msg.encoding}
        if counts[name] == 1 and msg.encoding == 'rgb8':
            path = args.output.with_name(f'{args.arena}-{name}.ppm')
            rows = b''.join(bytes(msg.data[i * msg.step:i * msg.step + msg.width * 3])
                            for i in range(msg.height))
            path.write_bytes(f'P6\n{msg.width} {msg.height}\n255\n'.encode() + rows)

    subscriptions = [
        node.create_subscription(Clock, '/clock', clock, qos_profile_sensor_data),
        node.create_subscription(Odometry, '/sauvc/odom', odom, qos_profile_sensor_data),
    ]
    if not args.no_cameras:
        for name in ('front', 'bottom'):
            subscriptions.append(node.create_subscription(
                Image, f'/sauvc/camera_{name}/image_raw',
                lambda msg, name=name: camera(msg, name), qos_profile_sensor_data))

    def command_for(seconds, x=0.0, z=0.0, turn=0.0):
        cmd = Twist()
        cmd.linear.x, cmd.linear.z, cmd.angular.z = x, z, turn
        deadline = time.monotonic() + seconds
        while time.monotonic() < deadline:
            pub.publish(cmd)
            rclpy.spin_once(node, timeout_sec=0.05)

    log_path = args.output.with_suffix('.log')
    with log_path.open('w') as log:
        process = subprocess.Popen([
            'bash', 'tools/ros.sh', 'launch', 'sauvc_sim', 'arena.launch.py',
            f'arena:={args.arena}', 'headless:=true',
            f'cameras:={str(not args.no_cameras).lower()}',
        ], stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
        try:
            deadline = time.monotonic() + 40
            required = ['clock', 'odom'] + ([] if args.no_cameras else ['front', 'bottom'])
            while not all(counts[key] > 0 for key in required):
                rclpy.spin_once(node, timeout_sec=0.1)
                if process.poll() is not None or time.monotonic() >= deadline:
                    raise RuntimeError(f'Missing ROS data; see {log_path}')
            origin = pose
            command_for(2, z=-0.2)
            submerged = pose
            command_for(3, x=0.3)
            moved = pose
            command_for(0.6)
            before_yaw = yaw
            command_for(1.5, turn=0.5)
            after_yaw = yaw
            command_for(0.6)
            stopped = pose
            command_for(1)
            checks = {
                'clock_and_odom': counts['clock'] > 10 and counts['odom'] > 10,
                'dive': submerged[2] < origin[2] - 0.15,
                'forward': moved[0] > submerged[0] + 0.3,
                'turn': abs(math.atan2(math.sin(after_yaw - before_yaw),
                                       math.cos(after_yaw - before_yaw))) > 0.2,
                'stop': math.dist(stopped, pose) < 0.05,
            }
            if not args.no_cameras:
                checks['cameras'] = all(counts[k] > 2 and frames[k]['width'] == 640
                                        and frames[k]['height'] == 480 for k in ('front', 'bottom'))
            result.update(checks=checks, origin=origin, submerged=submerged, moved=moved,
                          final=pose, yaw_change=after_yaw - before_yaw, passed=all(checks.values()))
        except Exception as exc:
            result['error'] = str(exc)
        finally:
            pub.publish(Twist())
            process.send_signal(signal.SIGINT) if process.poll() is None else None
            try:
                process.wait(timeout=12)
            except subprocess.TimeoutExpired:
                os.killpg(process.pid, signal.SIGKILL)
                process.wait()
                result['shutdown_forced'] = True
            node.destroy_node()
            rclpy.try_shutdown()
    args.output.write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result, indent=2))
    raise SystemExit(0 if result['passed'] else 1)


if __name__ == '__main__':
    main()
