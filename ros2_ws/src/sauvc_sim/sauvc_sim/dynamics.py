"""Seven-thruster allocation and velocity feedback; no simulator pose inputs."""
import math
import json
from pathlib import Path
import numpy as np
import yaml


def config():
    p=Path(__file__).resolve().parents[1]/'config/dynamics.yaml'
    if not p.exists():
        from ament_index_python.packages import get_package_share_directory
        p=Path(get_package_share_directory('sauvc_sim'))/'config/dynamics.yaml'
    cfg=yaml.safe_load(p.read_text())
    cfg['thruster_positions']=[v for motor in propulsion_profile()['thrusters'] for v in motor['position_m']]
    cfg['thruster_axes']=[v for motor in propulsion_profile()['thrusters'] for v in motor['axis']]
    return cfg


def propulsion_profile():
    path=Path(__file__).resolve().parents[1]/'config/propulsion.json'
    if not path.exists():
        from ament_index_python.packages import get_package_share_directory
        path=Path(get_package_share_directory('sauvc_sim'))/'config/propulsion.json'
    return json.loads(path.read_text())


def allocation():
    motors=propulsion_profile()['thrusters']
    return np.array([list(m['axis'])+list(np.cross(m['position_m'],m['axis'])) for m in motors]).T


def displaced_fraction(z, cfg):
    return max(0.,min(1.,(.5*cfg['buoyancy_height']-(z+cfg['buoyancy_z']))/cfg['buoyancy_height']))


class PropulsionController:
    def __init__(self,cfg=None):
        self.cfg=cfg or config()
        self.matrix=allocation()
        self.inverse=np.linalg.pinv(self.matrix)
        self.max_force=np.array([self.cfg['horizontal_thrust']]*4+[self.cfg['vertical_thrust']]*3)
        self.integral=np.zeros(4)

    def command(self, desired, measured, z, dt, armed=True, station_keeping=False):
        if not armed:
            self.integral[:]=0
            return [0.]*self.matrix.shape[1]
        if not all(math.isfinite(v) for v in (*desired,*measured,z,dt)) or not 0<dt<=.2:
            raise ValueError('invalid propulsion feedback')
        target=np.clip(desired,[-.9,-.6,-.3,-.7],[.9,.6,.3,.7])
        error=target-np.asarray(measured)
        self.integral=np.clip(self.integral+error*dt,-.8,.8)
        if not station_keeping:self.integral[np.abs(target)<.01]=0.  # Brake to zero without residual integral thrust.
        linear=np.array(self.cfg['linear_drag']+[self.cfg['angular_linear_drag'][2]])
        quad=np.array(self.cfg['quadratic_drag']+[self.cfg['angular_quadratic_drag'][2]])
        wrench=np.array([50.,50.,80.,3.])*error+np.array([8.,8.,12.,.5])*self.integral
        wrench+=linear*target+quad*target*np.abs(target)
        wrench[2]+=self.cfg['mass']*self.cfg['gravity']-self.cfg['density']*self.cfg['gravity']*self.cfg['volume']*displaced_fraction(z,self.cfg)
        forces=self.inverse@np.array([*wrench[:3],0.,0.,wrench[3]])
        ratio=max(1.,float(np.max(np.abs(forces)/self.max_force)))
        forces/=ratio
        if ratio>1:
            self.integral-=error*dt  # Do not integrate demand that saturated the allocator.
        return (np.sign(forces)*np.sqrt(np.abs(forces)/self.max_force)).tolist()
