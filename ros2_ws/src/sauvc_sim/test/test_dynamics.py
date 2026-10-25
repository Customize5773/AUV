import math
import unittest
import xml.etree.ElementTree as ET
import numpy as np
from sauvc_sim.arena import build_world
from sauvc_sim.dynamics import PropulsionController,allocation,config,displaced_fraction
from sauvc_sim.state_estimation import StateEstimator
from sauvc_sim.qualification import QualificationController
from sauvc_sim.referee import QualificationJudge


class DynamicsTest(unittest.TestCase):
    def test_physical_world_has_gravity_and_no_velocity_override(self):
        world=ET.fromstring(build_world('qualification',physical=True)).find('world')
        model=world.find("model[@name='sauvc_auv']")
        self.assertEqual(model.findtext('link/gravity'),'true')
        self.assertIsNone(model.find("plugin[@name='ignition::gazebo::systems::VelocityControl']"))
        self.assertIsNotNone(world.find("plugin[@name='sauvc::VehicleDynamics']"))
        self.assertEqual(world.findtext('gravity'),'0 0 -9.81')

    def test_allocation_axes_limits_and_reverse_braking(self):
        ctrl=PropulsionController()
        self.assertEqual(allocation().shape,(6,6))
        self.assertEqual(np.linalg.matrix_rank(ctrl.matrix),4)
        u=np.array(ctrl.command([0.,0.,0.,0.],[.8,0.,0.,0.],-.6,.02))
        forces=u*np.abs(u)*ctrl.max_force
        self.assertLess((ctrl.matrix@forces)[0],0.)
        self.assertTrue(np.all(np.abs(u)<=1))
        self.assertEqual(ctrl.command([1.,0.,0.,0.],[0.]*4,-.6,.02,False),[0.]*6)
        with self.assertRaises(ValueError):ctrl.command([float('nan')]*4,[0.]*4,-.6,.02)

    def test_archimedes_surface_equilibrium_and_drag_passivity(self):
        cfg=config()
        self.assertGreater(cfg['density']*cfg['volume'],cfg['mass'])
        fraction=cfg['mass']/(cfg['density']*cfg['volume'])
        z=cfg['buoyancy_height']*(.5-fraction)-cfg['buoyancy_z']
        self.assertAlmostEqual(cfg['density']*cfg['volume']*displaced_fraction(z,cfg),cfg['mass'])
        self.assertGreater(z+.1,0)
        for v in (-2.,-.3,.3,2.):
            force=-cfg['linear_drag'][0]*v-cfg['quadratic_drag'][0]*v*abs(v)
            self.assertLess(force*v,0.)


class EstimationTest(unittest.TestCase):
    def packet(self,t,yaw=0.,velocity=.5):
        return dict(time=t,gyro=[0.,0.,.001],accel=[0.,0.,9.81],
                    mag=[20*math.cos(yaw),-20*math.sin(yaw),-45.],
                    dvl=[velocity,0.,0.],pressure_pa=101325+1000*9.81*.6)

    def test_dead_reckoning_pressure_and_magnetic_heading(self):
        est=StateEstimator()
        for i in range(501):self.assertTrue(est.update(self.packet(i*.02)))
        self.assertAlmostEqual(est.x,5.3,delta=.01)
        self.assertAlmostEqual(est.z,-.6,delta=.002)
        self.assertAlmostEqual(est.yaw,0.,delta=.002)
        other=StateEstimator(lane=2)
        for i in range(501):other.update(self.packet(i*.02,math.pi/2))
        self.assertAlmostEqual(other.y,17.,delta=.01)
        self.assertAlmostEqual(other.x,.2,delta=.01)

    def test_missing_sensors_timestamp_and_invalid_data(self):
        for missing in ('gyro','dvl','pressure_pa'):
            est=StateEstimator();est.update(self.packet(0.))
            for i in range(1,20):
                p=self.packet(i*.02);del p[missing];valid=est.update(p)
            self.assertFalse(valid)
            self.assertEqual(est.reason,'stale_'+missing)
        est=StateEstimator();est.update(self.packet(1.))
        self.assertFalse(est.update(self.packet(1.)))
        bad=self.packet(1.1);bad['dvl'][0]=float('nan')
        with self.assertRaises(ValueError):est.update(bad)
        for key,value in (('mag',[0.,0.,0.]),('pressure_pa',0.),('dvl',[20.,0.,0.])):
            bad=self.packet(1.1);bad[key]=value
            with self.assertRaises(ValueError):est.update(bad)

    def test_noise_bearing_crosses_pi_without_heading_jump(self):
        est=StateEstimator();rng=np.random.default_rng(7)
        for i in range(500):
            p=self.packet(i*.02,math.pi-.001,0.)
            p['pressure_pa']+=float(rng.normal(0,20))
            p['dvl']=rng.normal(0,.003,3).tolist()
            self.assertTrue(est.update(p))
        self.assertAlmostEqual(est.z,-.6,delta=.005)
        self.assertLess(abs(math.atan2(math.sin(est.yaw-math.pi),math.cos(est.yaw-math.pi))),.005)


class DynamicMissionTest(unittest.TestCase):
    def test_short_clearance_brakes_before_turn_without_changing_ideal(self):
        ctrl=QualificationController(physical=True)
        ctrl.started=0.;ctrl.state='CLEAR_GATE';ctrl.turn_start=(10.6,4.)
        ctrl.command((11.19,4.,-.6,0.),1.,None,0.,{})
        self.assertEqual(ctrl.state,'CLEAR_GATE')
        command=ctrl.command((11.21,4.,-.6,0.),2.,None,0.,{})
        self.assertEqual(ctrl.state,'TURN')
        self.assertEqual(command[0],0.)
        ideal=QualificationController()
        ideal.started=0.;ideal.state='CLEAR_GATE';ideal.turn_start=(10.6,4.)
        ideal.command((11.21,4.,-.6,0.),2.,None,0.,{})
        self.assertEqual(ideal.state,'CLEAR_GATE')

    def test_surface_transition_commands_heave_not_yaw(self):
        ctrl=QualificationController()
        ctrl.started=0.;ctrl.state='PASS_BACK'
        command=ctrl.command((9.4,4.,-.6,math.pi),1.,None,0.,dict(qualification_passed=True))
        self.assertGreater(command[2],0.)
        self.assertEqual(command[3],0.)

    def test_stop_requires_a_continuously_surfaced_stationary_body(self):
        judge=QualificationJudge(physical=True)
        judge.started=0.;judge.run_started=0.;judge.finished=1.;judge.phase='QUALIFIED'
        judge.previous=(9.4,4.,-.11,math.pi)
        judge.update((9.4,4.,-.101,math.pi),2.)
        self.assertFalse(judge.surface_completed)
        for t,z in ((3.,-.095),(3.5,-.095),(4.,-.101),(4.5,-.095),(5.,-.095),(6.1,-.095)):
            judge.update((9.4,4.,z,math.pi),t)
        self.assertTrue(judge.result()['passed'])
        self.assertEqual(judge.phase,'COMPLETE')

    def test_physical_crossing_uses_estimate_and_stop_disarms(self):
        ctrl=QualificationController(physical=True)
        ctrl.started=0.;ctrl.state='PASS_OUT';ctrl.target=(10.,4.,0.)
        ctrl.command((10.7,4.,-.6,0.),1.,None,0.,{})
        self.assertEqual(ctrl.state,'CLEAR_GATE')
        ctrl.state='PASS_BACK';ctrl.target=(10.,4.,math.pi)
        ctrl.command((9.3,4.,-.6,math.pi),2.,None,0.,{})
        self.assertEqual(ctrl.state,'SURFACE')
        ctrl.state='STOP'
        self.assertEqual(ctrl.command((9.3,4.,-.096,math.pi),3.,None,0.,{}),(0.,0.,0.,0.))
        with self.assertRaises(ValueError):QualificationController('odom',physical=True)

    def test_reference_truth_does_not_direct_physical_transitions(self):
        ctrl=QualificationController(physical=True)
        ctrl.started=0.;ctrl.state='ALIGN'
        ctrl.command((1.,4.,-.6,0.),1.,dict(bearing=.0,distance=5.),0.,
            dict(qualification_passed=True,events=[dict(event='FULL_OUTBOUND')]))
        self.assertEqual(ctrl.state,'ALIGN')

    def test_physical_preflight_drift_is_not_a_mission_start(self):
        judge=QualificationJudge(physical=True)
        judge.update((.3,4.,-.05,0.),0.)
        judge.update((.3,4.,-.14,0.),1.)
        judge.update((.3,4.,-.096,0.),2.)
        self.assertEqual(judge.phase,'START')
        self.assertIsNone(judge.run_started)
        judge.arm(3.)
        judge.update((.3,4.,-.3,0.),3.)
        self.assertEqual(judge.phase,'OUTBOUND')
