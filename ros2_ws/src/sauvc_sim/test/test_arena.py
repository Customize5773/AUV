import math
import unittest
import xml.etree.ElementTree as ET

from sauvc_sim.arena import build_world, floor_z


class ArenaTest(unittest.TestCase):
    def world(self, arena):
        return ET.fromstring(build_world(arena,edition='2026')).find('world')

    def test_floor_collision_surfaces_match_depth_profile(self):
        world = self.world('finals')
        for x in (0, 6.25, 12.5, 18.75, 25):
            name = 'floor_start' if x <= 12.5 else 'floor_target'
            slab = world.find(f"model[@name='{name}']")
            px, _, pz, _, pitch, _ = map(float, slab.findtext('pose').split())
            # Top plane normal is (sin(pitch), 0, cos(pitch)).
            z = pz + (0.05 - math.sin(pitch) * (x - px)) / math.cos(pitch)
            self.assertAlmostEqual(z, floor_z(x), places=7)
        self.assertEqual(floor_z(0), -1.2)
        self.assertEqual(floor_z(12.5), -1.6)
        self.assertEqual(floor_z(25), -1.2)

    def test_qualification_lanes_and_clear_gate_width(self):
        world = self.world('qualification')
        for lane, y in [(1, 4), (2, 12)]:
            gate = world.find(f"model[@name='qualification_gate_{lane}']")
            pose = list(map(float, gate.findtext('pose').split()))
            self.assertEqual(pose[:2], [10, y])
            sides = gate.findall('link/collision')[:2]
            inner = []
            for side in sides:
                lateral = float(side.findtext('pose').split()[1])
                radius = float(side.findtext('geometry/cylinder/radius'))
                inner.append(abs(lateral) - radius)
            self.assertAlmostEqual(sum(inner), 1.5)
        self.assertIsNone(world.find("model[@name='navigation_gate']"))

    def test_final_props_have_expected_zones_dimensions_and_open_drums(self):
        world = self.world('finals')
        gate = world.find("model[@name='navigation_gate']")
        self.assertEqual(float(gate.findtext('pose').split()[0]), 16)
        self.assertEqual(float(gate.findtext('link/collision/geometry/cylinder/length')), 1)
        orange = world.find("model[@name='orange_flare']")
        self.assertTrue(4 <= float(orange.findtext('pose').split()[0]) <= 8)
        for i in range(1, 5):
            drum = world.find(f"model[@name='drum_{i}']")
            self.assertTrue(23 <= float(drum.findtext('pose').split()[0]) <= 25)
            solids = drum.findall('link/collision')
            self.assertEqual(len(solids), 33)
            self.assertEqual(float(solids[0].findtext('geometry/cylinder/radius')), 0.3)
            self.assertTrue(all(s.find('geometry/box') is not None for s in solids[1:]))
            self.assertTrue(all(float(s.findtext('geometry/box/size').split()[2]) == 0.3
                                for s in solids[1:]))
        for name in ('red', 'blue', 'yellow'):
            flare = world.find(f"model[@name='{name}_flare']")
            self.assertEqual(float(flare.findtext('link/collision/geometry/cylinder/radius')), 0.008)
            self.assertEqual(float(flare.findtext('link/collision/geometry/cylinder/length')), 0.8)

    def test_visual_markers_do_not_block_vehicle(self):
        for arena in ('qualification', 'finals'):
            world = self.world(arena)
            self.assertIsNone(world.find("model[@name='water_surface_visual_only']/link/collision"))
            for marker in world.findall('model'):
                if marker.get('name').startswith(('start_line', 'starting_zone')):
                    self.assertIsNone(marker.find('link/collision'))

    def test_dynamic_balls_and_alternate_fixture(self):
        world=ET.fromstring(build_world('finals',scene_variant=1,blue_drum=3,edition='2026')).find('world')
        gate=world.find("model[@name='navigation_gate']")
        self.assertEqual(float(gate.findtext('pose').split()[1]),8.6)
        for name in ('blue_flare_ball','red_flare_ball','yellow_flare_ball','payload_ball'):
            item=world.find(f"model[@name='{name}']")
            self.assertIsNone(item.find('static'))
            self.assertEqual(item.findtext('link/gravity'),'true')
            self.assertIsNotNone(item.find('link/collision/geometry/sphere'))
        self.assertEqual(world.findtext("model[@name='drum_3']/link/visual/material/diffuse"),'0.025 0.2 0.85 1')
        with self.assertRaises(ValueError): build_world('finals',blue_drum=0,edition='2026')
        with self.assertRaises(ValueError): build_world('finals',scene_variant=2,edition='2026')

    def test_invalid_arena_rejected_and_camera_disable_removes_renderer(self):
        with self.assertRaises(ValueError):
            build_world('../unknown',edition='2026')
        world = ET.fromstring(build_world('qualification', cameras=False,edition='2026')).find('world')
        self.assertEqual(world.findall(".//sensor[@type='camera']"), [])
        self.assertEqual(len(world.findall(".//sensor[@type='contact']")), 1)
        self.assertIsNone(world.find("plugin[@name='ignition::gazebo::systems::Sensors']"))


if __name__ == '__main__':
    unittest.main()
