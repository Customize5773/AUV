import math
import unittest
import numpy as np
from sauvc_sim.gate_detection import detect_gate
from sauvc_sim.referee import QualificationJudge, envelope
from sauvc_sim.qualification import QualificationController
from sauvc_sim.vehicle_geometry import qualification_start_x

START_X=qualification_start_x(0.)


class JudgeTest(unittest.TestCase):
    def start(self):
        j = QualificationJudge()
        j.update((START_X, 4, -.05, 0), 0)
        j.update((START_X, 4, -.3, 0), 1)
        j.update((START_X, 4, -.6, 0), 3)
        return j

    def out(self, j):
        for x in np.arange(.4, 11.11, .1):
            j.update((float(x), 4, -.6, 0), 3+float(x)*3)

    def test_center_alone_is_not_full_crossing(self):
        j = self.start()
        for x in np.arange(.4, 10.11, .1):
            j.update((float(x), 4, -.6, 0), 3+x*3)
        self.assertEqual(j.phase, 'OUTBOUND')
        self.assertFalse(j.qualified)
        j.update((10.34, 4, -.6, 0), 35)
        self.assertEqual(j.phase, 'RETURN')

    def test_full_course_then_surface_and_zero_stop(self):
        j = self.start()
        self.out(j)
        for yaw in np.linspace(0, -math.pi, 70):
            j.update((11.1, 4, -.6, float(yaw)), 40+abs(yaw))
        for x in np.arange(11.1, 9.51, -.1):
            j.update((float(x), 4, -.6, -math.pi), 45+(11.1-x)*3)
        self.assertTrue(j.qualified)
        finished = j.finished
        j.update((9.6, 4, -.3, -math.pi), 52, zero_command=False)
        j.update((9.6, 4, -.05, -math.pi), 53, zero_command=False)
        self.assertFalse(j.stopped)
        for t in np.arange(54, 56, .1):
            j.update((9.6, 4, -.05, -math.pi), float(t))
        self.assertTrue(j.result()['passed'])
        self.assertEqual(j.finished, finished)
        self.assertEqual(j.result()['start_to_surface_elapsed'], 53-j.run_started)
        self.assertGreater(j.result()['start_to_stop_elapsed'], j.result()['start_to_surface_elapsed'])

    def test_reverse_without_turn_does_not_qualify(self):
        j = self.start()
        self.out(j)
        for x in np.arange(11.1, 9.51, -.1):
            j.update((float(x), 4, -.6, 0), 45+(11.1-x)*3)
        self.assertEqual(j.reason, 'return_without_u_turn')

    def test_early_surface_and_wrong_gate_and_contacts(self):
        j = self.start()
        j.update((START_X, 4, -.15, 0), 9)
        j.update((START_X, 4, -.05, 0), 10)
        self.assertEqual(j.reason, 'early_surface')
        j = self.start()
        for x in np.arange(.4, 9.61, .1):
            j.update((float(x), 4, -.6, 0), 3+x*3)
        j.update((9.7, 4.3, -.6, 0), 35)
        j.update((9.8, 4.6, -.6, 0), 36)
        self.assertEqual(j.reason, 'outside_gate_opening')
        for name in ('qualification_gate_1', 'floor_start', 'wall_port'):
            j = self.start()
            j.update((.5, 4, -.6, 0), 5, [name])
            self.assertTrue(j.reason.startswith('contact:'))

    def test_start_wall_exception_expires(self):
        j = self.start()
        j.update((START_X, 4, -.6, 0), 4, ['wall_start'])
        self.assertNotEqual(j.phase, 'FAILED')
        j.update((.5, 4, -.6, 0), 5)
        j.update((START_X, 4, -.6, 0), 6, ['wall_start'])
        self.assertEqual(j.reason, 'contact:wall_start')

    def test_preflight_wait_is_not_scored_as_an_active_run(self):
        j = QualificationJudge()
        j.update((START_X, 4, -.05, 0), 0)
        j.update((START_X, 4, -.05, 0), 20, ['wall_start'])
        self.assertEqual(j.phase, 'START')
        self.assertIsNone(j.run_started)
        j.update((START_X, 4, -.08, 0), 21)
        j.update((START_X, 4, -.08, 0), 32)
        self.assertEqual(j.reason, 'dive_timeout')

    def test_turn_before_clearance_is_not_accepted(self):
        j = self.start()
        for x in np.arange(.4, 10.11, .1):
            j.update((float(x), 4, -.6, 0), 3+x*3)
        j.update((10.1, 4, -.6, math.pi), 36)
        self.assertFalse(j.turned)
        self.assertFalse(j.qualified)

    def test_teleport_cannot_count_as_a_crossing(self):
        j = self.start()
        j.update((11, 4, -.6, 0), 40)
        self.assertEqual(j.reason, 'pose_discontinuity')

    def test_envelope_rotates_hull_without_counting_virtual_camera(self):
        flat = envelope((10, 4, -.6, 0))
        pitched = envelope((10, 4, -.6, 0, math.pi/2, 0))
        self.assertAlmostEqual(flat[1], 10.259243)
        self.assertAlmostEqual(pitched[4], -.859243)


class VisionTest(unittest.TestCase):
    def test_2027_cruise_keeps_fixed_tool_inside_gate(self):
        pose=(10.,3.5,-.5,0.)
        bounds=envelope(pose)
        self.assertGreater(bounds[4],-1.)
        self.assertLess(bounds[5],0.)
        for physical in (False,True):
            c=QualificationController(physical=physical,edition='2027')
            c.started=0.;c.state='ALIGN'
            self.assertAlmostEqual(c.command(pose,1.,dict(bearing=0.,distance=8.),0.,{})[2],0.)

    def test_dynamic_2027_approaches_only_after_submerging_and_keeps_diving(self):
        c=QualificationController(physical=True,edition='2027')
        gate=dict(bearing=0.,distance=8.)
        self.assertEqual(c.command((START_X,3.5,-.249,0.),0.,gate,0.,{})[0],0.)
        self.assertEqual(c.state,'DIVE')
        c.command((START_X,3.5,-.25,0.),.1,gate,0.,{})
        self.assertEqual(c.state,'FIND_GATE')
        command=c.command((START_X,3.5,-.26,0.),.2,gate,0.,{})
        self.assertGreater(command[0],0.)
        self.assertLess(command[2],0.)
        for physical,edition in ((False,'2027'),(True,'2026')):
            legacy=QualificationController(physical=physical,edition=edition)
            legacy.command((START_X,3.5,-.26,0.),0.,gate,0.,{})
            self.assertEqual(legacy.state,'DIVE')

    def test_distant_gate_in_dense_water_with_bright_near_floor(self):
        from pathlib import Path
        with np.load(Path(__file__).parent/'fixtures/gate-dense-water.npz') as capture:
            clear=capture['clear'];water=capture['water']
        reference=detect_gate(clear.tobytes(),640,480,1920)
        detected=detect_gate(water.tobytes(),640,480,1920)
        self.assertIsNotNone(reference)
        self.assertIsNotNone(detected)
        self.assertAlmostEqual(detected['span'],reference['span'],delta=1.)
        self.assertAlmostEqual(detected['bearing'],reference['bearing'],delta=.003)

    def test_speed_scale_changes_motion_and_rejects_invalid_limits(self):
        judge = {'phase': 'OUTBOUND', 'events': []}
        slow = QualificationController(speed_scale=1)
        fast = QualificationController(speed_scale=8)
        pose = (START_X, 4, -.05, 0)
        self.assertAlmostEqual(fast.command(pose, 0, None, 0, judge)[2],
                               8*slow.command(pose, 0, None, 0, judge)[2])
        for invalid in (0, -1, 9, math.nan, math.inf):
            with self.assertRaises(ValueError):
                QualificationController(speed_scale=invalid)

    def test_fast_approach_waits_for_alignment_and_limits_camera_gain(self):
        c = QualificationController(speed_scale=8)
        j = {'phase': 'OUTBOUND', 'events': []}
        c.command((1, 4, -.6, 0), 0, None, 100, j)
        cmd = c.command((1, 4, -.6, 0), 1, {'bearing': .1, 'distance': 2.0}, 0, j)
        self.assertEqual(cmd[0], 0)
        self.assertAlmostEqual(cmd[3], .32)

    def frame(self):
        rgb = np.zeros((480, 640, 3), dtype=np.uint8)
        for x in (270, 370):
            for y in (150, 180, 210, 240):
                rgb[y:y+8, x:x+3] = (255, 90, 5)
        return rgb

    def test_pair_range_and_bearing_and_single_post_rejection(self):
        rgb = self.frame()
        d = detect_gate(rgb.tobytes(), 640, 480, 1920)
        self.assertIsNotNone(d)
        self.assertAlmostEqual(d['bearing'], 0, delta=.01)
        self.assertTrue(6 < d['distance'] < 8)
        rgb[:, 370:373] = 0
        self.assertIsNone(detect_gate(rgb.tobytes(), 640, 480, 1920))

    def test_invalid_image_rejected(self):
        self.assertIsNone(detect_gate(b'', 640, 480, 1920))
        self.assertIsNone(detect_gate(b'', 640, 480, 1920, 'mono8'))

    def test_shaded_reverse_side_still_detected(self):
        rgb = self.frame()
        rgb[rgb[:, :, 0] > 0] = (122, 82, 14)
        self.assertIsNotNone(detect_gate(rgb.tobytes(), 640, 480, 1920))

    def test_gate_under_water_cast_keeps_range_bearing_and_encoding_contract(self):
        from sauvc_sim.water_optics import attenuate
        rgb=self.frame()
        posts=rgb[:,:,0]>0
        rgb[:]=(175,195,205);rgb[posts]=(180,95,8)
        reference=detect_gate(rgb.tobytes(),640,480,1920)
        for coefficient,distance in ((.05,12.),(.1,8.)):
            frame=attenuate(rgb,np.full((480,640),distance),coefficient)
            detected=detect_gate(frame.tobytes(),640,480,1920)
            self.assertIsNotNone(detected)
            self.assertAlmostEqual(detected['distance'],reference['distance'],places=6)
            self.assertAlmostEqual(detected['bearing'],reference['bearing'],places=6)
            padded=np.zeros((480,1940),dtype=np.uint8)
            padded[:,:1920]=frame[:,:,::-1].reshape(480,1920)
            self.assertEqual(detected,detect_gate(padded.tobytes(),640,480,1940,'bgr8'))

    def test_water_cast_does_not_turn_single_post_or_neutral_tiles_into_gate(self):
        from sauvc_sim.water_optics import attenuate
        rgb=self.frame();posts=rgb[:,:,0]>0
        rgb[:]=(175,195,205);rgb[posts]=(180,95,8)
        rgb[:,370:373]=(175,195,205)
        tile=np.full_like(rgb,(175,195,205))
        tile[:,::50]=(90,110,115);tile[::50,:]=(90,110,115)
        for original in (rgb,tile,np.full_like(rgb,(38,82,92))):
            for coefficient in (.05,.1):
                frame=attenuate(original,np.full((480,640),12.),coefficient)
                self.assertIsNone(detect_gate(frame.tobytes(),640,480,1920))

    def test_controller_stops_after_failure_and_never_surfaces_early(self):
        c = QualificationController()
        j = {'phase': 'OUTBOUND', 'events': []}
        cmd = c.command((START_X, 4, -.05, 0), 1, None, 100, j)
        self.assertLess(cmd[2], 0)
        c.command((1, 4, -.6, 0), 2, None, 100, {'phase': 'FAILED', 'reason': 'contact'})
        self.assertEqual(c.state, 'ABORT')
        self.assertEqual(c.command((1, 4, -.6, 0), 3, None, 100, j), (0, 0, 0, 0))

    def test_visual_near_field_target_comes_from_image_range(self):
        c = QualificationController()
        judge = {'phase': 'OUTBOUND', 'events': []}
        c.command((50, 20, -.6, 0), 0, None, 100, judge)
        c.command((50, 20, -.6, 0), 1, {'bearing': 0, 'distance': 1.5}, 0, judge)
        self.assertEqual(c.state, 'PASS_OUT')
        self.assertAlmostEqual(c.target[0], 51.82)

    def test_detection_loss_stops_forward_and_times_out(self):
        c = QualificationController()
        j = {'phase': 'OUTBOUND', 'events': []}
        c.command((START_X, 4, -.6, 0), 0, None, 100, j)
        cmd = c.command((START_X, 4, -.6, 0), 1, None, 100, j)
        self.assertEqual(cmd[0], 0)
        c.command((START_X, 4, -.6, 0), 10, None, 100, j)
        self.assertEqual(c.state, 'ABORT')

    def test_dynamic_gate_search_uses_physical_yaw_rate_and_keeps_loss_timeout(self):
        for scale in (1,8):
            c=QualificationController(physical=True,speed_scale=scale,edition='2027')
            j={'phase':'OUTBOUND','events':[]}
            pose=(7.7,3.5,-.6,0.)
            c.command(pose,0,None,100,j)
            c.command(pose,1,{'bearing':.05,'distance':2.},0,j)
            cmd=c.command(pose,2,None,100,j)
            self.assertAlmostEqual(cmd[3],.18)
            self.assertEqual(cmd[0],0.)
            cmd=c.command(pose,3,None,100,j)
            self.assertAlmostEqual(cmd[3],.18*math.cos(.7))
            self.assertEqual(c.command(pose,10.1,None,100,j),(0.,0.,0.,0.))
            self.assertEqual(c.reason,'gate_lost')

    def test_return_requires_image_captured_after_turn_even_if_recently_received(self):
        from types import SimpleNamespace
        from unittest.mock import patch
        from sensor_msgs.msg import Image
        from sauvc_sim.runtime import Runtime
        node=SimpleNamespace(drop=lambda key:False,received={},frames=0,detections=0)
        c=QualificationController(physical=True,edition='2027')
        c.started=0.;c.state='FIND_RETURN_GATE';c.since=5.;c.gate=(10.,3.5)
        pose=(11.7,3.5,-.6,math.pi)
        msg=Image(width=1,height=1,step=3,encoding='rgb8',data=bytes(3))
        msg.header.stamp.sec=4;msg.header.stamp.nanosec=900000000
        with patch('sauvc_sim.runtime.detect_gate',return_value=dict(bearing=.08,distance=1.4)):
            Runtime.image(node,msg)
        self.assertAlmostEqual(node.detection['stamp'],4.9)
        command=c.command(pose,5.05,node.detection,.01,{})
        self.assertEqual(c.state,'FIND_RETURN_GATE')
        self.assertIsNone(c.target)
        self.assertEqual(command[3],0.)
        msg.header.stamp.sec=5;msg.header.stamp.nanosec=50000000
        with patch('sauvc_sim.runtime.detect_gate',return_value=dict(bearing=0.,distance=1.38)):
            Runtime.image(node,msg)
        c.command(pose,5.1,node.detection,.01,{})
        self.assertEqual(c.state,'PASS_BACK')


if __name__ == '__main__':
    unittest.main()
