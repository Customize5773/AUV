import math
import unittest
from sauvc_sim.arena_mission import ArenaController,valid_order
from sauvc_sim.arena_referee import ArenaJudge
from sauvc_sim.camera_geometry import CameraModel


class ArenaMissionTest(unittest.TestCase):
    def test_gate_mapping_corrects_short_oblique_range_before_crossing(self):
        model=CameraModel()
        pose=(10.,7.3,-1.,.3)
        pixels=[]
        for y in (8.6-.775,8.6+.775):
            dx,dy=16.-pose[0],y-pose[1]
            pixels.append(model.pixel((dx*math.cos(.3)+dy*math.sin(.3),
                                     -dx*math.sin(.3)+dy*math.cos(.3),.012),'front'))
        obj=dict(label='navigation_gate',confirmed=True,position_body_m=[5.,0.,0.],
                 bbox=[200,180,340,300],partial=False,
                 span_px=abs(pixels[0][0]-pixels[1][0]),
                 center_px=[sum(p[i] for p in pixels)/2 for i in (0,1)])
        packet=dict(fresh=True,valid_image=True,detections=[obj])
        ctrl=ArenaController()
        for _ in range(3): ctrl.observe(packet,pose)
        self.assertAlmostEqual(ctrl.targets['navigation_gate'][0],16.,places=6)
        self.assertAlmostEqual(ctrl.targets['navigation_gate'][1],8.6,places=6)
        ctrl.started=1.;ctrl.state='NAVIGATE';ctrl.since=1.;ctrl.avoided=True
        command=ctrl.command((16.233,8.6,-1.,0.),2.,{})
        self.assertGreater(command[0],0.)
        self.assertEqual(ctrl.state,'NAVIGATE')
        ctrl.command((16.4,8.6,-1.,0.),3.,dict(navigation_passed=True))
        self.assertEqual(ctrl.state,'CLEAR_GATE')
        other=ArenaController()
        obj['span_px']=20.
        for _ in range(3): other.observe(packet,pose)
        self.assertNotIn('navigation_gate',other.targets)

    def test_order_validation_and_camera_map_only_confirmed(self):
        self.assertEqual(valid_order('r-b-y'),['red_flare','blue_flare','yellow_flare'])
        for value in ('B-B-Y','B-R','B-R-Y-Z'):
            with self.assertRaises(ValueError): valid_order(value)
        ctrl=ArenaController()
        obj={'label':'blue_flare','position_body_m':[2.,0.,0.],'confirmed':False,
             'bbox':[100,50,104,150]}
        packet=dict(fresh=True,valid_image=True,detections=[obj])
        ctrl.observe(packet,(1.,2.,-1.,0.))
        self.assertEqual(ctrl.targets,{})
        obj['confirmed']=True
        for _ in range(3): ctrl.observe(packet,(1.,2.,-1.,0.))
        self.assertEqual(ctrl.targets['blue_flare'],[3.,2.,-1.])
        packet['fresh']=False;obj['position_body_m']=[10.,0.,0.]
        ctrl.observe(packet,(1.,2.,-1.,0.))
        self.assertEqual(ctrl.targets['blue_flare'],[3.,2.,-1.])

    def test_fragmented_flare_cannot_move_an_established_landmark(self):
        ctrl=ArenaController();ctrl.targets['yellow_flare']=[12.4,4.5,-1.2]
        def obj(point,height):
            return dict(label='yellow_flare',confirmed=True,position_body_m=point,
                        bbox=[100,100,102,100+height])
        packet=dict(fresh=True,valid_image=True,detections=[obj([21.,4.,-1.2],35),obj([12.45,4.5,-1.2],70)])
        ctrl.observe(packet,(0.,0.,0.,0.))
        self.assertLess(abs(ctrl.targets['yellow_flare'][0]-12.4),.02)
        packet['detections']=[obj([21.,4.,-1.2],35)]
        ctrl.observe(packet,(0.,0.,0.,0.))
        self.assertLess(abs(ctrl.targets['yellow_flare'][0]-12.4),.02)

    def test_failure_stops_and_release_waits_for_physical_proof(self):
        ctrl=ArenaController()
        ctrl.started=1.;ctrl.state='WAIT_PAYLOAD';ctrl.since=2.
        self.assertEqual(ctrl.command((24.,12.5,-.25,0.),3.,{}),(0.,0.,0.,0.))
        self.assertEqual(ctrl.state,'WAIT_PAYLOAD')
        ctrl.command((24.,12.5,-.25,0.),4.,{'payload_in_blue':True})
        self.assertEqual(ctrl.state,'SURFACE')
        self.assertEqual(ctrl.command((24.,12.5,-.25,0.),5.,{'phase':'FAILED','reason':'contact'}),(0.,0.,0.,0.))
        self.assertEqual(ctrl.state,'ABORT')
        other=ArenaController()
        self.assertEqual(other.command((float('nan'),0.,-1.,0.),1.,{}),(0.,0.,0.,0.))
        self.assertEqual(other.reason,'nonfinite_pose')

    def test_alignment_centres_payload_offset_before_release(self):
        ctrl=ArenaController();ctrl.started=1.;ctrl.state='ALIGN_DRUM';ctrl.since=2.
        ctrl.goal=[24.,12.5,-.9]
        cmd=ctrl.command((24.,12.5,-.12,0.),3.,{})
        self.assertLess(cmd[0],0.)
        self.assertFalse(ctrl.release)
        self.assertEqual(ctrl.command((23.8,12.5,-.12,0.),4.,{}),(0.,0.,0.,0.))
        ctrl.command((23.8,12.5,-.12,0.),5.1,{})
        self.assertTrue(ctrl.release)
        self.assertEqual(ctrl.state,'WAIT_PAYLOAD')

    def test_search_sweeps_other_rows_if_blue_drum_not_seen(self):
        ctrl=ArenaController();ctrl.started=1.;ctrl.state='TO_TARGET_ZONE';ctrl.since=2.
        ctrl.goal=[22.5,.4]
        ctrl.command((22.5,.4,-.12,0.),3.,{})
        self.assertEqual(ctrl.state,'SCAN_DRUMS')
        self.assertEqual(ctrl.goal,[24.,.4])
        while ctrl.scan:
            ctrl.command((*ctrl.goal,-.12,0.),4.,{})
        ctrl.command((*ctrl.goal,-.12,0.),5.,{})
        self.assertEqual(ctrl.state,'ABORT')
        self.assertEqual(ctrl.reason,'blue_drum_not_found')


class ArenaJudgeTest(unittest.TestCase):
    def start(self):
        judge=ArenaJudge()
        judge.update((.7,8.,-.05,0.),0.)
        judge.update((.7,8.,-.35,0.),.3)
        judge.update((.7,8.,-.65,0.),.6)
        judge.update((.7,8.,-1.,0.),1.)
        return judge

    def test_partial_crossing_is_not_navigation_and_early_flare_aborts(self):
        judge=self.start()
        judge.previous=None
        judge.update((16.,8.,-1.,0.),2.)
        self.assertFalse(judge.navigation)
        judge.update((16.4,8.,-1.,0.),3.)
        self.assertTrue(judge.navigation)
        other=self.start()
        other.update((.7,8.,-1.,0.),2.,['blue_flare::body::pole'])
        self.assertEqual(other.reason,'flare_before_navigation')

    def test_orange_and_premature_surface_fail(self):
        for contact in ('orange_flare::body::pole','wall_start::body::wall'):
            judge=self.start();judge.update((.7,8.,-1.,0.),2.,[contact])
            self.assertEqual(judge.phase,'FAILED')
        judge=self.start()
        judge.update((.7,8.,-.6,0.),1.3)
        judge.update((.7,8.,-.3,0.),1.6)
        judge.update((.7,8.,-.05,0.),2.)
        self.assertEqual(judge.reason,'premature_surface')

    def test_release_does_not_score_and_wrong_order_fails(self):
        judge=self.start();judge.navigation=True
        judge.contact_times['red_flare']=2.
        judge.physics(dict(time=1.,balls={'red_flare':dict(position=[14.,12.,-.7],released=False)}))
        judge.physics(dict(time=2.,balls={'red_flare':dict(position=[14.,12.,-.7],released=True)}))
        self.assertEqual(judge.fallen,[])
        judge.physics(dict(time=3.,balls={'red_flare':dict(position=[14.,12.,-1.],released=True)}))
        self.assertEqual(judge.reason,'wrong_flare_order')

    def test_blue_inside_requires_first_ball_settled_and_legal_tasks(self):
        judge=self.start();judge.navigation=True;judge.fallen=list(judge.order)
        def frame(t,x=24.,y=12.5,z=-1.19):
            return dict(time=t,balls={'payload':dict(position=[x,y,z],released=True)})
        judge.physics(frame(2.,x=23.6))
        self.assertFalse(judge.payload_in_blue)
        judge.physics(frame(3.));self.assertFalse(judge.payload_in_blue)
        judge.physics(frame(3.6));self.assertTrue(judge.payload_in_blue)
        other=self.start();other.navigation=True;other.fallen=list(other.order)
        other.physics(frame(2.,y=9.5));other.physics(frame(3.));other.physics(frame(4.))
        self.assertFalse(other.payload_in_blue)
        self.assertEqual(other.first_drum,1)

    def test_completed_result_is_terminal_during_shutdown(self):
        judge=self.start();judge.navigation=True;judge.fallen=list(judge.order)
        judge.payload_in_blue=True
        for t,z in ((2.,-.6),(3.,-.3),(4.,-.05),(4.5,-.05),(5.6,-.05)):
            judge.update((.7,8.,z,0.),t)
        self.assertTrue(judge.result()['passed'])
        self.assertEqual(judge.phase,'COMPLETE')
        judge.fail('stale_clock',6.)
        self.assertTrue(judge.result()['passed'])
