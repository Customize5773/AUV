"""Visual ARENA mission. The target map contains camera estimates, never prop poses."""
import math
import numpy as np
from sauvc_sim.camera_geometry import CameraModel, to_world
from sauvc_sim.referee import wrap
from sauvc_sim.arena import floor_z, PICKUP_X, PICKUP_Z
from sauvc_sim.vehicle_geometry import HULL_SIZE, COMPACT_RADIUS, COMPACT_CAMERA_TILT, COMPACT_RIM_CLEARANCE, PICKUP_RIM_CLEARANCE
from sauvc_sim.rules2027 import floor_z as floor2027


def level_rates(roll,pitch):
    return tuple(max(-.4,min(.4,-2*v)) for v in (roll,pitch))


def drum_center(points):
    if len(points)<10:return None
    xy=np.asarray(points)[:,:2]
    mean=xy.mean(axis=0)
    xy=xy-mean
    if np.linalg.svd(xy,compute_uv=False)[-1]<.10:return None
    fit=np.linalg.lstsq(np.column_stack((2*xy,np.ones(len(xy)))),
                        np.sum(xy*xy,axis=1),rcond=None)[0][:2]
    radii=np.linalg.norm(xy-fit,axis=1)
    if abs(radii.mean()-.28)>.018 or np.max(abs(radii-radii.mean()))>.009:return None
    return (fit+mean).tolist()


def pickup_clearance(ball, center, yaw):
    """Conservative circular inner wall, including 5 mm horizontal uncertainty."""
    scale=COMPACT_RADIUS/math.hypot(HULL_SIZE[0]/2,HULL_SIZE[1]/2)
    c,s=math.cos(yaw),math.sin(yaw)
    dx,dy=ball[0]-center[0],ball[1]-center[1]
    radii=[math.hypot(dx+c*x-s*y,dy+s*x+c*y)
           for x in (-HULL_SIZE[0]*scale/2,HULL_SIZE[0]*scale/2)
           for y in (-HULL_SIZE[1]*scale/2,HULL_SIZE[1]*scale/2)]
    return .28-max(radii)-.005


def pickup_heading(ball, center, yaw):
    dx,dy=ball[0]-center[0],ball[1]-center[1]
    if math.hypot(dx,dy)<.012:return yaw
    # Place the long side tangential to the rim; either end may lead.
    tangent=math.atan2(dy,dx)+math.pi/2
    return yaw+min((wrap(tangent-yaw),wrap(tangent+math.pi-yaw)),key=abs)


def valid_order(value):
    parts = value.upper().split('-')
    if len(parts) != 3 or set(parts) != {'B','R','Y'}:
        raise ValueError('flare_order must be a permutation of B-R-Y')
    return [dict(B='blue_flare',R='red_flare',Y='yellow_flare')[p] for p in parts]


class ArenaController:
    def __init__(self, extended=False,edition='2026',physical=False,prefer_pinger=False,compact=False):
        self.compact=compact
        self.physical=physical
        self.cruise_depth=-.3 if physical else -.12
        self.edition=edition
        self.flare_depth=-1.45 if edition=='2027' else -1.
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
        self.prefer_pinger=prefer_pinger or extended
        self.selected_drum=None
        self.extended=extended
        self.grasp_since=None
        self.grip=False
        self.acoustic_target=None
        self.acoustic_time=-math.inf
        self.tilt_since=None
        self.attitude=(0.,0.)
        self.estimated_speed=0.
        self.brake_origin=None
        self.lowering=False
        self.ball_fix_time=-math.inf
        self.visual_drum_center=None
        self.clearance_wait=None
        self.pickup_alignment=None
        self.ball_fix_count=0
        self.ball_fix=None
        self.acquisition_goal=None

    def change(self, state, t, reason=''):
        if self.state != state:
            self.history.append(dict(state=state,time=t,reason=reason))
            self.state,self.since,self.reason = state,t,reason

    def observe(self, packet, pose):
        if not packet.get('fresh') or not packet.get('valid_image'):
            return
        camera=CameraModel(packet.get('width',640),packet.get('height',480),
                           bottom_tilt=COMPACT_CAMERA_TILT if self.compact else 0.)
        candidates={}
        for obj in packet['detections']:
            if (self.compact and self.state in ('ALIGN_PICKUP','DESCEND_PICKUP')
                    and packet.get('camera')=='bottom' and obj['label']=='payload_ball'
                    and obj.get('confirmed')):
                cr,sr=math.cos(self.attitude[0]),math.sin(self.attitude[0])
                cp,sp=math.cos(self.attitude[1]),math.sin(self.attitude[1])
                def level(vec):
                    x,y,z=vec
                    return (cp*x+sp*(sr*y+cr*z),cr*y-sr*z,-sp*x+cp*(sr*y+cr*z))
                def project(pixel,height):
                    ray,origin=camera.ray(pixel,'bottom')
                    origin,ray=level(origin),level(ray)
                    if ray[2]>=-.1:return None
                    distance=(height-pose[2]-origin[2])/ray[2]
                    if distance<=0:return None
                    return to_world([o+distance*r for o,r in zip(origin,ray)],pose)
                point=project(obj['center_px'],-1.96)
                if point and math.dist(point[:2],self.acquisition_goal[:2])<.28:
                    if self.state=='ALIGN_PICKUP':
                        edge=(project(px,-1.98) for px in obj.get('drum_floor_edge_px',[]))
                        self.visual_drum_center=drum_center([p for p in edge if p is not None])
                    stamp=packet['stamp']
                    self.ball_fix_time=stamp['sec']+stamp['nanosec']*1e-9
                    self.ball_fix_count+=1
                    self.ball_fix=point
            if not obj.get('confirmed') or 'position_body_m' not in obj:
                continue
            label = obj['label']
            if label=='surfacing_square' and self.edition=='2027' and (self.state not in ('TO_SQUARE','FIND_SQUARE','ALIGN_SQUARE') or abs(math.sin(pose[3]))>.15):continue
            body=obj['position_body_m']
            if label in ('navigation_gate','surfacing_square'):
                if obj.get('span_px',0)<camera.width*.1: continue
                body=camera.gate_position(obj,pose[3],span_m=2. if label=='surfacing_square' else 1.55)
                if body is None: continue
            point = to_world(body,pose)
            if label=='surfacing_square':point[0]+=math.copysign(1.,math.cos(pose[3]))
            if label.endswith('_flare') and label != 'orange_flare':
                # A 0.8 m pole stands on the configured pool floor. Surface
                # markers and fragmented poles cannot supply its metric height.
                floor=floor2027(42-point[1]) if self.edition=='2027' else floor_z(point[0])
                if abs(point[2]-(floor+.4))>.25:continue
            if label.endswith('_flare') and label != 'orange_flare' and obj['position_body_m'][0] < 1:
                continue
            if not all(math.isfinite(v) for v in point) or not (0<point[0]<25 and (-8<point[1]<42 if self.edition=='2027' else 0<point[1]<16)):
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
            if self.extended and (COMPACT_RIM_CLEARANCE if self.compact else PICKUP_RIM_CLEARANCE)<0:
                self.change('ABORT',t,'fixed_gripper_unreachable');return zero
            self.started=t
            self.change('DIVE',t)
        if t-self.started > 850 or (t-self.since > 150 and self.state not in ('SCAN_DRUMS',)):
            self.change('ABORT',t,'mission_or_state_timeout')
            return zero
        x,y,z,yaw = pose
        nav_depth=-1. if self.edition=='2027' else (-.65 if x<3 or x>22 else -.8)
        if self.state == 'DIVE':
            if z < nav_depth+.06:
                self.change('NAVIGATE',t)
            return 0.,0.,max(-.3,min(.3,(nav_depth-z)*1.8)),0.
        if self.state == 'NAVIGATE':
            if judgement.get('navigation_passed'):
                if self.edition=='2027':
                    self.change('WAIT_ORDER',t);return zero
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
            if self.edition=='2027' and math.dist(pose[:2],(16.5,16.))>.2:
                return self.go(pose,(16.5,16.),.55,depth=self.flare_depth)
            return 0.,0.,max(-.2,min(.2,(self.flare_depth-z)*1.5)),.35
        if self.state == 'APPROACH_FLARE':
            label=self.order[self.index]
            if label in self.targets:
                self.goal=list(self.targets[label])
            if math.dist(pose[:2],self.goal[:2]) < .65:
                self.change('BUMP_FLARE',t)
            return self.go(pose,self.goal,.45,depth=self.flare_depth)
        if self.state == 'BUMP_FLARE':
            label=self.order[self.index]
            if label in judgement.get('fallen_flares',[]):
                self.origin=pose[:2]
                self.change('BACK_OFF',t)
                return zero
            if t-self.since > 8:
                self.change('ABORT',t,'flare_contact_did_not_drop_ball')
                return zero
            return .18,0.,max(-.2,min(.2,(self.flare_depth-z)*1.5)),0.
        if self.state == 'BACK_OFF':
            if math.dist(pose[:2],self.origin) > .75:
                self.index+=1
                if self.index == 3:
                    self.goal=[22.,12.] if self.edition=='2027' else [22.5,.4]
                    self.change('TO_TARGET_ZONE',t)
                else:
                    self.change('FIND_FLARE',t)
                return zero
            return -.3,0.,0.,0.
        if self.state == 'TO_TARGET_ZONE':
            if math.dist(pose[:2],self.goal) < .15:
                self.scan=[]
                for i,scan_x in enumerate((22.,21.7,22.3,21.4,22.6) if self.edition=='2027' else (24.,23.7,24.3,23.4,24.6)):
                    lo,hi=(12.,24.) if self.edition=='2027' else (.4,15.6)
                    ys=(lo,hi) if i%2==0 else (hi,lo)
                    self.scan.extend([[scan_x,scan_y] for scan_y in ys])
                self.goal=self.scan.pop(0)
                self.change('SCAN_DRUMS',t)
            return self.go(pose,self.goal,.7,depth=self.cruise_depth)
        if self.state == 'SCAN_DRUMS':
            if self.prefer_pinger and self.acoustic_target is not None and t-self.acoustic_time<=.5:
                self.scan_resume_goal=self.goal
                self.selected_drum='pinger'
                self.goal=[*self.acoustic_target, self.cruise_depth]
                self.change('ALIGN_DRUM',t)
                return zero
            if not self.extended and 'blue_drum' in self.targets:
                self.selected_drum='blue'
                self.goal=list(self.targets['blue_drum'])
                self.change('ALIGN_DRUM',t)
                return zero
            if math.dist(pose[:2],self.goal) < .08:
                if not self.scan:
                    self.change('ABORT',t,'blue_drum_not_found')
                    return zero
                self.goal=self.scan.pop(0)
            return self.go(pose,self.goal,.15,depth=self.cruise_depth)
        if self.state == 'ALIGN_DRUM':
            if self.extended or self.selected_drum=='pinger':
                if not self.extended and t-self.acoustic_time>.5:
                    self.prefer_pinger=False
                    self.selected_drum=None
                    self.aligned_since=None
                    self.goal=self.scan_resume_goal
                    self.change('SCAN_DRUMS',t,'pinger_stale_use_blue');return zero
                if t-self.acoustic_time>.5:
                    self.change('ABORT',t,'stale_acoustics');return zero
                self.goal=[*self.acoustic_target,self.cruise_depth]
            else:self.goal=list(self.targets.get('blue_drum',self.goal))
            # Both loading and pickup use the centered gripper.
            dx,dy=self.goal[0]-(x+PICKUP_X*math.cos(yaw)),self.goal[1]-(y+PICKUP_X*math.sin(yaw))
            drop_depth=self.cruise_depth
            if self.compact:
                if math.hypot(dx,dy)<.035 or self.lowering:
                    self.lowering=True
                    drop_depth=-2.+.11-PICKUP_Z
            if math.hypot(dx,dy) < (.015 if self.compact else .025) and (
                    not self.compact or (abs(z-drop_depth)<.010 and self.estimated_speed<.015)):
                if self.aligned_since is None: self.aligned_since=t
                if t-self.aligned_since > 1:
                    self.acquisition_goal=list(self.goal)
                    if self.compact:
                        self.brake_origin=pose[:2]
                        self.aligned_since=t
                        self.change('BRAKE_RELEASE',t)
                        return zero
                    self.release=True
                    self.change('WAIT_PAYLOAD',t)
                    return zero
                if not self.compact:return zero
            else:self.aligned_since=None
            vz=(drop_depth-z)*1.5
            if self.compact and z< -1.42:vz=max(-.045,vz)
            vx,vy=dx*.8,dy*.8
            return (max(-.2,min(.2,vx*math.cos(yaw)+vy*math.sin(yaw))),
                    max(-.2,min(.2,-vx*math.sin(yaw)+vy*math.cos(yaw))),
                    max(-.2,min(.2,vz)),0.)
        if self.state=='BRAKE_RELEASE':
            if math.dist(self.acquisition_goal[:2],pose[:2])>.025 or abs(z-(-2.+.11-PICKUP_Z))>.025:
                self.aligned_since=None
                self.change('ALIGN_DRUM',t)
            elif t-self.since>12:
                self.change('ABORT',t,'release_motion_not_settled')
            elif t-self.aligned_since>=2.:
                # Bound lateral drift across a window, instead of one noisy DVL sample.
                if math.dist(self.brake_origin,pose[:2])<=.003 and self.estimated_speed<.015:
                    self.release=True
                    self.change('WAIT_PAYLOAD',t)
                self.brake_origin=pose[:2]
                self.aligned_since=t
            return zero
        if self.state == 'WAIT_PAYLOAD':
            if judgement.get('payload_acquired' if self.extended else ('payload_in_pinger' if self.selected_drum=='pinger' else 'payload_in_blue')):
                if self.extended:
                    if self.edition=='2027':
                        if self.compact:
                            self.change('CLEAR_DRUM',t);return zero
                        self.goal=[20.3,self.acquisition_goal[1]]
                        self.change('EXIT_TARGET_ZONE',t);return zero
                    gate=self.targets['navigation_gate']
                    self.goal=[gate[0]+1.6,gate[1]]
                    self.change('TO_REACQUISITION_GATE',t)
                else:self.change('TO_SQUARE',t) if self.edition=='2027' else self.change('SURFACE',t)
            elif t-self.since > 8:
                self.change('ABORT',t,'payload_not_inside_selected_drum')
            return zero
        if self.state=='CLEAR_DRUM':
            if z< -1.2:
                return 0.,0.,.10,0.
            self.goal=[20.3,self.acquisition_goal[1]]
            self.change('EXIT_TARGET_ZONE',t)
            return zero
        if self.state=='EXIT_TARGET_ZONE':
            if judgement.get('target_zone_exited'):
                self.goal=list(self.acquisition_goal);self.change('TO_PICKUP',t)
            return self.go(pose,self.goal,.5,depth=-.9)
        if self.state=='TO_SQUARE':
            if self.goal is None or len(self.goal)!=2:self.goal=[11.,31.]
            # This is the search region beside qualification, not a square target pose.
            if self.goal!=[11.,31.]:self.goal=[11.,31.]
            if math.dist(pose[:2],self.goal)<.12:self.change('FIND_SQUARE',t)
            return self.go(pose,self.goal,.75,depth=-.6)
        if self.state=='FIND_SQUARE':
            if 'surfacing_square' in self.targets:
                self.goal=list(self.targets['surfacing_square']);self.aligned_since=None
                self.change('ALIGN_SQUARE',t);return zero
            return 0.,0.,max(-.15,min(.15,(-.6-z)*1.5)),.3
        if self.state=='ALIGN_SQUARE':
            self.goal=list(self.targets.get('surfacing_square',self.goal))
            if math.dist(pose[:2],self.goal[:2])<.05:
                if self.aligned_since is None:self.aligned_since=t
                if t-self.aligned_since>1:self.change('SURFACE',t)
                return zero
            self.aligned_since=None
            return self.go(pose,self.goal,.35,depth=-.6)
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
            return self.go(pose,self.goal,.65,depth=self.cruise_depth)
        if self.state in ('ALIGN_PICKUP','DESCEND_PICKUP','LIFT_PICKUP'):
            if (COMPACT_RIM_CLEARANCE if self.compact else PICKUP_RIM_CLEARANCE)<0:
                self.change('ABORT',t,'fixed_gripper_unreachable');return zero
            dx,dy=self.goal[0]-(x+PICKUP_X*math.cos(yaw)),self.goal[1]-(y+PICKUP_X*math.sin(yaw))
            if self.compact and self.state!='LIFT_PICKUP':
                if self.state=='DESCEND_PICKUP' and not self.grip and t-self.ball_fix_time>.5:
                    if t-self.ball_fix_time>3.:
                        self.change('ABORT',t,'pickup_ball_track_lost')
                    return zero
                if self.ball_fix is None:
                    survey=-2.+.39-PICKUP_Z
                    if t-self.since>40:
                        self.change('ABORT',t,'pickup_ball_not_visible');return zero
                    # Stay above the rim while searching from the acquisition location.
                    return (max(-.1,min(.1,(dx*math.cos(yaw)+dy*math.sin(yaw)))),
                            max(-.1,min(.1,(-dx*math.sin(yaw)+dy*math.cos(yaw)))),
                            max(-.10,min(.10,survey-z)),0.)
                self.goal=list(self.ball_fix)
                dx,dy=self.goal[0]-x,self.goal[1]-y
            pickup_depth=-2.+.08-PICKUP_Z if self.compact else None
            if self.compact and self.ball_fix is not None:
                roll,pitch=self.attitude
                lever_x=PICKUP_Z*math.sin(pitch)*math.cos(roll)
                lever_y=-PICKUP_Z*math.sin(roll)
                dx-=lever_x*math.cos(yaw)-lever_y*math.sin(yaw)
                dy-=lever_x*math.sin(yaw)+lever_y*math.cos(yaw)
                pickup_depth=-2.+.08-PICKUP_Z*math.cos(pitch)*math.cos(roll)
            yaw_error=0.
            if self.compact and self.state=='ALIGN_PICKUP' and self.ball_fix is not None:
                if self.pickup_alignment is None and abs(z-(-2.+.39-PICKUP_Z))<.04 and t-self.ball_fix_time<.3:
                    center=self.acoustic_target if self.acoustic_target is not None and t-self.acoustic_time<.5 else self.acquisition_goal
                    source='acoustic'
                    if (self.visual_drum_center is not None and
                            math.dist(self.ball_fix[:2],self.visual_drum_center)<.26):
                        center=self.visual_drum_center
                        source='bottom_camera'
                    heading=pickup_heading(self.ball_fix,center,yaw)
                    self.pickup_alignment=dict(time=t,heading=heading,center=center[:2],ball=self.ball_fix[:2],source=source)
            if self.compact and self.pickup_alignment is not None:
                yaw_error=wrap(self.pickup_alignment['heading']-yaw)
            if (self.state=='ALIGN_PICKUP' and math.hypot(dx,dy)<.012 and
                    (not self.compact or (abs(z-(-2.+.39-PICKUP_Z))<.012 and t-self.ball_fix_time<.3
                                          and self.pickup_alignment is not None and abs(yaw_error)<.035))):
                center=self.visual_drum_center
                clearance=pickup_clearance(self.ball_fix,center,yaw) if center is not None else -math.inf
                if clearance<=0:
                    if self.clearance_wait is None:self.clearance_wait=t
                    if t-self.clearance_wait>3:
                        self.change('ABORT',t,'pickup_clearance_unverified')
                    return zero
                self.clearance_wait=None
                self.change('DESCEND_PICKUP',t)
            if self.state=='DESCEND_PICKUP':
                if self.compact:
                    if abs(z-pickup_depth)<.002 and math.hypot(dx,dy)<.003:
                        if self.aligned_since is None:self.aligned_since=t
                        if t-self.aligned_since>.4:self.grip=True
                    else:self.aligned_since=None
                else:self.grip=True
                if judgement.get('payload_grasped'):
                    if self.grasp_since is None:self.grasp_since=t
                    if not self.compact or t-self.grasp_since>=2.:
                        self.change('LIFT_PICKUP',t)
                    else:return zero
                elif t-self.since>(45 if self.compact else 15):
                    self.change('ABORT',t,'pickup_not_proven');return zero
                else:self.grasp_since=None
            if self.compact and self.state=='LIFT_PICKUP' and not judgement.get('payload_grasped'):
                self.change('ABORT',t,'pickup_lost_during_lift');return zero
            if self.state=='LIFT_PICKUP' and z>(self.cruise_depth-.06 if self.physical else -.3):
                if self.compact and not judgement.get('payload_retrieved'):
                    self.change('ABORT',t,'pickup_lift_unverified');return zero
                self.change('TO_SQUARE' if self.edition=='2027' else 'SURFACE',t);return zero
            # A 2 mm contact approach makes the roof touch the ball before settling.
            depth=self.cruise_depth if self.state in ('ALIGN_PICKUP','LIFT_PICKUP') else (-2. if self.edition=='2027' else floor_z(self.goal[0]))-PICKUP_Z+(.08 if self.compact else .038)
            if self.compact and self.state=='DESCEND_PICKUP':depth=pickup_depth
            if self.compact and self.state=='ALIGN_PICKUP':
                depth=-2.+.39-PICKUP_Z
            vz=max(-.12,min(.12,(depth-z)*1.5))
            if self.compact and self.state=='LIFT_PICKUP':
                vz=min(.08,vz)
            if self.compact and self.state=='DESCEND_PICKUP':
                if z-depth<.24:
                    vz=max(-.04,vz)
                if max(map(abs,self.attitude))>math.radians(8):
                    if self.tilt_since is None:self.tilt_since=t
                    if t-self.tilt_since>.5:
                        self.change('ABORT',t,'pickup_excess_tilt');return zero
                    vz=0.
                else:self.tilt_since=None
                if math.hypot(dx,dy)>.015:vz=max(0.,vz)
            return (max(-.12,min(.12,(dx*math.cos(yaw)+dy*math.sin(yaw))*.8)),
                    max(-.12,min(.12,(-dx*math.sin(yaw)+dy*math.cos(yaw))*.8)),
                    vz,max(-.4,min(.4,yaw_error)))
        if self.state == 'SURFACE':
            if z >= -.055:
                self.change('STOP',t)
                return zero
            return 0.,0.,min(.25,max(.035,(-.05-z)*1.5)),0.
        if self.state == 'STOP' and judgement.get('passed'):
            self.change('DONE',t)
        return zero
