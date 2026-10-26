import unittest
from sauvc_sim.arena_scoring import ArenaScore
from sauvc_sim.arena_mission import valid_order


class ScoringTest(unittest.TestCase):
    def score(self):
        s=ArenaScore(valid_order('R-B-Y'),0,1);s.started=0
        s.award('navigation',1)
        return s

    def acquire(self,s,drum=0,ball='one'):
        s.award('payload',2,ball_id=ball)
        s.award('acquisition',3,ball_id=ball,drum=drum)

    def test_rulebook_examples(self):
        for case,expected in [(1,18),(2,15),(3,40+26.88),(4,85),(5,85+15),(6,105+15),(7,185)]:
            # Example 4 total has an arithmetic discrepancy; sum its listed components.
            # Examples 3/5/6 omit the timing bonus despite the formula applying to aborts.
            s=self.score()
            if case==1:s.contacts(2,{'gate'})
            if case>=3:self.acquire(s)
            if case==3:s.contacts(4,{'pool'})
            labels={4:['red_flare'],5:['red_flare','yellow_flare'],6:['red_flare','yellow_flare','blue_flare'],7:s.order}.get(case,[])
            for i,label in enumerate(labels):s.award('flare',10+i,label=label)
            s.finish(4 if case<4 else 400,'surface' if case in (1,4,7) else 'abort')
            self.assertAlmostEqual(s.result()['attempt_total'],expected,msg=str(case))

    def test_first_payload_miss_or_red_cannot_be_overridden(self):
        s=self.score();s.award('payload',2,ball_id='miss')
        self.acquire(s,ball='second');self.assertIsNone(s.acquisition)
        self.acquire(s,2,ball='miss');self.acquire(s,0,ball='miss')
        self.assertEqual(s.result()['target_acquisition'],10)
        s=self.score();self.acquire(s,1);self.assertEqual(s.result()['target_acquisition'],50)

    def test_retrieval_requires_same_ball_extra_full_crossing_and_retention(self):
        s=self.score();self.acquire(s)
        s.award('retrieval',5,ball_id='one',held=True);self.assertFalse(s.retrieved)
        s.award('navigation',6)
        s.award('retrieval',7,ball_id='other',held=True);self.assertFalse(s.retrieved)
        s.award('retrieval',8,ball_id='one',held=True);self.assertTrue(s.retrieved)
        s.award('retrieval',9,ball_id='one',held=False);self.assertFalse(s.retrieved)

    def test_continuous_contact_deduplicated_and_automatic_abort(self):
        s=self.score()
        for t in (2,3,4):s.contacts(t,{'gate','pool'})
        self.assertEqual(s.penalties,7);self.assertEqual(s.pool_touches,1)
        s.contacts(12,{'pool'});self.assertIsNone(s.ended)
        s.contacts(12.01,{'pool'});self.assertEqual(s.end_reason,'automatic_abort')
        s=self.score()
        for t in range(5):s.contacts(t*2,{'pool'});s.contacts(t*2+1,set())
        self.assertEqual(s.end_reason,'automatic_abort');self.assertEqual(s.penalties,25)

    def test_surface_abort_final_and_no_double_award(self):
        s=self.score()
        for _ in range(3):s.award('flare',3,label='red_flare')
        self.assertEqual(s.result()['communication_localization'],20)
        s.finish(901,'abort');a=s.result();self.assertEqual(a['timing_bonus'],0)
        s.finish(903,'surface');s.contacts(904,{'pool'})
        self.assertEqual(s.result(),a)


class PhysicsScoreIntegrationTest(unittest.TestCase):
    def test_release_alone_does_not_score_and_settling_is_independent_of_flare_task(self):
        from sauvc_sim.arena_referee import ArenaJudge
        j=ArenaJudge();j.navigation=True;j.score.started=0;j.score.award('navigation',1)
        def frame(t,z):
            return dict(time=t,balls={'payload':dict(position=[24.,12.5,z],released=True)})
        j.physics(frame(2.,-.5));self.assertEqual(j.result()['score']['target_acquisition'],0)
        j.physics(frame(3.,-1.19));j.physics(frame(3.6,-1.19))
        self.assertEqual(j.result()['score']['target_acquisition'],30)
        self.assertFalse(j.payload_in_blue)
        j.fail('controller_aborted',5.)
        self.assertEqual(j.result()['score']['target_acquisition'],30)
        self.assertEqual(j.result()['score']['surface_bonus'],0)

    def test_strict_abort_preserves_flare_points_without_order_bonus(self):
        from sauvc_sim.arena_referee import ArenaJudge
        j=ArenaJudge();j.navigation=True;j.score.started=0;j.score.award('navigation',1)
        j.contact_times['red_flare']=2
        j.physics(dict(time=2.,balls={'red_flare':dict(position=[14.,12.,-.7],released=False)}))
        j.physics(dict(time=3.,balls={'red_flare':dict(position=[14.,12.,-1.],released=True)}))
        self.assertEqual(j.reason,'wrong_flare_order')
        self.assertEqual(j.result()['score']['communication_localization'],20)
        self.assertEqual(j.result()['score']['flare_order_bonus'],0)

    def test_partial_surface_scores_ending_even_when_training_incomplete(self):
        from sauvc_sim.arena_referee import ArenaJudge
        j=ArenaJudge()
        for t,z in [(0.,-.05),(1.,-.35),(2.,-.05)]:j.update((.7,8.,z,0.),t)
        self.assertEqual(j.reason,'premature_surface')
        self.assertEqual(j.result()['score']['surface_bonus'],5)
        self.assertEqual(j.result()['score']['end_reason'],'surface')
        invalid=ArenaJudge();invalid.update((.7,8.,-.05,0.),float('nan'))
        self.assertEqual(invalid.reason,'nonfinite_pose')
