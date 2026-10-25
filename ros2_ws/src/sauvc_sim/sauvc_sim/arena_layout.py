"""Training fixtures read by world generation and referee, never the controller."""


def layout(variant=0):
    if variant not in (0,1):
        raise ValueError('scene_variant must be 0 or 1')
    if variant == 0:
        return dict(gate_y=8.,orange=(6.,8.),blue=(11.,11.),red=(14.,12.),yellow=(12.,4.))
    return dict(gate_y=8.6,orange=(5.5,8.2),blue=(10.8,10.5),red=(13.8,11.7),yellow=(12.4,4.5))
