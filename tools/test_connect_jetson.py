import unittest
from types import SimpleNamespace
from unittest.mock import patch

import connect_jetson as app


def result(code=0, out="", err=""):
    return SimpleNamespace(returncode=code, stdout=out, stderr=err)


class ConnectTest(unittest.TestCase):
    def setUp(self):
        available = patch.object(app.shutil, "which", return_value="/usr/bin/tool")
        available.start()
        self.addCleanup(available.stop)

    def test_active_hotspot_is_not_restarted_and_ssh_precedes_code(self):
        with patch.object(app, "run", side_effect=[result(out="AUV-Link\n"), result(), result()]) as run:
            app.connect()
        self.assertEqual([c.args[0] for c in run.call_args_list], ["nmcli", "ssh", "code"])
        self.assertIn("StrictHostKeyChecking=yes", run.call_args_list[1].args)

    def test_hotspot_failure_does_not_open_code(self):
        with patch.object(app, "run", side_effect=[result(out="realme Note 60"), result(1, err="activation failed")]) as run:
            with self.assertRaisesRegex(RuntimeError, "activation failed"):
                app.connect()
        self.assertEqual(run.call_count, 2)

    def test_missing_folder_and_auth_failure_do_not_open_code(self):
        for failure in (result(42), result(255, err="Permission denied"), result(255, err="Host key verification failed")):
            with self.subTest(failure=failure), patch.object(app, "run", side_effect=[result(out="AUV-Link"), failure]) as run:
                with self.assertRaises(RuntimeError):
                    app.connect()
                self.assertEqual(run.call_count, 2)

    def test_boot_delay_is_retried(self):
        with patch.object(app, "run", side_effect=[result(out="AUV-Link"), result(255, err="timeout"), result(), result()]) as run, patch.object(app.time, "sleep"):
            app.connect()
        self.assertEqual([c.args[0] for c in run.call_args_list], ["nmcli", "ssh", "ssh", "code"])

    def test_deadline_failure_does_not_open_code(self):
        with patch.object(app, "run", side_effect=[result(out="AUV-Link"), result(255, err="timeout")]) as run, patch.object(app.time, "monotonic", side_effect=[0, 1, 121]), patch.object(app.time, "sleep"):
            with self.assertRaisesRegex(RuntimeError, "timeout"):
                app.connect()
        self.assertEqual(run.call_count, 2)


if __name__ == "__main__":
    unittest.main()
