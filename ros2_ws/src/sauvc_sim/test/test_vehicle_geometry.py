import math
from pathlib import Path
import unittest
import xml.etree.ElementTree as ET
from sauvc_sim.arena import build_world
from sauvc_sim.referee import envelope, QualificationJudge
from sauvc_sim.vehicle_geometry import HULL_MIN,HULL_MAX,HULL_SIZE,qualification_start_x


class VehicleGeometryTest(unittest.TestCase):
    def test_actual_obj_bounds_match_collision(self):
        from sauvc_sim import vehicle_geometry
        mesh=Path(vehicle_geometry.__file__).parent/'meshes/sauvc_2027_v1.obj'
        lo=[math.inf]*3;hi=[-math.inf]*3
        for line in mesh.open():
            if line.startswith('v '):
                for i,value in enumerate(map(float,line.split()[1:4])):
                    lo[i]=min(lo[i],value);hi[i]=max(hi[i],value)
        self.assertEqual(tuple(lo),HULL_MIN);self.assertEqual(tuple(hi),HULL_MAX)
        w=ET.fromstring(build_world('qualification')).find('world')
        size=tuple(map(float,w.findtext("model[@name='sauvc_auv']/link/collision[@name='hull']/geometry/box/size").split()))
        self.assertEqual(size,HULL_SIZE)

    def test_yawed_spawn_touches_wall_and_estimator_uses_same_prior(self):
        from sauvc_sim.state_estimation import StateEstimator
        from test_dynamics import EstimationTest
        for yaw in (0.,.4,math.pi/2):
            world=ET.fromstring(build_world('qualification',yaw=yaw)).find('world')
            pose=tuple(map(float,world.findtext("model[@name='sauvc_auv']/pose").split()))
            self.assertAlmostEqual(envelope(pose)[0],0.,places=8)
            judge=QualificationJudge(edition='2027');judge.update(pose,0.)
            self.assertNotEqual(judge.phase,'FAILED')
            est=StateEstimator(edition='2027')
            est.update(EstimationTest().packet(0.,yaw,velocity=0.))
            self.assertAlmostEqual(est.x,qualification_start_x(yaw),places=5)

    def test_full_crossing_uses_body_rear_not_center_or_virtual_camera(self):
        j=QualificationJudge();j.update((qualification_start_x(0.),4.,-.05,0.),0.)
        j.update((qualification_start_x(0.),4.,-.3,0.),.5)
        for i in range(1,100):j.update((qualification_start_x(0.)+i*.1,4.,-.6,0.),i)
        boundary=10.025-HULL_MIN[0]
        j.update((boundary-.001,4.,-.6,0.),100.)
        self.assertEqual(j.phase,'OUTBOUND')
        j.update((boundary+.001,4.,-.6,0.),101.)
        self.assertEqual(j.phase,'RETURN')
        for t,x in ((102.,10.55),(103.,10.8)):
            j.update((x,4.,-.6,0.),t)
        j.update((10.8,4.,-.6,math.pi),104.)
        for t,x in ((105.,10.5),(106.,10.2),(107.,9.95)):
            j.update((x,4.,-.6,math.pi),t)
        return_boundary=9.975+HULL_MIN[0]
        j.update((return_boundary+.001,4.,-.6,math.pi),108.)
        self.assertFalse(j.qualified)
        j.update((return_boundary-.001,4.,-.6,math.pi),109.)
        self.assertTrue(j.qualified)
        old=QualificationJudge();old.update((.3,4.,-.05,0.),0.)
        self.assertEqual(old.reason,'invalid_start')
