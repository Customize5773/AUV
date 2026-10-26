"""Verify unit conversion and failure handling against synthetic thermal sysfs."""
import tempfile
import unittest
from pathlib import Path
import monitor


class ThermalTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.zone = self.root / 'thermal_zone0'
        self.zone.mkdir()
        (self.zone / 'type').write_text('cpu-thermal\n')
        (self.zone / 'temp').write_text('54250\n')
        monitor.PEAKS.clear()

    def test_conversion_trip_point_and_peak(self):
        (self.zone / 'trip_point_1_type').write_text('critical\n')
        (self.zone / 'trip_point_1_temp').write_text('105000\n')
        first = monitor.temperatures(self.root)[0]
        self.assertEqual(first['temperature'], 54.25)
        self.assertEqual(first['critical_temperature'], 105)
        (self.zone / 'temp').write_text('51000\n')
        self.assertEqual(monitor.temperatures(self.root)[0]['maximum_temperature'], 54.25)

    def test_missing_limit_is_unknown(self):
        self.assertIsNone(monitor.temperatures(self.root)[0]['critical_temperature'])

    def test_invalid_or_missing_sensor_fails(self):
        (self.zone / 'temp').write_text('999999\n')
        with self.assertRaises(ValueError): monitor.temperatures(self.root)
        (self.zone / 'temp').unlink()
        with self.assertRaises(OSError): monitor.temperatures(self.root)

    def test_empty_tree_fails(self):
        with tempfile.TemporaryDirectory() as root:
            with self.assertRaises(ValueError): monitor.temperatures(Path(root))


if __name__ == '__main__': unittest.main()
