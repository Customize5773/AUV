"""Verify camera-only detections on Gazebo frames from controlled viewpoints, not a mission."""
import argparse
import json
import math
import os
from pathlib import Path
import signal
import subprocess
import time
import numpy as np

import rclpy
from rclpy.qos import qos_profile_sensor_data
from nav_msgs.msg import Odometry
from sensor_msgs.msg import Image, CameraInfo
from std_msgs.msg import String
from sauvc_sim.gate_detection import decode_rgb
from sauvc_sim.camera_geometry import to_world, CameraModel


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--arena',choices=['qualification','finals'],default='finals')
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--robustness',action='store_true')
    args=parser.parse_args(); args.output.parent.mkdir(parents=True,exist_ok=True)
    rclpy.init(); node=rclpy.create_node('perception_check')
    latest={}; frames={}; pose=None; pose_time=0.; frames_seen={'front':0,'bottom':0}
    raw_frames={c:{} for c in ('front','bottom')}
    overlays={c:{} for c in ('front','bottom')}
    infos={c:{} for c in ('front','bottom')}
    def stamp_key(msg): return (msg.header.stamp.sec,msg.header.stamp.nanosec)
    def remember(buffer,msg):
        buffer[stamp_key(msg)]=msg
        while len(buffer)>40: del buffer[next(iter(buffer))]
    def perception(msg,camera): latest[camera]=json.loads(msg.data)
    def image(msg,camera):
        frames[camera]=msg;frames_seen[camera]+=1
        remember(raw_frames[camera],msg)
    def odom(msg):
        nonlocal pose,pose_time
        p=msg.pose.pose.position;pose=(p.x,p.y,p.z)
        pose_time=msg.header.stamp.sec+msg.header.stamp.nanosec*1e-9
    for camera in ('front','bottom'):
        node.create_subscription(String,'/sauvc/perception/'+camera,
                                 lambda m,c=camera: perception(m,c),10)
        node.create_subscription(Image,f'/sauvc/camera_{camera}/image_raw',
                                 lambda m,c=camera: image(m,c),qos_profile_sensor_data)
        node.create_subscription(Image,f'/sauvc/perception/{camera}/image_annotated',
                                 lambda m,c=camera: remember(overlays[c],m),qos_profile_sensor_data)
        node.create_subscription(CameraInfo,f'/sauvc/camera_{camera}/camera_info',
                                 lambda m,c=camera: remember(infos[c],m),qos_profile_sensor_data)
    node.create_subscription(Odometry,'/sauvc/odom',odom,qos_profile_sensor_data)
    report={'arena':args.arena,'passed':False,'cases':[],
            'method':'controlled camera viewpoints; no autonomous ARENA mission',
            'frames_seen':frames_seen}
    def until(condition,seconds):
        if condition(): return True
        deadline=time.monotonic()+seconds
        while time.monotonic()<deadline:
            rclpy.spin_once(node,timeout_sec=.05)
            if condition(): return True
            if process.poll() is not None: raise RuntimeError('launch exited unexpectedly')
        return False
    def service(name,typ,request):
        p=subprocess.run(['ign','service','-s',name,'--reqtype','ignition.msgs.'+typ,
                          '--reptype','ignition.msgs.Boolean','--timeout','3000','--req',request],
                         capture_output=True,text=True,timeout=6,check=True)
        if 'data: true' not in p.stdout: raise RuntimeError('service failed: '+p.stdout+p.stderr)
    def capture(name,camera,m):
        raw=b''.join(bytes(m.data[y*m.step:y*m.step+m.width*3]) for y in range(m.height))
        args.output.with_name(name+'-'+camera+'.ppm').write_bytes(
            f'P6\n{m.width} {m.height}\n255\n'.encode()+raw)
    if args.arena=='finals':
        cases=[
          ('navigation-gate','front',(13,8,-.9,0),{'navigation_gate'},set()),
          ('orange-flare','front',(3,8,-.6,0),{'orange_flare'},set()),
          ('blue-flare','front',(8.5,11,-.9,0),{'blue_flare'},set()),
          ('red-flare','front',(11.5,12,-.9,0),{'red_flare'},set()),
          ('yellow-flare','front',(9.5,4,-.9,0),{'yellow_flare'},set()),
          ('reverse-gate','front',(19,8,-.9,math.pi),{'navigation_gate'},set()),
          ('single-post','front',(14,8.7,-.9,0),set(),{'navigation_gate'}),
          ('empty-bottom','bottom',(20,8,-.6,0),set(),{'blue_drum','red_drum'}),
          ('red-drum','bottom',(24,9.5,-.15,0),{'red_drum'},{'blue_drum'}),
          ('blue-drum','bottom',(24,12.5,-.15,0),{'blue_drum'},{'red_drum'}),
        ]
        if args.robustness:
            cases += [
              ('gate-far','front',(9.5,8,-.95,0),{'navigation_gate'},set()),
              ('gate-angle','front',(12,7,-.9,.2),{'navigation_gate'},set()),
              ('gate-cropped','front',(15.1,8,-.9,0),set(),{'navigation_gate'}),
              ('blue-flare-far','front',(6,11,-.95,0),{'blue_flare'},set()),
              ('blue-flare-angle','front',(8.5,10.4,-.95,.2),{'blue_flare'},set()),
              ('drum-high','bottom',(24,12.5,-.12,0),{'blue_drum'},{'red_drum'}),
              ('drum-offset','bottom',(23.97,12.475,-.12,0),{'blue_drum'},{'red_drum'}),
              ('drum-cropped','bottom',(24,12.5,-.7,0),set(),{'blue_drum','red_drum'}),
            ]
    else:
        cases=[('qualification-gate','front',(.3,4,-.6,0),{'qualification_gate'},
                {'orange_flare','navigation_gate'})]
    with args.output.with_suffix('.log').open('w') as log:
        process=subprocess.Popen(['bash','tools/ros.sh','launch','sauvc_sim','arena.launch.py',
                    f'arena:={args.arena}','headless:=true','perception:=true'],
                    stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
        try:
            if not until(lambda: pose is not None and all(c in latest and c in frames for c in ('front','bottom')),40):
                raise RuntimeError('missing camera/perception/odometry data')
            for name,camera,target,expected,forbidden in cases:
                x,y,z,yaw=target
                service(f'/world/sauvc_{args.arena}/set_pose','Pose',
                    f'name:"sauvc_auv", position:{{x:{x} y:{y} z:{z}}}, orientation:{{w:{math.cos(yaw/2)} z:{math.sin(yaw/2)}}}')
                if not until(lambda: pose is not None and math.dist(pose,target[:3])<.025,5):
                    raise RuntimeError('viewpoint not reached: '+name)
                after=pose_time+.3
                matched=0; seen_stamp=None
                def matches():
                    nonlocal matched,seen_stamp
                    d=latest.get(camera,{})
                    raw_stamp=d.get('stamp',{})
                    key=(raw_stamp.get('sec'),raw_stamp.get('nanosec'))
                    stamp=raw_stamp.get('sec',0)+raw_stamp.get('nanosec',0)*1e-9
                    if not d.get('fresh') or not d.get('valid_image') or stamp<after or stamp==seen_stamp: return False
                    if any(key not in buffer[camera] for buffer in (raw_frames,overlays,infos)): return False
                    seen_stamp=stamp
                    labels={o['label'] for o in d['detections']}
                    confirmed={o['label'] for o in d['detections'] if o.get('confirmed')}
                    matched=matched+1 if expected<=confirmed and not forbidden&labels else 0
                    return matched>=3
                ok=until(matches,5)
                result=latest.get(camera,{})
                stamp=result.get('stamp',{})
                key=(stamp.get('sec'),stamp.get('nanosec'))
                synced=until(lambda: key in raw_frames[camera] and key in overlays[camera],2)
                overlay_ok=False
                info_ok=False
                if synced:
                    original=raw_frames[camera][key];marked=overlays[camera][key]
                    info=infos[camera].get(key)
                    info_ok=(info is not None and info.header==original.header
                             and info.width==original.width and info.height==original.height
                             and np.allclose(info.k,CameraModel(original.width,original.height).k)
                             and np.allclose(info.d,0.))
                    a=decode_rgb(original.data,original.width,original.height,original.step,original.encoding)
                    b=decode_rgb(marked.data,marked.width,marked.height,marked.step,marked.encoding)
                    overlay_ok=(marked.header==original.header and a is not None and b is not None
                                and a.shape==b.shape and
                                bool(np.any(a!=b))==bool(result['detections']))
                    capture(name,camera,original)
                    capture(name+'-annotated',camera,marked)
                row={'case':name,'camera':camera,'passed':ok and overlay_ok,
                     'overlay_matches_source_stamp':synced,'overlay_pixels_verified':overlay_ok,'expected':sorted(expected),
                     'forbidden':sorted(forbidden),'viewpoint':target,'result':result}
                known={'navigation_gate':(16.,8.,-1.488+.5),'orange_flare':(6.,8.,-.696),
                       'qualification_gate':(10.,4.,-.76),
                       'blue_flare':(11.,11.,-1.552+.4),
                       'red_flare':(14.,12.,-1.552+.4),
                       'yellow_flare':(12.,4.,-1.584+.4),
                       'blue_drum':(24.,12.5,-1.232+.32),
                       'red_drum':(24.,9.5,-1.232+.32)}
                errors={}
                for obj in result.get('detections',[]):
                    label=obj['label']
                    if label in expected and label in known and 'position_body_m' in obj:
                        estimated=to_world(obj['position_body_m'],target)
                        errors[label]=math.dist(estimated,known[label])
                row['projection_error_m']=errors
                row['camera_info_verified']=info_ok
                row['confirmed_targets']=all(any(o['label']==label and o.get('confirmed') for o in result.get('detections',[])) for label in expected)
                row['passed']=(row['passed'] and row['confirmed_targets'] and info_ok
                               and expected&known.keys() <= errors.keys() and all(e<.4 for e in errors.values()))
                report['cases'].append(row)
                print(name,row['passed'],[o['label'] for o in result.get('detections',[])],flush=True)
            service(f'/world/sauvc_{args.arena}/control','WorldControl','pause: true')
            stale=until(lambda: all(not latest.get(c,{}).get('fresh',True) and
                                    not latest[c]['detections'] for c in ('front','bottom')),4)
            report['stale_cameras_cleared']=stale
            def stale_overlays():
                for camera in ('front','bottom'):
                    if not overlays[camera]: return False
                    m=next(reversed(overlays[camera].values()))
                    rgb=decode_rgb(m.data,m.width,m.height,m.step,m.encoding)
                    if rgb is None or rgb.shape!=(480,640,3) or not rgb[:40].any() or rgb[40:].any():
                        return False
                return True
            report['stale_overlays_cleared']=until(stale_overlays,4)
            report['passed']=all(c['passed'] for c in report['cases']) and stale and report['stale_overlays_cleared']
        except Exception as exc:
            report['error']=str(exc)
        finally:
            if process.poll() is None: process.send_signal(signal.SIGINT)
            try:
                process.wait(timeout=12);report['shutdown_forced']=False
            except subprocess.TimeoutExpired:
                os.killpg(process.pid,signal.SIGKILL);process.wait();report['shutdown_forced']=True
                report['passed']=False
            node.destroy_node();rclpy.try_shutdown()
    log_text=args.output.with_suffix('.log').read_text()
    report['shutdown_clean']=not any(s in log_text for s in ('Traceback','process has died','Errno::ESRCH')) and not report.get('shutdown_forced')
    report['passed']=report['passed'] and report['shutdown_clean']
    args.output.write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({'passed':report['passed'],'cases':len(report['cases']),
                      'stale_cameras_cleared':report.get('stale_cameras_cleared'),
                      'error':report.get('error')},indent=2))
    raise SystemExit(0 if report['passed'] else 1)

if __name__=='__main__':
    main()
