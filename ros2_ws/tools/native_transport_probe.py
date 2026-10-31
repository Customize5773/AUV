"""Independent Gazebo CLI observer. Writes arrival times and producer diagnostics."""
import argparse
import json
import os
from pathlib import Path
import select
import signal
import subprocess
import time


def decode(line):
    if not line.startswith(b'data: '):return None
    return json.loads(json.loads(line[6:]))


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);args=p.parse_args()
    stopping=False
    def stop(*_):
        nonlocal stopping
        stopping=True
    signal.signal(signal.SIGINT,stop);signal.signal(signal.SIGTERM,stop)
    children=[];streams={};buffers={};last_heartbeat=0.
    with args.output.open('w') as out,args.output.with_suffix('.stderr.log').open('w') as errors:
        try:
            for topic in ('sensors','dynamics/telemetry'):
                child=subprocess.Popen(['stdbuf','-oL','-eL','ign','topic','-e','-t','/sauvc/'+topic],stdout=subprocess.PIPE,stderr=errors,start_new_session=True)
                children.append(child);fd=child.stdout.fileno();streams[fd]=topic;buffers[fd]=b''
            while not stopping:
                now=time.monotonic()
                if now-last_heartbeat>=.1:
                    out.write(json.dumps(dict(kind='heartbeat',wall_s=now))+'\n');out.flush();last_heartbeat=now
                for fd in select.select(list(streams),[],[],.05)[0]:
                    data=os.read(fd,65536)
                    if not data:raise RuntimeError('native observer CLI exited')
                    wall=time.monotonic();buffers[fd]+=data
                    while b'\n' in buffers[fd]:
                        line,buffers[fd]=buffers[fd].split(b'\n',1);packet=decode(line)
                        if packet is None:continue
                        record=dict(kind='native',topic=streams[fd],wall_s=wall,sim_s=packet['time'])
                        for key in ('sensor_sequence','producer_wall_s','sensor_publish_duration_s'):
                            if key in packet:record[key]=packet[key]
                        out.write(json.dumps(record)+'\n')
        finally:
            for child in children:
                try:os.killpg(child.pid,signal.SIGTERM)
                except ProcessLookupError:pass
            for child in children:
                try:child.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    os.killpg(child.pid,signal.SIGKILL);child.wait()


if __name__=='__main__':main()
