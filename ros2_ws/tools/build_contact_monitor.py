"""Compile the small Fortress contact heartbeat plugin using installed Gazebo headers."""
from pathlib import Path
import shlex
import subprocess

root = Path(__file__).resolve().parents[1]
flags = shlex.split(subprocess.check_output([
    'pkg-config', '--cflags', '--libs', 'ignition-gazebo6', 'ignition-plugin1',
    'ignition-transport11', 'ignition-msgs8'], text=True))
local_headers = root / '.native-deps/protobuf-3.12/usr/include'
if local_headers.exists():
    # Ubuntu 24.04 host with Fortress binaries from 22.04 needs matching headers/ABI.
    flags = ['-I' + str(local_headers)] + [
        '-l:libprotobuf.so.23' if f == '-lprotobuf' else f for f in flags]
package = root / 'src/sauvc_sim/sauvc_sim'
subprocess.run(['c++', '-std=c++17', '-shared', '-fPIC', '-O2',
                str(package / 'contact_monitor.cc'), '-o',
                str(package / 'libsauvc_contact_monitor.so'), *flags], check=True)
