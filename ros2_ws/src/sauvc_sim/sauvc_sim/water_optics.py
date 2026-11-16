"""Optional homogeneous-water RGB attenuation; rendered depth never feeds control."""
import math
import signal
from array import array
import numpy as np
import rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile, ReliabilityPolicy
from rclpy.signals import SignalHandlerOptions
from sensor_msgs.msg import Image
from sauvc_sim.camera_geometry import CameraModel
from sauvc_sim.gate_detection import decode_rgb

IMAGE_QOS=QoSProfile(depth=1,reliability=ReliabilityPolicy.BEST_EFFORT)
# RGB/depth arrive separately; retain the same three captures as FramePairs.
PAIR_QOS=QoSProfile(depth=3,reliability=ReliabilityPolicy.BEST_EFFORT)


def attenuate(rgb, depth, coefficient):
    if not math.isfinite(coefficient) or not 0<=coefficient<=.5:
        raise ValueError('invalid water attenuation')
    if rgb.dtype!=np.uint8 or rgb.ndim!=3 or rgb.shape[2]!=3 or depth.shape!=rgb.shape[:2]:
        raise ValueError('RGB/depth dimensions differ')
    if coefficient==0:return rgb.copy()
    h,w=depth.shape
    camera=CameraModel(w,h)
    y,x=np.ogrid[:h,:w]
    rays=np.sqrt(1+((x-(w-1)/2)/camera.focal)**2+((y-(h-1)/2)/camera.focal)**2)
    distance=np.clip(np.nan_to_num(depth,nan=30.,posinf=30.,neginf=0.),0.,30.)*rays
    transmission=np.exp(-distance[:,:,None]*coefficient*np.array([1.4,1.,.7]))
    # shortcut: fixed homogeneous water color, replace with measured optics for pool validation.
    background=np.array([38.,82.,92.])
    return np.clip(np.rint(rgb*transmission+background*(1-transmission)),0,255).astype(np.uint8)


class FramePairs:
    """Exact capture timestamps, bounded memory, no replay of old output."""
    def __init__(self):
        self.pending={};self.last=-1

    def add(self, kind, msg):
        stamp=msg.header.stamp.sec*10**9+msg.header.stamp.nanosec
        if stamp<=self.last:return None
        pair=self.pending.setdefault(stamp,{})
        pair[kind]=msg
        if len(pair)==2:
            self.last=stamp
            self.pending={s:p for s,p in self.pending.items() if s>stamp}
            return pair['rgb'],pair['depth']
        while len(self.pending)>3:self.pending.pop(min(self.pending))
        return None


def image(rgb, depth, coefficient):
    pixels=decode_rgb(rgb.data,rgb.width,rgb.height,rgb.step,rgb.encoding)
    if pixels is None or depth.encoding!='32FC1' or (depth.width,depth.height)!=(rgb.width,rgb.height):
        raise ValueError('invalid RGB/depth encoding or dimensions')
    if depth.step<depth.width*4 or len(depth.data)!=depth.height*depth.step:
        raise ValueError('invalid depth stride or buffer')
    values=np.ndarray((depth.height,depth.width),dtype='>f4' if depth.is_bigendian else '<f4',
                      buffer=bytes(depth.data),strides=(depth.step,4))
    result=Image(header=rgb.header,height=rgb.height,width=rgb.width,encoding='rgb8',
                 is_bigendian=0,step=rgb.width*3)
    # A typed buffer avoids ROS's Python validation loop over 921,600 byte values.
    result.data=array('B',attenuate(pixels,values,coefficient).tobytes())
    return result


class WaterOptics(Node):
    def __init__(self):
        super().__init__('sauvc_water_optics')
        self.coefficient=self.declare_parameter('attenuation',0.).value
        if not math.isfinite(self.coefficient) or not 0<self.coefficient<=.5:
            raise ValueError('water optics requires attenuation in (0, 0.5]')
        self.pairs={name:FramePairs() for name in ('front','bottom')}
        self.outputs={name:self.create_publisher(Image,f'/sauvc/camera_{name}/image_raw',IMAGE_QOS) for name in self.pairs}
        self.inputs=[]
        for name in self.pairs:
            for kind in ('rgb','depth'):
                self.inputs.append(self.create_subscription(Image,f'/sauvc/optics/{name}/{kind}',
                    lambda msg,c=name,k=kind:self.receive(c,k,msg),PAIR_QOS))

    def receive(self, camera, kind, msg):
        pair=self.pairs[camera].add(kind,msg)
        if pair is None:return
        try:output=image(*pair,self.coefficient)
        except ValueError as error:
            self.get_logger().error(str(error));return
        self.outputs[camera].publish(output)


def main():
    rclpy.init(signal_handler_options=SignalHandlerOptions.NO)
    stopping=False
    def stop(signum,frame):
        nonlocal stopping
        stopping=True
    signal.signal(signal.SIGINT,stop);signal.signal(signal.SIGTERM,stop)
    node=WaterOptics()
    try:
        while not stopping and rclpy.ok():rclpy.spin_once(node,timeout_sec=.1)
    finally:
        node.destroy_node();rclpy.try_shutdown()
