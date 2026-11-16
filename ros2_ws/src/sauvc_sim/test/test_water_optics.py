import copy
import unittest
import xml.etree.ElementTree as ET
import numpy as np
from sensor_msgs.msg import Image
from sauvc_sim.water_optics import attenuate,FramePairs,image
from sauvc_sim.arena import build_world
from sauvc_sim.conditions import conditions
from sauvc_sim.bridge_layout import water_camera_bridges,bridge_groups


class WaterOpticsTest(unittest.TestCase):
    def test_optics_keeps_latest_frame_best_effort_qos(self):
        from sauvc_sim.water_optics import IMAGE_QOS,PAIR_QOS
        from rclpy.qos import ReliabilityPolicy
        self.assertEqual(IMAGE_QOS.depth,1)
        self.assertEqual(IMAGE_QOS.reliability,ReliabilityPolicy.BEST_EFFORT)
        self.assertEqual(PAIR_QOS.depth,3)
        self.assertEqual(PAIR_QOS.reliability,ReliabilityPolicy.BEST_EFFORT)

    def test_zero_is_exact_and_far_objects_lose_more_red(self):
        rgb=np.full((1,3,3),240,dtype=np.uint8)
        depth=np.array([[0.,2.,10.]])
        self.assertTrue(np.array_equal(attenuate(rgb,depth,0.),rgb))
        out=attenuate(rgb,depth,.05)
        self.assertTrue(np.array_equal(out[0,0],rgb[0,0]))
        self.assertTrue(np.all(out[0,2]<out[0,1]))
        self.assertLess(out[0,2,0],out[0,2,2])
        self.assertTrue(np.array_equal(rgb,np.full_like(rgb,240)))

    def test_invalid_depth_is_bounded_and_bad_inputs_fail(self):
        rgb=np.full((1,3,3),200,dtype=np.uint8)
        out=attenuate(rgb,np.array([[np.nan,np.inf,-np.inf]]),.05)
        self.assertTrue(np.all(np.isfinite(out)))
        self.assertTrue(np.array_equal(out[0,2],rgb[0,2]))
        for coefficient in (-1.,.51,float('nan')):
            with self.assertRaises(ValueError):attenuate(rgb,np.zeros((1,3)),coefficient)
        with self.assertRaises(ValueError):attenuate(rgb,np.zeros((2,3)),.05)

    def test_exact_pairing_bounded_cache_and_missing_depth_produces_no_replay(self):
        pairs=FramePairs()
        def msg(stamp):
            m=Image();m.header.stamp.sec=stamp;return m
        self.assertIsNone(pairs.add('rgb',msg(1)))
        self.assertIsNone(pairs.add('depth',msg(2)))
        self.assertIsNone(pairs.add('rgb',msg(3)))
        rgb,depth=pairs.add('rgb',msg(2))
        self.assertEqual(rgb.header.stamp,depth.header.stamp)
        self.assertIsNone(pairs.add('depth',msg(1)))
        self.assertIsNone(pairs.add('rgb',msg(2)))
        for stamp in range(4,20):self.assertIsNone(pairs.add('rgb',msg(stamp)))
        self.assertEqual(len(pairs.pending),3)
        self.assertIsNone(pairs.add('depth',msg(3)))

    def test_strides_endianness_and_capture_header_are_preserved(self):
        rgb=Image(width=1,height=1,step=4,encoding='bgr8',data=bytes([100,150,200,9]))
        rgb.header.stamp.sec=7;rgb.header.frame_id='camera'
        depth=Image(width=1,height=1,step=8,encoding='32FC1',is_bigendian=1,
                    data=np.array([2.,9.],dtype='>f4').tobytes())
        output=image(rgb,depth,.05)
        expected=attenuate(np.array([[[200,150,100]]],dtype=np.uint8),np.array([[2.]]),.05)
        self.assertEqual(output.header,rgb.header)
        self.assertEqual(bytes(output.data),expected.tobytes())
        self.assertEqual((output.encoding,output.step),('rgb8',3))
        depth.step=3
        with self.assertRaises(ValueError):image(rgb,depth,.05)

    def test_opt_in_rgbd_and_bridges_do_not_publish_clear_images_as_raw(self):
        baseline=ET.fromstring(build_world('qualification')).find('world')
        world=ET.fromstring(build_world('qualification',test_conditions={'water_attenuation':.025})).find('world')
        for name in ('front','bottom'):
            path=f"model[@name='sauvc_auv']/link/sensor[@name='camera_{name}']"
            self.assertEqual(baseline.find(path).get('type'),'camera')
            self.assertEqual(world.find(path).get('type'),'rgbd_camera')
            self.assertEqual(world.find(path).findtext('topic'),f'/sauvc/optics/{name}')
        import yaml
        from ament_index_python.packages import get_package_share_directory
        from pathlib import Path
        entries=yaml.safe_load((Path(get_package_share_directory('sauvc_sim'))/'config/bridge.yaml').read_text())
        original=copy.deepcopy(entries);mapped=water_camera_bridges(entries)
        self.assertEqual(entries,original)
        topics={p['ros_topic_name'] for p in mapped}
        self.assertNotIn('/sauvc/camera_front/image_raw',topics)
        self.assertNotIn('/sauvc/camera_bottom/image_raw',topics)
        self.assertIn('/sauvc/optics/front/depth',topics)
        self.assertEqual(len(bridge_groups(mapped,'isolated')['sauvc_camera_bridge']),4)
        for value in (-.1,float('inf'),float('nan'),True):
            with self.assertRaises(ValueError):conditions({'water_attenuation':value})
        with self.assertRaises(ValueError):build_world('qualification',cameras=False,test_conditions={'water_attenuation':.025})
