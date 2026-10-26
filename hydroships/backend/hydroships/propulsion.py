"""Read-only seven-thruster profile shared with the SAUVC force simulator."""
import json
from pathlib import Path

PROFILE=json.loads(Path(__file__).with_name('propulsion.json').read_text())


def expected_parameters():
    result={'FRAME_CONFIG':PROFILE['frame_config']}
    for motor in PROFILE['thrusters']:
        result[f"SERVO{motor['output']}_FUNCTION"]=motor['function']
        result[f"MOT_{motor['motor']}_DIRECTION"]=motor['direction']
    return result


def propulsion_state(params,live):
    expected=expected_parameters()
    missing=[name for name in expected if name not in params]
    different=[name for name,value in expected.items() if name in params and params[name]['value']!=value]
    status='unavailable' if not live else 'mismatch' if different else 'waiting' if missing else 'match'
    return dict(profile_id=PROFILE['id'],name=PROFILE['name'],mapping_status=status,
                hardware_mixer_verified=PROFILE['hardware_mixer_verified'],
                different=different,missing=missing,
                motors=[{k:m[k] for k in ('id','motor','output','orientation','function','direction')}
                        for m in PROFILE['thrusters']])
