import json
from types import SimpleNamespace
from sauvc_sim.fault_schedule import FaultSchedule


def command(value):
    return SimpleNamespace(linear=SimpleNamespace(x=value,y=0.,z=0.),angular=SimpleNamespace(z=0.))


def test_fault_waits_through_long_preflight_and_latches_start():
    logs=[];clock=FaultSchedule('camera_loss',8,logs.append)
    clock.observe(command(0),100.)
    clock.observe(command(float('nan')),101.)
    assert not clock.drop('camera',200.)
    clock.observe(command(1),201.)
    clock.observe(command(1),205.)
    assert not clock.drop('camera',209.)
    assert not clock.drop('odom',210.)
    assert clock.drop('camera',209.1) and clock.drop('camera',220.)
    assert len(logs)==1 and json.loads(logs[0].split(' ',1)[1])['started_s']==201.


def test_clock_loss_remains_active_when_consumer_clock_freezes():
    clock=FaultSchedule('clock_loss',12,lambda _:None)
    clock.observe(command(1),30.)
    assert not clock.drop('clock',42.)
    assert clock.drop('clock',42.01) and clock.drop('clock',43.)


def test_disabled_fault_does_not_drop():
    clock=FaultSchedule('none',8,lambda _:None)
    clock.observe(command(1),1.)
    assert not clock.drop('camera',100.)


def test_runtime_proof_rejects_missing_or_preflight_fault():
    import importlib.util
    from pathlib import Path
    spec=importlib.util.spec_from_file_location('runtime_fault_check',Path(__file__).resolve().parents[3]/'tools/check_qualification.py')
    m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
    dynamics=[dict(time=30.,force_n=[1.]*7)]
    event=dict(fault='camera_loss',started_s=30.,injected_s=38.1)
    log=lambda: 'prefix FAULT_INJECTED '+json.dumps(event)
    assert m.runtime_fault_evidence(log(),'camera_loss',dynamics,8)['passed']
    assert not m.runtime_fault_evidence('','camera_loss',dynamics,8)['passed']
    assert not m.runtime_fault_evidence(log(),'command_loss',dynamics,8)['passed']
    event.update(started_s=0.,injected_s=8.1)
    assert not m.runtime_fault_evidence(log(),'camera_loss',dynamics,8)['passed']
