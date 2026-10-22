"""Procedural primitive geometry; metres, z=0 at the water surface.

Reference: https://sauvc.org/rulebook/ (2026 v6.1.0).
Prop positions are fixed training choices within the diagram's zones.
"""

import argparse
import math
from pathlib import Path
import xml.etree.ElementTree as ET


WHITE = '0.92 0.94 0.96 1'
RED = '0.85 0.025 0.025 1'
GREEN = '0.025 0.8 0.08 1'
BLUE = '0.025 0.2 0.85 1'
YELLOW = '1 0.8 0.02 1'
ORANGE = '1 0.35 0.02 1'
POOL = '0.55 0.75 0.85 1'


def tag(parent, element_name, text=None, **attrs):
    child = ET.SubElement(parent, element_name, attrs)
    if text is not None:
        child.text = str(text)
    return child


def numbers(values):
    return ' '.join(f'{v:.9g}' for v in values)


def floor_z(x):
    return -1.2 - 0.032 * min(x, 25 - x)


def plugin(parent, filename, name):
    return tag(parent, 'plugin', filename=f'ignition-gazebo-{filename}-system',
               name=f'ignition::gazebo::systems::{name}')


def model(world, name, pose):
    result = tag(world, 'model', name=name)
    tag(result, 'static', 'true')
    tag(result, 'pose', numbers(pose))
    return tag(result, 'link', name='body')


def geometry(parent, shape, size):
    geom = tag(tag(parent, 'geometry'), shape)
    if shape == 'box':
        tag(geom, 'size', numbers(size))
    elif shape == 'cylinder':
        tag(geom, 'radius', size[0])
        tag(geom, 'length', size[1])
    else:
        tag(geom, 'radius', size[0])


def part(link, name, pose, shape, size, color, collision=True):
    visual = tag(link, 'visual', name=f'{name}_visual')
    tag(visual, 'pose', numbers(pose))
    geometry(visual, shape, size)
    mat = tag(visual, 'material')
    tag(mat, 'ambient', color)
    tag(mat, 'diffuse', color)
    tag(visual, 'cast_shadows', 'false')
    if collision:
        solid = tag(link, 'collision', name=name)
        tag(solid, 'pose', numbers(pose))
        geometry(solid, shape, size)


def pool(world):
    angle = math.atan(0.032)
    length = math.hypot(12.5, 0.4)
    for name, x, pitch in [('floor_start', 6.25, angle), ('floor_target', 18.75, -angle)]:
        link = model(world, name, (x - 0.05 * math.sin(pitch), 8,
                                  -1.4 - 0.05 * math.cos(pitch), 0, pitch, 0))
        part(link, 'slab', (0, 0, 0, 0, 0, 0), 'box', (length, 16, 0.1), POOL)
    for name, pose, size in [
        ('wall_start', (-0.1, 8, -0.7, 0, 0, 0), (0.2, 16.4, 2)),
        ('wall_end', (25.1, 8, -0.7, 0, 0, 0), (0.2, 16.4, 2)),
        ('wall_port', (12.5, 16.1, -0.7, 0, 0, 0), (25, 0.2, 2)),
        ('wall_starboard', (12.5, -0.1, -0.7, 0, 0, 0), (25, 0.2, 2)),
    ]:
        part(model(world, name, pose), 'wall', (0, 0, 0, 0, 0, 0), 'box', size, WHITE)
    water = model(world, 'water_surface_visual_only', (12.5, 8, 0.005, 0, 0, 0))
    part(water, 'surface', (0, 0, 0, 0, 0, 0), 'box', (25, 16, 0.005),
         '0.1 0.6 0.8 0.08', collision=False)


def gate(world, name, x, y, qualification=False):
    bottom = floor_z(x)
    height = -bottom if qualification else 1.0
    link = model(world, name, (x, y, bottom, 0, 0, 0))
    # 1.50 m CLEAR opening; 5 cm pole thickness is a modelling assumption.
    for side, offset, color in [('port', 0.775, RED), ('starboard', -0.775, GREEN)]:
        part(link, side, (0, offset, height / 2, 0, 0, 0), 'cylinder',
             (0.025, height), WHITE)
        for i in range(5):
            part(link, f'{side}_stripe_{i}', (0, offset, (i + 0.5) * height / 5, 0, 0, 0),
                 'cylinder', (0.0255, height / 10), ORANGE if qualification else color,
                 collision=False)
    part(link, 'crossbar', (0, 0, height + 0.025, 0, 0, 0), 'box', (0.05, 1.6, 0.05), WHITE)


def drum(world, name, x, y, color):
    link = model(world, name, (x, y, floor_z(x), 0, 0, 0))
    # Open top, 60 cm outer diameter and 30 cm usable depth. No solid cap.
    part(link, 'base', (0, 0, 0.01, 0, 0, 0), 'cylinder', (0.3, 0.02), color)
    for i in range(32):
        angle = 2 * math.pi * i / 32
        part(link, f'rim_{i}', (0.29 * math.cos(angle), 0.29 * math.sin(angle),
                              0.17, 0, 0, angle), 'box', (0.02, 0.059, 0.3), color)


def props(world, arena):
    if arena == 'qualification':
        for lane, y in [(1, 4), (2, 12)]:
            gate(world, f'qualification_gate_{lane}', 10, y, qualification=True)
            start = model(world, f'start_line_{lane}', (0.012, y, 0, 0, 0, 0))
            part(start, 'mark', (0, 0, 0, 0, 0, 0), 'box', (0.02, 1, 0.15), YELLOW, False)
        return
    start = model(world, 'starting_zone_1p4m', (0.7, 8, 0.015, 0, 0, 0))
    for i, (x, y, sx, sy) in enumerate([
        (-0.69, 0, 0.02, 1.4), (0.69, 0, 0.02, 1.4),
        (0, -0.69, 1.4, 0.02), (0, 0.69, 1.4, 0.02),
    ]):
        part(start, f'edge_{i}', (x, y, 0, 0, 0, 0), 'box', (sx, sy, 0.02), WHITE, False)
    gate(world, 'navigation_gate', 16, 8)
    orange = model(world, 'orange_flare', (6, 8, floor_z(6), 0, 0, 0))
    part(orange, 'pole', (0, 0, -floor_z(6) / 2, 0, 0, 0), 'cylinder',
         (0.075, -floor_z(6)), ORANGE)
    for name, x, y, color in [
        ('blue_flare', 11, 11, BLUE), ('red_flare', 14, 12, RED),
        ('yellow_flare', 12, 4, YELLOW),
    ]:
        link = model(world, name, (x, y, floor_z(x), 0, 0, 0))
        part(link, 'pole', (0, 0, 0.4, 0, 0, 0), 'cylinder', (0.008, 0.8), color)
        part(link, 'golf_ball_visual', (0, 0, 0.82135, 0, 0, 0), 'sphere',
             (0.02135,), WHITE, False)
    for i, y in enumerate((12.5, 9.5, 6.5, 3.5)):
        drum(world, f'drum_{i + 1}', 24, y, BLUE if i == 0 else RED)


def auv(world, arena, cameras):
    vehicle = tag(world, 'model', name='sauvc_auv')
    tag(vehicle, 'pose', numbers((0.3 if arena == 'qualification' else 0.7,
                                4 if arena == 'qualification' else 8, -0.05, 0, 0, 0)))
    link = tag(vehicle, 'link', name='base_link')
    # shortcut: ideal velocity control bypasses thrust/drag; replace for controller tuning.
    tag(link, 'gravity', 'false')
    inertial = tag(link, 'inertial')
    tag(inertial, 'mass', 20)
    inertia = tag(inertial, 'inertia')
    for key, value in [('ixx', 0.333333), ('iyy', 0.666667), ('izz', 0.866667)]:
        tag(inertia, key, value)
    part(link, 'hull', (0, 0, 0, 0, 0, 0), 'box', (0.6, 0.4, 0.2), YELLOW)
    part(link, 'nose', (0.305, 0, 0, 0, 0, 0), 'box', (0.01, 0.22, 0.12),
         '0.03 0.04 0.05 1', False)
    control = plugin(vehicle, 'velocity-control', 'VelocityControl')
    tag(control, 'topic', '/sauvc/cmd_vel')
    odom = plugin(vehicle, 'odometry-publisher', 'OdometryPublisher')
    tag(odom, 'odom_topic', '/sauvc/odom')
    tag(odom, 'odom_frame', 'world')
    tag(odom, 'robot_base_frame', 'sauvc_auv/base_link')
    tag(odom, 'dimensions', 3)
    tag(odom, 'odom_publish_frequency', 30)
    if cameras:
        for name, pose in [('front', (0.32, 0, 0, 0, 0, 0)),
                           ('bottom', (0, 0, -0.12, 0, math.pi / 2, 0))]:
            sensor = tag(link, 'sensor', name=f'camera_{name}', type='camera')
            tag(sensor, 'pose', numbers(pose))
            tag(sensor, 'always_on', 'true')
            tag(sensor, 'update_rate', 10)
            tag(sensor, 'topic', f'/sauvc/camera_{name}/image_raw')
            camera = tag(sensor, 'camera')
            tag(camera, 'horizontal_fov', 1.22173)
            image = tag(camera, 'image')
            tag(image, 'width', 640)
            tag(image, 'height', 480)
            tag(image, 'format', 'R8G8B8')
            clip = tag(camera, 'clip')
            tag(clip, 'near', 0.03)
            tag(clip, 'far', 30)


def build_world(arena, cameras=True):
    if arena not in ('qualification', 'finals'):
        raise ValueError('arena must be qualification or finals')
    sdf = ET.Element('sdf', version='1.9')
    world = tag(sdf, 'world', name=f'sauvc_{arena}')
    physics = tag(world, 'physics', name='physics', type='ignored')
    tag(physics, 'max_step_size', 0.002)
    tag(physics, 'real_time_factor', 1)
    for filename, name in [('physics', 'Physics'), ('user-commands', 'UserCommands'),
                           ('scene-broadcaster', 'SceneBroadcaster')]:
        plugin(world, filename, name)
    if cameras:
        tag(plugin(world, 'sensors', 'Sensors'), 'render_engine', 'ogre2')
    scene = tag(world, 'scene')
    tag(scene, 'ambient', '0.65 0.7 0.75 1')
    tag(scene, 'background', '0.12 0.22 0.32 1')
    tag(scene, 'grid', 'false')
    light = tag(world, 'light', name='pool_light', type='directional')
    tag(light, 'pose', '12 8 10 0 0 0')
    tag(light, 'diffuse', '0.9 0.9 0.9 1')
    tag(light, 'direction', '0.1 0.2 -1')
    attenuation = tag(light, 'attenuation')
    tag(attenuation, 'range', 100)
    tag(attenuation, 'constant', 1)
    gui = tag(world, 'gui', fullscreen='false')
    view = tag(gui, 'plugin', name='3D View', filename='MinimalScene')
    tag(view, 'engine', 'ogre2')
    tag(view, 'scene', 'scene')
    tag(view, 'ambient_light', '0.65 0.7 0.75')
    tag(view, 'background_color', '0.12 0.22 0.32')
    tag(view, 'camera_pose', '12.5 -12 18 0 0.732815 1.5707963')
    appearance = tag(view, 'ignition-gui')
    tag(appearance, 'property', 'false', key='showTitleBar', type='bool')
    tag(appearance, 'property', 'docked', key='state', type='string')
    for filename in ('GzSceneManager', 'InteractiveViewControl', 'CameraTracking'):
        appearance = tag(tag(gui, 'plugin', name=filename, filename=filename), 'ignition-gui')
        for key, value, kind in [('state', 'floating', 'string'), ('width', '5', 'double'),
                                 ('height', '5', 'double'), ('showTitleBar', 'false', 'bool')]:
            tag(appearance, 'property', value, key=key, type=kind)
    pool(world)
    props(world, arena)
    auv(world, arena, cameras)
    ET.indent(sdf)
    return ET.tostring(sdf, encoding='unicode', xml_declaration=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--arena', choices=['qualification', 'finals'], required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--no-cameras', action='store_true')
    args = parser.parse_args()
    args.output.write_text(build_world(args.arena, not args.no_cameras))


if __name__ == '__main__':
    main()
