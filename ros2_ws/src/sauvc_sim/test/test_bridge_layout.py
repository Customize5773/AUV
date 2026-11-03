from collections import Counter
from pathlib import Path
import pytest
import yaml
from sauvc_sim.bridge_layout import bridge_groups, camera_qos


def entries():return yaml.safe_load((Path(__file__).resolve().parents[1]/'config/bridge.yaml').read_text())


def test_isolation_preserves_every_mapping_once_and_all_critical_topics():
    original=entries();groups=bridge_groups(original,'isolated')
    rows=[row for group in groups.values() for row in group]
    assert Counter(row['ros_topic_name'] for row in rows)==Counter(row['ros_topic_name'] for row in original)
    assert sum(row['ros_topic_name']=='/clock' for row in rows)==1
    assert {row['ros_topic_name'] for row in groups['sauvc_camera_bridge']}=={'/sauvc/camera_front/image_raw','/sauvc/camera_bottom/image_raw'}
    assert all(row['ros_type_name']=='sensor_msgs/msg/Image' for row in groups['sauvc_camera_bridge'])
    assert {row['ros_topic_name'] for row in groups['sauvc_bridge']} >= {'/clock','/sauvc/sensors','/sauvc/thrusters','/sauvc/cmd_vel'}
    assert all(row in original for row in rows)


def test_single_layout_preserves_legacy_config_and_input_is_not_mutated():
    original=entries();before=yaml.safe_dump(original)
    assert bridge_groups(original,'single')=={'sauvc_bridge':original}
    bridge_groups(original,'isolated')
    assert yaml.safe_dump(original)==before


def test_invalid_layout_is_rejected():
    with pytest.raises(ValueError):bridge_groups(entries(),'invalid')


def test_camera_qos_is_latest_frame_only_without_changing_critical_topics():
    groups=bridge_groups(entries(),'isolated')
    assert camera_qos(groups['sauvc_bridge'])=={}
    qos=camera_qos(groups['sauvc_camera_bridge'])
    assert len(qos)==6
    for camera in ('front','bottom'):
        prefix='qos_overrides./sauvc/camera_'+camera+'/image_raw.publisher.'
        assert qos[prefix+'reliability']=='best_effort'
        assert qos[prefix+'history']=='keep_last' and qos[prefix+'depth']==1
    assert camera_qos(entries())==qos


def test_image_shared_memory_can_hold_both_full_frames_and_keeps_udp():
    import xml.etree.ElementTree as ET
    path=Path(__file__).resolve().parents[1]/'config/fastdds-images.xml'
    root=ET.parse(path).getroot();ns={'d':'http://www.eprosima.com/XMLSchemas/fastRTPS_Profiles'}
    transports=root.findall('d:transport_descriptors/d:transport_descriptor',ns)
    shm=next(t for t in transports if t.findtext('d:type',namespaces=ns)=='SHM')
    assert int(shm.findtext('d:segment_size',namespaces=ns))>2*640*480*3
    assert any(t.findtext('d:type',namespaces=ns)=='UDPv4' for t in transports)
    refs={t.text for t in root.findall('d:participant/d:rtps/d:userTransports/d:transport_id',ns)}
    assert refs=={t.findtext('d:transport_id',namespaces=ns) for t in transports}
    assert root.findtext('d:participant/d:rtps/d:useBuiltinTransports',namespaces=ns)=='false'
