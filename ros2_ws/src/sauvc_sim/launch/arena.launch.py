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
from sauvc_sim.qualification import MAX_SPEED_SCALE


def start(context):
    arena = LaunchConfiguration('arena').perform(context)
    cameras = LaunchConfiguration('cameras').perform(context) == 'true'
    headless = LaunchConfiguration('headless').perform(context) == 'true'
    autonomous = LaunchConfiguration('autonomous').perform(context) == 'true'
    lane = int(LaunchConfiguration('lane').perform(context))
    mode = LaunchConfiguration('mode').perform(context)
    if autonomous and (arena != 'qualification' or (mode == 'vision' and not cameras)):
        raise ValueError('autonomous requires qualification; vision requires cameras')
    directory = tempfile.TemporaryDirectory(prefix='sauvc-')
    world = Path(directory.name) / f'{arena}.sdf'
    world.write_text(build_world(arena, cameras, lane,
                                float(LaunchConfiguration('lateral_offset').perform(context)),
                                float(LaunchConfiguration('yaw').perform(context))))
    actions = [
        RegisterEventHandler(OnShutdown(on_shutdown=[
            OpaqueFunction(function=lambda context: directory.cleanup()),
        ])),
        ExecuteProcess(cmd=['ign', 'gazebo', '-r', '-s', '--force-version', '6', str(world)], output='screen',
                       on_exit=Shutdown()),
        Node(package='ros_gz_bridge', executable='parameter_bridge',
             name='sauvc_bridge', output='screen',
             parameters=[{'config_file': str(Path(get_package_share_directory('sauvc_sim'))
                                            / 'config' / 'bridge.yaml')}]),
    ]
    if not headless:
        # Let launch own both processes instead of the Ruby GUI/server fork wrapper.
        actions.append(ExecuteProcess(cmd=['ign', 'gazebo', '-g', '--force-version', '6', str(world)],
                                      output='screen', on_exit=Shutdown()))
    if autonomous:
        params = {'lane': lane, 'mode': mode,
                  'speed_scale': float(LaunchConfiguration('speed_scale').perform(context)),
                  'output': LaunchConfiguration('output').perform(context),
                  'fault': LaunchConfiguration('fault').perform(context)}
        for executable in ('qualification_referee', 'command_guard', 'qualification'):
            actions.append(Node(package='sauvc_sim', executable=executable,
                                parameters=[params], output='screen', on_exit=Shutdown()))
    return actions


def generate_launch_description():
    return LaunchDescription([
        DeclareLaunchArgument('arena', default_value='qualification', choices=['qualification', 'finals']),
        DeclareLaunchArgument('headless', default_value='false', choices=['true', 'false']),
        DeclareLaunchArgument('cameras', default_value='true', choices=['true', 'false']),
        DeclareLaunchArgument('autonomous', default_value='false', choices=['true', 'false']),
        DeclareLaunchArgument('lane', default_value='1', choices=['1', '2']),
        DeclareLaunchArgument('mode', default_value='vision', choices=['vision', 'odom']),
        DeclareLaunchArgument('speed_scale', default_value=str(MAX_SPEED_SCALE)),
        DeclareLaunchArgument('lateral_offset', default_value='0.0'),
        DeclareLaunchArgument('yaw', default_value='0.0'),
        DeclareLaunchArgument('output', default_value=''),
        DeclareLaunchArgument('fault', default_value='none',
                             choices=['none', 'camera_loss', 'command_loss',
                                      'odom_loss', 'contact_loss', 'clock_loss']),
        OpaqueFunction(function=start),
    ])
