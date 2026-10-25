"""Visual ARENA mission. The target map contains camera estimates, never prop poses."""
import math
from sauvc_sim.camera_geometry import CameraModel, to_world
from sauvc_sim.referee import wrap
from sauvc_sim.arena import floor_z


def level_rates(roll,pitch):
    return tuple(max(-.4,min(.4,-2*v)) for v in (roll,pitch))


def valid_order(value):
    parts = value.upper().split('-')
    if len(parts) != 3 or set(parts) != {'B','R','Y'}:
        raise ValueError('flare_order must be a permutation of B-R-Y')
    return [dict(B='blue_flare',R='red_flare',Y='yellow_flare')[p] for p in parts]


class ArenaController:
    def __init__(self, extended=False):
        self.state = 'WAIT'
        self.since = 0.
        self.started = None
        self.reason = ''
        self.history = []
        self.targets = {}
        self.pending = {}
        self.order = None
        self.index = 0
        self.avoid = []
        self.avoided = False
        self.goal = None
        self.origin = None
        self.aligned_since = None
        self.release = False
        self.scan = []
        self.extended=extended
        self.grip=False
        self.acoustic_target=None
        self.acoustic_time=-math.inf
        self.acquisition_goal=None

    def change(self, state, t, reason=''):
        if self.state != state:
            self.history.append(dict(state=state,time=t,reason=reason))
            self.state,self.since,self.reason = state,t,reason

    def observe(self, packet, pose):
        if not packet.get('fresh') or not packet.get('valid_image'):
            return
        camera=CameraModel(packet.get('width',640),packet.get('height',480))
        candidates={}
        for obj in packet['detections']:
            if not obj.get('confirmed') or 'position_body_m' not in obj:
                continue
            label = obj['label']
            body=obj['position_body_m']
            if label=='navigation_gate':
                if obj.get('span_px',0)<camera.width*.1: continue
                body=camera.gate_position(obj,pose[3])
                if body is None: continue
            point = to_world(body,pose)
            if label.endswith('_flare') and label != 'orange_flare' and obj['position_body_m'][0] < 1:
                continue
            if not all(math.isfinite(v) for v in point) or not (0<point[0]<25 and 0<point[1]<16):
                continue
            candidates.setdefault(label,[]).append((point,obj))
        for label,choices in candidates.items():
            old=self.targets.get(label)
            if old is not None:
                point,_=min(choices,key=lambda row:math.dist(old[:2],row[0][:2]))
                # Static props cannot jump metres when a thin pole fragments in the image.
                if math.dist(old[:2],point[:2])>.75: continue
                self.targets[label]=[a*.75+b*.25 for a,b in zip(old,point)]
            else:
                point,_=max(choices,key=lambda row:row[1]['bbox'][3]-row[1]['bbox'][1])
                prior,hits=self.pending.get(label,(point,0))
                if math.dist(prior[:2],point[:2])>.4: hits=0
                filtered=[a*.5+b*.5 for a,b in zip(prior,point)] if hits else point
                self.pending[label]=(filtered,hits+1)
                if hits+1>=3: self.targets[label]=filtered

    def go(self, pose, goal, speed=.65, depth=-1.):
        x,y,z,yaw = pose
        dx,dy = goal[0]-x,goal[1]-y
        distance = math.hypot(dx,dy)
        angle = wrap(math.atan2(dy,dx)-yaw)
        turn = max(-.7,min(.7,angle*1.8)) if distance > .05 else 0.
        forward = min(speed,distance*.8) if abs(angle) < .25 else 0.
        return forward,0.,max(-.3,min(.3,(depth-z)*1.5)),turn

    def command(self, pose, t, judgement):
        zero = (0.,0.,0.,0.)
        if self.state in ('ABORT','DONE'):
            return zero
        if not all(math.isfinite(v) for v in (*pose,t)):
            self.change('ABORT',t,'nonfinite_pose')
            return zero
        if judgement.get('phase') == 'FAILED':
            self.change('ABORT',t,judgement.get('reason','referee_failed'))
            return zero
        if self.started is None:
            self.started=t
            self.change('DIVE',t)
        if t-self.started > 850 or (t-self.since > 150 and self.state not in ('SCAN_DRUMS',)):
            self.change('ABORT',t,'mission_or_state_timeout')
            return zero
        x,y,z,yaw = pose
        nav_depth=(-.65 if x<3 or x>22 else -.8) if self.extended else -1.
        if self.state == 'DIVE':
            if z < nav_depth+.06:
                self.change('NAVIGATE',t)
            return 0.,0.,max(-.3,min(.3,(nav_depth-z)*1.8)),0.
        if self.state == 'NAVIGATE':
            if judgement.get('navigation_passed'):
                gate=self.targets.get('navigation_gate')
                self.goal=[x+1.2,y] if gate is None else [gate[0]+1.6,gate[1]]
                self.change('CLEAR_GATE',t)
                return zero
            orange=self.targets.get('orange_flare')
            if orange and not self.avoided and not self.avoid:
                self.avoid=[[orange[0]-1.3,orange[1]-1.3],[orange[0]+1.5,orange[1]-1.3]]
            if self.avoid:
                if math.dist(pose[:2],self.avoid[0]) < .15:
                    self.avoid.pop(0)
                    if not self.avoid: self.avoided=True
                else:
                    return self.go(pose,self.avoid[0],depth=nav_depth)
            gate=self.targets.get('navigation_gate')
            if gate:
                depth=nav_depth if self.extended else max(-1.15,min(-.85,gate[2]))
                return self.go(pose,[gate[0]+1.2,gate[1]],.45,depth)
            if x > 21:
                self.change('ABORT',t,'gate_not_found')
                return zero
            return self.go(pose,[x+2,8.],.45,depth=nav_depth)
        if self.state == 'CLEAR_GATE':
            if math.dist(pose[:2],self.goal) < .15:
                gate=self.targets['navigation_gate']
                self.goal=[gate[0]-1.4,gate[1]]
                self.change('RETURN_GATE',t)
            return self.go(pose,self.goal,.4,depth=nav_depth)
        if self.state == 'RETURN_GATE':
            if math.dist(pose[:2],self.goal) < .15:
                self.change('WAIT_ORDER',t)
                return zero
            return self.go(pose,self.goal,.4,depth=nav_depth)
        if self.state == 'WAIT_ORDER':
            if self.order is not None:
                self.change('FIND_FLARE',t)
            return zero
        if self.state == 'FIND_FLARE':
            label=self.order[self.index]
            if label in self.targets:
                self.goal=list(self.targets[label])
                self.change('APPROACH_FLARE',t)
                return zero
            return 0.,0.,max(-.2,min(.2,(-1.-z)*1.5)),.35
        if self.state == 'APPROACH_FLARE':
            label=self.order[self.index]
            if label in self.targets:
                self.goal=list(self.targets[label])
            if math.dist(pose[:2],self.goal[:2]) < .65:
                self.change('BUMP_FLARE',t)
            return self.go(pose,self.goal,.45)
        if self.state == 'BUMP_FLARE':
            label=self.order[self.index]
            if label in judgement.get('fallen_flares',[]):
                self.origin=pose[:2]
                self.change('BACK_OFF',t)
                return zero
            if t-self.since > 8:
                self.change('ABORT',t,'flare_contact_did_not_drop_ball')
                return zero
            return .18,0.,max(-.2,min(.2,(-1.-z)*1.5)),0.
        if self.state == 'BACK_OFF':
            if math.dist(pose[:2],self.origin) > .75:
                self.index+=1
                if self.index == 3:
                    self.goal=[22.5,.4]
                    self.change('TO_TARGET_ZONE',t)
                else:
                    self.change('FIND_FLARE',t)
                return zero
            return -.3,0.,0.,0.
        if self.state == 'TO_TARGET_ZONE':
            if math.dist(pose[:2],self.goal) < .15:
                self.scan=[]
                for i,scan_x in enumerate((24.,23.7,24.3,23.4,24.6)):
                    ys=(.4,15.6) if i%2==0 else (15.6,.4)
                    self.scan.extend([[scan_x,scan_y] for scan_y in ys])
                self.goal=self.scan.pop(0)
                self.change('SCAN_DRUMS',t)
            return self.go(pose,self.goal,.7,depth=-.12)
        if self.state == 'SCAN_DRUMS':
            if self.extended and self.acoustic_target is not None:
                self.goal=[*self.acoustic_target, -.12]
                self.change('ALIGN_DRUM',t)
                return zero
            if not self.extended and 'blue_drum' in self.targets:
                self.goal=list(self.targets['blue_drum'])
                self.change('ALIGN_DRUM',t)
                return zero
            if math.dist(pose[:2],self.goal) < .08:
                if not self.scan:
                    self.change('ABORT',t,'blue_drum_not_found')
                    return zero
                self.goal=self.scan.pop(0)
            return self.go(pose,self.goal,.15,depth=-.12)
        if self.state == 'ALIGN_DRUM':
            if self.extended:
                if t-self.acoustic_time>.5:
                    self.change('ABORT',t,'stale_acoustics');return zero
                self.goal=[*self.acoustic_target,-.12]
            else:self.goal=list(self.targets.get('blue_drum',self.goal))
            # Payload is 20 cm forward of the body origin, clear of the bottom lens.
            dx,dy=self.goal[0]-(x+.2*math.cos(yaw)),self.goal[1]-(y+.2*math.sin(yaw))
            if math.hypot(dx,dy) < .025:
                if self.aligned_since is None: self.aligned_since=t
                if t-self.aligned_since > 1:
                    self.acquisition_goal=list(self.goal)
                    self.release=True
                    self.change('WAIT_PAYLOAD',t)
                return zero
            self.aligned_since=None
            vx,vy=dx*.8,dy*.8
            return (max(-.2,min(.2,vx*math.cos(yaw)+vy*math.sin(yaw))),
                    max(-.2,min(.2,-vx*math.sin(yaw)+vy*math.cos(yaw))),
                    max(-.2,min(.2,(-.12-z)*1.5)),0.)
        if self.state == 'WAIT_PAYLOAD':
            if judgement.get('payload_acquired' if self.extended else 'payload_in_blue'):
                if self.extended:
                    gate=self.targets['navigation_gate']
                    self.goal=[gate[0]+1.6,gate[1]]
                    self.change('TO_REACQUISITION_GATE',t)
                else:self.change('SURFACE',t)
            elif t-self.since > 8:
                self.change('ABORT',t,'payload_not_inside_blue_drum')
            return zero
        if self.state in ('TO_REACQUISITION_GATE','REACQUISITION_CROSS','REACQUISITION_EXIT'):
            if math.dist(pose[:2],self.goal)<.1:
                gate=self.targets['navigation_gate']
                if self.state=='TO_REACQUISITION_GATE':
                    self.goal=[gate[0]-1.6,gate[1]];self.change('REACQUISITION_CROSS',t)
                elif self.state=='REACQUISITION_CROSS':
                    if not judgement.get('reacquisition_crossed'):
                        self.change('ABORT',t,'missing_reacquisition_crossing');return zero
                    self.goal=[gate[0]+1.6,gate[1]];self.change('REACQUISITION_EXIT',t)
                else:
                    self.goal=list(self.acquisition_goal);self.change('TO_PICKUP',t)
            return self.go(pose,self.goal,.65,depth=nav_depth)
        if self.state=='TO_PICKUP':
            if math.dist(pose[:2],self.goal[:2])<.4:
                self.aligned_since=None;self.change('ALIGN_PICKUP',t)
            return self.go(pose,self.goal,.65,depth=-.12)
        if self.state in ('ALIGN_PICKUP','DESCEND_PICKUP','LIFT_PICKUP'):
            dx,dy=self.goal[0]-(x-.2*math.cos(yaw)),self.goal[1]-(y-.2*math.sin(yaw))
            if self.state=='ALIGN_PICKUP' and math.hypot(dx,dy)<.012:
                self.change('DESCEND_PICKUP',t)
            if self.state=='DESCEND_PICKUP':
                self.grip=True
                if judgement.get('payload_grasped'):
                    self.change('LIFT_PICKUP',t)
                elif t-self.since>15:
                    self.change('ABORT',t,'pickup_not_proven');return zero
            if self.state=='LIFT_PICKUP' and z>-.3:
                self.change('SURFACE',t)
            depth=-.12 if self.state in ('ALIGN_PICKUP','LIFT_PICKUP') else floor_z(self.goal[0])+.49
            return (max(-.12,min(.12,(dx*math.cos(yaw)+dy*math.sin(yaw))*.8)),
                    max(-.12,min(.12,(-dx*math.sin(yaw)+dy*math.cos(yaw))*.8)),
                    max(-.12,min(.12,(depth-z)*1.5)),0.)
        if self.state == 'SURFACE':
            if z >= -.055:
                self.change('STOP',t)
                return zero
            return 0.,0.,min(.25,max(.035,(-.05-z)*1.5)),0.
        if self.state == 'STOP' and judgement.get('passed'):
            self.change('DONE',t)
        return zero
