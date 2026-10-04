import copy
import json
import os
import signal
import time

import pytest
from fastapi.testclient import TestClient

from auv2027_autonomy.core import DEFAULT_PLAN, MissionEngine, validate_plan
from hydroships.app import create_app

HEADERS = {'X-Hydroships-Client': 'dashboard'}


def wait_for(fn, timeout=15):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        value = fn()
        if value: return value
        time.sleep(.05)
    raise AssertionError('Condition did not become true')


def test_plan_and_mission_lifecycle():
    clock = [0.0]
    engine = MissionEngine(lambda: clock[0])
    plan = copy.deepcopy(DEFAULT_PLAN)
    plan['steps'][0]['timeout'] = 2
    for bad in [None, {}, {**plan, 'unknown': 1}, {**plan, 'time_limit': float('nan')},
                {**plan, 'steps': []}, {**plan, 'steps': plan['steps'] * 9},
                {**plan, 'steps': [{'name': 'a', 'task': 'physical_arm', 'timeout': 3}]},
                {**plan, 'steps': [{'name': 'a', 'task': 'navigation', 'timeout': True}]}]:
        with pytest.raises(ValueError): validate_plan(bad)
    engine.start('one', plan, 'success', 1)
    first = engine.outbox[-1][1]
    with pytest.raises(ValueError): engine.start('two', plan, 'success', 1)
    engine.result({'run_id': 'foreign', 'request_id': first['request_id'], 'status': 'succeeded'})
    assert engine.run['step_index'] == 0
    clock[0] = 1
    engine.result({**first, 'status': 'succeeded'})
    assert engine.run['step_index'] == 1
    engine.result({**first, 'status': 'succeeded'})
    assert engine.run['step_index'] == 1  # duplicate/late result cannot finish another step
    engine.result({**engine.outbox[-1][1], 'status': 'succeeded'})
    assert engine.run['status'] == 'succeeded'
    assert all(s['status'] == 'succeeded' for s in engine.run['steps'])
    engine.start('timeout', plan, 'no_response', 1)
    request = engine.outbox[-1][1]
    clock[0] = 3  # result exactly at the timeout is rejected
    engine.result({**request, 'status': 'succeeded'})
    assert engine.run['status'] == 'failed' and 'Timeout' in engine.run['detail']
    engine.start('abort', plan, 'success', 1)
    with pytest.raises(ValueError): engine.abort('old')
    engine.abort('abort')
    assert engine.run['status'] == 'aborted'
    assert engine.outbox[-1][0] == 'cancel'
    plan['time_limit'] = 1
    engine.start('total', plan, 'success', 1)
    clock[0] += 1
    engine.tick()
    assert 'keseluruhan' in engine.run['detail']


def test_autonomy_api_validation_and_persistence(tmp_path, monkeypatch):
    monkeypatch.setenv('HYDROSHIPS_ROS_ENABLED', '0')
    with TestClient(create_app(tmp_path), base_url='http://127.0.0.1:8081') as client:
        assert client.get('/api/autonomy').json()['runtime']['status'] == 'stopped'
        assert client.put('/api/autonomy/plan', json={'revision': 1, 'plan': DEFAULT_PLAN}).status_code == 403
        saved = client.put('/api/autonomy/plan', json={'revision': 1, 'plan': DEFAULT_PLAN}, headers=HEADERS)
        assert saved.status_code == 200 and saved.json()['revision'] == 2
        assert client.put('/api/autonomy/plan', json={'revision': 1, 'plan': DEFAULT_PLAN}, headers=HEADERS).status_code == 409
        assert client.put('/api/autonomy/plan', json={'revision': 2, 'plan': {}}, headers=HEADERS).status_code == 422
        assert client.post('/api/autonomy/run', json={'revision': 2, 'mode': 'physical'}, headers=HEADERS).status_code == 422
        assert client.post('/api/autonomy/run', json={'revision': 2}, headers=HEADERS).status_code == 409
        assert client.get('/api/autonomy/runs/not-found').status_code == 404
    with TestClient(create_app(tmp_path), base_url='http://127.0.0.1:8081') as client:
        assert client.get('/api/autonomy').json()['config']['revision'] == 2


@pytest.mark.skipif(os.environ.get('HYDROSHIPS_TEST_ROS') != '1', reason='Requires installed ROS 2 Humble on Jetson')
def test_actual_ros_transport_and_failure_recovery(tmp_path, monkeypatch):
    monkeypatch.setenv('HYDROSHIPS_ROS_ENABLED', '1')
    monkeypatch.setenv('HYDROSHIPS_ROS_DOMAIN_ID', '78')
    with TestClient(create_app(tmp_path), base_url='http://127.0.0.1:8081') as client:
        state = lambda: client.get('/api/autonomy').json()
        wait_for(lambda: state()['runtime']['status'] == 'ready')
        wait_for(lambda: '/auv2027/mission_executor' in state()['graph']['nodes'])
        assert all('/cmd_vel' not in topic['name'] for topic in state()['graph']['topics'])
        plan = copy.deepcopy(DEFAULT_PLAN)
        for step in plan['steps']: step['timeout'] = 2.5
        assert client.put('/api/autonomy/plan', json={'revision': 1, 'plan': plan}, headers=HEADERS).status_code == 200
        for scenario, expected in [('success', 'succeeded'), ('failure', 'failed'), ('no_response', 'failed')]:
            response = client.post('/api/autonomy/run', json={'revision': 2, 'scenario': scenario}, headers=HEADERS)
            assert response.status_code == 200, response.text
            identifier = response.json()['run_id']
            assert client.post('/api/autonomy/run', json={'revision': 2}, headers=HEADERS).status_code == 409
            assert client.put('/api/autonomy/plan', json={'revision': 2, 'plan': plan}, headers=HEADERS).status_code == 409
            wait_for(lambda: state()['current']['status'] == expected)
            report = client.get('/api/autonomy/runs/' + identifier)
            assert report.json()['scenario'] == scenario and report.json()['mode'] == 'software_test'
            assert 'attachment' in report.headers['content-disposition']
        identifier = client.post('/api/autonomy/run', json={'revision': 2}, headers=HEADERS).json()['run_id']
        wait_for(lambda: state()['current']['status'] == 'running')
        assert client.post('/api/autonomy/abort', json={'run_id': identifier}, headers=HEADERS).status_code == 200
        wait_for(lambda: state()['current']['status'] == 'aborted')
        client.post('/api/autonomy/run', json={'revision': 2, 'scenario': 'no_response'}, headers=HEADERS)
        wait_for(lambda: state()['current']['status'] == 'running')
        os.kill(state()['runtime']['pid'], signal.SIGKILL)
        wait_for(lambda: state()['current']['status'] == 'interrupted')
        assert client.post('/api/autonomy/runtime', headers=HEADERS).status_code == 200
        wait_for(lambda: state()['runtime']['status'] == 'ready')
        assert state()['current']['status'] == 'interrupted'
        assert len(state()['history']) == 5
    with TestClient(create_app(tmp_path), base_url='http://127.0.0.1:8081') as client:
        result = client.get('/api/autonomy').json()
        assert len(result['history']) == 5 and result['config']['revision'] == 2
        assert not result['current'] or result['current']['status'] != 'running'
    # External tasks must not silently fall back to synthetic success.
    monkeypatch.setenv('HYDROSHIPS_ROS_TEST_TASKS', '0')
    with TestClient(create_app(tmp_path), base_url='http://127.0.0.1:8081') as client:
        state = lambda: client.get('/api/autonomy').json()
        wait_for(lambda: state()['runtime']['status'] == 'ready')
        wait_for(lambda: len(state()['graph']['nodes']) == 2)
        assert state()['runtime']['task_driver'] == 'external'
        assert '/auv2027/software_test_tasks' not in state()['graph']['nodes']
        assert client.post('/api/autonomy/run', json={'revision': 2, 'scenario': 'success'}, headers=HEADERS).status_code == 200
        wait_for(lambda: state()['current'] and state()['current']['status'] == 'failed')
        assert 'Timeout' in state()['current']['detail']
