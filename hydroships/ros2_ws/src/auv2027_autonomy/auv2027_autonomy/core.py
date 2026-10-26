"""Deterministic mission lifecycle; no ROS, vehicle I/O, or actuator commands."""
import copy
import math
import time
import uuid

TASKS = {
    'navigation': 'Navigasi gerbang',
    'acquisition': 'Akuisisi target',
    'reacquisition': 'Pengambilan kembali',
    'localization': 'Lokalisasi akustik',
}
SCENARIOS = ('success', 'failure', 'no_response')
DEFAULT_PLAN = {'name': 'Latihan alur SAUVC', 'time_limit': 90,
                'steps': [{'name': 'Lewati gerbang', 'task': 'navigation', 'timeout': 15},
                          {'name': 'Temukan target', 'task': 'acquisition', 'timeout': 15}]}


def validate_plan(plan):
    if not isinstance(plan, dict) or set(plan) != {'name', 'time_limit', 'steps'}:
        raise ValueError('Rencana harus berisi name, time_limit, dan steps.')
    name = plan['name']
    if not isinstance(name, str) or not 1 <= len(name.strip()) <= 80:
        raise ValueError('Nama misi harus 1–80 karakter.')
    def duration(value, limit):
        return type(value) in (int, float) and math.isfinite(value) and 1 <= value <= limit
    if not duration(plan['time_limit'], 1800):
        raise ValueError('Batas waktu misi harus 1–1800 detik.')
    if not isinstance(plan['steps'], list) or not 1 <= len(plan['steps']) <= 16:
        raise ValueError('Misi harus memiliki 1–16 tahap.')
    for step in plan['steps']:
        if not isinstance(step, dict) or set(step) != {'name', 'task', 'timeout'}:
            raise ValueError('Setiap tahap harus berisi name, task, dan timeout.')
        if not isinstance(step['name'], str) or not 1 <= len(step['name'].strip()) <= 80:
            raise ValueError('Nama tahap harus 1–80 karakter.')
        if not isinstance(step['task'], str) or step['task'] not in TASKS:
            raise ValueError('Jenis tugas tidak dikenal.')
        if not duration(step['timeout'], 600):
            raise ValueError('Timeout tahap harus 1–600 detik.')
    return copy.deepcopy(plan)


class MissionEngine:
    def __init__(self, clock=time.monotonic):
        self.clock = clock
        self.run = None
        self.outbox = []
        self.started = self.step_started = 0

    @property
    def active(self):
        return self.run is not None and self.run['status'] == 'running'

    def start(self, run_id, plan, scenario, revision):
        if self.active:
            raise ValueError('Misi masih berjalan.')
        if not isinstance(run_id, str) or len(run_id) > 64 or not run_id:
            raise ValueError('ID eksekusi tidak valid.')
        if scenario not in SCENARIOS:
            raise ValueError('Skenario uji tidak dikenal.')
        if type(revision) is not int or revision < 1:
            raise ValueError('Revisi tidak valid.')
        plan = validate_plan(plan)
        self.started = self.clock()
        self.run = {'run_id': run_id, 'mode': 'software_test', 'status': 'running',
                    'plan': plan, 'revision': revision, 'scenario': scenario, 'step_index': 0,
                    'steps': [{'name': s['name'], 'task': s['task'], 'status': 'pending', 'elapsed': 0} for s in plan['steps']],
                    'elapsed': 0, 'detail': '', 'started_at': time.time(), 'finished_at': None,
                    'events': [{'elapsed': 0, 'message': 'Uji software dimulai.'}]}
        self._enter_step()

    def _event(self, message):
        self.run['events'].append({'elapsed': round(self.clock() - self.started, 3), 'message': message[:300]})

    def _enter_step(self):
        index = self.run['step_index']
        self.step_started = self.clock()
        self.run['steps'][index]['status'] = 'running'
        step = self.run['plan']['steps'][index]
        self.run['detail'] = f"Menunggu hasil: {step['name']}"
        self._event(self.run['detail'])
        self.request_id = str(uuid.uuid4())
        self.outbox.append(('request', {'run_id': self.run['run_id'], 'request_id': self.request_id,
                                       'step_index': index, 'task': step['task'], 'timeout': step['timeout'],
                                       'mode': 'software_test', 'scenario': self.run['scenario']}))

    def result(self, message):
        if not self.active or not isinstance(message, dict):
            return
        if message.get('run_id') != self.run['run_id'] or message.get('request_id') != self.request_id:
            return
        # Enforce deadlines before accepting a result arriving at/after timeout.
        self.tick()
        if not self.active or message.get('status') not in ('succeeded', 'failed'):
            return
        if message['status'] == 'failed':
            self.finish('failed', str(message.get('detail', 'Modul tugas gagal.'))[:300])
            return
        index = self.run['step_index']
        self.run['steps'][index].update(status='succeeded', elapsed=round(self.clock() - self.step_started, 3))
        self._event(f"Tahap selesai: {self.run['steps'][index]['name']}")
        if index + 1 == len(self.run['steps']):
            self.finish('succeeded', 'Seluruh tahap uji software selesai.')
        else:
            self.run['step_index'] += 1
            self._enter_step()

    def tick(self):
        if not self.active:
            return
        elapsed = self.clock() - self.started
        index = self.run['step_index']
        if elapsed >= self.run['plan']['time_limit']:
            self.finish('failed', 'Batas waktu keseluruhan misi terlampaui.')
        elif self.clock() - self.step_started >= self.run['plan']['steps'][index]['timeout']:
            self.finish('failed', f"Timeout: {self.run['steps'][index]['name']}")

    def abort(self, run_id):
        if not self.active or run_id != self.run['run_id']:
            raise ValueError('Eksekusi aktif tidak cocok; muat ulang status.')
        self.finish('aborted', 'Uji dihentikan oleh operator.')

    def finish(self, status, detail):
        index = self.run['step_index']
        if self.run['steps'][index]['status'] == 'running':
            self.run['steps'][index].update(status=status, elapsed=round(self.clock() - self.step_started, 3))
        for step in self.run['steps']:
            if step['status'] == 'pending': step['status'] = 'skipped'
        self.run.update(status=status, detail=detail, elapsed=round(self.clock() - self.started, 3), finished_at=time.time())
        self._event(detail)
        self.outbox.append(('cancel', {'run_id': self.run['run_id'], 'request_id': self.request_id}))

    def snapshot(self):
        if self.run is None:
            return None
        result = copy.deepcopy(self.run)
        if self.active:
            result['elapsed'] = round(self.clock() - self.started, 3)
            result['steps'][result['step_index']]['elapsed'] = round(self.clock() - self.step_started, 3)
        return result
