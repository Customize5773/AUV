import importlib.util
from pathlib import Path

spec=importlib.util.spec_from_file_location('reception',Path(__file__).resolve().parents[3]/'tools/reception_monitor.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)


def test_wall_gap_is_distinct_from_simulation_gap_and_snapshot_is_stable():
    monitor=m.ReceptionMonitor()
    monitor.record('sensors',1.,10.)
    monitor.record('sensors',1.01,10.01)
    monitor.record('sensors',2.,10.01)
    snapshot=monitor.summary()
    assert len(snapshot['gaps'])==1
    assert snapshot['gaps'][0]['sim_before']==snapshot['gaps'][0]['sim_after']
    assert snapshot['streams']['sensors']['max_wall_gap_s']==.99
    monitor.record('sensors',2.01,12.)
    assert snapshot['streams']['sensors']['count']==3
    assert monitor.summary()['streams']['sensors']['count']==4


def test_gap_log_is_bounded_and_counts_overflow():
    monitor=m.ReceptionMonitor()
    for i in range(1003):monitor.record('health',float(i),float(i))
    result=monitor.summary()
    assert len(result['gaps'])==1000 and result['dropped_events']==2
