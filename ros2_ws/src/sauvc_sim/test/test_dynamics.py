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
        world=ET.fromstring(build_world('qualification',physical=True,edition='2026')).find('world')
        model=world.find("model[@name='sauvc_auv']")
        self.assertEqual(model.findtext('link/gravity'),'true')
        self.assertIsNone(model.find("plugin[@name='ignition::gazebo::systems::VelocityControl']"))
        self.assertIsNotNone(world.find("plugin[@name='sauvc::VehicleDynamics']"))
        self.assertEqual(world.findtext('gravity'),'0 0 -9.81')

    def test_arena_uses_same_seven_force_plant_at_surveyed_start(self):
        world=ET.fromstring(build_world('finals',physical=True,extended=True)).find('world')
        model=world.find("model[@name='sauvc_auv']")
        self.assertEqual(model.findtext('link/gravity'),'true')
        self.assertIsNone(model.find("plugin[@name='ignition::gazebo::systems::VelocityControl']"))
        plant=world.find("plugin[@name='sauvc::VehicleDynamics']")
        self.assertEqual(len(plant.findtext('thruster_axes').split()),21)
        self.assertAlmostEqual(float(model.findtext('pose').split()[5]),math.pi/2,places=7)

    def test_arena_estimator_uses_surveyed_xy_and_measured_heading(self):
        est=StateEstimator(edition='2027',arena='finals')
        for i in range(501):self.assertTrue(est.update(EstimationTest().packet(i*.02,math.pi/2)))
        self.assertAlmostEqual(est.x,34.,delta=.01)
        self.assertAlmostEqual(est.y,5.7,delta=.01)
        self.assertAlmostEqual(est.z,-.6,delta=.002)
        self.assertAlmostEqual(est.yaw,math.pi/2,delta=.002)

    def test_propulsion_waits_for_mission_and_disarms_at_stop(self):
        from types import SimpleNamespace
        from sauvc_sim.physical_runtime import PhysicalRuntime
        node=SimpleNamespace(role='propulsion',active=False,disarmed=False)
        PhysicalRuntime.state(node,SimpleNamespace(data='WAIT'))
        self.assertFalse(node.active)
        PhysicalRuntime.state(node,SimpleNamespace(data='DIVE'))
        self.assertTrue(node.active)
        PhysicalRuntime.state(node,SimpleNamespace(data='STOP'))
        self.assertTrue(node.disarmed)

    def test_arena_passive_preflight_heave_does_not_start_attempt(self):
        from sauvc_sim.arena_referee import ArenaJudge
        judge=ArenaJudge(edition='2027',physical=True)
        judge.update((.7,8.,-.05,0.),0.)
        judge.update((.7,8.,-.15,0.),.5)
        judge.update((.7,8.,-.05,0.),1.)
        self.assertEqual(judge.phase,'START')
        self.assertIsNone(judge.score.started)
        judge.thrust(2.,True);judge.update((.7,8.,-.2,0.),2.1)
        self.assertEqual(judge.phase,'RUNNING')
        judge.update((.7,8.,-.05,0.),3.)
        self.assertEqual(judge.reason,'premature_surface')

    def test_manual_nonzero_command_arms_but_zero_preflight_does_not(self):
        from types import SimpleNamespace
        from geometry_msgs.msg import Twist
        from sauvc_sim.physical_runtime import PhysicalRuntime
        node=SimpleNamespace(role='propulsion',active=False)
        PhysicalRuntime.command(node,Twist())
        self.assertFalse(node.active)
        cmd=Twist();cmd.linear.z=-.2
        PhysicalRuntime.command(node,cmd)
        self.assertTrue(node.active)

    def test_allocation_axes_limits_and_reverse_braking(self):
        ctrl=PropulsionController()
        self.assertEqual(allocation().shape,(6,7))
        self.assertEqual(np.linalg.matrix_rank(ctrl.matrix),6)
        u=np.array(ctrl.command([0.,0.,0.,0.],[.8,0.,0.,0.],-.6,.02))
        forces=u*np.abs(u)*ctrl.max_force
        self.assertLess((ctrl.matrix@forces)[0],0.)
        self.assertTrue(np.all(np.abs(u)<=1))
        self.assertEqual(ctrl.command([1.,0.,0.,0.],[0.]*4,-.6,.02,False),[0.]*7)
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

    def test_stationary_preflight_bias_is_frozen_before_motion(self):
        est=StateEstimator(calibrate_dvl=True)
        for i in range(60):
            packet=self.packet(i*.05,velocity=0.);packet['dvl']=[.004,-.003,.12]
            self.assertTrue(est.update(packet))
        self.assertEqual(est.bias_samples,60)
        np.testing.assert_allclose(est.dvl_bias,[.004,-.003])
        self.assertAlmostEqual(est.velocity[2],.12,places=6)
        est.finish_calibration();at_start=est.pose()
        for i in range(60,4060):
            packet=self.packet(i*.05,velocity=0.);packet['dvl']=[.004,-.003,0.]
            self.assertTrue(est.update(packet))
        self.assertLess(math.dist(est.pose()[:2],at_start[:2]),.002)
        self.assertEqual(est.bias_samples,60)
        moving=self.packet(203.,velocity=.4);moving['dvl']=[.404,-.003,0.]
        self.assertTrue(est.update(moving))
        np.testing.assert_allclose(est.dvl_bias,[.004,-.003])
        self.assertGreater(est.velocity[0],.1)

    def test_bias_does_not_learn_obvious_motion_or_short_preflight(self):
        est=StateEstimator(calibrate_dvl=True)
        for i in range(30):self.assertTrue(est.update(self.packet(i*.05)))
        self.assertEqual(est.bias_samples,0)
        self.assertAlmostEqual(est.velocity[0],.5)
        for i in range(30,35):
            packet=self.packet(i*.05,velocity=.005);est.update(packet)
        self.assertEqual(est.bias_samples,5)
        est.finish_calibration()
        for i in range(35,60):
            packet=self.packet(i*.05,velocity=.005);est.update(packet)
        self.assertEqual(est.bias_samples,5)
        self.assertAlmostEqual(est.velocity[0],.005,delta=.0001)

    def test_mission_activation_latches_bias_calibration_off(self):
        from types import SimpleNamespace
        from geometry_msgs.msg import Twist
        from sauvc_sim.physical_runtime import PhysicalRuntime
        node=SimpleNamespace(role='state_estimator',active=False,estimator=StateEstimator(calibrate_dvl=True))
        PhysicalRuntime.state(node,SimpleNamespace(data='WAIT'))
        self.assertTrue(node.estimator.calibrating)
        PhysicalRuntime.state(node,SimpleNamespace(data='DIVE'))
        PhysicalRuntime.state(node,SimpleNamespace(data='WAIT'))
        self.assertFalse(node.estimator.calibrating)
        manual=SimpleNamespace(role='state_estimator',active=False,estimator=StateEstimator(calibrate_dvl=True))
        cmd=Twist();cmd.linear.z=-.1;PhysicalRuntime.command(manual,cmd)
        self.assertFalse(manual.estimator.calibrating)

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


class SevenThrusterTest(unittest.TestCase):
    def test_vertical_allocation_balances_roll_pitch_and_uses_all_three(self):
        ctrl=PropulsionController()
        u=np.array(ctrl.command([0.,0.,.15,0.],[0.]*4,-.6,.02))
        forces=u*np.abs(u)*ctrl.max_force
        wrench=ctrl.matrix@forces
        self.assertTrue(np.all(np.abs(forces[4:])>.01))
        self.assertGreater(wrench[2],0.)
        self.assertAlmostEqual(wrench[3],0.,places=8)
        self.assertAlmostEqual(wrench[4],0.,places=8)

    def test_packaged_profile_and_native_geometry_contract(self):
        from sauvc_sim.dynamics import propulsion_profile
        profile=propulsion_profile()
        self.assertEqual([m['output'] for m in profile['thrusters']],list(range(1,8)))
        self.assertEqual([m['orientation'] for m in profile['thrusters']],['horizontal']*4+['vertical']*3)
        self.assertFalse(profile['hardware_mixer_verified'])
        cfg=config()
        self.assertEqual(len(cfg['thruster_positions']),21)
        self.assertEqual(len(cfg['thruster_axes']),21)
