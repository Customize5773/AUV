"""Launch one SAUVC arena, an ideal AUV, and the ROS transport bridge."""
from pathlib import Path
import tempfile

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, ExecuteProcess, OpaqueFunction, RegisterEventHandler, Shutdown
from launch.event_handlers import OnShutdown
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node

from sauvc_sim.arena import build_world


def start(context):
    arena = LaunchConfiguration('arena').perform(context)
    cameras = LaunchConfiguration('cameras').perform(context) == 'true'
    headless = LaunchConfiguration('headless').perform(context) == 'true'
    directory = tempfile.TemporaryDirectory(prefix='sauvc-')
    world = Path(directory.name) / f'{arena}.sdf'
    world.write_text(build_world(arena, cameras))
    return [
        RegisterEventHandler(OnShutdown(on_shutdown=[
            OpaqueFunction(function=lambda context: directory.cleanup()),
        ])),
        ExecuteProcess(cmd=['ign', 'gazebo', '-r', '--force-version', '6']
                       + (['-s'] if headless else []) + [str(world)], output='screen',
                       on_exit=Shutdown()),
        Node(package='ros_gz_bridge', executable='parameter_bridge',
             name='sauvc_bridge', output='screen',
             parameters=[{'config_file': str(Path(get_package_share_directory('sauvc_sim'))
                                            / 'config' / 'bridge.yaml')}]),
    ]


def generate_launch_description():
    return LaunchDescription([
        DeclareLaunchArgument('arena', default_value='qualification', choices=['qualification', 'finals']),
        DeclareLaunchArgument('headless', default_value='false', choices=['true', 'false']),
        DeclareLaunchArgument('cameras', default_value='true', choices=['true', 'false']),
        OpaqueFunction(function=start),
    ])
