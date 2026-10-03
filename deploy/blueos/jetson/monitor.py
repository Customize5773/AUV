#!/usr/bin/env python3
"""Read-only Jetson thermal/platform adapter for BlueOS 1.4.6."""
import json
import platform
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

THERMAL = Path('/run/jetson/thermal')
MODEL = Path('/run/jetson/model')
PEAKS = {}
LOCK = threading.Lock()


def temperatures(root=THERMAL):
    result = []
    with LOCK:
        for zone in sorted(root.glob('thermal_zone*')):
            name = (zone / 'type').read_text().strip()
            current = int((zone / 'temp').read_text()) / 1000
            if not -40 <= current <= 150:
                raise ValueError(f'Invalid sensor reading: {name}')
            critical = None
            for kind in zone.glob('trip_point_*_type'):
                if kind.read_text().strip() == 'critical':
                    critical = int(kind.with_name(kind.name.replace('_type', '_temp')).read_text()) / 1000
            PEAKS[name] = max(PEAKS.get(name, current), current)
            result.append({'name': name, 'temperature': current,
                           'maximum_temperature': PEAKS[name],
                           'critical_temperature': critical})
    if not result or not any('cpu' in item['name'].lower() for item in result):
        raise ValueError('Jetson CPU thermal sensor unavailable')
    return result


def platform_info():
    model = MODEL.read_text().rstrip('\x00\n')
    if 'Jetson' not in model:
        raise ValueError('Mounted model is not a Jetson')
    # Do not impersonate Raspberry Pi or report unsupported Pi power events.
    return {'jetson': {'model': model, 'arch': platform.machine(),
                       'thermal_source': 'Linux thermal sysfs',
                       'power_events_supported': False}}


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        try:
            if self.path == '/temperature':
                data = temperatures()
            elif self.path == '/platform':
                data = platform_info()
            elif self.path == '/health':
                data = {'status': 'ok', 'platform': platform_info(), 'sensor_count': len(temperatures())}
            else:
                self.send_json(404, {'detail': 'Unknown adapter endpoint'})
                return
            self.send_json(200, data)
        except (OSError, ValueError) as error:
            self.send_json(503, {'detail': str(error)})

    def send_json(self, status, data):
        body = json.dumps(data, allow_nan=False).encode()
        self.send_response(status)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Cache-Control', 'no-store')
        self.send_header('Content-Length', str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format, *args):
        if len(args) > 1 and str(args[1]) != '200':
            super().log_message(format, *args)


if __name__ == '__main__':
    ThreadingHTTPServer(('127.0.0.1', 9140), Handler).serve_forever()
