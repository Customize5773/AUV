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


def qualification_start_x(yaw):
    return -min(a*math.cos(yaw)-b*math.sin(yaw) for a,b,_ in HULL_CORNERS)
