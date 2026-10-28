"""Explicit simulator test conditions; never sent to the vehicle controller."""
import json
import math
from pathlib import Path
from sauvc_sim.dynamics import config


def conditions(values=None):
    cfg=config()
    defaults=dict(seed=cfg['seed'],current=cfg['current'],prior_error=[0.,0.],light_scale=1.)
    values={} if values is None else values
    if not isinstance(values,dict) or set(values)-defaults.keys():
        raise ValueError('unknown simulation conditions')
    result={**defaults,**values}
    if type(result['seed']) is not int or not 0<=result['seed']<2**32:
        raise ValueError('seed must be a uint32')
    for key,size in (('current',3),('prior_error',2)):
        v=result[key]
        if not isinstance(v,(list,tuple)) or len(v)!=size or not all(type(x) in (int,float) and math.isfinite(x) for x in v):
            raise ValueError('invalid '+key)
        result[key]=list(v)
    if type(result['light_scale']) not in (int,float) or not .25<=result['light_scale']<=1.5:
        raise ValueError('light_scale must be in [0.25, 1.5]')
    return result


def load_conditions(path=''):
    return conditions(json.loads(Path(path).read_text()) if path else None)
