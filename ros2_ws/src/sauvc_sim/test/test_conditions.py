import json
import tempfile
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path
from sauvc_sim.conditions import conditions,load_conditions
from sauvc_sim.arena import build_world
from sauvc_sim.state_estimation import StateEstimator


class ConditionsTest(unittest.TestCase):
    def test_current_seed_and_light_reach_world_without_moving_true_spawn(self):
        values=dict(seed=7,current=[.02,-.01,0.],prior_error=[.1,-.1],light_scale=.7)
        world=ET.fromstring(build_world('finals',physical=True,test_conditions=values)).find('world')
        baseline=ET.fromstring(build_world('finals',physical=True)).find('world')
        self.assertEqual(world.findtext("model[@name='sauvc_auv']/pose"),baseline.findtext("model[@name='sauvc_auv']/pose"))
        plant=world.find("plugin[@name='sauvc::VehicleDynamics']")
        self.assertEqual(plant.findtext('seed'),'7')
        self.assertEqual(list(map(float,plant.findtext('current').split())),[.02,-.01,0.])
        self.assertAlmostEqual(float(world.findtext('scene/ambient').split()[0]),.65*.7)
        self.assertAlmostEqual(float(world.findtext('light/diffuse').split()[0]),.9*.7)
        est=StateEstimator(edition='2027',arena='finals',prior_error=values['prior_error'])
        self.assertAlmostEqual(est.x,34.1);self.assertAlmostEqual(est.y,.6)

    def test_qualification_prior_error_is_applied_once_after_heading_initialization(self):
        from test_dynamics import EstimationTest
        a=StateEstimator(edition='2027');b=StateEstimator(edition='2027',prior_error=(.1,-.1))
        for i in range(10):
            packet=EstimationTest().packet(i*.02)
            self.assertTrue(a.update(packet));self.assertTrue(b.update(packet))
        self.assertAlmostEqual(b.x-a.x,.1);self.assertAlmostEqual(b.y-a.y,-.1)

    def test_invalid_conditions_fail_instead_of_silently_changing_test(self):
        for value in ([],{'sead':7},{'seed':-1},{'seed':True},{'seed':2**32},
                      {'current':[0,0]},{'prior_error':[0,float('nan')]},{'light_scale':0}):
            with self.subTest(value=value),self.assertRaises(ValueError):conditions(value)
        with self.assertRaises(ValueError):build_world('finals',test_conditions={'current':[.02,0,0]})
        with tempfile.TemporaryDirectory() as d:
            path=Path(d)/'conditions.json';path.write_text(json.dumps({'seed':7}))
            self.assertEqual(load_conditions(path)['seed'],7)
            self.assertEqual(load_conditions()['current'],[0,0,0])
