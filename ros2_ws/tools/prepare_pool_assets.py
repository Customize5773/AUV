"""Deterministic pool textures/UV meshes; no downloads or extra dependencies."""
import math
from pathlib import Path
import struct
import zlib


def png(path, size, pixel):
    def chunk(kind, data):
        return struct.pack('!I',len(data))+kind+data+struct.pack('!I',zlib.crc32(kind+data)&0xffffffff)
    raw=b''.join(b'\0'+bytes(c for x in range(size) for c in pixel(x,y,size)) for y in range(size))
    path.write_bytes(b'\x89PNG\r\n\x1a\n'+chunk(b'IHDR',struct.pack('!2I5B',size,size,8,2,0,0,0))+
                     chunk(b'IDAT',zlib.compress(raw,9))+chunk(b'IEND',b''))


def normal(x,y,n):
    u,v=2*math.pi*x/n,2*math.pi*y/n
    dx=.13*math.cos(3*u+2*v)+.07*math.cos(5*u-v)
    dy=.13*2/3*math.cos(3*u+2*v)-.07/5*math.cos(5*u-v)
    length=math.sqrt(1+dx*dx+dy*dy)
    return tuple(round(127.5*(1+c/length)) for c in (-dx,-dy,1))


def tile(x,y,n):
    if min(x,y,n-1-x,n-1-y)<2:return (156,181,184)
    shade=round(2*math.sin(x*.17)*math.sin(y*.13))
    return (190+shade,211+shade,215+shade)


def main():
    from sauvc_sim.rules2027 import floor_z
    target=Path(__file__).resolve().parents[1]/'src/sauvc_sim/sauvc_sim/pool_assets'
    target.mkdir(exist_ok=True)
    png(target/'water-normal.png',128,normal)
    png(target/'tile.png',128,tile)
    (target/'water.obj').write_text('# Optical surface; decorative normals, not physical waves.\n'
        'v 0 0 0\nv 50 0 0\nv 50 25 0\nv 0 25 0\n'
        'vt 0 0\nvt 50 0\nvt 50 25\nvt 0 25\n'
        'vn 0 0 1\nf 1/1/1 2/2/1 3/3/1\nf 1/1/1 3/3/1 4/4/1\n')
    rows=['# Liner follows collision floor; UV repeats every 0.5 m.']
    for i,(a,b) in enumerate(((0,1.8),(1.8,19.3),(19.3,50))):
        for x,y in ((a,0),(b,0),(b,25),(a,25)):rows.append(f'v {x} {y} {floor_z(x)+.001:.9g}')
        for x,y in ((a,0),(b,0),(b,25),(a,25)):rows.append(f'vt {x*2} {y*2}')
        slope=(floor_z(b)-floor_z(a))/(b-a);length=math.hypot(slope,1)
        rows.append(f'vn {-slope/length:.9g} 0 {1/length:.9g}')
        k=i*4+1
        for face in ((k,k+1,k+2),(k,k+2,k+3)):
            rows.append('f '+' '.join(f'{v}/{v}/{i+1}' for v in face))
    (target/'liner.obj').write_text('\n'.join(rows)+'\n')


if __name__=='__main__':main()
