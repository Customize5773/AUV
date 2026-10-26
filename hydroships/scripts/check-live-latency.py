"""Read-only receive-to-monitor latency probe, run on the backend host."""
import argparse
import json
import statistics
import time
from pathlib import Path
from websockets.sync.client import connect

parser = argparse.ArgumentParser()
parser.add_argument('--url', default='http://127.0.0.1:8081')
parser.add_argument('--samples', type=int, default=40)
parser.add_argument('--output', type=Path, required=True)
args = parser.parse_args()
assert 10 <= args.samples <= 1000
intervals, ages, sources = [], [], set()
previous = None
with connect(args.url.replace('http', 'ws', 1) + '/api/live', origin=args.url, proxy=None) as ws:
    for _ in range(args.samples):
        packet = json.loads(ws.recv(timeout=5))
        received = time.monotonic()
        vehicle = packet['vehicle']
        assert vehicle['status'] == 'connected'
        sources.add(vehicle['connection']['kind'])
        roll = vehicle['fields'].get('roll')
        assert roll and not roll['stale']
        ages.append(max(0, time.time() - roll['ts']) * 1000)
        if previous is not None: intervals.append((received - previous) * 1000)
        previous = received
result = {'samples': args.samples, 'sources': sorted(sources),
          'update_interval_ms_median': round(statistics.median(intervals), 1),
          'receive_to_client_ms_median': round(statistics.median(ages), 1),
          'receive_to_client_ms_max': round(max(ages), 1),
          'scope': 'MAVLink receipt timestamp on Jetson to WebSocket client on same host; excludes sensor sampling delay'}
args.output.parent.mkdir(parents=True, exist_ok=True)
args.output.write_text(json.dumps(result, indent=2))
print(json.dumps(result, indent=2))
