import math
import unittest
import numpy as np
from sauvc_sim.gate_detection import detect_gate
from sauvc_sim.referee import QualificationJudge, envelope
from sauvc_sim.qualification import QualificationController


class JudgeTest(unittest.TestCase):
    def start(self):
        j = QualificationJudge()
        j.update((.3, 4, -.05, 0), 0)
        j.update((.3, 4, -.3, 0), 1)
        j.update((.3, 4, -.6, 0), 3)
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
        j.update((.3, 4, -.15, 0), 9)
        j.update((.3, 4, -.05, 0), 10)
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
        j.update((.3, 4, -.6, 0), 4, ['wall_start'])
        self.assertNotEqual(j.phase, 'FAILED')
        j.update((.5, 4, -.6, 0), 5)
        j.update((.3, 4, -.6, 0), 6, ['wall_start'])
        self.assertEqual(j.reason, 'contact:wall_start')

    def test_preflight_wait_is_not_scored_as_an_active_run(self):
        j = QualificationJudge()
        j.update((.3, 4, -.05, 0), 0)
        j.update((.3, 4, -.05, 0), 20, ['wall_start'])
        self.assertEqual(j.phase, 'START')
        self.assertIsNone(j.run_started)
        j.update((.3, 4, -.08, 0), 21)
        j.update((.3, 4, -.08, 0), 32)
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

    def test_envelope_accounts_for_pitch_and_protruding_camera(self):
        flat = envelope((10, 4, -.6, 0))
        pitched = envelope((10, 4, -.6, 0, math.pi/2, 0))
        self.assertAlmostEqual(flat[1], 10.32)
        self.assertAlmostEqual(pitched[4], -.92)


class VisionTest(unittest.TestCase):
    def test_speed_scale_changes_motion_and_rejects_invalid_limits(self):
        judge = {'phase': 'OUTBOUND', 'events': []}
        slow = QualificationController(speed_scale=1)
        fast = QualificationController(speed_scale=8)
        pose = (.3, 4, -.05, 0)
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

    def test_controller_stops_after_failure_and_never_surfaces_early(self):
        c = QualificationController()
        j = {'phase': 'OUTBOUND', 'events': []}
        cmd = c.command((.3, 4, -.05, 0), 1, None, 100, j)
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
        c.command((.3, 4, -.6, 0), 0, None, 100, j)
        cmd = c.command((.3, 4, -.6, 0), 1, None, 100, j)
        self.assertEqual(cmd[0], 0)
        c.command((.3, 4, -.6, 0), 10, None, 100, j)
        self.assertEqual(c.state, 'ABORT')


if __name__ == '__main__':
    unittest.main()
