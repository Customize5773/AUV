"""Training collision bounds from the packaged visual mesh, in FLU metres."""
from itertools import product
import json
import math
from pathlib import Path

_metadata=json.loads((Path(__file__).parent/'meshes/sauvc_2027_v1.json').read_text())
# OBJ coordinates are exported at six decimal places.
HULL_MIN,HULL_MAX=(tuple(round(float(v),6) for v in row) for row in _metadata['output_bounds'])
if not all(math.isfinite(a) and math.isfinite(b) and a<b for a,b in zip(HULL_MIN,HULL_MAX)):
    raise ValueError('invalid vehicle mesh bounds')
HULL_SIZE=tuple(b-a for a,b in zip(HULL_MIN,HULL_MAX))
HULL_CENTER=tuple((a+b)/2 for a,b in zip(HULL_MIN,HULL_MAX))
HULL_CORNERS=tuple(product(*zip(HULL_MIN,HULL_MAX)))
PICKUP_X=0.
PICKUP_Z=-.18
# Settled ball center 4 cm above floor; drum rim 32 cm above floor.
PICKUP_RIM_CLEARANCE=.04-PICKUP_Z+HULL_MIN[2]-.32
BOTTOM_CAMERA_POSITION=(.16,0.,-.12)
STOWED_CORNERS=HULL_CORNERS+tuple(product((PICKUP_X-.04,PICKUP_X+.04),(-.04,.04),(PICKUP_Z-.009,-.09)))


def qualification_start_x(yaw):
    return -min(a*math.cos(yaw)-b*math.sin(yaw) for a,b,_ in HULL_CORNERS)
