import math
import unittest
from sauvc_sim.acoustics import AcousticTracker
from sauvc_sim.arena import build_world
from sauvc_sim.arena_referee import ArenaJudge
from sauvc_sim.arena_mission import ArenaController


def ping(t,pose,source=(24.,9.5,-1.08)):
    x,y,z,yaw=pose
    distances=[]
    for hx,hy in ((.1,0),(-.1,0),(0,.1),(0,-.1)):
        distances.append(math.dist(source,(x+hx*math.cos(yaw)-hy*math.sin(yaw),
                                           y+hx*math.sin(yaw)+hy*math.cos(yaw),z)))
    return dict(time=t,frequency_hz=45000,tdoa_s=[(d-distances[0])/1500 for d in distances])


class AcousticPickupTest(unittest.TestCase):
    def test_retention_rotates_capture_point_without_relaxing_distance(self):
        j=ArenaJudge(extended=True,edition='2027')
        j.navigation=True;j.score.started=0
        j.score.award('navigation',1)
        j.score.award('payload',2,ball_id='payload')
        j.score.award('acquisition',3,ball_id='payload',drum=1)
        j.score.award('target_zone_exit',4)
        j.previous=(22.,19.,-.3,0.,.2,0.)
        point=[22.-.2*math.cos(.2)-.45*math.sin(.2),19.,-.3+.2*math.sin(.2)-.45*math.cos(.2)]
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
        self.assertIsNotNone(w.find("world/model[@name='sauvc_auv']/link/collision[@name='pickup_finger_0']"))
        with self.assertRaises(ValueError):build_world('finals',extended=True,pinger_drum=1,edition='2026')

    def test_tool_envelope_rejects_floor_and_extended_dive_is_shallower(self):
        j=ArenaJudge(extended=True)
        j.update((.7,8.,-.05,0.),0.)
        j.update((.7,8.,-.4,0.),1.)
        j.update((.7,8.,-.8,0.),2.)
        self.assertEqual(j.reason,'pool_envelope')
        c=ArenaController(extended=True)
        c.command((.7,8.,-.65,0.),1.,{})
        self.assertEqual(c.state,'NAVIGATE')

    def test_retrieval_requires_attachment_distance_and_loses_credit(self):
        j=ArenaJudge(extended=True)
        j.navigation=True;j.score.started=0;j.score.award('navigation',1)
        j.score.award('payload',2,ball_id='payload');j.score.award('acquisition',3,ball_id='payload',drum=1)
        j.score.award('navigation',4);j.previous=(24.2,9.5,-.74,0.)
        def frame(t,attached,x=24.):
            return dict(time=t,payload_attached=attached,balls={'payload':dict(position=[x,9.5,-1.19],released=True)})
        j.physics(frame(5,False));self.assertFalse(j.payload_grasped)
        j.physics(frame(6,True));self.assertTrue(j.payload_grasped)
        j.physics(frame(6.6,True));self.assertEqual(j.score.result()['target_reacquisition'],60)
        j.physics(frame(7,True,x=23.));self.assertFalse(j.payload_retrieved)
        self.assertEqual(j.score.result()['target_reacquisition'],0)

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
