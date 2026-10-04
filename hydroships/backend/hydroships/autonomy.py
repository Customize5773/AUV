"""Supervise the ROS 2 platform without loading rclpy into the web virtualenv."""
import asyncio
import contextlib
import copy
import json
import os
import signal
import time
import uuid
from collections import deque
from pathlib import Path

from auv2027_autonomy.core import DEFAULT_PLAN, SCENARIOS, TASKS, validate_plan

ROOT = Path(__file__).resolve().parents[2]


class AutonomyError(Exception):
    pass


class CommandRejected(AutonomyError):
    pass


class Autonomy:
    def __init__(self, storage):
        self.storage = storage
        self.config = storage.setting('autonomy.plan', {'revision': 1, 'plan': copy.deepcopy(DEFAULT_PLAN)})
        self.process = None
        self.reader = None
        self.stderr = None
        self.pending = {}
        self.start_pending = False
        self.guard = asyncio.Lock()
        self.status = 'stopped'
        self.error = None
        self.received = None
        self.ros = None
        self.current = None
        self.signature = None
        self.logs = deque(maxlen=30)
        self.stopping = False
        self.domain = int(os.environ.get('HYDROSHIPS_ROS_DOMAIN_ID', '0'))
        self.setup = Path(os.environ.get('HYDROSHIPS_ROS_SETUP', '/opt/ros/humble/setup.bash'))
        self.test_tasks = os.environ.get('HYDROSHIPS_ROS_TEST_TASKS', '1') == '1'
        self._interrupt('Layanan dimulai ulang; eksekusi sebelumnya tidak dilanjutkan.')

    def _interrupt(self, reason):
        for run in self.storage.runs(100):
            if run['status'] in ('starting', 'running'):
                if self.current and self.current['run_id'] == run['run_id']:
                    run = copy.deepcopy(self.current)
                run.update(status='interrupted', detail=reason, finished_at=time.time())
                for step in run.get('steps', []):
                    if step['status'] == 'running': step['status'] = 'interrupted'
                    elif step['status'] == 'pending': step['status'] = 'skipped'
                run.setdefault('events', []).append({'elapsed': run.get('elapsed', 0), 'message': reason})
                self.storage.save_run(run)
                self.current = run
                self.storage.event('autonomy.interrupted', reason, 'warning', run_id=run['run_id'])

    def save_plan(self, revision, plan):
        if self.start_pending or self.current and self.current['status'] in ('starting', 'running'):
            raise AutonomyError('Hentikan eksekusi sebelum mengubah rencana.')
        if revision != self.config['revision']:
            raise AutonomyError('Rencana telah berubah di sesi lain. Muat ulang sebelum menyimpan.')
        config = {'revision': revision + 1, 'plan': validate_plan(plan)}
        self.storage.save('autonomy.plan', config)
        self.config = config
        return config

    async def start(self):
        async with self.guard:
            if self.reader and not self.reader.done():
                return
            if not self.setup.is_file():
                self.status = 'unavailable'; self.error = f'ROS setup tidak tersedia: {self.setup}'
                raise AutonomyError(self.error)
            if not 0 <= self.domain <= 232:
                raise AutonomyError('ROS domain harus 0–232.')
            self.stopping = False
            self.status = 'starting'; self.error = None; self.received = None; self.ros = None; self.signature = None
            env = dict(os.environ, PYTHONNOUSERSITE='1', ROS_DOMAIN_ID=str(self.domain))
            # Source only the administrator-configured ROS setup; arguments never become shell code.
            command = 'source "$1" && export PYTHONPATH="$2${PYTHONPATH:+:$PYTHONPATH}" && exec /usr/bin/python3 -m auv2027_autonomy.ros --console "$3"'
            self.process = await asyncio.create_subprocess_exec(
                '/bin/bash', '--noprofile', '--norc', '-c', command, 'hydroships-ros', str(self.setup),
                str(ROOT / 'ros2_ws/src/auv2027_autonomy'), '--test-tasks' if self.test_tasks else '--external-tasks', env=env, start_new_session=True,
                stdin=asyncio.subprocess.PIPE, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE,
                limit=131072)
            self.stderr = asyncio.create_task(self._read_errors(self.process))
            self.reader = asyncio.create_task(self._read(self.process))

    async def _read_errors(self, process):
        while line := await process.stderr.readline():
            self.logs.append(line.decode(errors='replace').strip()[:400])

    async def _read(self, process):
        started = time.monotonic()
        try:
            while True:
                line = await asyncio.wait_for(process.stdout.readline(), 6)
                if not line:
                    raise AutonomyError('Proses ROS 2 berhenti.')
                try:
                    packet = json.loads(line)
                except ValueError:
                    self.logs.append(line.decode(errors='replace').strip()[:400])
                    packet = {}
                if packet.get('kind') == 'ack':
                    ack = packet['data']; future = self.pending.get(ack.get('command_id'))
                    if future and not future.done(): future.set_result(ack)
                elif packet.get('kind') == 'snapshot':
                    self.ros = packet; self.received = time.monotonic()
                    executor_age = packet.get('executor_age')
                    if executor_age is not None and executor_age > 6:
                        raise AutonomyError('Heartbeat executor misi terhenti.')
                    self.status = 'ready' if executor_age is not None and executor_age < 3 and packet.get('command_subscribers', 0) else 'starting'
                    run = (packet.get('executor') or {}).get('mission')
                    if run:
                        self._accept_run(run)
                if time.monotonic() - (self.received or started) > 6:
                    raise AutonomyError('Pembaruan ROS 2 terhenti.')
        except (Exception, asyncio.CancelledError) as exc:
            if not self.stopping:
                self.status = 'error'; self.error = str(exc) or 'Pembaruan ROS 2 timeout.'
        finally:
            await self._terminate(process)
            for future in self.pending.values():
                if not future.done(): future.set_exception(AutonomyError('Runtime ROS 2 terputus.'))
            self._interrupt('Runtime ROS 2 terputus; eksekusi dihentikan.')
            if self.stopping: self.status = 'stopped'
            self.process = None

    def _accept_run(self, run):
        # Only our bounded mission contract is persisted, never arbitrary ROS messages.
        if not isinstance(run, dict) or run.get('mode') != 'software_test' or run.get('status') not in ('running', 'succeeded', 'failed', 'aborted'):
            raise AutonomyError('Format status misi ROS 2 tidak valid.')
        uuid.UUID(run['run_id'])
        validate_plan(run['plan'])
        if len(run.get('events', [])) > 100 or len(run.get('steps', [])) > 16:
            raise AutonomyError('Status misi melebihi batas.')
        signature = (run['run_id'], run['status'], run['step_index'], len(run['events']))
        if signature != self.signature:
            self.storage.save_run(run)
            self.storage.event('autonomy.' + run['status'], run['detail'][:300],
                               'warning' if run['status'] in ('failed', 'aborted') else 'info', run_id=run['run_id'])
            self.signature = signature
            self.current = run
        elif self.current and self.current['run_id'] == run['run_id']:
            self.current = run

    async def _terminate(self, process):
        if process.returncode is None:
            with contextlib.suppress(ProcessLookupError): os.killpg(process.pid, signal.SIGTERM)
            try:
                await asyncio.wait_for(process.wait(), 3)
            except asyncio.TimeoutError:
                with contextlib.suppress(ProcessLookupError): os.killpg(process.pid, signal.SIGKILL)
                await process.wait()

    async def stop(self):
        async with self.guard:
            self.stopping = True
            if self.process: await self._terminate(self.process)
            if self.reader: await self.reader
            if self.stderr: await self.stderr
            self.status = 'stopped'

    async def command(self, data):
        if self.snapshot()['runtime']['status'] != 'ready' or not self.process:
            raise AutonomyError('Runtime ROS 2 belum siap.')
        identifier = str(uuid.uuid4())
        future = asyncio.get_running_loop().create_future()
        self.pending[identifier] = future
        try:
            self.process.stdin.write((json.dumps(dict(data, command_id=identifier)) + '\n').encode())
            await self.process.stdin.drain()
            ack = await asyncio.wait_for(future, 5)
            if not ack.get('accepted'):
                raise CommandRejected(ack.get('error', 'Perintah ditolak oleh ROS 2.'))
            return ack
        except asyncio.TimeoutError as exc:
            raise AutonomyError('Konfirmasi ROS 2 belum diterima. Periksa status; perintah tidak dikirim ulang.') from exc
        except (BrokenPipeError, ConnectionResetError) as exc:
            raise AutonomyError('Koneksi proses ROS 2 terputus. Periksa status eksekusi.') from exc
        finally:
            self.pending.pop(identifier, None)

    async def run(self, revision, scenario):
        if self.start_pending or self.current and self.current['status'] in ('starting', 'running'):
            raise AutonomyError('Eksekusi masih aktif.')
        if revision != self.config['revision']:
            raise AutonomyError('Revisi rencana berubah. Muat ulang sebelum menjalankan.')
        if scenario not in SCENARIOS:
            raise ValueError('Skenario tidak valid.')
        if self.snapshot()['runtime']['status'] != 'ready':
            raise AutonomyError('Runtime ROS 2 belum siap.')
        self.start_pending = True
        identifier = str(uuid.uuid4())
        run = {'run_id': identifier, 'mode': 'software_test', 'plan': copy.deepcopy(self.config['plan']),
               'revision': revision, 'scenario': scenario, 'status': 'starting', 'steps': [], 'step_index': 0,
               'started_at': time.time(), 'finished_at': None, 'elapsed': 0, 'events': [], 'detail': 'Menunggu konfirmasi ROS 2.'}
        self.current = run; self.storage.save_run(run)
        try:
            await self.command({'action': 'start', 'mode': 'software_test', 'run_id': identifier,
                                'plan': run['plan'], 'revision': revision, 'scenario': scenario})
            return {'run_id': identifier}
        except CommandRejected as exc:
            run.update(status='rejected', detail=str(exc), finished_at=time.time())
            self.storage.save_run(run)
            self.current = run
            raise
        except Exception:
            # A lost acknowledgement does not prove the start failed. Keep the run
            # until ROS status or a runtime failure resolves its actual outcome.
            if self.current and self.current['run_id'] == identifier and self.current['status'] == 'starting':
                self.current['detail'] = 'Konfirmasi belum diterima; periksa status ROS 2.'
                self.storage.save_run(self.current)
            raise
        finally:
            self.start_pending = False

    async def abort(self, identifier):
        return await self.command({'action': 'abort', 'run_id': identifier})

    def snapshot(self):
        age = None if self.received is None else time.monotonic() - self.received
        status = self.status
        if status == 'ready' and (age is None or age > 3): status = 'stale'
        history = [{key: run.get(key) for key in ('run_id', 'status', 'started_at', 'finished_at', 'elapsed', 'scenario')}
                   | {'name': run['plan']['name']} for run in self.storage.runs(20)]
        return {'config': self.config, 'tasks': TASKS,
                'runtime': {'status': status, 'error': self.error, 'domain': self.domain, 'age': age,
                            'pid': self.process.pid if self.process else None, 'logs': list(self.logs),
                            'task_driver': 'synthetic' if self.test_tasks else 'external'},
                'graph': (self.ros or {}).get('graph', {'nodes': [], 'topics': []}),
                'legacy': (self.ros or {}).get('legacy'), 'current': self.current, 'history': history}
