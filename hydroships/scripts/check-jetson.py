"""Validate the local Jetson host; --restart also tests the disconnected service."""
import argparse
import json
import os
import platform
import sqlite3
import subprocess
import time
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

parser = argparse.ArgumentParser()
parser.add_argument('--restart', action='store_true', help='Restart and crash-test HydroShips only when disconnected')
parser.add_argument('--output', type=Path, default=Path('evidence/jetson-check.json'))
args = parser.parse_args()
root = Path(__file__).resolve().parents[1]
unit = 'hydroships.service'
report = {'started_at': datetime.now(timezone.utc).isoformat(), 'ok': False, 'checks': [], 'samples': [], 'failures': []}


def command(*argv):
    return subprocess.check_output(argv, text=True, timeout=20).strip()


def api(path):
    with urllib.request.urlopen('http://127.0.0.1:8081/api/' + path, timeout=5) as response:
        return json.load(response)


def service():
    output = command('systemctl', '--user', 'show', unit, '-p', 'MainPID', '-p', 'ActiveState',
                     '-p', 'NRestarts', '-p', 'ExecMainStartTimestampMonotonic', '-p', 'Restart')
    return dict(line.split('=', 1) for line in output.splitlines())


def check(condition, label):
    if not condition:
        raise AssertionError(label)
    if label not in report['checks']:
        report['checks'].append(label)


def disconnected():
    vehicle = api('state')['vehicle']
    check(vehicle['status'] == 'disconnected' and vehicle['connection'] is None,
          'No vehicle connection before lifecycle test')


try:
    report['boot_id'] = Path('/proc/sys/kernel/random/boot_id').read_text().strip()
    report['architecture'] = platform.machine()
    report['model'] = Path('/proc/device-tree/model').read_text().rstrip('\0\n')
    report['l4t'] = Path('/etc/nv_tegra_release').read_text().strip()
    check(report['architecture'] == 'aarch64' and 'Jetson' in report['model'], 'Native Jetson ARM64 host')
    report['service_before'] = before = service()
    pid = int(before['MainPID'])
    check(before['ActiveState'] == 'active' and pid > 0, 'HydroShips systemd service active')
    report['process'] = {'pid': pid, 'executable': os.readlink(f'/proc/{pid}/exe'),
                         'command': Path(f'/proc/{pid}/cmdline').read_bytes().replace(b'\0', b' ').decode(),
                         'cgroup': Path(f'/proc/{pid}/cgroup').read_text().strip()}
    check(os.readlink(f'/proc/{pid}/ns/mnt') == os.readlink('/proc/self/ns/mnt'), 'App shares local host mount namespace')
    check('hydroships.service' in report['process']['cgroup'] and '-m hydroships' in report['process']['command'], 'Local service process identified')
    report['enabled'] = command('systemctl', '--user', 'is-enabled', unit)
    report['linger'] = command('loginctl', 'show-user', str(os.getuid()), '-p', 'Linger')
    check(report['enabled'] == 'enabled' and report['linger'] == 'Linger=yes', 'Startup enabled with user lingering')
    report['service_start_seconds_after_boot'] = int(before['ExecMainStartTimestampMonotonic']) / 1_000_000
    meminfo = dict(line.split(':', 1) for line in Path('/proc/meminfo').read_text().splitlines())
    total_memory = int(meminfo['MemTotal'].split()[0]) * 1024
    disk = os.statvfs(root / '.data')
    sample_start = time.monotonic()
    for index in range(10):
        check(api('health')['ok'], 'HTTP health and MAVLink worker healthy')
        system = api('state')['system']
        zones = { (zone / 'type').read_text().strip(): int((zone / 'temp').read_text()) / 1000
                  for zone in Path('/sys/class/thermal').glob('thermal_zone*') }
        check(system['model'] == report['model'] and system['kernel'] == platform.release(), 'API model and kernel match host')
        check(system['cpu_count'] == os.cpu_count() and 0 <= system['cpu_percent'] <= 100, 'CPU count matches host and usage is valid')
        check(system['memory']['total'] == total_memory, 'API RAM capacity matches /proc/meminfo')
        check(system['disk']['total'] == disk.f_blocks * disk.f_frsize, 'API disk capacity matches host filesystem')
        check(abs(system['uptime'] - float(Path('/proc/uptime').read_text().split()[0])) < 5, 'API uptime matches host')
        check(abs(time.time() - system['ts']) < 5, 'Host metrics refresh within five seconds')
        temperatures = system['temperatures']
        check(bool(temperatures) and {s['name'] for s in temperatures} == set(zones), 'All host thermal zones reported')
        difference = max(abs(sensor['celsius'] - zones[sensor['name']]) for sensor in temperatures)
        check(difference < 5, 'API temperatures agree with sysfs within sampling tolerance')
        report['samples'].append({'elapsed_seconds': round(time.monotonic() - sample_start, 3),
                                  'system': system, 'sysfs_temperatures': zones, 'max_temperature_difference': difference})
        if index != 9:
            time.sleep(3)
    if args.restart:
        report['lifecycle'] = []
        for action in ('restart', 'crash-recovery'):
            disconnected()
            settings = api('settings')
            previous = service()
            started = time.monotonic()
            if action == 'restart':
                command('systemctl', '--user', 'restart', unit)
            else:
                check(previous['Restart'] == 'on-failure', 'Automatic crash recovery configured')
                command('systemctl', '--user', 'kill', '--kill-who=main', '--signal=SIGKILL', unit)
            deadline = time.monotonic() + 20
            while time.monotonic() < deadline:
                current = service()
                if current['ActiveState'] == 'active' and int(current['MainPID']) > 0 and current['MainPID'] != previous['MainPID']:
                    try:
                        if api('health')['ok']:
                            break
                    except (OSError, ValueError):
                        pass
                time.sleep(.25)
            else:
                raise AssertionError(f'{action}: service did not recover within 20 seconds')
            check(api('settings') == settings, f'{action}: settings preserved')
            disconnected()
            if action == 'crash-recovery':
                check(int(current['NRestarts']) > int(previous['NRestarts']), 'systemd restarted the failed process')
            report['lifecycle'].append({'action': action, 'before': previous, 'after': current,
                                        'recovery_seconds': round(time.monotonic() - started, 3), 'settings_preserved': True})
    with sqlite3.connect((root / '.data/hydroships.sqlite3').as_uri() + '?mode=ro', uri=True) as db:
        report['sqlite_quick_check'] = db.execute('PRAGMA quick_check').fetchall()
    check(report['sqlite_quick_check'] == [('ok',)], 'SQLite integrity check passes')
    report['service_after'] = service()
    report['controlled_host_reboot_tested'] = False
    report['ok'] = True
except Exception as exc:
    report['failures'].append(str(exc))
finally:
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps({key: value for key, value in report.items() if key != 'samples'}, indent=2))
raise SystemExit(0 if report['ok'] else 1)
