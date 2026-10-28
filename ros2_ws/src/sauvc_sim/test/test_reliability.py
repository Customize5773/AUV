import importlib.util
from pathlib import Path


def runner():
    path=Path(__file__).resolve().parents[3]/'tools/check_reliability.py'
    spec=importlib.util.spec_from_file_location('check_reliability',path)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    return module


def test_matrix_covers_declared_conditions_without_overwriting_names():
    rows=runner().matrix()
    assert len(rows)==len({r['name'] for r in rows})==18
    assert sum(r['suite']=='qualification' for r in rows)==12
    assert any(r['conditions']['current']!=[0,0,0] for r in rows)
    assert any(r['conditions']['prior_error']!=[0,0] for r in rows)
    assert any(r['conditions']['light_scale']==.7 for r in rows)


def test_mission_success_does_not_hide_accuracy_failure():
    data=dict(passed=True,state='DONE',result=dict(passed=True),estimation_error=dict(qualification_reference_passed=False,max_xy_m=.4))
    result=runner().metrics(data)
    assert result['mission_complete'] and not result['accepted']
    assert 'accuracy_reference' in result['failed_checks']
    assert not runner().metrics({})['accepted']


def test_qualification_time_is_not_replaced_by_arena_score_time():
    data=dict(passed=True,state='DONE',result=dict(passed=True,start_to_surface_elapsed=28.,elapsed=24.,start_to_stop_elapsed=33.),estimation_error=dict(passed=True))
    result=runner().metrics(data)
    assert result['surface_s']==28. and result['qualification_s']==24. and result['stop_s']==33.
