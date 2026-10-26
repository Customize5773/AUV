"""Pressure + gyro/magnetometer AHRS + bottom-track DVL dead reckoning.

Inputs are noisy sensor measurements, never pose/orientation ground truth.
The deployment mark supplies the initial XY prior; drift is not globally corrected.
"""
import math


def wrap(a): return math.atan2(math.sin(a),math.cos(a))


class StateEstimator:
    def __init__(self, lane=1, lateral_offset=0., density=1000., gravity=9.81,edition='2026'):
        from sauvc_sim.rules2027 import LANES
        self.y=(LANES[lane-1] if edition=='2027' else (4. if lane==1 else 12.))+lateral_offset
        self.x=None
        self.z=0.
        self.roll=self.pitch=self.yaw=0.
        self.velocity=[0.,0.,0.]
        self.yaw_rate=0.
        self.density,self.gravity=density,gravity
        self.last=None
        self.seen={}
        self.instruments={}
        self.reason='waiting_sensors'
        self.xy_variance=0.

    def update(self, packet):
        t=packet['time']
        if not math.isfinite(t): raise ValueError('invalid sensor timestamp')
        if self.last is not None and t<=self.last:
            self.reason='nonmonotonic_sensors';return False
        dt=0. if self.last is None else t-self.last
        if dt>.25:
            self.reason='sensor_gap';self.last=t;return False
        for key in ('gyro','accel','mag','dvl'):
            if key in packet and (len(packet[key])!=3 or not all(math.isfinite(v) for v in packet[key])):
                raise ValueError('invalid '+key)
        if 'pressure_pa' in packet and not math.isfinite(packet['pressure_pa']):
            raise ValueError('invalid pressure')
        if 'pressure_pa' in packet and not 90000<packet['pressure_pa']<250000:
            raise ValueError('pressure outside instrument range')
        if 'mag' in packet and not 5<math.sqrt(sum(v*v for v in packet['mag']))<100:
            raise ValueError('invalid magnetic field')
        if 'dvl' in packet and math.sqrt(sum(v*v for v in packet['dvl']))>5:
            raise ValueError('DVL outside instrument range')
        for key in ('gyro','accel','mag','dvl','pressure_pa'):
            if key in packet:
                self.seen[key]=t;self.instruments[key]=packet[key]
        missing=next((k for k in ('gyro','accel','mag','dvl','pressure_pa') if t-self.seen.get(k,-1e6)>.25),None)
        if missing or packet.get('actuator_timeout'):
            self.reason='stale_'+(missing or 'actuator');self.last=t;return False
        if 'dvl' in packet:
            a=1. if self.last is None else 1-math.exp(-.05/.08)
            self.velocity=[v+a*(m-v) for v,m in zip(self.velocity,packet['dvl'])]
        wx,wy,wz=self.instruments['gyro']
        cr,sr,cp=math.cos(self.roll),math.sin(self.roll),max(.2,math.cos(self.pitch))
        self.roll=wrap(self.roll+dt*(wx+math.tan(self.pitch)*(sr*wy+cr*wz)))
        self.pitch=max(-1.2,min(1.2,self.pitch+dt*(cr*wy-sr*wz)))
        self.yaw_rate=(sr*wy+cr*wz)/cp
        self.yaw=wrap(self.yaw+self.yaw_rate*dt)
        ax,ay,az=self.instruments['accel']
        stationary=math.sqrt(sum(v*v for v in self.velocity))<.05 and math.sqrt(wx*wx+wy*wy+wz*wz)<.05
        if self.last is None or stationary:
            a=1. if self.last is None else 1-math.exp(-dt/2.)
            self.roll+=a*wrap(math.atan2(ay,az)-self.roll)
            self.pitch+=a*(math.atan2(-ax,math.hypot(ay,az))-self.pitch)
        mx,my,mz=self.instruments['mag']
        cr,sr,cp,sp=math.cos(self.roll),math.sin(self.roll),math.cos(self.pitch),math.sin(self.pitch)
        heading=math.atan2(-(cr*my-sr*mz),cp*mx+sp*(sr*my+cr*mz))
        a=1. if self.last is None else 1-math.exp(-dt/.4)
        self.yaw=wrap(self.yaw+a*wrap(heading-self.yaw))
        if self.x is None:
            # Hull touches the known starting wall; heading is measured by AHRS.
            self.x=.3*abs(math.cos(self.yaw))+.2*abs(math.sin(self.yaw))
        vx,vy,vz=self.velocity
        # Rotate DVL FLU velocity by the estimated full attitude.
        bx,by,bz=vx,cr*vy-sr*vz,sr*vy+cr*vz
        bx,bz=cp*bx+sp*bz,-sp*bx+cp*bz
        self.x+=dt*(bx*math.cos(self.yaw)-by*math.sin(self.yaw))
        self.y+=dt*(bx*math.sin(self.yaw)+by*math.cos(self.yaw))
        self.z+=dt*bz
        if 'pressure_pa' in packet:
            depth=-(packet['pressure_pa']-101325.)/(self.density*self.gravity)
            a=1. if self.last is None else 1-math.exp(-.05/.12)
            self.z+=a*(depth-self.z)
        self.xy_variance+=dt*(.003**2+.001**2*t)
        self.last=t;self.reason=''
        return True

    def pose(self): return (self.x,self.y,self.z,self.yaw)
