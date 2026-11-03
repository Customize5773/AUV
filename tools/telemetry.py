"""Bounded passive MAVLink capture. No heartbeat, parameter or command transmission."""
import argparse
from collections import Counter
import json
from pathlib import Path
import time


def capture(link, seconds, clock=time.monotonic):
    start = clock()
    counts = Counter()
    latest = {}
    target = None
    heartbeat_at = None
    while clock() - start < seconds:
        msg = link.recv_match(blocking=True, timeout=min(.5, max(0, seconds - (clock() - start))))
        if msg is None or msg.get_type() == 'BAD_DATA':
            continue
        kind = msg.get_type()
        source = (msg.get_srcSystem(), msg.get_srcComponent())
        if target is None and kind == 'HEARTBEAT' and msg.autopilot != 8:
            target = source
        if target is None or source != target:
            continue
        counts[kind] += 1
        if kind == 'HEARTBEAT':
            heartbeat_at = clock()
        if kind in ('HEARTBEAT', 'SYS_STATUS', 'ATTITUDE', 'SCALED_PRESSURE',
                    'SCALED_PRESSURE2', 'SERVO_OUTPUT_RAW', 'STATUSTEXT'):
            latest[kind] = {'at_seconds': clock() - start, 'data': msg.to_dict()}
    age = None if heartbeat_at is None else clock() - heartbeat_at
    return {'ok': age is not None and age < 3, 'mode': 'passive_receive_only',
            'target': target, 'heartbeat_age': age, 'messages': dict(counts), 'latest': latest}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('device', help='/dev/serial/by-id/...')
    parser.add_argument('--seconds', type=float, default=10)
    args = parser.parse_args()
    if not 1 <= args.seconds <= 60:
        parser.error('seconds must be between 1 and 60')
    if not args.device.startswith('/dev/serial/by-id/') or not Path(args.device).is_char_device():
        parser.error('select an existing stable /dev/serial/by-id/ device')
    from pymavlink import mavutil
    link = mavutil.mavlink_connection(args.device, baud=115200, autoreconnect=False)
    try:
        link.port.exclusive = True
        result = capture(link, args.seconds)
    finally:
        link.close()
    print(json.dumps(result, indent=2))
    return 0 if result['ok'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
