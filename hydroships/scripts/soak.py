"""Read-only endurance probe; never changes a connection or parameter."""
import argparse
import json
import time
from datetime import datetime, timezone
from pathlib import Path

import httpx

parser = argparse.ArgumentParser()
parser.add_argument("--url", default="http://127.0.0.1:8081")
parser.add_argument("--seconds", type=int, default=3600)
parser.add_argument("--output", type=Path, default=Path("evidence/soak.json"))
args = parser.parse_args()
args.output.parent.mkdir(parents=True, exist_ok=True)
report = {"started_at": datetime.now(timezone.utc).isoformat(), "target_seconds": args.seconds,
          "completed": False, "samples": 0, "failures": [], "max_process_bytes": 0,
          "min_process_bytes": None, "source": None, "session": None, "elapsed_seconds": 0}
start = time.monotonic()
last_received = None
with httpx.Client(base_url=args.url, timeout=5) as client:
    while True:
        try:
            health = client.get('/api/health')
            health.raise_for_status()
            response = client.get('/api/state')
            response.raise_for_status()
            state = response.json()
            vehicle = state['vehicle']
            if report['session'] is None:
                report['session'] = vehicle['session']
                report['source'] = vehicle['connection']
                report['identity'] = vehicle['identity']
                report['initial_messages'] = vehicle['received']
            assert vehicle['session'] == report['session'], 'Session changed'
            assert vehicle['status'] == 'connected', vehicle['status']
            assert vehicle['heartbeat_age'] is not None and vehicle['heartbeat_age'] < 3, 'Stale heartbeat'
            assert vehicle['parameters']['state'] == 'complete', 'Parameter download incomplete'
            assert last_received is None or vehicle['received'] > last_received, 'No new MAVLink messages'
            last_received = vehicle['received']
            memory = state['system']['process_memory']
            report['max_process_bytes'] = max(report['max_process_bytes'], memory)
            report['min_process_bytes'] = min(report['min_process_bytes'] or memory, memory)
            report['last_messages'] = vehicle['received']
        except Exception as exc:
            report['failures'].append({'elapsed': round(time.monotonic()-start, 2), 'error': str(exc)})
        report['samples'] += 1
        report['elapsed_seconds'] = round(time.monotonic()-start, 2)
        report['completed'] = report['elapsed_seconds'] >= args.seconds
        report['ok'] = report['completed'] and not report['failures']
        temporary = args.output.with_suffix('.tmp')
        temporary.write_text(json.dumps(report, indent=2))
        temporary.replace(args.output)
        if report['completed']:
            break
        time.sleep(min(5, max(.1, args.seconds-(time.monotonic()-start))))
print(json.dumps(report, indent=2))
raise SystemExit(0 if report['ok'] else 1)
