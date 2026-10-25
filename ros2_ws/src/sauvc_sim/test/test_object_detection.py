import json
import unittest
import numpy as np
from sauvc_sim.object_detection import detect_objects, components


class ObjectsTest(unittest.TestCase):
    def frame(self):
        return np.zeros((240, 320, 3), dtype=np.uint8)

    def detect(self, frame, camera='front', arena='finals'):
        result = detect_objects(frame.tobytes(), 320, 240, 960, 'rgb8', camera, arena)
        json.dumps(result)
        return result

    def gate(self, colours=((210, 5, 5),(5, 190, 15))):
        a = self.frame()
        for x, colour in zip((80,240), colours):
            for y in (50,75,100,125,150):
                a[y:y+8,x:x+4] = colour
        return a

    def test_navigation_gate_needs_both_striped_posts(self):
        a = self.gate()
        d = self.detect(a)['detections']
        self.assertEqual([x['label'] for x in d], ['navigation_gate'])
        self.assertAlmostEqual(d[0]['error_normalized'][0], 0, delta=.03)
        self.assertEqual(d[0]['stripe_count'], [5,5])
        a[:,240:244] = 0
        self.assertNotIn('navigation_gate', [x['label'] for x in self.detect(a)['detections']])

    def test_reverse_gate_and_shaded_stripes(self):
        a = self.gate(((5,100,8),(110,5,5)))
        self.assertIn('navigation_gate', [x['label'] for x in self.detect(a)['detections']])

    def test_solid_poles_do_not_form_a_gate(self):
        a = self.frame(); a[40:160,80:84]=(210,5,5);a[40:160,240:244]=(5,190,15)
        self.assertNotIn('navigation_gate', [x['label'] for x in self.detect(a)['detections']])

    def test_background_red_drum_does_not_shift_gate_post(self):
        a=self.gate()
        a[85:101,82:112]=(210,5,5)
        gate=next(o for o in self.detect(a)['detections'] if o['label']=='navigation_gate')
        self.assertEqual(gate['span_px'],160.)

    def test_four_flare_colours_are_distinct_and_stripes_are_not_flares(self):
        a = self.frame()
        for x, colour in [(30,(220,90,5)),(100,(5,45,210)),(180,(210,5,5)),(250,(220,190,5))]:
            a[50:180,x:x+4] = colour
        self.assertEqual({x['label'] for x in self.detect(a)['detections']},
                         {'orange_flare','blue_flare','red_flare','yellow_flare'})
        self.assertFalse(any(x['label'].endswith('_flare') for x in self.detect(self.gate())['detections']))

    def test_qualification_reuses_orange_gate_without_flare_labels(self):
        d = self.detect(self.gate(((220,90,5),(220,90,5))), arena='qualification')
        self.assertEqual([x['label'] for x in d['detections']], ['qualification_gate'])

    def test_blue_and_red_drums_from_bottom_camera(self):
        a=self.frame(); yy,xx=np.indices(a.shape[:2])
        a[(xx-90)**2+(yy-120)**2 <= 30**2]=(5,40,210)
        a[(xx-230)**2+(yy-120)**2 <= 30**2]=(210,5,5)
        d=self.detect(a,'bottom')['detections']
        self.assertEqual({x['label'] for x in d}, {'blue_drum','red_drum'})
        blue=next(x for x in d if x['label']=='blue_drum')
        self.assertEqual(blue['center_px'],[90,120])
        self.assertLess(blue['error_normalized'][0],0)
        self.assertFalse(blue['partial'])
        self.assertFalse(any(x['label'].endswith('_flare') for x in self.detect(a)['detections']))

    def test_water_full_blue_frame_partial_circle_and_small_dot_are_not_drums(self):
        for colour in ((140,191,217),(5,40,210)):
            a=self.frame();a[:]=colour
            self.assertEqual(self.detect(a,'bottom')['detections'],[])
        a=self.frame();yy,xx=np.indices(a.shape[:2])
        a[xx**2+(yy-120)**2 <= 30**2]=(5,40,210)
        a[(xx-200)**2+(yy-120)**2 <= 5**2]=(5,40,210)
        self.assertEqual(self.detect(a,'bottom')['detections'],[])

    def test_rgb_bgr_and_padded_rows_give_same_result(self):
        a=self.gate(); expected=self.detect(a)
        padded=np.zeros((240,964),dtype=np.uint8)
        padded[:,:960]=a[:,:,::-1].reshape(240,960)
        self.assertEqual(expected,detect_objects(padded.tobytes(),320,240,964,'bgr8'))

    def test_invalid_frame_and_context(self):
        for args in [(b'',320,240,960),(b'',0,240,960),(b'',320,0,960)]:
            self.assertFalse(detect_objects(*args)['valid_image'])
        self.assertFalse(detect_objects(b'',320,240,960,'mono8')['valid_image'])
        with self.assertRaises(ValueError):
            detect_objects(b'',320,240,960,camera='unknown')

    def test_dim_yellow_and_blurred_red_do_not_become_orange(self):
        a=self.frame()
        a[50:180,30:34]=(71,66,8)
        a[50:180,100:104]=(153,94,94)
        a[50:180,180:184]=(220,90,5)
        self.assertEqual({o['label'] for o in self.detect(a)['detections']},
                         {'yellow_flare','red_flare','orange_flare'})

    def test_components_preserve_thin_connected_pixels_and_separate_objects(self):
        a=np.eye(12,dtype=bool)
        self.assertEqual(components(a),[{'bbox':[0,0,12,12],'area_px':12}])
        a=np.zeros((20,30),dtype=bool);a[1:15,2]=True;a[1:15,20]=True
        self.assertEqual(len(components(a)),2)


if __name__ == '__main__':
    unittest.main()
