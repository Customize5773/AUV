import math
import unittest
from sauvc_sim.acoustics import AcousticTracker
from sauvc_sim.arena import build_world,PICKUP_X,PICKUP_Z
from sauvc_sim.vehicle_geometry import PICKUP_RIM_CLEARANCE
from sauvc_sim.arena_referee import ArenaJudge, MISSION_STATUS_FIELDS
from sauvc_sim.arena_mission import ArenaController


def ping(t,pose,source=(24.,9.5,-1.08)):
    x,y,z,yaw=pose
    distances=[]
    for hx,hy in ((.1,0),(-.1,0),(0,.1),(0,-.1)):
        distances.append(math.dist(source,(x+hx*math.cos(yaw)-hy*math.sin(yaw),
                                           y+hx*math.sin(yaw)+hy*math.cos(yaw),z)))
    return dict(time=t,frequency_hz=45000,tdoa_s=[(d-distances[0])/1500 for d in distances])


class AcousticPickupTest(unittest.TestCase):
    def test_initial_ball_is_in_centered_fixed_gripper_in_both_arena_modes(self):
        import xml.etree.ElementTree as ET
        from sauvc_sim.camera_geometry import CameraModel
        for edition in ('2026','2027'):
            for extended in (False,True):
                world=ET.fromstring(build_world('finals',edition=edition,extended=extended)).find('world')
                vehicle=world.find("model[@name='sauvc_auv']")
                body=list(map(float,vehicle.findtext('pose').split()))
                ball=list(map(float,world.findtext("model[@name='payload_ball']/pose").split()))
                carrier=vehicle.find("link[@name='payload_gripper']")
                point=list(map(float,carrier.findtext('pose').split()))
                self.assertEqual(point[:3],[0.,0.,PICKUP_Z])
                self.assertEqual(ball[:2],body[:2])
                self.assertAlmostEqual(ball[2]-body[2],PICKUP_Z)
                self.assertEqual(vehicle.find("joint[@name='pickup_mount_fixed']").get('type'),'fixed')
                self.assertIsNone(vehicle.find("joint[@name='pickup_slide']"))
                jaw=vehicle.find("link[@name='pickup_jaw_0']")
                finger=jaw.find("collision[@name='pickup_finger_0']")
                dy=abs(float(jaw.findtext('pose').split()[1])+float(finger.findtext('pose').split()[1]))
                radius=float(finger.findtext('geometry/sphere/radius'))
                self.assertGreater(2*(dy-radius),.04)
        pixel=CameraModel().pixel((0.,0.,PICKUP_Z),'bottom')
        self.assertGreater(pixel[1],480)

    def test_pinger_drop_uses_fresh_fix_then_falls_back_before_release(self):
        c=ArenaController(prefer_pinger=True,edition='2027',physical=True)
        pose=(22.,15.,-.3,0.)
        c.command(pose,0.,{})
        self.assertEqual(c.state,'DIVE')
        c.change('SCAN_DRUMS',1.)
        c.goal=[22.,16.]
        c.targets['blue_drum']=[21.,17.,-.3]
        c.acoustic_time=1.
        c.acoustic_target=[22.,15.]
        c.command(pose,1.1,{})
        self.assertEqual(c.selected_drum,'pinger')
        c.command(pose,1.8,{})
        self.assertEqual(c.state,'SCAN_DRUMS')
        self.assertFalse(c.release)
        self.assertEqual(c.goal,[22.,16.])
        c.command(pose,1.9,{})
        self.assertEqual(c.selected_drum,'blue')
        self.assertEqual(c.goal,c.targets['blue_drum'])

    def test_pinger_drop_requires_correct_drum_and_skips_pickup(self):
        judge=ArenaJudge(blue_drum=1,pinger_drum=3,prefer_pinger=True,edition='2027')
        judge.score.acquisition=1
        self.assertFalse(judge.drop_task_complete())
        judge.score.acquisition=2
        self.assertTrue(judge.drop_task_complete())
        c=ArenaController(prefer_pinger=True,edition='2027')
        c.started=0.
        c.selected_drum='pinger'
        c.change('WAIT_PAYLOAD',1.)
        c.command((22.,15.,-.3,0.),2.,{'payload_acquired':True})
        self.assertEqual(c.state,'WAIT_PAYLOAD')
        result=judge.result()
        c.command((22.,15.,-.3,0.),3.,{key:result[key] for key in MISSION_STATUS_FIELDS})
        self.assertEqual(c.state,'TO_SQUARE')
        self.assertFalse(c.grip)

    def test_fixed_gripper_rejects_unreachable_pickup_before_motion(self):
        self.assertAlmostEqual(PICKUP_RIM_CLEARANCE,-.17)
        for state,started in (('WAIT',None),('DESCEND_PICKUP',0.)):
            c=ArenaController(extended=True,edition='2027',physical=True)
            c.state=state;c.started=started;c.since=0.;c.goal=[22.,15.]
            command=c.command((22.,15.,-.3,0.),1.,{})
            self.assertEqual(command,(0.,0.,0.,0.))
            self.assertEqual(c.state,'ABORT')
            self.assertEqual(c.reason,'fixed_gripper_unreachable')
            self.assertFalse(c.grip)

    def test_supported_geometry_can_reach_ball_without_hull_contact(self):
        from unittest.mock import patch
        c=ArenaController(extended=True,edition='2027',physical=True)
        with patch('sauvc_sim.arena_mission.PICKUP_RIM_CLEARANCE',.02), patch('sauvc_sim.arena_mission.PICKUP_Z',-.4):
            command=c.command((34.,.7,-.05,0.),0.,{})
            self.assertEqual(c.state,'DIVE');self.assertLess(command[2],0.)
            c.state='DESCEND_PICKUP';c.goal=[22.,15.]
            depth=-2.+.4+.038
            command=c.command((22.,15.,depth,0.),1.,{})
            self.assertTrue(c.grip);self.assertAlmostEqual(command[2],0.)
            self.assertAlmostEqual(depth-.1-(-2.+.32),.018)

    def test_retention_rotates_capture_point_without_relaxing_distance(self):
        j=ArenaJudge(extended=True,edition='2027')
        j.navigation=True;j.score.started=0
        j.score.award('navigation',1)
        j.score.award('payload',2,ball_id='payload')
        j.score.award('acquisition',3,ball_id='payload',drum=1)
        j.score.award('target_zone_exit',4)
        j.previous=(22.,19.,-.3,0.,.2,0.)
        point=[22.+PICKUP_X*math.cos(.2)+PICKUP_Z*math.sin(.2),19.,-.3-PICKUP_X*math.sin(.2)+PICKUP_Z*math.cos(.2)]
        def frame(t,attached=True,offset=0.):
            return dict(time=t,payload_attached=attached,balls={'payload':dict(position=[point[0]+offset,*point[1:]],released=True)})
        j.physics(frame(5));j.physics(frame(5.6))
        self.assertTrue(j.payload_retrieved)
        j.physics(frame(6,offset=.08))
        self.assertFalse(j.payload_retrieved)
        j.physics(frame(7));j.physics(frame(7.6))
        self.assertTrue(j.payload_retrieved)
        j.physics(frame(8,attached=False))
        self.assertFalse(j.payload_retrieved)

    def test_fixed_mount_connects_roof_to_hull(self):
        import xml.etree.ElementTree as ET
        w=ET.fromstring(build_world('finals',extended=True,edition='2027'))
        body=w.find("world/model[@name='sauvc_auv']/link[@name='payload_gripper']")
        self.assertEqual(list(map(float,body.findtext('pose').split()))[:3],[0.,0.,PICKUP_Z])
        mount=body.find("collision[@name='pickup_mount']")
        center=float(mount.findtext('pose').split()[2])
        height=float(mount.findtext('geometry/cylinder/length'))
        self.assertAlmostEqual(center+height/2+PICKUP_Z,-.08)
        self.assertAlmostEqual(center-height/2+PICKUP_Z,PICKUP_Z+.03)
        roof=body.find("collision[@name='pickup_roof']")
        roof_top=float(roof.findtext('pose').split()[2])+float(roof.findtext('geometry/cylinder/length'))/2
        self.assertAlmostEqual(center-height/2,roof_top)
        self.assertAlmostEqual(-.1-(center-height/2+PICKUP_Z),.08)
        self.assertAlmostEqual(float(roof.findtext('geometry/cylinder/radius')),.022)

    def test_curved_jaws_keep_drop_corridor_clear_when_fully_open(self):
        import xml.etree.ElementTree as ET
        vehicle=ET.fromstring(build_world('finals',edition='2027')).find("world/model[@name='sauvc_auv']")
        for i,side in enumerate((-1,1)):
            jaw=vehicle.find(f"link[@name='pickup_jaw_{i}']")
            pivot=list(map(float,jaw.findtext('pose').split()))
            self.assertAlmostEqual(pivot[3]+side*.35,0.)
            for solid in jaw.findall('collision'):
                pose=list(map(float,solid.findtext('pose').split()));geom=solid.find('geometry')
                if geom.find('sphere') is not None:
                    extent=float(geom.findtext('sphere/radius'))
                elif geom.find('cylinder') is not None:
                    extent=float(geom.findtext('cylinder/radius'))*abs(math.cos(pose[3]))+float(geom.findtext('cylinder/length'))/2*abs(math.sin(pose[3]))
                else:
                    size=list(map(float,geom.findtext('box/size').split()))
                    extent=size[1]/2*abs(math.cos(pose[3]))+size[2]/2*abs(math.sin(pose[3]))
                self.assertGreater(abs(pose[1]+pivot[1])-extent,.0225,solid.get('name'))

    def test_jaws_use_limited_revolute_force_controllers(self):
        import xml.etree.ElementTree as ET
        vehicle=ET.fromstring(build_world('finals',edition='2027')).find("world/model[@name='sauvc_auv']")
        total=sum(float(vehicle.findtext(f"link[@name='{name}']/inertial/mass")) for name in ('payload_gripper','pickup_jaw_0','pickup_jaw_1'))
        self.assertAlmostEqual(total,.05)
        for i,side in enumerate((-1,1)):
            hinge=vehicle.find(f"joint[@name='pickup_hinge_{i}']")
            self.assertEqual(hinge.get('type'),'revolute')
            self.assertEqual(hinge.findtext('parent'),'payload_gripper')
            self.assertEqual(hinge.findtext('axis/xyz'),'1 0 0')
            self.assertAlmostEqual(float(hinge.findtext('axis/limit/lower')),min(0,side*.35))
            self.assertAlmostEqual(float(hinge.findtext('axis/limit/upper')),max(0,side*.35))
            servo=next(p for p in vehicle.findall('plugin') if p.findtext('joint_name')==f'pickup_hinge_{i}')
            self.assertIsNone(servo.find('use_velocity_commands'))
            self.assertAlmostEqual(float(servo.findtext('cmd_max')),.04)

    def test_vertical_ping_keeps_only_an_established_nearby_target(self):
        a=AcousticTracker()
        for i in range(50):
            pose=(.7+i*.3,8-i*.025,-.65,.2)
            a.update(ping(i,pose),pose)
        target=list(a.target);rays=list(a.rays)
        pose=(24.,9.5,-.3,0.)
        self.assertEqual(a.update(ping(51,pose),pose),target)
        self.assertEqual(a.rays,rays)
        self.assertIsNone(a.update(ping(51,pose),pose))
        bad=ping(52,pose);bad['frequency_hz']=0
        self.assertIsNone(a.update(bad,pose))
        self.assertIsNone(a.update(dict(time=53,frequency_hz=45000,tdoa_s=[0]*4),(1.,8.,-.3,0.)))
        self.assertIsNone(AcousticTracker().update(ping(0,pose),pose))

    def test_source_triangulation_without_source_coordinates(self):
        a=AcousticTracker()
        for i in range(50):
            pose=(.7+i*.3,8-i*.025,-.65,.2)
            a.update(ping(i,pose),pose)
        self.assertIsNotNone(a.target)
        self.assertLess(math.dist(a.target,(24.,9.5)),.04)
        self.assertIsNone(a.update(dict(time=51,frequency_hz=45000,tdoa_s=[0,float('nan'),0,0]),pose))
        self.assertIsNone(a.update(ping(0,pose),pose))
        self.assertIsNone(a.update({},pose))
        self.assertIsNone(a.update({'time':55,'tdoa_s':None},pose))

    def test_stationary_source_cannot_be_triangulated(self):
        a=AcousticTracker();pose=(1.,8.,-.65,0.)
        for i in range(20):a.update(ping(i,pose),pose)
        self.assertIsNone(a.target)

    def test_world_metadata_is_not_in_acoustic_measurements(self):
        import xml.etree.ElementTree as ET
        w=ET.fromstring(build_world('finals',extended=True,edition='2026'))
        self.assertIsNotNone(w.find("world/model[@name='pinger_source']"))
        self.assertIsNotNone(w.find("world/model[@name='sauvc_auv']/link[@name='pickup_jaw_0']/collision[@name='pickup_finger_0']"))
        with self.assertRaises(ValueError):build_world('finals',extended=True,pinger_drum=1,edition='2026')

    def test_fixed_tool_envelope_rejects_floor_and_short_pickup_aborts(self):
        j=ArenaJudge(extended=True)
        j.update((.7,8.,-.05,0.),0.)
        j.update((.7,8.,-.4,0.),1.)
        j.update((.7,8.,-.75,0.),2.)
        self.assertEqual(j.reason,'')
        j.update((.7,8.,-1.04,0.),3.)
        self.assertEqual(j.reason,'pool_envelope')
        c=ArenaController(extended=True)
        c.command((.7,8.,-.65,0.),1.,{})
        self.assertEqual(c.state,'ABORT')
        self.assertEqual(c.reason,'fixed_gripper_unreachable')

    def test_retrieval_requires_attachment_distance_and_loses_credit(self):
        j=ArenaJudge(extended=True)
        j.navigation=True;j.score.started=0;j.score.award('navigation',1)
        j.score.award('payload',2,ball_id='payload');j.score.award('acquisition',3,ball_id='payload',drum=1)
        j.score.award('navigation',4);j.previous=(24.,9.5,-.3,0.)
        def frame(t,attached,x=24.):
            return dict(time=t,payload_attached=attached,balls={'payload':dict(position=[x,9.5,-.3+PICKUP_Z],released=True)})
        j.physics(frame(5,False));self.assertFalse(j.payload_grasped)
        j.physics(frame(6,True));self.assertTrue(j.payload_grasped)
        j.physics(frame(6.6,True));self.assertEqual(j.score.result()['target_reacquisition'],60)
        j.physics(frame(7,True,x=23.));self.assertFalse(j.payload_retrieved)
        self.assertEqual(j.score.result()['target_reacquisition'],0)

    def test_contact_only_retrieval_requires_lifting_the_ball(self):
        j=ArenaJudge(extended=True,edition='2027')
        j.score.retrieval_crossing=True
        def sample(t,z,grip,dy=0.):
            j.previous=(22.,19.,z-PICKUP_Z,0.)
            j.physics(dict(time=t,payload_attached=False,unlatched_bilateral_grip=grip,
                           balls={'payload':dict(position=[22.,19.+dy,z],released=True)}))
        sample(1,-1.96,True)
        sample(2,-1.96,True)
        self.assertTrue(j.payload_grasped)
        self.assertFalse(j.payload_retrieved)
        sample(3,-1.6,True)
        self.assertTrue(j.payload_retrieved)
        sample(3.2,-1.96,True)
        self.assertFalse(j.payload_retrieved)
        sample(3.8,-1.6,True)
        self.assertTrue(j.payload_retrieved)
        sample(4,-1.6,True,.09)
        self.assertFalse(j.payload_retrieved)
        sample(5,-1.6,False)
        self.assertFalse(j.payload_grasped)

    def test_only_aperture_crossing_after_acquisition_qualifies(self):
        for y,expected in ((4.,False),(8.,True)):
            j=ArenaJudge(extended=True);j.started=0.;j.phase='RUNNING';j.navigation=True
            j.score.started=0.;j.score.award('navigation',1.)
            j.score.award('payload',2.,ball_id='payload')
            j.score.award('acquisition',3.,ball_id='payload',drum=1)
            for t,x in ((4.,15.6),(5.,16.),(6.,16.4)):j.update((x,y,-.65,0.),t)
            self.assertEqual(j.phase,'RUNNING')
            self.assertEqual(j.score.retrieval_crossing,expected)

    def test_level_correction_and_gate_depth_with_capture_tool(self):
        from sauvc_sim.arena_mission import level_rates
        roll,pitch=level_rates(.1,-.2)
        self.assertLess(roll,0);self.assertGreater(pitch,0)
        self.assertLessEqual(max(abs(v) for v in level_rates(1.,-1.)),.4)
        c=ArenaController(extended=True);c.started=1.;c.state='CLEAR_GATE';c.since=1.
        c.goal=[17.6,8.]
        self.assertLess(c.command((16.5,8.,-.65,0.),2.,{})[2],0.)

    def test_stale_acoustics_aborts_alignment_without_release(self):
        c=ArenaController(extended=True);c.started=1.;c.state='ALIGN_DRUM';c.since=1.
        c.acoustic_target=[24.,9.5];c.acoustic_time=1.
        self.assertEqual(c.command((23.8,9.5,-.12,0.),2.,{}),(0.,0.,0.,0.))
        self.assertEqual(c.reason,'stale_acoustics');self.assertFalse(c.release)


def test_compact_release_needs_low_pose_and_pickup_needs_visible_ball():
    ctrl=ArenaController(extended=True,edition='2027',physical=True,compact=True)
    ctrl.started=0.
    ctrl.state='ALIGN_DRUM'
    ctrl.acoustic_target=(22.,17.)
    def command(t,z):
        ctrl.acoustic_time=t
        return ctrl.command((22.,17.,z,0.),t,{})
    assert command(1.,-.3)[2]<0
    command(3.,-.3)
    assert not ctrl.release
    command(4.,-1.4)
    command(5.1,-1.4)
    assert ctrl.release
    ctrl.change('ALIGN_PICKUP',6.)
    command(47.,-1.4)
    assert ctrl.reason=='pickup_ball_not_visible'
    assert not ctrl.grip


def test_compact_pickup_pauses_then_aborts_on_sustained_tilt():
    ctrl=ArenaController(extended=True,edition='2027',physical=True,compact=True)
    ctrl.started=0.
    ctrl.state='DESCEND_PICKUP'
    ctrl.goal=ctrl.ball_fix=[22.,17.,-1.96]
    ctrl.ball_fix_time=2.5
    pose=(22.,17.,-1.5,0.)
    ctrl.attitude=(.18,0.)
    assert ctrl.command(pose,1.,{})[2]==0.
    ctrl.attitude=(0.,0.)
    assert ctrl.command(pose,1.4,{})[2]==-.04
    ctrl.attitude=(0.,-.18)
    assert ctrl.command(pose,2.,{})[2]==0.
    assert ctrl.command(pose,2.6,{})==(0.,0.,0.,0.)
    assert ctrl.reason=='pickup_excess_tilt'


def test_compact_lift_requires_sustained_grasp_and_retention():
    ctrl=ArenaController(extended=True,edition='2027',physical=True,compact=True)
    ctrl.started=0.
    ctrl.state='DESCEND_PICKUP'
    ctrl.goal=ctrl.ball_fix=[22.,17.,-1.96]
    ctrl.grip=True
    pose=(22.,17.,-1.71,0.)
    held={'payload_grasped':True}
    assert ctrl.command(pose,1.,held)==(0.,0.,0.,0.)
    assert ctrl.command(pose,2.9,held)==(0.,0.,0.,0.)
    assert ctrl.command(pose,3.1,held)[2]==.08
    assert ctrl.state=='LIFT_PICKUP'
    assert ctrl.command(pose,3.2,{})==(0.,0.,0.,0.)
    assert ctrl.reason=='pickup_lost_during_lift'
