import json
import math
from types import SimpleNamespace
from unittest.mock import Mock
import pytest
from sauvc_sim.state_estimation import StateEstimator
from sauvc_sim.runtime import Runtime
from sauvc_sim.arena_runtime import ArenaRuntime


def packet(i,noise=0.):
    return dict(time=i*.05,gyro=[0.,0.,0.],accel=[0.,0.,9.81],mag=[20.,0.,-45.],
                pressure_pa=101325.,dvl=[.001+noise,-.001-noise,0.],deployment_held=True)


def test_quality_requires_enough_samples_even_with_zero_scatter():
    e=StateEstimator(calibrate_dvl=True)
    assert e.dvl_bias_uncertainty is None and not e.calibration_ready
    for i in range(199):assert e.update(packet(i))
    assert e.dvl_bias_uncertainty==0. and not e.calibration_ready
    assert e.update(packet(199)) and e.calibration_ready


def test_noisy_bias_requires_more_samples_and_freezes_after_release():
    e=StateEstimator(calibrate_dvl=True)
    for i in range(200):e.update(packet(i,.003 if i%2 else -.003))
    assert not e.calibration_ready
    for i in range(200,500):e.update(packet(i,.003 if i%2 else -.003))
    assert e.calibration_ready
    assert e.dvl_bias_uncertainty==pytest.approx(2*math.sqrt(2*.003**2/499))
    before=(e.dvl_bias[:],e.bias_m2[:],e.bias_samples,e.dvl_bias_uncertainty)
    p=packet(500);p.update(deployment_held=False,dvl=[.012,.004,0.]);e.update(p)
    assert not e.calibrating and before==(e.dvl_bias,e.bias_m2,e.bias_samples,e.dvl_bias_uncertainty)


@pytest.mark.parametrize('arena',[False,True])
def test_mission_waits_for_calibration_then_requires_steady_stream(monkeypatch,arena):
    import time
    now=[10.];monkeypatch.setattr(time,'monotonic',lambda:now[0])
    ctrl=SimpleNamespace(started=None,state='WAIT_READY' if arena else 'WAIT',command=Mock(return_value=(0.,0.,0.,0.)),change=Mock(),grip=False,release=False)
    received={key:10. for key in ('clock','odom','contacts','estimate_health','camera','referee','front','bottom')}
    n=SimpleNamespace(controller=ctrl,ctrl=ctrl,role='qualification',referee=False,physical=True,mode='vision',
                      pose=(.3,3.5,-.05,0.),first_clock=0.,t=10.,received=received,calibration_ready=False,
                      ready_since=5.,started_wall=0.,start_wall=0.,judgement={'phase':'START'},
                      state_pub=Mock(),velocity_pub=Mock(),cmd=Mock(),grip=Mock(),logged_state=ctrl.state,logged=ctrl.state,
                      detection=None,detection_time=10.,drop=lambda key:False,stale=lambda keys,t:None)
    runtime=ArenaRuntime if arena else Runtime
    runtime.tick(n)
    assert not ctrl.command.called and n.ready_since is None
    runtime.estimate_health(n,SimpleNamespace(data=json.dumps(dict(valid=True))))
    runtime.tick(n);assert not ctrl.command.called
    runtime.estimate_health(n,SimpleNamespace(data=json.dumps(dict(valid=True,dvl_calibration_ready=True))))
    runtime.tick(n);assert not ctrl.command.called
    now[0]=13.;n.t=13.;n.received={key:13. for key in received}
    runtime.tick(n);assert ctrl.command.call_count==1
    ctrl.command.reset_mock();n.calibration_ready=False;now[0]=46.;n.t=46.;n.received={key:46. for key in received}
    runtime.tick(n)
    assert not ctrl.command.called
    ctrl.change.assert_called_with('ABORT',46.,'dvl_calibration_not_ready')


def test_acceptance_requires_quality_before_thrust_and_physical_restraint():
    import importlib.util
    from pathlib import Path
    spec=importlib.util.spec_from_file_location('quality_check',Path(__file__).resolve().parents[3]/'tools/check_qualification.py')
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    ready=dict(time=2.1,valid=True,dvl_calibration_ready=True,dvl_bias_samples=500,dvl_bias_uncertainty_mps=.0003,dvl_calibrating=False)
    data=dict(dynamics=[dict(time=2.,force_n=[1.]*7)],
              trajectory=[[i*.02,0.,0.,-.05] for i in range(100)],
              health=[dict(ready,time=1.9,dvl_calibration_ready=False),ready])
    assert not module.calibration_evidence(data)['passed']
    data['health'][0]['dvl_calibration_ready']=True
    assert module.calibration_evidence(data)['passed']
    data['trajectory'][50][1]=.01
    assert not module.calibration_evidence(data)['passed']


def test_native_fault_proof_rejects_preflight_or_missing_injection():
    import importlib.util
    from pathlib import Path
    spec=importlib.util.spec_from_file_location('native_check',Path(__file__).resolve().parents[3]/'tools/check_qualification.py')
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    rows=[dict(time=12.,force_n=[0.]*7,injected_fault='dvl_loss'),
          dict(time=28.,force_n=[1.]*7,injected_fault='')]
    assert not module.native_fault_evidence(dict(dynamics=rows),'dvl_loss')['passed']
    rows[0]['injected_fault']=''
    assert not module.native_fault_evidence(dict(dynamics=rows),'dvl_loss')['passed']
    rows.append(dict(time=40.,force_n=[1.]*7,injected_fault='dvl_loss'))
    assert module.native_fault_evidence(dict(dynamics=rows),'dvl_loss')['passed']
    assert not module.native_fault_evidence(dict(dynamics=rows),'imu_loss')['passed']
