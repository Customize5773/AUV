import importlib.util
from pathlib import Path
import subprocess
import unittest
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('telemetry', ROOT / 'tools/telemetry.py')
telemetry = importlib.util.module_from_spec(spec)
spec.loader.exec_module(telemetry)


class OpsTest(unittest.TestCase):
    def test_invalid_operation_and_mission_rejected(self):
        for args in [('arm',), ('sim-start', 'physical'), ('camera-check', '/dev/null')]:
            result = subprocess.run(['bash', str(ROOT/'tools/auv.sh'), *args], capture_output=True)
            self.assertEqual(result.returncode, 2)

    def test_profile_is_shared_without_gui_dependency(self):
        canonical = ROOT/'config/propulsion.json'
        self.assertEqual((ROOT/'ros2_ws/src/sauvc_sim/config/propulsion.json').resolve(), canonical)
        self.assertEqual((ROOT/'GUI-prototype/backend/hydroships/propulsion.json').resolve(), canonical)

    def test_no_heartbeat_is_not_ready(self):
        ticks = iter(i*.1 for i in range(100))
        link = SimpleNamespace(recv_match=lambda **kw: None)
        self.assertFalse(telemetry.capture(link, 1, lambda: next(ticks))['ok'])

    def test_receive_only_filters_other_sources(self):
        ticks = iter(i*.05 for i in range(1000))
        def message(system):
            return SimpleNamespace(autopilot=3, get_type=lambda: 'HEARTBEAT',
                get_srcSystem=lambda: system, get_srcComponent=lambda: 1,
                to_dict=lambda: {'base_mode': 0})
        messages = iter([message(1), message(2)])
        link = SimpleNamespace(recv_match=lambda **kw: next(messages, None))
        result = telemetry.capture(link, 1, lambda: next(ticks))
        self.assertTrue(result['ok'])
        self.assertEqual(result['messages'], {'HEARTBEAT': 1})
        self.assertEqual(result['target'], (1, 1))


if __name__ == '__main__':
    unittest.main()
