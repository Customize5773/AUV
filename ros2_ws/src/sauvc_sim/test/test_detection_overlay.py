import unittest
import numpy as np

from sauvc_sim.detection_overlay import annotate, unavailable_image


class OverlayTest(unittest.TestCase):
    def test_labels_boxes_centres_and_source_are_preserved(self):
        source = np.full((120, 160, 3), 50, dtype=np.uint8)
        before = source.copy()
        raw = annotate(source, 160, 120, 480, 'rgb8', [
            {'label': 'blue_drum', 'bbox': [40, 40, 100, 100], 'center_px': [69.5, 69.5]}])
        result = np.frombuffer(raw, dtype=np.uint8).reshape(source.shape)
        np.testing.assert_array_equal(source, before)
        np.testing.assert_array_equal(result[40, 40], [255, 0, 255])
        self.assertTrue(np.any(np.all(result[65:75, 65:75] == 255, axis=2)))
        self.assertTrue(np.any(np.all(result[:40] == 255, axis=2)))
        np.testing.assert_array_equal(result[110, 110], before[110, 110])

    def test_empty_detection_preserves_rgb_and_decodes_padded_bgr(self):
        source = np.full((20, 30, 3), [10, 20, 30], dtype=np.uint8)
        padded = np.zeros((20, 94), dtype=np.uint8)
        padded[:, :90] = source[:, :, ::-1].reshape(20, 90)
        self.assertEqual(annotate(padded, 30, 20, 94, 'bgr8', []), source.tobytes())

    def test_edge_boxes_and_invalid_images(self):
        source = np.zeros((20, 30, 3), dtype=np.uint8)
        self.assertEqual(len(annotate(source, 30, 20, 90, 'rgb8', [
            {'label': 'navigation_gate', 'bbox': [0, 0, 30, 20], 'center_px': [14.5, 9.5]}])), 1800)
        self.assertIsNone(annotate(b'', 30, 20, 90, 'rgb8', []))

    def test_unavailable_frame_replaces_previous_detections_with_status(self):
        raw = unavailable_image('CAMERA STALE - NO DETECTIONS')
        image = np.frombuffer(raw, dtype=np.uint8).reshape(480, 640, 3)
        self.assertTrue(image[:40].any())
        self.assertFalse(image[40:].any())


if __name__ == '__main__':
    unittest.main()
