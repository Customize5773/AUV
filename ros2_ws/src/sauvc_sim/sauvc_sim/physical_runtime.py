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
from sauvc_sim.dynamics import PropulsionController,config
from sauvc_sim.state_estimation import StateEstimator


class PhysicalRuntime(Node):
    def __init__(self,role):
        super().__init__('sauvc_'+role)
        self.role=role;self.cfg=config();self.last_received=0.;self.valid=False
        self.reason='waiting_sensors';self.stamp=0.;self.desired=[0.]*4
        self.measured=[0.]*4;self.z=0.;self.cmd_time=0.;self.disarmed=False;self.active=False
        self.declare_parameter('arena','qualification');self.arena=self.get_parameter('arena').value
        self.declare_parameter('edition','2027');self.declare_parameter('lane',1);self.declare_parameter('lateral_offset',0.)
        if role=='state_estimator':
            self.estimator=StateEstimator(self.get_parameter('lane').value,
                    self.get_parameter('lateral_offset').value,self.cfg['density'],self.cfg['gravity'],edition=self.get_parameter('edition').value,arena=self.arena,calibrate_dvl=True)
            self.odom=self.create_publisher(Odometry,'/sauvc/state/odom',qos_profile_sensor_data)
            self.health=self.create_publisher(String,'/sauvc/state/health',10)
            self.create_subscription(String,'/sauvc/sensors',self.sensor,10)
            self.create_subscription(Twist,'/sauvc/cmd_vel',self.command,10)
        else:
            self.controller=PropulsionController(self.cfg)
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

    def feedback(self,msg):
        self.last_received=time.monotonic()
        v=msg.twist.twist
        self.measured=[v.linear.x,v.linear.y,v.linear.z,v.angular.z]
        self.z=msg.pose.pose.position.z

    def estimate_health(self,msg): self.valid=json.loads(msg.data).get('valid',False)

    def command(self,msg):
        self.cmd_time=time.monotonic()
        self.desired=[msg.linear.x,msg.linear.y,msg.linear.z,msg.angular.z]
        if any(abs(v)>1e-6 for v in self.desired):self.active=True
        if self.role=='state_estimator' and self.active:self.estimator.finish_calibration()

    def state(self,msg):
        if self.role=='state_estimator':
            if msg.data not in ('WAIT','WAIT_READY'):self.estimator.finish_calibration()
            return
        if msg.data in ('STOP','DONE','ABORT'):self.disarmed=True
        elif msg.data not in ('WAIT','WAIT_READY'):self.active=True

    def tick(self):
        now=time.monotonic()
        fresh=now-self.last_received<.3
        if self.role=='state_estimator':
            self.health.publish(String(data=json.dumps(dict(valid=self.valid and fresh,
                reason=self.reason if fresh else 'stale_sensors',time=self.stamp,
                source='pressure_gyro_magnetometer_dvl',dvl_bias_xy_mps=self.estimator.dvl_bias,
                dvl_bias_samples=self.estimator.bias_samples,
                dvl_calibrating=self.estimator.calibrating))))
        else:
            armed=self.active and self.valid and fresh and now-self.cmd_time<.5 and not self.disarmed
            try:
                u=self.controller.command(self.desired,self.measured,self.z,.02,armed)
            except ValueError:
                self.disarmed=True;u=[0.]*self.controller.matrix.shape[1]
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
