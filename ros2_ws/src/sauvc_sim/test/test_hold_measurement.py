"""Long holds must not hide earlier drift by measuring only their last 30 seconds."""
import importlib.util
from pathlib import Path
import pytest

spec=importlib.util.spec_from_file_location('hold_check',Path(__file__).resolve().parents[3]/'tools/surface_hold_check.py')
hold=importlib.util.module_from_spec(spec);spec.loader.exec_module(hold)


def observation(duration):
    return dict(trajectory=[[i*.05,i*.05*.001,0.,-.06] for i in range(int(duration/.05)+1)],
                dynamics=[dict(time=duration,force_n=[1.]*7)],hold_status=[dict(active=True)])


def test_long_window_exposes_accumulated_drift():
    data=observation(180.)
    assert hold.hold_metrics(data,30.)['passed']
    result=hold.hold_metrics(data,180.)
    assert not result['passed'] and result['max_xy_drift_m']==pytest.approx(.18)
    assert result['duration_s']==180.


def test_hold_requires_full_window_and_continuous_samples():
    assert not hold.hold_metrics(observation(30.),180.)['passed']
    data=observation(30.);data['trajectory']=[p for p in data['trajectory'] if not 10<p[0]<11]
    assert not hold.hold_metrics(data)['passed']
    for duration in (0.,-1.,float('nan'),float('inf')):
        with pytest.raises(ValueError):hold.hold_metrics(observation(30.),duration)
