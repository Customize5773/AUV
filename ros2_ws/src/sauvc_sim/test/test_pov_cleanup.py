import importlib.util
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import tempfile
import time
import unittest


class PovCleanupTest(unittest.TestCase):
    def test_terminates_qt_child_even_when_launcher_has_exited(self):
        path=Path(__file__).resolve().parents[3]/'tools/check_arena.py'
        spec=importlib.util.spec_from_file_location('arena_checker',path)
        module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
        child_script='import signal,time;signal.signal(signal.SIGTERM,signal.SIG_IGN);print("ready",flush=True);time.sleep(30)'
        with tempfile.TemporaryDirectory() as directory:
            ready=Path(directory)/'ready.json'
            launcher_script=('import subprocess,sys,time,json;'
                f'p=subprocess.Popen([sys.executable,"-c",{child_script!r}],stdout=subprocess.PIPE,text=True);'
                'p.stdout.readline();'
                f'open({str(ready)!r},"w").write(json.dumps(p.pid));'
                'time.sleep(30)')
            launcher=subprocess.Popen([sys.executable,'-c',launcher_script],start_new_session=True)
            try:
                deadline=time.monotonic()+5
                while not ready.exists() and time.monotonic()<deadline:time.sleep(.01)
                self.assertTrue(ready.exists())
                child=json.loads(ready.read_text())
                self.assertIn(launcher.pid,module.stop_viewers([launcher]))
                self.assertIsNotNone(launcher.poll())
                deadline=time.monotonic()+2
                def running():
                    p=Path(f'/proc/{child}/stat')
                    return p.exists() and p.read_text().split(') ',1)[1][0]!='Z'
                while running() and time.monotonic()<deadline:time.sleep(.01)
                self.assertFalse(running())
            finally:
                try:os.killpg(launcher.pid,signal.SIGKILL)
                except ProcessLookupError:pass
                launcher.wait()
