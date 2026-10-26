"""2027.2.1 dimensions and documented practice coordinates, not measured pool positions.

World X spans 50 m, Y spans 25 m. ARENA mission coordinates use U=Y,
V=42-X, so its gate normal is U while qualification stays along world X.
"""
import math

VERSION='2027.2.1'
LANES=(3.5,12.5,22.)
GATE_U=12.7
DRUM_U=22.
DRUM_V=(21.,19.,17.,15.)
TARGET=(21.,23.,14.,22.)  # U min/max, V min/max, 2 x 8 m mat
SQUARE=(7.,30.9)


def floor_z(x):
    # Practice interpretation: 1.8 m shelf followed by 17.5 m slope, then flat.
    return -1.28-.72*max(0.,min(1.,(x-1.8)/17.5))


def to_world(u,v,z=0.,yaw=0.):return (42-v,u,z,yaw+math.pi/2)


def to_local(pose):
    x,y,z=pose[:3]
    yaw=math.atan2(math.sin(pose[-1]-math.pi/2),math.cos(pose[-1]-math.pi/2))
    return (y,42-x,z,*pose[3:-1],yaw)
