"""Bounded colour/noise/occlusion checks on saved, actual simulator camera frames."""
import argparse
import json
from pathlib import Path
import numpy as np
from sauvc_sim.object_detection import detect_objects


def read_ppm(path):
    header,width_height,maximum,pixels=path.read_bytes().split(b'\n',3)
    if header!=b'P6' or maximum!=b'255': raise ValueError('expected RGB8 PPM')
    width,height=map(int,width_height.split())
    return np.frombuffer(pixels,dtype=np.uint8).reshape(height,width,3)


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--source',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True)
    args=p.parse_args()
    source=json.loads(args.source.read_text())
    rng=np.random.default_rng(2027)
    checks=[]
    for case in source['cases']:
        if not case['expected']: continue
        name,camera=case['case'],case['camera']
        frame=read_ppm(args.source.with_name(name+'-'+camera+'.ppm'))
        noise=rng.integers(-8,9,frame.shape)
        variants={
            'original':frame,
            'dim-55pct':np.clip(frame.astype(float)*.55,0,255).astype(np.uint8),
            'bright-125pct':np.clip(frame.astype(float)*1.25,0,255).astype(np.uint8),
            'blue-gain-85pct':np.clip(frame*np.array([1.,1.,.85]),0,255).astype(np.uint8),
            'noise-plusminus8':np.clip(frame.astype(np.int16)+noise,0,255).astype(np.uint8),
            'blur-3px':(sum(np.roll(frame.astype(float),i,axis=1) for i in (-1,0,1))/3).astype(np.uint8),
        }
        for change,image in variants.items():
            h,w=image.shape[:2]
            result=detect_objects(image.tobytes(),w,h,w*3,camera=camera,arena=source['arena'])
            labels={d['label'] for d in result['detections']}
            ok=set(case['expected'])<=labels and not set(case['forbidden'])&labels
            checks.append(dict(case=name,variation=change,passed=ok,labels=sorted(labels)))
    # One gate post hidden must not invent a full gate; partial drum is rejected.
    for case in source['cases']:
        objects=case['result']['detections']
        target=next((o for o in objects if o['label'] in ('navigation_gate','blue_drum')),None)
        if target is None: continue
        image=read_ppm(args.source.with_name(case['case']+'-'+case['camera']+'.ppm')).copy()
        left,top,right,bottom=target['bbox']
        image[:,:int((left+right)/2)]=(140,191,217)
        if target['label']=='blue_drum':
            image=image[:,int((left+right)/2):].copy()
        h,w=image.shape[:2]
        result=detect_objects(image.tobytes(),w,h,w*3,camera=case['camera'],arena=source['arena'])
        labels={o['label'] for o in result['detections']}
        checks.append(dict(case=case['case'],variation='occluded-or-cropped',passed=target['label'] not in labels,labels=sorted(labels)))
    report=dict(passed=all(c['passed'] for c in checks),cases=len(checks),checks=checks,
                scope='saved simulator RGB frames; bounded synthetic perturbations, not real-pool validation')
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(dict(passed=report['passed'],cases=len(checks),failures=[c for c in checks if not c['passed']]),indent=2))
    raise SystemExit(0 if report['passed'] else 1)


if __name__=='__main__': main()
