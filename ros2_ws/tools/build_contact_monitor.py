"""Build SAUVC native plugins and the camera probe against the installed Fortress ABI."""
from pathlib import Path
import shlex
import subprocess
import sys

root = Path(__file__).resolve().parents[1]
def pkg_flags(*packages):
    flags = shlex.split(subprocess.check_output(
        ['pkg-config', '--cflags', '--libs', *packages], text=True))
    local_headers = root / '.native-deps/protobuf-3.12/usr/include'
    if local_headers.exists():
        # Match the protobuf ABI of the Fortress binaries on the 24.04 host.
        flags = ['-I' + str(local_headers)] + [
            '-l:libprotobuf.so.23' if f == '-lprotobuf' else f for f in flags]
    return flags


flags = pkg_flags('ignition-gazebo6', 'ignition-plugin1', 'ignition-transport11', 'ignition-msgs8')
package = root / 'src/sauvc_sim/sauvc_sim'
for source,library in [('contact_monitor.cc','libsauvc_contact_monitor.so'),
                       ('vehicle_dynamics.cc','libsauvc_vehicle_dynamics.so')]:
    subprocess.run(['c++', '-std=c++17', '-shared', '-fPIC', '-O2',
                    str(package/source), '-o',str(package/library),*flags],check=True)

# Fortress 6.18 sensor implementation with serialized render-thread shutdown.
sensor_libs = ['camera', 'depth_camera', 'gpu_lidar', 'rgbd_camera',
               'thermal_camera', 'boundingbox_camera', 'segmentation_camera']
sensor_flags = pkg_flags('ignition-gazebo6-rendering', 'ignition-common4-events',
                         'ignition-sensors6-rendering',
                         *['ignition-sensors6-' + name for name in sensor_libs])
subprocess.run(['c++', '-std=c++17', '-shared', '-fPIC', '-O2', '-fvisibility=hidden',
                str(package/'fortress_sensors/Sensors.cc'), '-o', str(package/'libsauvc_sensors.so'),
                *sensor_flags, '-Wl,-z,defs'], check=True)

if '--check-sensor-stop' in sys.argv[1:]:
    test = root / 'build/concurrent_sensor_stop'
    test.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(['c++', '-std=c++17', '-O2', str(package.parent/'test/concurrent_sensor_stop.cc'),
                    '-o', str(test), *sensor_flags, '-pthread'], check=True)
    subprocess.run([str(test)], check=True, timeout=5)

probe = root / 'build/native_camera_probe'
probe.parent.mkdir(parents=True, exist_ok=True)
subprocess.run(['c++', '-std=c++17', '-O2', str(root/'tools/native_camera_probe.cc'),
                '-o', str(probe), *flags],check=True)
