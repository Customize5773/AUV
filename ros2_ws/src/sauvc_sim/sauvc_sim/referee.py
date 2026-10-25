"""Independent qualification judge for the published 2026 training geometry."""
import math
from sauvc_sim.arena import floor_z


def wrap(angle):
    return math.atan2(math.sin(angle), math.cos(angle))


def envelope(pose):
    x, y, z, yaw = *pose[:3], pose[-1]
    roll, pitch = pose[3:5] if len(pose) == 6 else (0., 0.)
    c, s = math.cos(yaw), math.sin(yaw)
    cr, sr, cp, sp = math.cos(roll), math.sin(roll), math.cos(pitch), math.sin(pitch)
    corners = []
    for a in (-.3, .32):
        for b in (-.2, .2):
            for d in (-.12, .1):
                bx, by, bz = a, b*cr-d*sr, b*sr+d*cr
                bx, bz = bx*cp+bz*sp, -bx*sp+bz*cp
                corners.append((x+bx*c-by*s, y+bx*s+by*c, z+bz))
    return (min(p[0] for p in corners), max(p[0] for p in corners),
            min(p[1] for p in corners), max(p[1] for p in corners),
            min(p[2] for p in corners), max(p[2] for p in corners))


class QualificationJudge:
    def __init__(self, lane=1, physical=False):
        self.gate_y = 4 if lane == 1 else 12
        self.physical=physical
        self.phase = 'START'
        self.reason = ''
        self.events = []
        self.started = None
        self.run_started = None
        self.finished = None
        self.departed_wall = False
        self.turned = False
        self.surface_completed = False
        self.surface_time = None
        self.stop_time = None
        self.stopped = False
        self.stop_since = None
        self.previous = None

    def arm(self,t):
        if self.physical and self.run_started is None:
            self.run_started=t;self.events.append(dict(event='RUN_STARTED',time=t))

    @property
    def qualified(self):
        return self.finished is not None

    def fail(self, reason, t):
        if self.physical and self.phase=='COMPLETE':return
        if self.phase != 'FAILED':
            self.phase, self.reason = 'FAILED', reason
            self.events.append({'event': 'FAILED', 'time': t, 'reason': reason})

    def event(self, name, t, pose):
        self.events.append({'event': name, 'time': t, 'pose': list(pose)})

    def update(self, pose, t, contacts=(), zero_command=True):
        if self.phase in ('FAILED','COMPLETE'):
            return
        x, y, z, yaw = *pose[:3], pose[-1]
        if not all(math.isfinite(v) for v in (*pose, t)):
            self.fail('nonfinite_pose', t)
            return
        lo, hi, bottom_y, top_y, bottom_z, top_z = envelope(pose)
        if self.started is None:
            self.started = t
            hull_rear = x - .3*abs(math.cos(yaw)) - .2*abs(math.sin(yaw))
            if abs(hull_rear) > .015 or abs(y-self.gate_y) > .5 or hi >= 9.975:
                self.fail('invalid_start', t)
                return
            self.event('START_WALL', t, pose)
        if self.previous is not None and math.dist(pose[:3], self.previous[:3]) > .5:
            self.fail('pose_discontinuity', t)
            return
        if not self.physical and self.run_started is None and self.previous is not None and math.dist(pose[:3], self.previous[:3]) > .0005:
            self.run_started = t
            self.event('RUN_STARTED', t, pose)
        launching = (not self.departed_wall and x < .8 and
                     (self.run_started is None or t-self.run_started < 12))
        if lo > .04:
            self.departed_wall = True
        for name in contacts:
            if launching and 'wall_start' in name:
                continue
            self.fail('contact:' + name, t)
            return
        if bottom_y <= 0 or top_y >= 16 or hi >= 25 or (lo < -.025 and not launching):
            self.fail('pool_boundary', t)
            return
        if bottom_z <= max(floor_z(max(0, lo)), floor_z(min(25, hi))):
            self.fail('floor_envelope', t)
            return
        if self.physical and self.run_started is None:
            self.previous=pose
            return
        if self.phase == 'START':
            if top_z < -.02:
                self.phase = 'OUTBOUND'
                self.event('UNDERWATER', t, pose)
            elif (self.run_started is not None and t-self.run_started > 10) or x > .8:
                self.fail('dive_timeout', t)
                return
        elif not self.qualified and top_z >= 0:
            self.fail('early_surface', t)
            return
        if not self.qualified and lo <= 10.025 and hi >= 9.975:
            if bottom_y <= self.gate_y-.75 or top_y >= self.gate_y+.75 or top_z >= 0:
                self.fail('outside_gate_opening', t)
                return
        if self.phase == 'OUTBOUND' and lo > 10.025:
            if abs(wrap(yaw)) > math.pi/3:
                self.fail('outbound_not_forward', t)
                return
            self.phase = 'RETURN'
            self.event('FULL_OUTBOUND', t, pose)
        elif self.phase == 'RETURN':
            if lo > 10.025 and abs(wrap(yaw-math.pi)) < .15 and not self.turned:
                self.turned = True
                self.event('U_TURN', t, pose)
            if hi < 9.975:
                if not self.turned or abs(wrap(yaw-math.pi)) > math.pi/3:
                    self.fail('return_without_u_turn', t)
                    return
                self.finished = t
                self.phase = 'QUALIFIED'
                self.event('FULL_RETURN_QUALIFIED', t, pose)
        at_surface=top_z>=0 if self.physical else z>=-.06
        if self.qualified and at_surface:
            if z > .03:
                self.fail('surface_overshoot', t)
                return
            if not self.surface_completed:
                self.surface_completed = True
                self.surface_time = t
                self.event('SURFACE', t, pose)
            moved = (self.previous is None or math.dist(pose[:3], self.previous[:3]) > .001
                     or abs(wrap(yaw-self.previous[-1])) > .001)
            if not zero_command or moved:
                self.stop_since = None
            elif self.stop_since is None:
                self.stop_since = t
            elif t-self.stop_since >= 1 and not self.stopped:
                self.stopped = True
                if self.physical:self.phase='COMPLETE'
                self.stop_time = t
                self.event('STOPPED', t, pose)
        elif self.qualified:
            self.stop_since=None
        self.previous = pose

    def result(self):
        return {'phase': self.phase, 'reason': self.reason,
                'qualification_passed': self.qualified,
                'qualification_finish_time': self.finished,
                'elapsed': None if self.finished is None else self.finished-self.run_started,
                'start_to_surface_elapsed': None if self.surface_time is None else self.surface_time-self.run_started,
                'start_to_stop_elapsed': None if self.stop_time is None else self.stop_time-self.run_started,
                'surface_completed': self.surface_completed, 'stopped': self.stopped,
                'passed': self.qualified and self.surface_completed and self.stopped
                          and self.phase != 'FAILED', 'events': self.events}
