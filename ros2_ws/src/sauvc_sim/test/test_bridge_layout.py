from collections import Counter
from pathlib import Path
import pytest
import yaml
from sauvc_sim.bridge_layout import bridge_groups


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
