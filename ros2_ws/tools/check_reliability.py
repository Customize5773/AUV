"""Serial, bounded reliability matrix. Preserve failures and every run's conditions."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import signal
import statistics
import subprocess
from datetime import datetime
from zoneinfo import ZoneInfo
from sauvc_sim.conditions import conditions


def matrix():
    rows=[]
    for i,seed in enumerate((7,42,91)):
        for group,values,extra in (
            ('nominal',{},[]),
            ('prior',dict(prior_error=[.1,-.1]),['--lane',str(i+1),'--lateral-offset','.15','--yaw','.1']),
            ('dim',dict(light_scale=.7),[]),
            ('current',dict(current=[0.,.02,0.]),[])):
            rows.append(dict(name=f'q-{group}-{seed}',suite='qualification',group=group,
                             conditions=conditions(dict(seed=seed,**values)),args=extra))
    for name,values,extra in (
        ('nominal-7',dict(seed=7),[]),('nominal-91',dict(seed=91),[]),
        ('prior',dict(prior_error=[.1,-.1]),['--scene-variant','1','--blue-drum','2','--order','R-Y-B']),
        ('dim',dict(seed=7,light_scale=.7),['--blue-drum','3','--order','Y-B-R']),
        ('current',dict(current=[.02,0.,0.]),[]),
        ('pinger-91',dict(seed=91),['--extended','--scene-variant','1','--blue-drum','3','--pinger-drum','4','--order','Y-B-R'])):
        rows.append(dict(name='a-'+name,suite='arena',group=name.split('-')[0],
                         conditions=conditions(values),args=extra))
    return rows


def metrics(data):
    error=data.get('estimation_error',{})
    accuracy=error.get('qualification_reference_passed',error.get('passed',False))
    passed=bool(data.get('passed') and accuracy)
    result=data.get('result',{})
    complete=data.get('state')=='DONE' and result.get('passed',False)
    failures=[key for key in ('passed','stationary','zero_command','thrusters_zero','shutdown_clean') if not data.get(key,False)]
    if not accuracy:failures.append('accuracy_reference')
    return dict(accepted=passed,mission_complete=complete,
                failed_checks=failures,state=data.get('state'),max_xy_m=error.get('max_xy_m'),
                surface_s=result.get('score',{}).get('run_time_s',result.get('start_to_surface_elapsed')) if complete else None,
                qualification_s=result.get('elapsed') if complete else None,stop_s=result.get('start_to_stop_elapsed') if complete else None,
                error=data.get('error'))


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--suite',choices=['qualification','arena','all'],default='all')
    parser.add_argument('--case',help='Run one named case from the matrix')
    parser.add_argument('--output',type=Path,required=True,help='New evidence directory; existing directories are rejected')
    args=parser.parse_args()
    rows=[r for r in matrix() if (args.suite=='all' or r['suite']==args.suite) and (not args.case or r['name']==args.case)]
    if not rows:parser.error('no matching cases')
    args.output.mkdir(parents=True,exist_ok=False)
    paths=sorted(p for root in ('src/sauvc_sim','tools') for p in Path(root).rglob('*') if p.suffix in ('.py','.cc','.json','.yaml'))
    hashes={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}
    report=dict(started=datetime.now(ZoneInfo('Asia/Jakarta')).isoformat(),status='running',matrix=rows,source_sha256=hashes,runs=[])
    def save():
        runs=report['runs'];report['completed']=len(runs);report['accepted']=sum(r['accepted'] for r in runs)
        groups={}
        for key in sorted({(r['suite'],r['group']) for r in runs}):
            group=[r for r in runs if (r['suite'],r['group'])==key]
            times=[r['surface_s'] for r in group if r['mission_complete'] and r['surface_s'] is not None]
            groups['/'.join(key)]=dict(total=len(group),accepted=sum(r['accepted'] for r in group),mission_complete=sum(r['mission_complete'] for r in group),
                completed_mission_surface_s=dict(count=len(times),minimum=min(times),median=statistics.median(times),maximum=max(times)) if times else {})
        report['groups']=groups
        tmp=args.output/'summary.tmp';tmp.write_text(json.dumps(report,indent=2)+'\n');tmp.replace(args.output/'summary.json')
    save()
    for row in rows:
        if any(hashlib.sha256(Path(p).read_bytes()).hexdigest()!=h for p,h in hashes.items()):
            report['status']='source_changed';save();raise RuntimeError('source changed during batch; use a new output directory')
        output=args.output/(row['name']+'.json');condition_path=args.output/(row['name']+'-conditions.json')
        condition_path.write_text(json.dumps(row['conditions'],indent=2)+'\n')
        cmd=['bash','tools/ros.sh','python',f"tools/check_{row['suite']}.py",'--vehicle-model','dynamic','--conditions',str(condition_path),'--output',str(output),*row['args']]
        env=dict(os.environ,ROS_DOMAIN_ID='230',IGN_PARTITION='sauvc_reliability_matrix')
        with output.with_suffix('.console.log').open('w') as log:
            process=subprocess.Popen(cmd,stdout=log,stderr=subprocess.STDOUT,env=env,start_new_session=True)
            try:code=process.wait()
            except KeyboardInterrupt:
                os.killpg(process.pid,signal.SIGINT)
                try:process.wait(timeout=40)
                except subprocess.TimeoutExpired:
                    os.killpg(process.pid,signal.SIGTERM);process.wait(timeout=10)
                report.update(status='interrupted',interrupted_case=row['name']);save();return
        data=json.loads(output.read_text()) if output.exists() else {}
        controller=output.with_name(output.stem+'-controller.json')
        reason=json.loads(controller.read_text()).get('reason') if controller.exists() else None
        result=dict(name=row['name'],suite=row['suite'],group=row['group'],command=cmd,conditions=row['conditions'],exit_code=code,
                    reason=reason or data.get('result',{}).get('reason') or data.get('error'),**metrics(data))
        report['runs'].append(result);save();print(json.dumps(result),flush=True)
    report['status']='complete';save()
    raise SystemExit(0 if report['accepted']==report['completed'] else 1)


if __name__=='__main__':main()
