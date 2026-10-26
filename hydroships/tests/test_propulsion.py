import time
from types import SimpleNamespace
from hydroships.propulsion import PROFILE,expected_parameters,propulsion_state
from hydroships.storage import Storage
from hydroships.vehicle import Vehicle


def test_read_only_profile_comparison_rejects_missing_mismatch_and_old_frame():
    values={k:{'value':v} for k,v in expected_parameters().items()}
    assert len(PROFILE['thrusters'])==7
    assert propulsion_state(values,True)['mapping_status']=='match'
    values['SERVO7_FUNCTION']['value']=28
    assert propulsion_state(values,True)['different']==['SERVO7_FUNCTION']
    assert propulsion_state(values,True)['mapping_status']=='mismatch'
    del values['SERVO7_FUNCTION']
    assert propulsion_state(values,True)['mapping_status']=='waiting'
    assert propulsion_state(values,False)['mapping_status']=='unavailable'
    assert not propulsion_state(values,True)['hardware_mixer_verified']


def test_seventh_pwm_is_motor_telemetry_with_staleness(tmp_path):
    v=Vehicle(Storage(tmp_path));v.status='connected';v.target=(1,1);v.spec={'kind':'serial'}
    v.last_heartbeat=time.monotonic()
    v.params={k:{'value':value} for k,value in expected_parameters().items()}
    msg=SimpleNamespace(get_type=lambda:'SERVO_OUTPUT_RAW',get_srcSystem=lambda:1,
                        get_srcComponent=lambda:1,to_dict=lambda:{'mavpackettype':'SERVO_OUTPUT_RAW'},
                        **{f'servo{i}_raw':1490+i for i in range(1,9)})
    v._receive(msg)
    assert v.snapshot()['fields']['thruster_7_pwm']['value']==1497
    assert 'thruster_8_pwm' not in v.snapshot()['fields']
    v.params['SERVO7_FUNCTION']['value']=28
    v._receive(msg)
    assert 'thruster_7_pwm' not in v.snapshot()['fields']
    v.params['SERVO7_FUNCTION']['value']=39
    v._receive(msg)
    v.last_heartbeat-=5
    assert v.snapshot()['propulsion']['mapping_status']=='unavailable'
    v.status='disconnected'
    assert v.snapshot()['fields']['thruster_7_pwm']['stale']


def test_ros_relay_preserves_seven_motor_profile_and_expires_mapping():
    from auv2027_autonomy.telemetry import vehicle_frame
    source={'status':'connected','heartbeat_age':.1,'session':'test',
            'propulsion':propulsion_state({k:{'value':v} for k,v in expected_parameters().items()},True),
            'fields':{'thruster_7_pwm':dict(value=1500,age=.1,stale=False)}}
    fresh=vehicle_frame(source,.2)
    assert len(fresh['propulsion']['motors'])==7
    assert fresh['fields']['thruster_7_pwm']['value']==1500
    stale=vehicle_frame(source,3.)
    assert stale['propulsion']['mapping_status']=='unavailable'
    assert stale['fields']['thruster_7_pwm']['stale']
    assert source['propulsion']['mapping_status']=='match'
