"""Opening POV viewers must not throttle detection or retain stale detections."""
import json
from types import SimpleNamespace
from unittest import TestCase
from unittest.mock import Mock, patch
from sensor_msgs.msg import Image
from sauvc_sim.perception import Perception
from sauvc_sim.tracking import Tracker


class PovTest(TestCase):
    def node(self):
        node=SimpleNamespace(arena='finals',last_received={},last_overlay={},
            trackers={'front':Tracker()},info={'front':Mock()},
            publishers_by_camera={'front':Mock()},annotated={'front':Mock()},
            unavailable=Mock())
        node.annotated['front'].get_subscription_count.return_value=2
        node.publish=lambda camera,result:Perception.publish(node,camera,result)
        return node

    def test_viewers_do_not_throttle_detection_and_preserve_source_stamp(self):
        node=self.node()
        with patch('sauvc_sim.perception.time.monotonic') as clock:
            for i,now in enumerate([100.,100.1,100.21]):
                clock.return_value=now
                msg=Image(width=20,height=20,step=60,encoding='rgb8',data=bytes(1200))
                msg.header.stamp.sec=i
                Perception.image(node,msg,'front')
        reports=[json.loads(c.args[0].data) for c in node.publishers_by_camera['front'].publish.call_args_list]
        self.assertEqual([r['stamp']['sec'] for r in reports],[0,1,2])
        self.assertTrue(all(r['fresh'] and r['valid_image'] for r in reports))
        overlays=node.annotated['front'].publish.call_args_list
        self.assertEqual([c.args[0].header.stamp.sec for c in overlays],[0,2])
        self.assertEqual(bytes(overlays[-1].args[0].data),bytes(1200))

    def test_missing_camera_still_clears_detections_with_viewers(self):
        node=self.node();node.last_received['front']=100.
        with patch('sauvc_sim.perception.time.monotonic',return_value=101.1):
            Perception.expire(node)
        result=json.loads(node.publishers_by_camera['front'].publish.call_args.args[0].data)
        self.assertFalse(result['fresh']);self.assertEqual(result['detections'],[])
        node.unavailable.assert_called_once_with('front','CAMERA STALE - NO DETECTIONS')
