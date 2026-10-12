"""Read-only vehicle relay. Ages include time spent in the bridge."""
import copy


def vehicle_frame(snapshot, relay_age):
    frame = copy.deepcopy(snapshot)
    frame['relay_age'] = relay_age
    expired = relay_age > 2
    if expired:
        frame['status'] = 'stale'
    if frame['heartbeat_age'] is not None:
        frame['heartbeat_age'] += relay_age
        if frame['heartbeat_age'] >= 3 and frame['status'] == 'connected':
            frame['status'] = 'stale'
    for field in frame['fields'].values():
        field['age'] += relay_age
        field['stale'] = field['stale'] or field['age'] > 3 or frame['status'] != 'connected'
    return frame
