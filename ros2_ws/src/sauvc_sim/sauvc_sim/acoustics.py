"""Four-hydrophone far-field bearing and planar triangulation; no source coordinates."""
import math


class AcousticTracker:
    def __init__(self):
        self.rays=[]
        self.target=None
        self.last=None

    def update(self,packet,pose):
        if not isinstance(packet,dict):return None
        t=packet.get('time');delays=packet.get('tdoa_s',[])
        if not isinstance(delays,list) or len(delays)!=4 or len(pose)!=4:return None
        if not all(isinstance(v,(int,float)) and math.isfinite(v) for v in [*delays,*pose,t]):return None
        if packet.get('frequency_hz')!=45000 or max(abs(v) for v in delays)>.0002:return None
        if self.last is not None and t<=self.last:return None
        self.last=t
        dx=(delays[1]-delays[0])*1500/.2
        dy=(delays[3]-delays[2])*1500/.2
        if math.hypot(dx,dy)<.1:return None
        bearing=math.atan2(dy,dx)+pose[3]
        if self.rays and math.dist(pose[:2],self.rays[-1][:2])<.3:return self.target
        self.rays.append((pose[0],pose[1],bearing));self.rays=self.rays[-120:]
        aa=ab=bb=ac=bc=0.
        for x,y,a in self.rays:
            nx,ny=-math.sin(a),math.cos(a);c=nx*x+ny*y
            aa+=nx*nx;ab+=nx*ny;bb+=ny*ny;ac+=nx*c;bc+=ny*c
        det=aa*bb-ab*ab
        if det<.0001*(aa+bb)**2:return None
        x,y=(ac*bb-bc*ab)/det,(bc*aa-ac*ab)/det
        if not (0<x<25 and 0<y<16):return None
        residual=sum((-(x-rx)*math.sin(a)+(y-ry)*math.cos(a))**2 for rx,ry,a in self.rays)/len(self.rays)
        if residual>.04:return None
        self.target=[x,y]
        return self.target
