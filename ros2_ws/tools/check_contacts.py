"""Prove the Gazebo contact monitor emits empty frames and actual hull impacts."""
import json
import os
from pathlib import Path
import signal
import subprocess
import time
import rclpy
from rclpy.qos import qos_profile_sensor_data
from ros_gz_interfaces.msg import Contacts


def main():
    output = Path('evidence/qualification-autonomous/contact-probe.json')
    output.parent.mkdir(parents=True, exist_ok=True)
    rclpy.init()
    node = rclpy.create_node('contact_probe')
    counts = {'empty': 0, 'impact': 0}
    names = set()
    def contact(msg):
        counts['impact' if msg.contacts else 'empty'] += 1
        for item in msg.contacts:
            names.add(item.collision1.name+'|'+item.collision2.name)
    node.create_subscription(Contacts, '/sauvc/contacts', contact, qos_profile_sensor_data)
    passed = False
    with output.with_suffix('.log').open('w') as log:
        proc = subprocess.Popen(['bash', 'tools/ros.sh', 'launch', 'sauvc_sim', 'arena.launch.py',
                                 'headless:=true', 'cameras:=false'], stdout=log,
                                stderr=subprocess.STDOUT, start_new_session=True)
        try:
            deadline = time.monotonic()+35
            while counts['empty'] < 10 and time.monotonic() < deadline:
                rclpy.spin_once(node, timeout_sec=.1)
            if counts['empty'] < 10:
                raise RuntimeError('no empty contact heartbeat')
            call = subprocess.run(['ign', 'service', '-s', '/world/sauvc_qualification/set_pose',
                '--reqtype', 'ignition.msgs.Pose', '--reptype', 'ignition.msgs.Boolean',
                '--timeout', '3000', '--req',
                'name: "sauvc_auv", position: {x:10 y:4.775 z:-0.6}'],
                capture_output=True, text=True, timeout=6, check=True)
            deadline = time.monotonic()+3
            while time.monotonic() < deadline:
                rclpy.spin_once(node, timeout_sec=.1)
            passed = counts['empty'] >= 10 and counts['impact'] > 0 and any(
                'qualification_gate_1' in n and 'sauvc_auv' in n for n in names)
        finally:
            if proc.poll() is None:
                proc.send_signal(signal.SIGINT)
            try:
                proc.wait(timeout=12)
            except subprocess.TimeoutExpired:
                os.killpg(proc.pid, signal.SIGKILL)
                proc.wait()
                passed = False
            node.destroy_node()
            rclpy.try_shutdown()
    report = dict(passed=passed, counts=counts, collisions=sorted(names))
    output.write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps(report, indent=2))
    raise SystemExit(0 if passed else 1)

if __name__ == '__main__':
    main()
