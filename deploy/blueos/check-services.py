#!/usr/bin/env python3
"""Read-only HTTP checks for the local BlueOS bench; no hardware commands."""

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import sys
import urllib.error
import urllib.request


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    base = 'http://127.0.0.1:8080'
    checks = [
        ('frontend', '/', 200, 'html'),
        ('nginx_status', '/status', 204, None),
        ('helper', '/helper/v1.0/openapi.json', 200, 'schema'),
        ('settings_service', '/bag/v1.0/openapi.json', 200, 'schema'),
        ('autopilot_manager_api', '/ardupilot-manager/v1.0/openapi.json', 200, 'schema'),
        ('serial_devices', '/ardupilot-manager/v1.0/serials', 200, 'list'),
        ('video_sources', '/mavlink-camera-manager/v4l', 200, 'list'),
        ('video_streams', '/mavlink-camera-manager/streams', 200, 'list'),
        ('system_cpu', '/system-information/system/cpu', 200, 'list'),
        ('system_memory', '/system-information/system/memory', 200, 'dict'),
        ('mavlink_rest', '/mavlink2rest/mavlink', 200, 'dict'),
        ('jetson_adapter', '/jetson-bench/health', 200, 'dict'),
        ('jetson_platform', '/system-information/platform', 200, 'dict'),
        ('jetson_temperature', '/system-information/system/temperature', 200, 'list'),
    ]
    rows = []
    for name, path, expected, kind in checks:
        row = {'name': name, 'url': base + path, 'passed': False}
        try:
            with urllib.request.urlopen(base + path, timeout=15) as response:
                body = response.read()
                row['status'] = response.status
                row['bytes'] = len(body)
                valid = response.status == expected
                if kind in ('schema', 'list', 'dict'):
                    value = json.loads(body)
                    valid = valid and isinstance(value, list if kind == 'list' else dict)
                    if kind == 'schema':
                        valid = valid and 'openapi' in value
                    if name == 'jetson_adapter':
                        valid = valid and value.get('status') == 'ok' and value.get('sensor_count', 0) > 0
                    if name == 'jetson_platform':
                        valid = valid and 'Jetson' in value.get('jetson', {}).get('model', '')
                    if name == 'jetson_temperature':
                        valid = valid and any('cpu' in sensor.get('name', '') for sensor in value)
                elif kind == 'html':
                    valid = valid and b'<html' in body.lower() and b'<script' in body.lower()
                row['passed'] = valid
        except (OSError, ValueError) as error:
            row['error'] = str(error)
        rows.append(row)
        print(f"{'PASS' if row['passed'] else 'FAIL'} {name}: {row.get('status', row.get('error'))}")
    report = {
        'checked_at': datetime.now(timezone.utc).isoformat(),
        'scope': 'HTTP, service schemas and read-only runtime data; not browser rendering or hardware operation',
        'all_passed': all(row['passed'] for row in rows),
        'checks': rows,
    }
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(report, indent=2) + '\n')
    return 0 if report['all_passed'] else 1


if __name__ == '__main__':
    sys.exit(main())
