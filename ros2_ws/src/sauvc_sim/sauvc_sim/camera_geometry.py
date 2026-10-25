"""Calibrated pinhole projection for the two simulated cameras (body: FLU).

Real cameras must supply their measured K and optical-to-body transform; these
defaults describe only arena.py, with zero distortion and square pixels.
"""
import math
from dataclasses import dataclass
from collections import deque


@dataclass(frozen=True)
class CameraModel:
    width: int = 640
    height: int = 480
    hfov: float = 1.22173

    def __post_init__(self):
        if self.width <= 0 or self.height <= 0 or not 0 < self.hfov < math.pi:
            raise ValueError('invalid camera calibration')

    @property
    def focal(self):
        return self.width / (2*math.tan(self.hfov/2))

    @property
    def k(self):
        f = self.focal
        return [f, 0., (self.width-1)/2, 0., f, (self.height-1)/2, 0., 0., 1.]

    def ray(self, pixel, camera):
        u, v = pixel
        a, b = (u-self.k[2])/self.focal, (v-self.k[5])/self.focal
        if camera == 'front':
            return (1., -a, -b), (.32, 0., 0.)
        if camera == 'bottom':
            return (-b, -a, -1.), (0., 0., -.12)
        raise ValueError('unknown camera')

    def pixel(self, point, camera):
        x, y, z = point
        if camera == 'front':
            depth, a, b = x-.32, -y, -z
        elif camera == 'bottom':
            depth, a, b = -z-.12, -y, -x
        else:
            raise ValueError('unknown camera')
        if depth <= 0:
            return None
        return [self.k[2]+self.focal*a/depth, self.k[5]+self.focal*b/depth]

    def locate(self, obj, camera):
        """Metric estimates from known prop dimensions; no world coordinates."""
        l, t, r, b = obj['bbox']
        label = obj['label']
        if label.endswith('_gate') and not obj['partial']:
            depth = self.focal*1.55/obj['span_px']
            method = 'known_gate_span_frontoparallel'
        elif label == 'orange_flare' and l > 0 and r < self.width:
            depth = self.focal*.15/(r-l)
            method = 'known_orange_diameter'
        elif label.endswith('_flare') and not obj['partial'] and b-t >= 30:
            depth = self.focal*.8/(b-t)
            method = 'known_flare_height'
        elif label.endswith('_drum') and not obj['partial']:
            depth = self.focal*.6/max(r-l, b-t)
            method = 'known_drum_diameter'
        else:
            return None
        ray, origin = self.ray(obj['center_px'], camera)
        return dict(position_body_m=[origin[i]+depth*ray[i] for i in range(3)],
                    range_method=method)


def to_world(point, pose):
    x,y,z,yaw = pose
    a,b,c = point
    return [x+a*math.cos(yaw)-b*math.sin(yaw),
            y+a*math.sin(yaw)+b*math.cos(yaw), z+c]


class PoseHistory:
    """Interpolate the vehicle pose at the image timestamp, not callback receipt time."""
    def __init__(self):
        self.samples=deque(maxlen=240)

    def add(self, stamp, pose):
        if self.samples and stamp <= self.samples[-1][0]:
            if stamp == self.samples[-1][0]: return
            self.samples.clear()
        self.samples.append((stamp,pose))

    def at(self, stamp):
        if not self.samples or stamp<self.samples[0][0]-.05 or stamp>self.samples[-1][0]+.05:
            return None
        for (a,p),(b,q) in zip(self.samples,list(self.samples)[1:]):
            if a <= stamp <= b:
                f=(stamp-a)/(b-a)
                yaw=p[3]+f*math.atan2(math.sin(q[3]-p[3]),math.cos(q[3]-p[3]))
                return tuple(p[i]+f*(q[i]-p[i]) for i in range(3))+(yaw,)
        return min(self.samples,key=lambda row:abs(row[0]-stamp))[1]
