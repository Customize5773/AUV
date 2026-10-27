"""ROS adapters for visual ARENA control and independent task proof."""
import json
import math
from pathlib import Path
import signal
import time

import rclpy
from rclpy.node import Node
from rclpy.qos import qos_profile_sensor_data
from rclpy.signals import SignalHandlerOptions
from geometry_msgs.msg import Twist
from nav_msgs.msg import Odometry
from rosgraph_msgs.msg import Clock
from ros_gz_interfaces.msg import Contacts
from std_msgs.msg import String, Bool

from sauvc_sim.arena_mission import ArenaController, valid_order, level_rates
from sauvc_sim.arena_referee import ArenaJudge
from sauvc_sim.runtime import STATUS_QOS, values
from sauvc_sim.camera_geometry import PoseHistory
from sauvc_sim.acoustics import AcousticTracker
from sauvc_sim.rules2027 import to_local


class ArenaRuntime(Node):
    def __init__(self, referee=False):
        super().__init__('sauvc_arena_referee' if referee else 'sauvc_arena')
        self.referee=referee
        self.declare_parameter('output','')
        self.declare_parameter('flare_order','B-R-Y')
        self.declare_parameter('fault','none')
        self.output=self.get_parameter('output').value
        self.fault=self.get_parameter('fault').value
        self.order=self.get_parameter('flare_order').value
        valid_order(self.order)
        self.declare_parameter('edition','2027')
        self.edition=self.get_parameter('edition').value
        self.declare_parameter('physical',False)
        self.physical=self.get_parameter('physical').value
        self.declare_parameter('extended',False)
        self.extended=self.get_parameter('extended').value
        self.ctrl=ArenaController(extended=self.extended,edition=self.edition,physical=self.physical)
        self.acoustic=AcousticTracker(bounds=(0.,25.,-8.,42.) if self.edition=='2027' else (0.,25.,0.,16.))
        if referee:
            self.declare_parameter('scene_variant',0)
            self.declare_parameter('blue_drum',1)
            self.declare_parameter('pinger_drum',0)
            self.judge=ArenaJudge(self.order,self.get_parameter('scene_variant').value,
                                  self.get_parameter('blue_drum').value,self.extended,
                                  self.get_parameter('pinger_drum').value,edition=self.edition,physical=self.physical)
        self.pose=None
        self.attitude=(0.,0.)
        self.t=0.
        self.first_clock=None
        self.received={}
        self.contacts=[]
        self.zero=True
        self.command_zero=True;self.force_zero=True
        self.judgement={}
        self.ready_since=None
        self.start_wall=time.monotonic()
        self.logged=None
        self.release_sent=False
        self.camera_stamps={}
        self.pose_history=PoseHistory()
        self.state_pub=self.create_publisher(String,'/sauvc/arena/state',STATUS_QOS)
        self.report=self.create_publisher(String,'/sauvc/arena/result',STATUS_QOS)
        self.status_pub=self.create_publisher(String,'/sauvc/arena/status',STATUS_QOS) if referee and self.physical else None
        self.order_pub=self.create_publisher(String,'/sauvc/arena/flare_order',STATUS_QOS)
        self.cmd=self.create_publisher(Twist,'/sauvc/mission/cmd_vel',10) if not referee else None
        self.grip=self.create_publisher(Bool,'/sauvc/payload/grip',10) if not referee else None
        self.payload=self.create_publisher(Bool,'/sauvc/payload/release',10) if not referee else None
        self.create_subscription(Clock,'/clock',self.clock,qos_profile_sensor_data)
        self.create_subscription(Odometry,'/sauvc/state/odom' if self.physical and not referee else '/sauvc/odom',self.odom,qos_profile_sensor_data)
        if self.physical and not referee:self.create_subscription(String,'/sauvc/state/health',self.estimate_health,10)
        self.create_subscription(Contacts,'/sauvc/contacts',self.contact,qos_profile_sensor_data)
        self.create_subscription(String,'/sauvc/guard/fault',self.guard_fault,STATUS_QOS)
        if referee:
            self.create_subscription(Twist,'/sauvc/cmd_vel',self.actual_command,10)
            if self.physical:self.create_subscription(String,'/sauvc/dynamics/telemetry',self.dynamics,10)
            self.create_subscription(String,'/sauvc/arena/physics',self.physics,10)
            self.create_subscription(String,'/sauvc/arena/state',self.controller_state,STATUS_QOS)
        else:
            self.create_subscription(String,'/sauvc/arena/status' if self.physical else '/sauvc/arena/result',self.result,STATUS_QOS)
            self.create_subscription(String,'/sauvc/arena/flare_order',self.order_received,STATUS_QOS)
            if self.extended:self.create_subscription(String,'/sauvc/acoustics',self.ping,10)
            for camera in ('front','bottom'):
                self.create_subscription(String,'/sauvc/perception/'+camera,
                                         lambda m,c=camera:self.perception(m,c),1)
        self.create_timer(.05,self.tick)

    def actual_command(self,msg):
        self.command_zero=all(abs(v)<1e-6 for v in values(msg))
        self.zero=self.command_zero and self.force_zero
        if not self.physical:self.judge.thrust(self.t,not self.zero)

    def dynamics(self,msg):
        packet=json.loads(msg.data)
        forces=packet['force_n']
        self.force_zero=all(abs(f)<.05 for f in forces)
        self.zero=self.command_zero and self.force_zero
        self.judge.thrust(packet['time'],any(abs(f)>.05 for f in forces))

    def estimate_health(self,msg):
        packet=json.loads(msg.data)
        if packet.get('valid'):self.received['estimate_health']=time.monotonic()
        elif self.ctrl.started is not None and self.ctrl.state not in ('DONE','ABORT'):
            self.ctrl.change('ABORT',self.t,packet.get('reason','invalid_estimate'))

    def drop(self,key):
        return self.fault==key+'_loss' and self.first_clock is not None and self.t-self.first_clock>12

    def clock(self,msg):
        t=msg.clock.sec+msg.clock.nanosec*1e-9
        if self.drop('clock'): return
        if t>self.t: self.received['clock']=time.monotonic()
        if self.first_clock is None: self.first_clock=t
        self.t=t

    def odom(self,msg):
        if self.drop('odom'): return
        p,q=msg.pose.pose.position,msg.pose.pose.orientation
        yaw=math.atan2(2*(q.w*q.z+q.x*q.y),1-2*(q.y*q.y+q.z*q.z))
        self.attitude=(math.atan2(2*(q.w*q.x+q.y*q.z),1-2*(q.x*q.x+q.y*q.y)),
                       math.asin(max(-1.,min(1.,2*(q.w*q.y-q.z*q.x)))))
        self.pose=(p.x,p.y,p.z,yaw)
        if self.edition=='2027':self.pose=to_local(self.pose)
        self.pose_history.add(msg.header.stamp.sec+msg.header.stamp.nanosec*1e-9,self.pose)
        self.received['odom']=time.monotonic()
        if self.referee and 'contacts' in self.received:
            roll=math.atan2(2*(q.w*q.x+q.y*q.z),1-2*(q.x*q.x+q.y*q.y))
            pitch=math.asin(max(-1.,min(1.,2*(q.w*q.y-q.z*q.x))))
            self.judge.update((*self.pose[:3],roll,pitch,self.pose[-1]),self.t,self.contacts,self.zero)
            self.contacts=[]

    def contact(self,msg):
        if self.drop('contact'): return
        self.received['contacts']=time.monotonic()
        if self.referee:
            for contact in msg.contacts:
                self.contacts.append(contact.collision1.name+'|'+contact.collision2.name)

    def physics(self,msg):
        self.received['physics']=time.monotonic()
        packet=json.loads(msg.data)
        if self.edition=='2027':
            for ball in packet['balls'].values():ball['position']=list(to_local((*ball['position'],0.))[:3])
        self.judge.physics(packet)

    def perception(self,msg,camera):
        if self.drop('camera'): return
        packet=json.loads(msg.data)
        if packet.get('fresh') and packet.get('valid_image'):
            stamp=packet.get('stamp',{})
            stamp=stamp.get('sec',0)+stamp.get('nanosec',0)*1e-9
            if stamp<=self.camera_stamps.get(camera,-1): return
            self.camera_stamps[camera]=stamp
            self.received[camera]=time.monotonic()
            pose=self.pose_history.at(stamp)
            if pose:
                self.ctrl.observe(packet,pose)

    def ping(self,msg):
        try:packet=json.loads(msg.data)
        except (ValueError,TypeError):return
        if not isinstance(packet,dict) or not isinstance(packet.get('time'),(int,float)) or not math.isfinite(packet['time']):return
        pose=self.pose_history.at(packet.get('time',-1))
        if pose and abs(self.t-packet['time'])<.2:
            target=self.acoustic.update(packet,pose)
            if target:
                self.ctrl.acoustic_target=target
                self.ctrl.acoustic_time=self.t

    def result(self,msg):
        packet=json.loads(msg.data)
        self.judgement={key:packet[key] for key in
                        ('phase','reason','navigation_passed','fallen_flares','payload_in_blue','payload_acquired','payload_grasped','reacquisition_crossed','payload_retrieved','target_zone_exited','passed')
                        if key in packet}
        self.received['referee']=time.monotonic()

    def order_received(self,msg):
        if not self.judgement.get('navigation_passed'): return
        try:
            order=valid_order(msg.data)
        except ValueError:
            self.ctrl.change('ABORT',self.t,'invalid_flare_order');return
        if self.ctrl.order is None: self.ctrl.order=order
        elif self.ctrl.order!=order: self.ctrl.change('ABORT',self.t,'order_changed_during_task')

    def guard_fault(self,msg):
        if self.referee: self.judge.fail('guard:'+msg.data,self.t)
        elif self.ctrl.state not in ('DONE','ABORT'):
            self.ctrl.change('ABORT',self.t,'guard:'+msg.data)

    def controller_state(self,msg):
        if msg.data=='ABORT': self.judge.fail('controller_aborted',self.t)

    def save(self,suffix,data):
        if self.output:
            path=Path(self.output+suffix+'.json');path.parent.mkdir(parents=True,exist_ok=True)
            path.write_text(json.dumps(data,indent=2)+'\n')

    def tick(self):
        now=time.monotonic()
        required=['clock','odom','contacts']+(['physics'] if self.referee else ['referee','front','bottom'])
        if self.physical and not self.referee:required.append('estimate_health')
        stale=next((k for k in required if now-self.received.get(k,0)>2),None)
        if self.referee:
            if self.judge.phase not in ('START','COMPLETE','FAILED') and stale:
                self.judge.fail('stale_'+stale,self.t)
            result=self.judge.result()
            self.report.publish(String(data=json.dumps(result)))
            if self.status_pub:self.status_pub.publish(String(data=json.dumps({key:result[key] for key in ('phase','reason','navigation_passed','fallen_flares','payload_in_blue','payload_acquired','payload_grasped','reacquisition_crossed','payload_retrieved','target_zone_exited','passed')})))
            if self.judge.navigation: self.order_pub.publish(String(data=self.order))
            if result['passed'] or result['phase']=='FAILED': self.save('-referee',result)
            return
        ctrl=self.ctrl
        if ctrl.started is None:
            steady=self.pose and self.first_clock is not None and self.t-self.first_clock>1 and all(now-self.received.get(k,0)<.5 for k in required)
            if not steady: self.ready_since=None
            elif self.ready_since is None: self.ready_since=now
            if not steady or now-self.ready_since<2:
                if now-self.start_wall>45: ctrl.change('ABORT',self.t,'startup_missing_data')
                self.state_pub.publish(String(data=ctrl.state))
                return
        if stale and ctrl.state not in ('DONE','ABORT'): ctrl.change('ABORT',self.t,'stale_'+stale)
        if self.drop('command') and ctrl.state not in ('DONE','ABORT'): return
        velocity=ctrl.command(self.pose,self.t,self.judgement) if self.pose else (0.,0.,0.,0.)
        cmd=Twist()
        cmd.linear.x,cmd.linear.y,cmd.linear.z,cmd.angular.z=velocity
        if not self.physical and (self.extended or self.edition=='2027') and ctrl.state not in ('ABORT','DONE','STOP'):
            cmd.angular.x,cmd.angular.y=level_rates(*self.attitude)
        self.cmd.publish(cmd)
        self.grip.publish(Bool(data=ctrl.grip))
        if ctrl.release and not self.release_sent:
            self.payload.publish(Bool(data=True));self.release_sent=True
        self.state_pub.publish(String(data=ctrl.state))
        if ctrl.state!=self.logged:
            self.get_logger().info(ctrl.state+': '+ctrl.reason);self.logged=ctrl.state
        if ctrl.state in ('DONE','ABORT'):
            self.save('-controller',dict(state=ctrl.state,reason=ctrl.reason,history=ctrl.history,
                                        state_source='pressure_gyro_magnetometer_dvl' if self.physical else 'ground_truth',
                                        targets=ctrl.targets,order=ctrl.order,release_sent=self.release_sent,
                                        acoustic_target=ctrl.acoustic_target,acoustic_rays=len(self.acoustic.rays),
                                        extended=self.extended,grip_requested=ctrl.grip))


def run(referee=False):
    rclpy.init(signal_handler_options=SignalHandlerOptions.NO)
    stopping=False
    def stop(signum,frame):
        nonlocal stopping
        stopping=True
    signal.signal(signal.SIGINT,stop);signal.signal(signal.SIGTERM,stop)
    node=ArenaRuntime(referee)
    executor=rclpy.executors.SingleThreadedExecutor();executor.add_node(node)
    try:
        while not stopping: executor.spin_once(timeout_sec=.1)
    finally:
        signal.signal(signal.SIGINT,signal.SIG_IGN)
        if node.cmd is not None: node.cmd.publish(Twist())
        executor.shutdown();node.destroy_node();rclpy.try_shutdown()


def mission_main(): run()
def referee_main(): run(True)
