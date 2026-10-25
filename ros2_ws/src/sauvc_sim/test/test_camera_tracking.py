import math
import unittest
from sauvc_sim.camera_geometry import CameraModel, to_world, PoseHistory
from sauvc_sim.tracking import Tracker


class CameraTest(unittest.TestCase):
    def gate_observation(self, pose):
        model=CameraModel()
        x,y,z,yaw=pose
        pixels=[]
        for post_y in (8.6-.775,8.6+.775):
            dx,dy=16.-x,post_y-y
            point=(dx*math.cos(yaw)+dy*math.sin(yaw),
                   -dx*math.sin(yaw)+dy*math.cos(yaw),-.988-z)
            pixels.append(model.pixel(point,'front'))
        return dict(span_px=abs(pixels[0][0]-pixels[1][0]),partial=False,
                    center_px=[sum(p[i] for p in pixels)/2 for i in (0,1)])

    def test_gate_plane_projection_oblique_and_reverse(self):
        model=CameraModel()
        for pose in ((5.,6.9,-1.,-.25),(10.,7.3,-1.,.3),(19.,8.4,-1.,math.pi+.2)):
            obj=self.gate_observation(pose)
            corrected=to_world(model.gate_position(obj,pose[3]),pose)
            self.assertAlmostEqual(corrected[0],16.,places=6)
            self.assertAlmostEqual(corrected[1],8.6,places=6)
        self.assertIsNone(model.gate_position(dict(obj,partial=True),0.))
        self.assertIsNone(model.gate_position(dict(obj,span_px=0.),0.))
        self.assertIsNone(model.gate_position(obj,math.pi/2))

    def test_image_pose_interpolates_turn_and_rejects_old_frames(self):
        poses=PoseHistory()
        poses.add(1.,(1.,0.,-1.,3.1))
        poses.add(1.2,(2.,0.,-1.,-3.1))
        mid=poses.at(1.1)
        self.assertAlmostEqual(mid[0],1.5)
        self.assertAlmostEqual(mid[3],math.pi)
        self.assertIsNone(poses.at(.5))
        self.assertIsNone(poses.at(2.))
        poses.add(.2,(0.,0.,-1.,0.))
        self.assertIsNone(poses.at(1.))

    def test_extrinsics_and_projection_round_trip(self):
        model=CameraModel()
        for camera,point in [('front',(3.,.3,-.2)),('bottom',(.2,-.3,-1.1))]:
            pixel=model.pixel(point,camera)
            ray,origin=model.ray(pixel,camera)
            depth=(point[0]-.32) if camera=='front' else -point[2]-.12
            for a,b in zip(point,[origin[i]+ray[i]*depth for i in range(3)]):
                self.assertAlmostEqual(a,b)
        self.assertIsNone(model.pixel((0.,0.,0.),'front'))
        self.assertEqual(to_world((1.,0.,-.1),(2.,3.,-.5,math.pi/2)),[2.,4.,-.6])

    def test_known_dimensions_and_partial_rejection(self):
        model=CameraModel()
        obj=dict(label='navigation_gate',bbox=[100,100,400,300],span_px=300.,
                 center_px=[319.5,239.5],partial=False)
        loc=model.locate(obj,'front')
        self.assertAlmostEqual(loc['position_body_m'][0],.32+model.focal*1.55/300)
        self.assertAlmostEqual(loc['position_body_m'][1],0.)
        self.assertIsNone(model.locate(dict(obj,partial=True),'front'))
        obj.update(label='blue_drum',bbox=[200,100,400,300])
        self.assertLess(model.locate(obj,'bottom')['position_body_m'][2],-.12)
        obj.update(label='blue_flare',bbox=[200,100,202,120])
        self.assertIsNone(model.locate(obj,'front'))
        with self.assertRaises(ValueError): CameraModel(hfov=0)


class TrackingTest(unittest.TestCase):
    def obj(self,x,label='blue_flare'):
        return dict(label=label,center_px=[x,100.],bbox=[x-2,50,x+2,150])

    def test_confirmation_motion_occlusion_and_expiry(self):
        tracker=Tracker()
        a=tracker.update([self.obj(100)],1.)[0]
        self.assertFalse(a['confirmed'])
        self.assertEqual(tracker.update([self.obj(110)],1.1)[0]['track_id'],a['track_id'])
        self.assertTrue(tracker.update([self.obj(120)],1.2)[0]['confirmed'])
        self.assertEqual(tracker.update([],1.3),[])
        self.assertEqual(tracker.update([self.obj(140)],1.4)[0]['track_id'],a['track_id'])
        self.assertNotEqual(tracker.update([self.obj(140)],2.2)[0]['track_id'],a['track_id'])

    def test_one_to_one_classes_and_timestamp_reset(self):
        tracker=Tracker()
        a=tracker.update([self.obj(100),self.obj(130),self.obj(100,'red_flare')],1.)
        self.assertEqual(len({x['track_id'] for x in a}),3)
        b=tracker.update([self.obj(105),self.obj(135)],1.1)
        self.assertEqual([x['track_id'] for x in b],[x['track_id'] for x in a[:2]])
        self.assertEqual(tracker.update([self.obj(105)],1.1),[])
        self.assertFalse(tracker.update([self.obj(105)],.5)[0]['confirmed'])
        tracker.clear()
        self.assertFalse(tracker.update([self.obj(105)],.6)[0]['confirmed'])
