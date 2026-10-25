"""Independent ARENA task proof from hull contacts and physics ball positions."""
import math
from sauvc_sim.arena import floor_z
from sauvc_sim.referee import envelope, wrap
from sauvc_sim.arena_mission import valid_order
from sauvc_sim.arena_layout import layout
from sauvc_sim.arena_scoring import ArenaScore


class ArenaJudge:
    def __init__(self, order='B-R-Y', scene_variant=0, blue_drum=1, extended=False, pinger_drum=0):
        self.order=valid_order(order)
        self.gate_y=layout(scene_variant)['gate_y']
        if blue_drum not in (1,2,3,4): raise ValueError('invalid blue drum index')
        self.blue_drum=blue_drum-1
        self.extended=extended
        if pinger_drum==0:pinger_drum=next(i for i in range(1,5) if i!=blue_drum)
        self.score=ArenaScore(self.order,self.blue_drum,pinger_drum-1 if extended else None)
        self.payload_acquired=False
        self.payload_grasped=False
        self.payload_retrieved=False
        self.grasp_since=None
        self.gate_side=None
        self.crossing_seen=False
        self.acquisition_since=None
        self.acquisition_candidate=None
        self.phase='START'
        self.reason=''
        self.events=[]
        self.started=None
        self.navigation=False
        self.fallen=[]
        self.contact_times={}
        self.payload_in_blue=False
        self.inside_since=None
        self.surface=False
        self.stopped=False
        self.stop_since=None
        self.previous=None
        self.first_drum=None
        self.ball_initial={}

    def event(self,name,t,**extra):
        self.events.append(dict(event=name,time=t,**extra))
        if name=='NAVIGATION_FULL_CROSSING': self.score.award('navigation',t)
        elif name=='START': self.score.started=t
        elif name=='SURFACE': self.score.finish(t,'surface')

    def fail(self,reason,t):
        if self.phase not in ('FAILED','COMPLETE'):
            self.score.finish(t if math.isfinite(t) else (self.score.last_contact_time or 0.),
                              'training_abort:'+reason)
            self.phase,self.reason='FAILED',reason
            self.event('FAILED',t,reason=reason)

    def update(self,pose,t,contacts=(),zero=True):
        if self.phase in ('FAILED','COMPLETE'): return
        if not all(math.isfinite(v) for v in (*pose,t)):
            self.fail('nonfinite_pose',t);return
        lo,hi,yl,yh,zl,zh=envelope(pose)
        if self.extended:
            # Include the permanently deployed capture tool in the vehicle envelope.
            roll,pitch=pose[3:5] if len(pose)==6 else (0.,0.)
            cr,sr,cp,sp=math.cos(roll),math.sin(roll),math.cos(pitch),math.sin(pitch)
            cy,sy=math.cos(pose[-1]),math.sin(pose[-1])
            for a in (-.24,-.16):
                for b in (-.04,.04):
                    for d in (-.459,-.41):
                        bx,by,bz=a,b*cr-d*sr,b*sr+d*cr
                        bx,bz=bx*cp+bz*sp,-bx*sp+bz*cp
                        px,py,pz=pose[0]+bx*cy-by*sy,pose[1]+bx*sy+by*cy,pose[2]+bz
                        lo,hi,yl,yh,zl,zh=min(lo,px),max(hi,px),min(yl,py),max(yh,py),min(zl,pz),max(zh,pz)
        kinds=set()
        for contact in contacts:
            if 'navigation_gate' in contact: kinds.add('gate')
            if any(k in contact for k in ('wall_','floor_')): kinds.add('pool')
            if 'drum_' in contact: kinds.add('drum')
        self.score.contacts(t,kinds)
        if self.score.end_reason=='automatic_abort':
            self.fail('automatic_abort',t);return
        if self.started is not None and t-self.started>=900:
            self.score.finish(t,'time_limit');self.fail('time_limit',t);return
        if self.started is None:
            self.started=t
            if not (.3 < pose[0] < 1.1 and 7.6 < pose[1] < 8.4):
                self.fail('invalid_start',t);return
            self.event('START',t)
        if self.previous and math.dist(pose[:3],self.previous[:3])>.5:
            self.fail('pose_discontinuity',t);return
        if lo<=0 or hi>=25 or yl<=0 or yh>=16 or zl<=max(floor_z(lo),floor_z(hi)):
            self.fail('pool_envelope',t);return
        if self.phase=='START':
            if hi>1.4 and zh>=-.02:
                self.fail('left_start_before_submerged',t);return
            if zh<-.02:
                self.phase='RUNNING';self.event('UNDERWATER',t)
        elif zh>=0:
            self.score.finish(t,'surface')
            if not (self.navigation and len(self.fallen)==3 and
                    (self.payload_acquired and self.payload_retrieved if self.extended else self.payload_in_blue)):
                self.fail('premature_surface',t);return
            if not self.surface:
                self.surface=True;self.event('SURFACE',t)
        for contact in contacts:
            if 'orange_flare' in contact:
                self.fail('orange_flare_contact',t);return
            for label in self.order:
                if label+'::' in contact:
                    if not self.navigation:
                        self.fail('flare_before_navigation',t);return
                    self.contact_times.setdefault(label,t)
            if any(k in contact for k in ('wall_','floor_','navigation_gate','drum_')):
                self.fail('training_contact:'+contact,t);return
        if (self.extended or not self.navigation) and lo<=16.025 and hi>=15.975:
            if yl<=self.gate_y-.75 or yh>=self.gate_y+.75 or zl<=floor_z(16) or zh>=floor_z(16)+1:
                if not self.navigation:
                    self.fail('outside_navigation_opening',t);return
                self.crossing_seen=False
            else:self.crossing_seen=True
        side=1 if lo>16.025 else -1 if hi<15.975 else None
        if side is not None:
            if self.gate_side is not None and side!=self.gate_side and self.crossing_seen and self.score.acquisition is not None:
                self.score.award('navigation',t)
                self.event('REACQUISITION_FULL_CROSSING',t)
            if side!=self.gate_side:self.crossing_seen=False
            self.gate_side=side
        if not self.navigation and lo>16.025:
            if abs(wrap(pose[-1]))>math.pi/3:
                self.fail('navigation_direction',t);return
            self.navigation=True
            self.event('NAVIGATION_FULL_CROSSING',t)
            self.event('ORDER_ISSUED',t,order=self.order)
        if self.surface:
            moved=self.previous is None or math.dist(pose[:3],self.previous[:3])>.001 or abs(wrap(pose[-1]-self.previous[-1]))>.001
            if not zero or moved: self.stop_since=None
            elif self.stop_since is None: self.stop_since=t
            elif t-self.stop_since>=1 and not self.stopped:
                self.stopped=True;self.phase='COMPLETE';self.event('STOPPED',t)
        self.previous=pose

    def physics(self,data):
        if self.phase in ('FAILED','COMPLETE'): return
        t=data['time']
        for label,ball in data['balls'].items():
            pos=ball['position']
            if not all(math.isfinite(v) for v in pos):
                self.fail('nonfinite_ball_pose',t);return
            if not ball['released']:
                self.ball_initial[label]=pos[2]
            if label in self.order and ball['released'] and label not in self.fallen:
                if label in self.ball_initial and pos[2]<self.ball_initial[label]-.12:
                    if not self.navigation or label not in self.contact_times:
                        self.fail('ball_drop_without_legal_contact',t);return
                    self.score.award('flare',t,label=label)
                    if label != self.order[len(self.fallen)]:
                        self.fail('wrong_flare_order',t);return
                    self.fallen.append(label);self.event('FLARE_BALL_FELL',t,label=label,position=pos)
        ball=data['balls'].get('payload',{})
        if not ball.get('released'): return
        self.score.award('payload',t,ball_id='payload')
        x,y,z=ball['position']
        drum=next((i for i,cy in enumerate((12.5,9.5,6.5,3.5))
                   if math.hypot(x-24,y-cy)<.255 and floor_z(24)+.02<z<floor_z(24)+.16),None)
        if drum != self.acquisition_candidate:
            self.acquisition_candidate=drum;self.acquisition_since=t if drum is not None else None
        if drum is not None and self.acquisition_since is not None and t-self.acquisition_since>.5:
            self.score.award('acquisition',t,ball_id='payload',drum=drum)
            self.payload_acquired=self.score.acquisition is not None
        if self.extended and self.previous is not None:
            pose=self.previous;yaw=pose[-1]
            point=(pose[0]-.2*math.cos(yaw),pose[1]-.2*math.sin(yaw),pose[2]-.45)
            attached=bool(data.get('payload_attached')) and math.dist((x,y,z),point)<.075
            self.payload_grasped=attached and self.score.retrieval_crossing
            if self.payload_grasped:
                if self.grasp_since is None:
                    self.grasp_since=t;self.event('PAYLOAD_GRASPED',t,position=[x,y,z])
                if t-self.grasp_since>.5 and not self.payload_retrieved:
                    self.payload_retrieved=True
                    self.score.award('retrieval',t,ball_id='payload',held=True)
            else:
                self.grasp_since=None
                if self.payload_retrieved:
                    self.event('PAYLOAD_RETENTION_LOST',t)
                    self.score.award('retrieval',t,ball_id='payload',held=False)
                self.payload_retrieved=False
        if drum is not None and self.first_drum is None:
            self.first_drum=drum;self.event('FIRST_PAYLOAD_INSIDE_DRUM',t,drum=drum+1,position=[x,y,z])
        if drum==self.blue_drum and self.first_drum==self.blue_drum and self.navigation and len(self.fallen)==3:
            if self.inside_since is None: self.inside_since=t
            if t-self.inside_since>.5 and not self.payload_in_blue:
                self.payload_in_blue=True;self.event('PAYLOAD_SETTLED_BLUE',t,position=[x,y,z])
        else:
            self.inside_since=None

    def result(self):
        return dict(payload_acquired=self.payload_acquired,payload_grasped=self.payload_grasped,
                    payload_retrieved=self.payload_retrieved,reacquisition_crossed=self.score.retrieval_crossing,
                    score=self.score.result(),scoring_policy='strict_training_abort',phase=self.phase,reason=self.reason,navigation_passed=self.navigation,
                    fallen_flares=self.fallen,payload_in_blue=self.payload_in_blue,
                    surface_completed=self.surface,stopped=self.stopped,
                    passed=self.phase!='FAILED' and self.navigation and len(self.fallen)==3
                           and (self.payload_acquired and self.payload_retrieved if self.extended else self.payload_in_blue) and self.surface and self.stopped,
                    events=self.events)
