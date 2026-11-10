"""Software-only integration check: real ROS/perception, synthetic camera input."""
import json
from pathlib import Path
import runpy
import subprocess
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

import numpy as np


class SyntheticCapture:
    def __init__(self, *args):
        pass

    def isOpened(self):
        return True

    def read(self):
        return True, np.zeros((120, 160, 3), dtype=np.uint8)

    def release(self):
        pass


class PhysicalCameraCheckTest(unittest.TestCase):
    def test_processes_images_expires_and_shuts_down(self):
        fake_cv2 = SimpleNamespace(VideoCapture=SyntheticCapture, CAP_V4L2=200,
            COLOR_BGR2RGB=4, cvtColor=lambda frame, code: frame)
        with tempfile.TemporaryDirectory() as directory, patch.dict(sys.modules, cv2=fake_cv2):
            output = Path(directory)/'verification.json'
            script = Path(__file__).with_name('check_physical_camera.py')
            with patch.object(sys, 'argv', [str(script), '/dev/v4l/by-id/synthetic',
                    '--seconds', '5', '--output', str(output)]), \
                    patch.object(Path, 'is_char_device', return_value=True), \
                    patch.object(subprocess, 'run', return_value=SimpleNamespace(returncode=1)):
                runpy.run_path(str(script), run_name='__main__')
            result = json.loads(output.read_text())
            self.assertTrue(result['accepted'])
            self.assertGreater(result['processed'], 0)
            self.assertGreater(result['stale_messages'], 0)
            self.assertEqual(result['perception_exit'], 0)
            self.assertFalse(result['metric_geometry_validated'])


if __name__ == '__main__':
    unittest.main()
