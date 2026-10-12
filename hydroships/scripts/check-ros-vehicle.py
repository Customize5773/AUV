"""Observe the vehicle topic using system Python/ROS 2; never publish commands."""
import argparse
import json
import time
from pathlib import Path

import rclpy
from std_msgs.msg import String

parser = argparse.ArgumentParser()
parser.add_argument('--source', choices=('serial', 'demo'), default='serial')
parser.add_argument('--output', type=Path, required=True)
args = parser.parse_args()
rclpy.init()
node = rclpy.create_node('hydroships_vehicle_check')
frames = []


def receive(message):
    frame = json.loads(message.data)
    if frame['status'] == 'connected' and (frame['connection'] or {}).get('kind') == args.source:
        frames.append(frame)


node.create_subscription(String, '/auv2027/vehicle/state', receive, 1)
try:
    deadline = time.monotonic() + 20
    while len(frames) < 6 and time.monotonic() < deadline:
        rclpy.spin_once(node, timeout_sec=.2)
    assert len(frames) >= 6, 'No six live frames from the expected source within 20 seconds'
    assert all(f['schema_version'] == 1 and f['relay_age'] <= 2 and f['heartbeat_age'] < 3 for f in frames)
    assert len({f['session'] for f in frames}) == 1, 'Vehicle session changed during probe'
    assert frames[-1]['received'] > frames[0]['received'], 'MAVLink receive counter did not advance'
    assert all(key in frames[-1]['fields'] and not frames[-1]['fields'][key]['stale'] for key in ('roll', 'pitch', 'heading'))
    result = {'result': 'passed', 'topic': '/auv2027/vehicle/state', 'source': args.source,
              'frames': len(frames), 'first_received': frames[0]['received'], 'latest': frames[-1]}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2))
    print(json.dumps({'result': 'passed', 'frames': len(frames), 'source': args.source}))
finally:
    node.destroy_node()
    rclpy.shutdown()
