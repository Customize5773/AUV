"""Read-only validation of an already connected serial ArduSub via HydroShips."""
import argparse
import hashlib
import json
import time
from pathlib import Path

import httpx

parser = argparse.ArgumentParser()
parser.add_argument('--url', default='http://127.0.0.1:8081')
parser.add_argument('--seconds', type=int, default=60)
parser.add_argument('--output', type=Path, default=Path('evidence/pixhawk'))
args = parser.parse_args()
assert 5 <= args.seconds <= 3600
args.output.mkdir(parents=True, exist_ok=True)
with httpx.Client(base_url=args.url, timeout=10) as client:
    first = client.get('/api/state').json()['vehicle']
    assert first['status'] == 'connected' and first['connection']['kind'] == 'serial'
    assert first['identity']['autopilot'] == 3 and first['identity']['vehicle_type'] == 12
    assert first['parameters']['state'] == 'complete'
    before = client.get('/api/parameters/export').content
    (args.output / 'pixhawk-before.params').write_bytes(before)
    events = client.get('/api/events?limit=1').json()['items']
    last_event = events[0]['id'] if events else 0
    samples = []
    started = time.monotonic()
    while time.monotonic() - started < args.seconds:
        vehicle = client.get('/api/state').json()['vehicle']
        samples.append({'elapsed': round(time.monotonic() - started, 3), 'vehicle': vehicle})
        time.sleep(1)
    after = client.get('/api/parameters/export').content
    (args.output / 'pixhawk-after.params').write_bytes(after)
    recent = client.get(f'/api/events?after={last_event}&limit=10000').json()['items']
    # Export comment timestamps can change; compare all parameter data rows.
    rows = lambda raw: [s for s in raw.decode().splitlines() if s and not s.startswith('#')]
    checks = {
        'serial_connected_throughout': all(s['vehicle']['status'] == 'connected' and s['vehicle']['connection']['kind'] == 'serial' for s in samples),
        'same_session': all(s['vehicle']['session'] == first['session'] for s in samples),
        'heartbeat_fresh': all(s['vehicle']['heartbeat_age'] is not None and s['vehicle']['heartbeat_age'] < 3 for s in samples),
        'disarmed_throughout': all(s['vehicle']['identity'].get('armed') is False for s in samples),
        'orientation_fresh': all(all(k in s['vehicle']['fields'] and not s['vehicle']['fields'][k]['stale'] for k in ('roll', 'pitch', 'heading')) for s in samples),
        'mavlink_counter_advanced': samples[-1]['vehicle']['received'] > first['received'],
        'parameters_complete': all(s['vehicle']['parameters']['state'] == 'complete' for s in samples),
        'parameter_rows_unchanged': rows(before) == rows(after),
        'no_parameter_write_events': not any(e['kind'].startswith('parameter.') for e in recent),
    }
    result = {'result': 'passed' if all(checks.values()) else 'failed', 'seconds': round(time.monotonic()-started, 1),
              'checks': checks, 'first': first, 'samples': samples, 'events': recent,
              'parameter_sha256': hashlib.sha256('\n'.join(rows(after)).encode()).hexdigest()}
    (args.output / 'hardware.json').write_text(json.dumps(result, indent=2))
    print(json.dumps({k: v for k, v in result.items() if k not in ('first', 'samples', 'events')}, indent=2))
    assert all(checks.values()), checks
