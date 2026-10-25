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
    perception = LaunchConfiguration('perception').perform(context) == 'true'
    vehicle_model=LaunchConfiguration('vehicle_model').perform(context)
    physical=vehicle_model=='dynamic' or (vehicle_model=='auto' and arena=='qualification' and autonomous and mode=='vision')
    if physical and (arena!='qualification' or mode!='vision'):
        raise ValueError('dynamic vehicle currently requires qualification vision mode')
    if autonomous and ((mode == 'vision' and not cameras) or
                       (arena == 'finals' and (not cameras or not perception or mode != 'vision'))):
        raise ValueError('visual autonomous requires cameras; finals also requires perception and vision mode')
    directory = tempfile.TemporaryDirectory(prefix='sauvc-')
    world = Path(directory.name) / f'{arena}.sdf'
    world.write_text(build_world(arena, cameras, lane,
                                float(LaunchConfiguration('lateral_offset').perform(context)),
                                float(LaunchConfiguration('yaw').perform(context)),
                                int(LaunchConfiguration('scene_variant').perform(context)),
                                int(LaunchConfiguration('blue_drum').perform(context)),physical,
                                LaunchConfiguration('fault').perform(context),
                                LaunchConfiguration('extended').perform(context)=='true',
                                int(LaunchConfiguration('pinger_drum').perform(context))))
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
    if cameras and perception:
        actions.append(Node(package='sauvc_sim', executable='perception',
                            parameters=[{'arena': arena}], output='screen', on_exit=Shutdown()))
    if physical:
        for executable in ('state_estimator','propulsion'):
            actions.append(Node(package='sauvc_sim',executable=executable,parameters=[dict(
                lane=lane,lateral_offset=float(LaunchConfiguration('lateral_offset').perform(context)))],
                output='screen',on_exit=Shutdown()))
    if autonomous:
        params = {'lane': lane, 'mode': mode,
                  'physical':physical,
                  'speed_scale': float(LaunchConfiguration('speed_scale').perform(context)),
                  'output': LaunchConfiguration('output').perform(context),
                  'fault': LaunchConfiguration('fault').perform(context)}
        executables=('qualification_referee','command_guard','qualification')
        if arena == 'finals':
            params={'mission':'finals','output':LaunchConfiguration('output').perform(context),
                    'flare_order':LaunchConfiguration('flare_order').perform(context),
                    'extended':LaunchConfiguration('extended').perform(context)=='true',
                    'fault':LaunchConfiguration('fault').perform(context)}
            executables=('arena_referee','command_guard','arena_mission')
        for executable in executables:
            node_params=dict(params)
            if executable=='arena_referee':
                node_params.update(scene_variant=int(LaunchConfiguration('scene_variant').perform(context)),
                                   blue_drum=int(LaunchConfiguration('blue_drum').perform(context)),
                                   pinger_drum=int(LaunchConfiguration('pinger_drum').perform(context)))
            actions.append(Node(package='sauvc_sim', executable=executable,
                                parameters=[node_params], output='screen', on_exit=Shutdown()))
    return actions


def generate_launch_description():
    return LaunchDescription([
        DeclareLaunchArgument('arena', default_value='qualification', choices=['qualification', 'finals']),
        DeclareLaunchArgument('headless', default_value='false', choices=['true', 'false']),
        DeclareLaunchArgument('cameras', default_value='true', choices=['true', 'false']),
        DeclareLaunchArgument('perception', default_value='true', choices=['true', 'false']),
        DeclareLaunchArgument('autonomous', default_value='false', choices=['true', 'false']),
        DeclareLaunchArgument('vehicle_model',default_value='auto',choices=['auto','ideal','dynamic']),
        DeclareLaunchArgument('lane', default_value='1', choices=['1', '2']),
        DeclareLaunchArgument('mode', default_value='vision', choices=['vision', 'odom']),
        DeclareLaunchArgument('speed_scale', default_value=str(MAX_SPEED_SCALE)),
        DeclareLaunchArgument('lateral_offset', default_value='0.0'),
        DeclareLaunchArgument('yaw', default_value='0.0'),
        DeclareLaunchArgument('output', default_value=''),
        DeclareLaunchArgument('extended',default_value='false',choices=['true','false']),
        DeclareLaunchArgument('pinger_drum',default_value='0',choices=['0','1','2','3','4']),
        DeclareLaunchArgument('flare_order', default_value='B-R-Y'),
        DeclareLaunchArgument('scene_variant', default_value='0',choices=['0','1']),
        DeclareLaunchArgument('blue_drum', default_value='1',choices=['1','2','3','4']),
        DeclareLaunchArgument('fault', default_value='none',
                             choices=['none', 'camera_loss', 'command_loss',
                                      'odom_loss', 'contact_loss', 'clock_loss','imu_loss',
                                      'pressure_loss','dvl_loss','actuator_loss']),
        OpaqueFunction(function=start),
    ])
