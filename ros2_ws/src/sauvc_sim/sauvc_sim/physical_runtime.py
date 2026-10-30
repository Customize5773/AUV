"""Separate sensor estimator and thruster feedback nodes for the dynamic AUV."""
import json
import math
import signal
import time
import rclpy
from rclpy.node import Node
from rclpy.signals import SignalHandlerOptions
from rclpy.qos import qos_profile_sensor_data
from geometry_msgs.msg import Twist
from nav_msgs.msg import Odometry
from std_msgs.msg import String
from sensor_msgs.msg import Image
from sauvc_sim.gate_detection import detect_gate
from sauvc_sim.state_estimation import wrap
from sauvc_sim.dynamics import PropulsionController,config
from sauvc_sim.state_estimation import StateEstimator


class PhysicalRuntime(Node):
    def __init__(self,role):
        super().__init__('sauvc_'+role)
        self.role=role;self.cfg=config();self.last_received=0.;self.valid=False
        self.reason='waiting_sensors';self.stamp=0.;self.desired=[0.]*4
        self.measured=[0.]*4;self.z=0.;self.cmd_time=0.;self.disarmed=False;self.active=False
        self.mission_state='WAIT';self.hold_target=None;self.pose=None
        self.declare_parameter('surface_hold',False);self.surface_hold=self.get_parameter('surface_hold').value
        self.declare_parameter('arena','qualification');self.arena=self.get_parameter('arena').value
        self.declare_parameter('edition','2027');self.declare_parameter('lane',1);self.declare_parameter('lateral_offset',0.)
        self.declare_parameter('prior_error_x',0.);self.declare_parameter('prior_error_y',0.)
        if role=='state_estimator':
            self.estimator=StateEstimator(self.get_parameter('lane').value,
                    self.get_parameter('lateral_offset').value,self.cfg['density'],self.cfg['gravity'],edition=self.get_parameter('edition').value,arena=self.arena,calibrate_dvl=True,
                    prior_error=(self.get_parameter('prior_error_x').value,self.get_parameter('prior_error_y').value))
            if self.arena=='qualification':self.create_subscription(Image,'/sauvc/camera_front/image_raw',self.gate_image,qos_profile_sensor_data)
            self.odom=self.create_publisher(Odometry,'/sauvc/state/odom',qos_profile_sensor_data)
            self.health=self.create_publisher(String,'/sauvc/state/health',10)
            self.create_subscription(String,'/sauvc/sensors',self.sensor,10)
            self.create_subscription(Twist,'/sauvc/cmd_vel',self.command,10)
        else:
            self.controller=PropulsionController(self.cfg)
            self.hold_status=self.create_publisher(String,'/sauvc/surface_hold/status',10)
            self.create_subscription(String,'/sauvc/guard/fault',self.guard_fault,10)
            self.thrusters=self.create_publisher(String,'/sauvc/thrusters',10)
            self.create_subscription(Odometry,'/sauvc/state/odom',self.feedback,qos_profile_sensor_data)
            self.create_subscription(String,'/sauvc/state/health',self.estimate_health,10)
            self.create_subscription(Twist,'/sauvc/cmd_vel',self.command,10)
        self.create_subscription(String,'/sauvc/'+('arena' if self.arena=='finals' else 'qualification')+'/state',self.state,10)
        self.create_timer(.02,self.tick)

    def sensor(self,msg):
        self.last_received=time.monotonic()
        try:
            packet=json.loads(msg.data)
            self.valid=self.estimator.update(packet)
            self.reason=self.estimator.reason
            if not self.valid:return
            e=self.estimator;self.stamp=packet['time']
            out=Odometry();out.header.stamp.sec=int(self.stamp)
            out.header.stamp.nanosec=int((self.stamp-int(self.stamp))*1e9)
            out.header.frame_id='sauvc_local';out.child_frame_id='base_link'
            out.pose.pose.position.x=e.x;out.pose.pose.position.y=e.y;out.pose.pose.position.z=e.z
            cr,sr=math.cos(e.roll/2),math.sin(e.roll/2)
            cp,sp=math.cos(e.pitch/2),math.sin(e.pitch/2)
            cy,sy=math.cos(e.yaw/2),math.sin(e.yaw/2)
            q=out.pose.pose.orientation
            q.w=cr*cp*cy+sr*sp*sy;q.x=sr*cp*cy-cr*sp*sy
            q.y=cr*sp*cy+sr*cp*sy;q.z=cr*cp*sy-sr*sp*cy
            out.twist.twist.linear.x,out.twist.twist.linear.y,out.twist.twist.linear.z=e.velocity
            out.twist.twist.angular.z=e.yaw_rate
            for i,v in enumerate((e.xy_variance+.0001,e.xy_variance+.0001,.00001,.0001,.0001,.0001)):
                out.pose.covariance[i*7]=v
            self.odom.publish(out)
        except (ValueError,KeyError,TypeError):
            self.valid=False;self.reason='invalid_sensors'

    def gate_image(self,msg):
        if self.mission_state not in ('FIND_GATE','ALIGN'):return
        stamp=msg.header.stamp.sec+msg.header.stamp.nanosec*1e-9
        detection=detect_gate(msg.data,msg.width,msg.height,msg.step,msg.encoding)
        self.estimator.observe_gate(detection,stamp)

    def guard_fault(self,msg):
        self.disarmed=True

    def feedback(self,msg):
        self.last_received=time.monotonic()
        v=msg.twist.twist
        self.measured=[v.linear.x,v.linear.y,v.linear.z,v.angular.z]
        p,q=msg.pose.pose.position,msg.pose.pose.orientation
        self.z=p.z
        self.pose=(p.x,p.y,p.z,math.atan2(2*(q.w*q.z+q.x*q.y),1-2*(q.y*q.y+q.z*q.z)))

    def estimate_health(self,msg): self.valid=json.loads(msg.data).get('valid',False)

    def command(self,msg):
        self.cmd_time=time.monotonic()
        self.desired=[msg.linear.x,msg.linear.y,msg.linear.z,msg.angular.z]
        if any(abs(v)>1e-6 for v in self.desired):self.active=True
        if self.role=='state_estimator' and self.active:self.estimator.finish_calibration()

    def state(self,msg):
        self.mission_state=msg.data
        if self.role=='state_estimator':
            if msg.data not in ('WAIT','WAIT_READY'):self.estimator.finish_calibration()
            return
        if msg.data=='ABORT':self.disarmed=True
        elif msg.data in ('STOP','DONE'):
            if self.surface_hold and not self.disarmed and self.pose is not None and self.pose[2]>=-.12:
                if self.hold_target is None:self.hold_target=self.pose
            else:self.disarmed=True
        elif msg.data not in ('WAIT','WAIT_READY'):self.active=True

    def tick(self):
        now=time.monotonic()
        fresh=now-self.last_received<.3
        if self.role=='state_estimator':
            self.health.publish(String(data=json.dumps(dict(valid=self.valid and fresh,
                reason=self.reason if fresh else 'stale_sensors',time=self.stamp,
                source='pressure_gyro_magnetometer_dvl',dvl_bias_xy_mps=self.estimator.dvl_bias,
                dvl_bias_samples=self.estimator.bias_samples,
                dvl_calibrating=self.estimator.calibrating,gate_corrections=self.estimator.gate_corrections))))
        else:
            armed=self.active and self.valid and fresh and now-self.cmd_time<.5 and not self.disarmed
            holding=self.hold_target is not None and not self.disarmed
            if holding and (not armed or self.pose is None or not all(math.isfinite(v) for v in (*self.pose,*self.hold_target))):
                self.disarmed=True;holding=False
            desired=self.desired
            if holding:
                x,y,z,yaw=self.pose;tx,ty,tz,tyaw=self.hold_target
                dx,dy=tx-x,ty-y;c,s=math.cos(yaw),math.sin(yaw)
                desired=[max(-.15,min(.15,.6*(c*dx+s*dy))),max(-.15,min(.15,.6*(-s*dx+c*dy))),
                         max(-.08,min(.08,.7*(tz-z))),max(-.2,min(.2,.8*wrap(tyaw-yaw)))]
            try:
                u=self.controller.command(desired,self.measured,self.z,.02,armed and not self.disarmed,station_keeping=holding)
            except ValueError:
                self.disarmed=True;u=[0.]*self.controller.matrix.shape[1]
            self.hold_status.publish(String(data=json.dumps(dict(active=holding and not self.disarmed,disarmed=self.disarmed,target=self.hold_target))))
            self.thrusters.publish(String(data=' '.join(f'{v:.9g}' for v in u)))


def run(role):
    rclpy.init(signal_handler_options=SignalHandlerOptions.NO)
    stopping=False
    def stop(signum,frame):
        nonlocal stopping
        stopping=True
    signal.signal(signal.SIGINT,stop);signal.signal(signal.SIGTERM,stop)
    node=PhysicalRuntime(role);executor=rclpy.executors.SingleThreadedExecutor();executor.add_node(node)
    try:
        while not stopping:executor.spin_once(timeout_sec=.05)
    finally:
        signal.signal(signal.SIGINT,signal.SIG_IGN)
        if role=='propulsion':node.thrusters.publish(String(data=' '.join(['0']*node.controller.matrix.shape[1])))
        executor.shutdown();node.destroy_node();rclpy.try_shutdown()


def estimator_main():run('state_estimator')
def propulsion_main():run('propulsion')
