import importlib.util
import json
from pathlib import Path
import pytest

spec=importlib.util.spec_from_file_location('native_probe',Path(__file__).resolve().parents[3]/'tools/native_transport_probe.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)


def test_protobuf_string_line_preserves_packet_and_ignores_nondata_lines():
    packet=dict(time=12.34,producer_wall_s=5678.123,sensor_publish_duration_s=.0001)
    line=('data: '+json.dumps(json.dumps(packet))).encode()
    assert m.decode(line)==packet
    assert m.decode(b'') is None and m.decode(b'CLI startup info') is None
    with pytest.raises(ValueError):m.decode(b'data: "not json"')

spec2=importlib.util.spec_from_file_location('diagnosis',Path(__file__).resolve().parents[3]/'tools/transport_diagnosis.py')
d=importlib.util.module_from_spec(spec2);spec2.loader.exec_module(d)


def observation():
    native=[];ros=[]
    for i in range(101):
        wall=i*.05
        native.append(dict(kind='heartbeat',wall_s=wall))
        ros.append(dict(kind='heartbeat',wall_s=wall))
        for kind,rows in (('native',native),('ros',ros)):
            for topic in ('sensors','dynamics/telemetry'):
                rows.append(dict(kind=kind,topic=topic,wall_s=wall,sim_s=wall,
                                 producer_wall_s=wall-.002,sensor_sequence=i,sensor_publish_duration_s=.0001))
        ros.append(dict(kind='ros',topic='state/health',wall_s=wall,sim_s=wall,sensor_age_wall_s=.01))
    return native,ros


@pytest.mark.parametrize('fault,label',[
    ('none','no_stale_sensor_event'),('producer','producer_or_simulation_stall'),
    ('bridge','bridge_or_ros_transport_delay'),('estimator','estimator_or_subscription_stall'),
    ('observer','ros_observer_delay'),('native_observer','native_observer_delay'),
    ('clock','inconclusive_clock_or_probe')])
def test_independent_signatures_and_uncertain_clock_are_distinguished(fault,label):
    native,ros=observation()
    in_gap=lambda p:1.<p['wall_s']<2.
    if fault=='producer':
        native=[p for p in native if not (in_gap(p) and p['kind']=='native')]
        ros=[p for p in ros if not (in_gap(p) and p.get('topic') in ('sensors','dynamics/telemetry'))]
        for i,p in enumerate([r for r in native if r.get('topic')=='dynamics/telemetry']):p['sensor_sequence']=i
    if fault=='bridge':ros=[p for p in ros if not (in_gap(p) and p.get('topic') in ('sensors','dynamics/telemetry'))]
    if fault in ('producer','bridge'):
        for p in ros:
            if p.get('topic')=='state/health' and in_gap(p):p['sensor_age_wall_s']=p['wall_s']-1.
    if fault=='estimator':ros=[p for p in ros if not(in_gap(p) and p.get('topic')=='state/health')]
    if fault=='observer':ros=[p for p in ros if not in_gap(p)]
    if fault=='native_observer':native=[p for p in native if not(in_gap(p) and p['kind']=='heartbeat')]
    if fault=='clock':
        for p in native:
            if 'producer_wall_s' in p:p['producer_wall_s']+=100.
    result=d.diagnose(native,ros,{},.5,2.5)
    assert result['classification']==label
    assert result['clock_basis_valid']==(fault!='clock')


def test_pov_management_excludes_unrelated_user_windows(monkeypatch):
    from types import SimpleNamespace
    path=Path(__file__).resolve().parents[3]/'tools/pov_windows.py'
    spec=importlib.util.spec_from_file_location('pov_owner',path)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    def output(cmd,**kwargs):
        if cmd[0]=='ps':return '10 1\n11 10\n22 1\n'
        if cmd[0]=='xwininfo' and '-tree' not in cmd:return 'Width: 1920\nHeight: 1080\n'
        if cmd[0]=='xwininfo':return ' 0x10 "ours": ("rqt_image_view" "rqt_image_view")\n 0x20 "user": ("rqt_image_view" "rqt_image_view")\n'
        return '_NET_WM_PID(CARDINAL) = '+('11' if cmd[2]=='0x10' else '22')
    monkeypatch.setattr(module.subprocess,'check_output',output)
    assert module.owned_windows([SimpleNamespace(pid=10)])==[16]
    messages=[];monkeypatch.setattr(module,'send',lambda *args:messages.append(args))
    assert module.arrange([SimpleNamespace(pid=10)])==[16]
    assert messages[0][0]==[16] and messages[0][1]=='_NET_MOVERESIZE_WINDOW'
