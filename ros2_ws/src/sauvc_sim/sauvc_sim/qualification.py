"""Feedback controller; the visual mode estimates gate position only from images."""
import math
from sauvc_sim.referee import wrap


def clamp(value, limit):
    return max(-limit, min(limit, value))


class QualificationController:
    def __init__(self, mode='vision', lane=1):
        if mode not in ('vision', 'odom'):
            raise ValueError('unknown navigation mode')
        self.mode = mode
        self.state = 'WAIT_READY'
        self.reason = ''
        self.since = 0
        self.started = None
        self.gate = None
        self.target = None
        self.lane_y = 4 if lane == 1 else 12
        self.turn_start = None
        self.turn_progress = 0
        self.last_yaw = None
        self.lost_since = None
        self.history = []

    def change(self, state, t, reason=''):
        self.state, self.since, self.reason = state, t, reason
        self.history.append({'state': state, 'time': t, 'reason': reason})

    def command(self, pose, t, detection, detection_age, judge):
        x, y, z, yaw = pose
        if self.state in ('DONE', 'ABORT'):
            return (0., 0., 0., 0.)
        if self.started is None:
            self.started = t
            self.change('DIVE', t)
        if t-self.started > 180 or judge.get('phase') == 'FAILED':
            self.change('ABORT', t, judge.get('reason') or 'mission_timeout')
            return (0., 0., 0., 0.)
        vx = vy = yaw_rate = 0.
        vz = clamp((-0.6-z)*1.5, .2)
        if self.state == 'DIVE':
            if abs(z+.6) < .025:
                self.change('FIND_GATE', t)
        elif self.state == 'TURN':
            if self.last_yaw is not None:
                self.turn_progress += wrap(yaw-self.last_yaw)
            self.last_yaw = yaw
            remaining = -math.pi-self.turn_progress
            yaw_rate = clamp(remaining*1.8, .5)
            if abs(remaining) < .025:
                self.target = None
                self.change('FIND_RETURN_GATE', t)
        elif self.state == 'CLEAR_GATE':
            vx = .3
            # Leave enough stand-off for both posts to fit the front camera after turning.
            if math.dist((x, y), self.turn_start) > 1.8:
                self.last_yaw = yaw
                self.turn_progress = 0
                self.change('TURN', t)
        elif self.state in ('SURFACE', 'STOP'):
            vz = clamp((-.05-z)*1.5, .2)
            if z >= -.06:
                vz = 0.
                if self.state == 'SURFACE':
                    self.change('STOP', t)
                if judge.get('passed'):
                    self.change('DONE', t)
        else:
            returning = self.state in ('FIND_RETURN_GATE', 'ALIGN_RETURN', 'PASS_BACK')
            if judge.get('qualification_passed'):
                self.change('SURFACE', t)
                return (0., 0., 0., clamp((-.05-z)*1.5, .2))
            if not returning and any(e['event'] == 'FULL_OUTBOUND' for e in judge.get('events', [])):
                self.turn_start = (x, y)
                self.change('CLEAR_GATE', t)
                return (0., 0., vz, 0.)
            if self.mode == 'odom':
                dx, dy = 10-x, self.lane_y-y
                bearing = wrap(math.atan2(dy, dx)-yaw)
                distance = math.hypot(dx, dy)
                seen = True
            else:
                seen = detection is not None and detection_age < .6
                bearing = detection['bearing'] if seen else 0.
                distance = detection['distance'] if seen else math.inf
            passing = self.state in ('PASS_OUT', 'PASS_BACK')
            if passing:
                # Hold the last visual heading through the near-field blind zone.
                dx, dy = self.target[0]-x, self.target[1]-y
                along = dx*math.cos(self.target[2]) + dy*math.sin(self.target[2])
                yaw_rate = clamp(wrap(self.target[2]-yaw)*2, .4)
                vx = .25
                if along < -.65:
                    self.change('ABORT', t, 'crossing_not_confirmed')
                    vx = yaw_rate = 0.
            elif seen:
                self.lost_since = None
                yaw_rate = clamp(1.6*bearing, .4)
                if self.state.startswith('FIND'):
                    self.change('ALIGN_RETURN' if returning else 'ALIGN', t)
                vx = .3 if abs(bearing) < .12 else .08
                if abs(bearing) < .035 and distance < 1.8:
                    angle = yaw+bearing
                    # Camera is 0.32 m in front of the odometry origin.
                    offset = .32 if self.mode == 'vision' else 0.
                    self.target = (x + offset*math.cos(yaw) + distance*math.cos(angle),
                                   y + offset*math.sin(yaw) + distance*math.sin(angle), angle)
                    self.change('PASS_BACK' if returning else 'PASS_OUT', t)
            else:
                if self.lost_since is None:
                    self.lost_since = t
                if t-self.lost_since > 8:
                    self.change('ABORT', t, 'gate_lost')
                else:
                    yaw_rate = .18*math.cos((t-self.lost_since)*.7)
        if self.state == 'ABORT':
            return (0., 0., 0., 0.)
        return vx, vy, vz, yaw_rate
