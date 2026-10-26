import math
import unittest
import xml.etree.ElementTree as ET
import numpy as np
from sauvc_sim.arena import build_world
from sauvc_sim.rules2027 import LANES,to_world,to_local,floor_z,SQUARE
from sauvc_sim.arena_referee import ArenaJudge
from sauvc_sim.arena_scoring import ArenaScore
from sauvc_sim.arena_mission import valid_order,ArenaController
from sauvc_sim.object_detection import detect_objects
from sauvc_sim.camera_geometry import CameraModel


class Rules2027Test(unittest.TestCase):
    def test_pool_three_lanes_gate_and_zone_geometry(self):
        w=ET.fromstring(build_world('finals',extended=True)).find('world')
        for i,y in enumerate(LANES,1):
            gate=w.find(f"model[@name='qualification_gate_{i}']")
            self.assertEqual([float(v) for v in gate.findtext('pose').split()][:3],[10.,y,-1.])
        gate=w.find("model[@name='navigation_gate']")
        pose=[float(v) for v in gate.findtext('pose').split()]
        self.assertAlmostEqual(pose[1],12.7);self.assertAlmostEqual(pose[5],math.pi/2,places=7)
        self.assertEqual(w.find("model[@name='wall_end']/pose").text.split()[0],'50.1')
        self.assertEqual(w.find("model[@name='target_zone_mat']/link/visual/geometry/box/size").text,'8 2 0.004')
        self.assertIsNotNone(w.find("model[@name='surfacing_square']"))
        self.assertEqual(floor_z(0),-1.28);self.assertEqual(floor_z(50),-2.)
        for lane in (1,2,3):
            q=ET.fromstring(build_world('qualification',lane=lane)).find('world')
            self.assertEqual(float(q.find("model[@name='sauvc_auv']/pose").text.split()[1]),LANES[lane-1])

    def test_main_coordinate_transform_preserves_camera_relative_position(self):
        for p in [(3.,8.,-.6,.2),(22.,21.,-.12,math.pi)]:
            local=to_local(to_world(*p))
            self.assertLess(math.dist(p[:3],local[:3]),1e-8)
            self.assertAlmostEqual(math.atan2(math.sin(p[3]-local[3]),math.cos(p[3]-local[3])),0.)

    def test_zone_exit_requires_every_part_after_acquisition(self):
        j=ArenaJudge(extended=True,edition='2027');j.started=0.;j.phase='RUNNING';j.navigation=True
        j.score.started=1.;j.score.award('navigation',1.)
        j.score.award('payload',2.,ball_id='payload');j.score.award('acquisition',3.,ball_id='payload',drum=0)
        j.score.award('navigation',4.);self.assertFalse(j.score.retrieval_crossing)
        for t,x in ((5,22.),(6,21.6),(7,21.2),(8,20.8)):j.update((x,21.,-.12,0.),t)
        self.assertFalse(j.score.retrieval_crossing)
        j.update((20.6,21.,-.12,0.),9.)
        self.assertTrue(j.result()['target_zone_exited'])
        self.assertIn('TARGET_ZONE_FULL_EXIT',[e['event'] for e in j.events])

    def test_square_bonus_inside_touch_outside_and_navigation_prerequisite(self):
        for inside,touch,nav,bonus in [(True,False,True,20),(True,True,True,0),(False,False,True,0),(True,False,False,0)]:
            j=ArenaJudge(edition='2027');j.started=0.;j.phase='RUNNING';j.navigation=nav
            j.score.started=1.;j.fallen=list(j.order);j.payload_in_blue=True
            if nav:j.score.award('navigation',1.)
            u,v=SQUARE;u+=0 if inside else 2
            j.update((u,v,-.05,0.),10.,['surfacing_square::body::edge_0'] if touch else [])
            self.assertEqual(j.result()['score']['surfacing_square_bonus'],bonus)
            self.assertEqual(j.result()['score']['surface_bonus'],5)

    def test_timer_from_actual_thrust_and_arena_gate_is_penalty(self):
        j=ArenaJudge(edition='2027');j.update((.7,8.,-.05,0.),0.)
        self.assertIsNone(j.score.started);j.thrust(2.,False);self.assertIsNone(j.score.started)
        j.thrust(3.,True);j.thrust(4.,True);self.assertEqual(j.score.started,3.)
        j.update((.7,8.,-.4,0.),4.,['navigation_gate::body::port'])
        self.assertNotEqual(j.phase,'FAILED');self.assertEqual(j.score.penalties,2)

    def test_square_camera_pair_has_metric_location_and_single_post_rejected(self):
        im=np.zeros((480,640,3),dtype=np.uint8)
        im[200:250,150:157]=(5,50,220);im[200:250,450:457]=(5,50,220)
        packet=detect_objects(im.tobytes(),640,480,1920,'rgb8','front','finals')
        obj=next(o for o in packet['detections'] if o['label']=='surfacing_square')
        self.assertIsNotNone(CameraModel().locate(obj,'front'))
        im[:,450:457]=0
        self.assertNotIn('surfacing_square',[o['label'] for o in detect_objects(im.tobytes(),640,480,1920)['detections']])

    def test_pickup_leaves_zone_instead_of_gate_and_square_is_camera_target(self):
        c=ArenaController(extended=True,edition='2027');c.started=1.;c.state='WAIT_PAYLOAD';c.since=1.
        c.acquisition_goal=[22.,21.,-.12]
        c.command((22.,21.,-.12,0.),2.,{'payload_acquired':True})
        self.assertEqual(c.state,'EXIT_TARGET_ZONE')
        c.command((20.6,21.,-.9,0.),3.,{'target_zone_exited':True})
        self.assertEqual(c.state,'TO_PICKUP')
        c.state='FIND_SQUARE';c.command((11.,31.,-.6,math.pi),4.,{})
        self.assertEqual(c.state,'FIND_SQUARE')

    def test_qualification_return_rejects_neighbouring_gate(self):
        from sauvc_sim.qualification import QualificationController
        c=QualificationController(lane=3,physical=True,edition='2027')
        c.started=0.;c.state='FIND_RETURN_GATE';c.gate=(10.,22.)
        command=c.command((11.5,22.,-.6,-math.pi/2),1.,{'bearing':0.,'distance':9.},0.,{})
        self.assertEqual(c.state,'FIND_RETURN_GATE')
        self.assertLess(command[0],0.)
        c.command((13.,22.,-.6,math.pi),2.,{'bearing':0.,'distance':2.68},0.,{})
        self.assertEqual(c.state,'ALIGN_RETURN')

    def test_square_camera_map_uses_marker_edge_offset_and_rejects_oblique_pair(self):
        model=CameraModel();c=ArenaController(edition='2027');c.state='FIND_SQUARE'
        pose=(11.,31.,-.6,math.pi);pixels=[]
        for v in (29.9,31.9):
            du,dv=8.-pose[0],v-pose[1]
            pixels.append(model.pixel((du*math.cos(pose[3])+dv*math.sin(pose[3]),
                                       -du*math.sin(pose[3])+dv*math.cos(pose[3]),.45),'front'))
        obj=dict(label='surfacing_square',confirmed=True,partial=False,position_body_m=[3.,0.,0.],
                 bbox=[100,100,500,160],span_px=abs(pixels[0][0]-pixels[1][0]),
                 center_px=[sum(p[i] for p in pixels)/2 for i in (0,1)])
        packet=dict(fresh=True,valid_image=True,detections=[obj])
        for _ in range(3):c.observe(packet,pose)
        self.assertAlmostEqual(c.targets['surfacing_square'][0],7.,places=5)
        self.assertAlmostEqual(c.targets['surfacing_square'][1],30.9,places=5)
        other=ArenaController(edition='2027');other.state='FIND_SQUARE'
        for _ in range(4):other.observe(packet,(11.,31.,-.6,2.4))
        self.assertNotIn('surfacing_square',other.targets)

    def test_gate_does_not_pair_posts_from_different_lanes(self):
        from sauvc_sim.gate_detection import detect_gate
        image=np.zeros((480,640,3),dtype=np.uint8)
        image[190:250,50:57]=(220,100,0)
        image[190:250,550:557]=(220,100,0)
        self.assertIsNone(detect_gate(image.tobytes(),640,480,1920))
        image[190:250,140:147]=(220,100,0)
        self.assertIsNotNone(detect_gate(image.tobytes(),640,480,1920))
