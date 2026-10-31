"""Analyze a recorded native/ROS/checker trio without running the simulator."""
import argparse
import hashlib
import json
from pathlib import Path
from transport_diagnosis import load,diagnose


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('native','ros','checker','output'):p.add_argument('--'+name,type=Path,required=True)
    p.add_argument('--injection',type=Path,help='Optional JSON with stop_wall_s/resume_wall_s')
    args=p.parse_args()
    sources=[args.native,args.ros,args.checker]+([args.injection] if args.injection else [])
    if args.output.resolve() in {path.resolve() for path in sources}:p.error('output must differ from input logs')
    native=load(args.native);ros=load(args.ros);checker=json.loads(args.checker.read_text())
    if args.injection:
        injection=json.loads(args.injection.read_text());start=injection['stop_wall_s']-.2;end=injection['resume_wall_s']+.5
    else:
        thrust=checker['calibration_verification']['first_thrust_s']
        if thrust is None:raise ValueError('no thrust observed; select an explicit injection interval')
        finish=checker.get('hold_verification',{}).get('window_end_s')
        if finish is None:finish=next((e['time'] for e in checker['result'].get('events',[]) if e['event']=='STOPPED'),checker['trajectory'][-1][0])
        sensors=[row for row in ros if row.get('topic')=='sensors']
        if not sensors or sensors[0]['sim_s']>thrust:raise ValueError('ROS capture starts after thrust; full mission window unavailable')
        native_sensors=[row for row in native if row.get('topic')=='sensors']
        if not native_sensors or native_sensors[0]['sim_s']>thrust:raise ValueError('native capture starts after thrust')
        if sensors[-1]['sim_s']<finish or native_sensors[-1]['sim_s']<finish:raise ValueError('capture does not cover the end of the window')
        start=next(row['wall_s'] for row in sensors if row['sim_s']>=thrust)
        end=next((row['wall_s'] for row in sensors if row['sim_s']>=finish),sensors[-1]['wall_s'])
    if end<=start:raise ValueError('measurement window has no duration')
    for rows in (native,ros):
        heartbeat=[row['wall_s'] for row in rows if row['kind']=='heartbeat']
        if not heartbeat or heartbeat[0]>start or heartbeat[-1]<end:raise ValueError('observer heartbeat does not cover measurement window')
    result=diagnose(native,ros,checker,start,end)
    result['input_sha256']={str(path):hashlib.sha256(path.read_bytes()).hexdigest() for path in sources}
    args.output.parent.mkdir(parents=True,exist_ok=True);args.output.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:result[k] for k in ('classification','max_estimator_sensor_age_s','clock_basis_valid')}))


if __name__=='__main__':main()
