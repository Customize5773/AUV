"""ROS adapters for qualification, independent judging and command timeout."""
import json
import math
from pathlib import Path
import signal
import time

import rclpy
from rclpy.node import Node
from rclpy.signals import SignalHandlerOptions
from rclpy.qos import QoSProfile, DurabilityPolicy, qos_profile_sensor_data
from geometry_msgs.msg import Twist
from nav_msgs.msg import Odometry
from rosgraph_msgs.msg import Clock
from ros_gz_interfaces.msg import Contacts
from sensor_msgs.msg import Image
from std_msgs.msg import String

from sauvc_sim.gate_detection import detect_gate
from sauvc_sim.qualification import MAX_SPEED_SCALE, QualificationController
from sauvc_sim.referee import QualificationJudge


STATUS_QOS = QoSProfile(depth=1, durability=DurabilityPolicy.TRANSIENT_LOCAL)


def values(msg):
    return (msg.linear.x, msg.linear.y, msg.linear.z, msg.angular.x, msg.angular.y, msg.angular.z)


class Runtime(Node):
    def __init__(self, role):
        super().__init__('sauvc_' + role)
        self.role = role
        self.declare_parameter('lane', 1)
        self.declare_parameter('edition','2027')
        self.edition=self.get_parameter('edition').value
        self.declare_parameter('mode', 'vision')
        self.declare_parameter('output', '')
        self.declare_parameter('fault', '')
        self.declare_parameter('speed_scale', MAX_SPEED_SCALE)
        self.declare_parameter('mission', 'qualification')
        self.declare_parameter('physical',False)
        self.physical=self.get_parameter('physical').value
        self.mission = self.get_parameter('mission').value
        self.camera_stamps = {}
        self.speed_scale = float(self.get_parameter('speed_scale').value)
        lane = self.get_parameter('lane').value
        self.mode = self.get_parameter('mode').value
        self.output = self.get_parameter('output').value
        self.fault = self.get_parameter('fault').value
        self.t = 0.
        self.first_clock = None
        self.received = {}
        self.pose = None
        self.contacts = []
        self.contact_events = []
        self.detection = None
        self.detection_time = 0.
        self.frames = 0
        self.detections = 0
        self.judgement = {}
        self.zero = True
        self.terminal = False
        self.logged_state = None
        self.command = Twist()
        self.controller = QualificationController(self.mode, lane, self.speed_scale,self.physical,edition=self.edition)
        self.judge = QualificationJudge(lane,self.physical,edition=self.edition)
        self.started_wall = time.monotonic()
        self.ready_since = None
        self.report = self.create_publisher(String, '/sauvc/qualification/result', STATUS_QOS)
        self.feedback_pub=self.create_publisher(String,'/sauvc/qualification/status',STATUS_QOS) if self.physical and role=='referee' else None
        self.state_pub = self.create_publisher(String, '/sauvc/qualification/state', STATUS_QOS)
        self.fault_pub = self.create_publisher(String, '/sauvc/guard/fault', STATUS_QOS)
        topic = '/sauvc/cmd_vel' if role == 'command_guard' else '/sauvc/mission/cmd_vel'
        self.velocity_pub = None if role == 'referee' else self.create_publisher(Twist, topic, 10)
        self.create_subscription(Clock, '/clock', self.clock, qos_profile_sensor_data)
        pose_topic='/sauvc/state/odom' if self.physical and role!='referee' else '/sauvc/odom'
        self.create_subscription(Odometry,pose_topic,self.odom,qos_profile_sensor_data)
        if self.physical and role!='referee':
            self.create_subscription(String,'/sauvc/state/health',self.estimate_health,10)
        self.create_subscription(Contacts, '/sauvc/contacts', self.contact, qos_profile_sensor_data)
        if role == 'qualification':
            self.create_subscription(Image, '/sauvc/camera_front/image_raw', self.image,
                                     qos_profile_sensor_data)
            feedback_topic='/sauvc/qualification/status' if self.physical else '/sauvc/qualification/result'
            self.create_subscription(String,feedback_topic,self.result,STATUS_QOS)
            self.create_subscription(String, '/sauvc/guard/fault', self.guard_fault, STATUS_QOS)
        elif role == 'command_guard':
            self.create_subscription(Twist, '/sauvc/mission/cmd_vel', self.input_command, 10)
            prefix = '/sauvc/arena' if self.mission == 'finals' else '/sauvc/qualification'
            self.create_subscription(String, prefix+'/state', self.state, STATUS_QOS)
            self.create_subscription(String,prefix+('/status' if self.physical else '/result'),self.result,STATUS_QOS)
            if self.mission == 'finals':
                for camera in ('front','bottom'):
                    self.create_subscription(String,'/sauvc/perception/'+camera,
                        lambda m,c=camera: self.perception_status(m,c),10)
        else:
            self.create_subscription(Twist, '/sauvc/cmd_vel', self.actual_command, 10)
            self.create_subscription(String, '/sauvc/guard/fault', self.guard_fault, STATUS_QOS)
            self.create_subscription(String, '/sauvc/qualification/state', self.state, STATUS_QOS)
        self.create_timer(.05, self.tick)

    def clock(self, msg):
        value = msg.clock.sec + msg.clock.nanosec*1e-9
        if self.fault == 'clock_loss' and self.first_clock is not None and value-self.first_clock > 8:
            return
        if value > self.t:
            self.received['clock'] = time.monotonic()
        if self.first_clock is None:
            self.first_clock = value
        self.t = value

    def odom(self, msg):
        if self.drop('odom'):
            return
        p, q = msg.pose.pose.position, msg.pose.pose.orientation
        yaw = math.atan2(2*(q.w*q.z+q.x*q.y), 1-2*(q.y*q.y+q.z*q.z))
        self.pose = p.x, p.y, p.z, yaw
        self.received['odom'] = time.monotonic()
        if self.role == 'referee' and 'contacts' in self.received:
            roll = math.atan2(2*(q.w*q.x+q.y*q.z), 1-2*(q.x*q.x+q.y*q.y))
            pitch = math.asin(max(-1., min(1., 2*(q.w*q.y-q.z*q.x))))
            self.judge.update((p.x, p.y, p.z, roll, pitch, yaw), self.t, self.contacts, self.zero)
            self.contacts = []

    def contact(self, msg):
        if self.drop('contact'):
            return
        self.received['contacts'] = time.monotonic()
        if self.role != 'referee':
            return
        for item in msg.contacts:
            names = item.collision1.name + '|' + item.collision2.name
            self.contacts.append(names)
            if not self.contact_events or self.contact_events[-1]['names'] != names:
                self.contact_events.append({'time': self.t, 'names': names})

    def image(self, msg):
        if self.drop('camera'):
            return
        self.received['camera'] = time.monotonic()
        self.frames += 1
        self.detection = detect_gate(msg.data, msg.width, msg.height, msg.step, msg.encoding)
        self.detection_time = time.monotonic()
        self.detections += self.detection is not None

    def result(self, msg):
        packet=json.loads(msg.data)
        self.judgement = {k:packet[k] for k in ('phase','reason','passed') if k in packet} if self.physical else packet
        self.received['referee'] = time.monotonic()

    def estimate_health(self,msg):
        packet=json.loads(msg.data)
        if packet.get('valid'):self.received['estimate_health']=time.monotonic()
        elif self.role=='command_guard' and 'command' in self.received:
            self.trip(packet.get('reason','invalid_estimate'))
        elif self.controller.started is not None and self.controller.state not in ('DONE','ABORT'):
            self.controller.change('ABORT',self.t,packet.get('reason','invalid_estimate'))

    def perception_status(self, msg, camera):
        packet = json.loads(msg.data)
        if packet.get('fresh') and packet.get('valid_image'):
            stamp=packet.get('stamp',{})
            stamp=stamp.get('sec',0)+stamp.get('nanosec',0)*1e-9
            if stamp<=self.camera_stamps.get(camera,-1): return
            self.camera_stamps[camera]=stamp
            self.received[camera] = time.monotonic()

    def drop(self, key):
        return (self.fault == key + '_loss' and self.first_clock is not None
                and self.t-self.first_clock > 8)

    def guard_fault(self, msg):
        if self.role == 'referee':
            self.judge.fail('guard:' + msg.data, self.t)
        elif self.controller.state not in ('DONE', 'ABORT'):
            self.controller.change('ABORT', self.t, 'guard:' + msg.data)

    def state(self, msg):
        if self.role=='referee' and self.physical and msg.data=='DIVE':self.judge.arm(self.t)
        if msg.data in ('DONE', 'ABORT'):
            self.terminal = True
        if msg.data == 'ABORT' and self.role == 'referee':
            self.judge.fail('controller_aborted', self.t)

    def actual_command(self, msg):
        self.zero = all(abs(v) < 1e-6 for v in values(msg))

    def input_command(self, msg):
        if not all(math.isfinite(v) for v in values(msg)):
            self.trip('nonfinite_command')
            return
        self.command = msg
        self.received['command'] = time.monotonic()

    def trip(self, reason):
        if not self.terminal:
            self.get_logger().error(reason)
            self.fault_pub.publish(String(data=reason))
        self.terminal = True

    def stale(self, required, now):
        return next((key for key in required if now-self.received.get(key, 0) >
                     (.5 if key == 'command' else 2.)), None)

    def save(self, suffix, data):
        if self.output:
            path = Path(self.output + suffix + '.json')
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(json.dumps(data, indent=2) + '\n')

    def tick(self):
        now = time.monotonic()
        required = ['clock', 'odom', 'contacts']
        if self.physical and self.role!='referee':required.append('estimate_health')
        if self.role == 'qualification' and self.mode == 'vision':
            required.append('camera')
        if self.role in ('qualification', 'command_guard'):
            required.append('referee')
        if self.role == 'command_guard' and self.mission == 'finals':
            required += ['front','bottom']
        ready = all(k in self.received for k in required)
        stale = self.stale(required, now)
        if self.role == 'command_guard':
            cmd = Twist()
            if 'command' in self.received:
                stale = self.stale(required + ['command'], now)
                if stale:
                    self.trip('stale_' + stale)
                if not self.terminal and self.judgement.get('phase') != 'FAILED':
                    scale = self.speed_scale if self.mission != 'finals' else 3.
                    cmd.linear.x = max(-.3*scale, min(.3*scale, self.command.linear.x))
                    cmd.linear.y = max(-.3*scale, min(.3*scale, self.command.linear.y))
                    cmd.linear.z = max(-.2*scale, min(.2*scale, self.command.linear.z))
                    cmd.angular.z = max(-.5*scale, min(.5*scale, self.command.angular.z))
                    if self.mission=='finals':
                        cmd.angular.x=max(-.4,min(.4,self.command.angular.x))
                        cmd.angular.y=max(-.4,min(.4,self.command.angular.y))
            self.velocity_pub.publish(cmd)
        elif self.role == 'referee':
            if self.judge.started is not None and self.judge.phase != 'START' and stale:
                self.judge.fail('stale_' + stale, self.t)
            result = self.judge.result()
            self.report.publish(String(data=json.dumps(result)))
            if self.feedback_pub is not None:
                self.feedback_pub.publish(String(data=json.dumps({k:result[k] for k in ('phase','reason','passed')})))
            if result['passed'] or result['phase'] == 'FAILED':
                self.save('-referee', dict(result, contacts=self.contact_events,
                                          rulebook='2027.2.1' if self.edition=='2027' else '2026 v6.1.0'))
        else:
            ctrl = self.controller
            if ctrl.started is None:
                # Require a steady stream before arming; Ogre can stall physics during startup.
                steady = ready and self.first_clock is not None and self.t-self.first_clock >= 1
                steady = steady and all(now-self.received[k] < .5 for k in required)
                if not steady:
                    self.ready_since = None
                elif self.ready_since is None:
                    self.ready_since = now
                ready = steady and now-self.ready_since >= 2
            if ready and not stale and self.judgement and self.pose:
                if self.drop('command') and ctrl.state not in ('DONE', 'ABORT'):
                    return
                vx, vy, vz, turn = ctrl.command(self.pose, self.t, self.detection,
                                               now-self.detection_time, self.judgement)
                cmd = Twist()
                cmd.linear.x, cmd.linear.y, cmd.linear.z, cmd.angular.z = vx, vy, vz, turn
                self.velocity_pub.publish(cmd)
            elif ctrl.started is not None and stale and ctrl.state not in ('DONE', 'ABORT'):
                ctrl.change('ABORT', self.t, 'stale_' + stale)
                self.velocity_pub.publish(Twist())
            elif now-self.started_wall > 45 and ctrl.started is None:
                ctrl.change('ABORT', self.t, 'startup_missing_data')
            self.state_pub.publish(String(data=ctrl.state))
            if ctrl.state in ('DONE', 'ABORT'):
                self.velocity_pub.publish(Twist())
                self.save('-controller', {'state': ctrl.state, 'reason': ctrl.reason,
                                         'mode': self.mode, 'history': ctrl.history,
                                         'speed_scale': self.speed_scale,
                                         'turn_clearance_m':ctrl.turn_clearance,
                                         'state_source':'pressure_gyro_magnetometer_dvl' if self.physical else 'ground_truth_odom',
                                         'progress_source':'estimated_gate_crossing' if self.physical else 'referee',
                                         'frames': self.frames, 'detections': self.detections})
            if self.logged_state != ctrl.state:
                self.get_logger().info(ctrl.state + (': ' + ctrl.reason if ctrl.reason else ''))
                self.logged_state = ctrl.state


def run(role):
    # Keep the context alive until our final zero command and cleanup have finished.
    rclpy.init(signal_handler_options=SignalHandlerOptions.NO)
    stopping = False
    def stop(signum, frame):
        nonlocal stopping
        stopping = True
    signal.signal(signal.SIGINT, stop)
    signal.signal(signal.SIGTERM, stop)
    node = Runtime(role)
    executor = rclpy.executors.SingleThreadedExecutor()
    executor.add_node(node)
    try:
        while not stopping:
            executor.spin_once(timeout_sec=.1)
    finally:
        signal.signal(signal.SIGINT, signal.SIG_IGN)
        if rclpy.ok() and node.velocity_pub is not None:
            node.velocity_pub.publish(Twist())
        executor.shutdown()
        node.destroy_node()
        rclpy.try_shutdown()


def mission_main():
    run('qualification')


def referee_main():
    run('referee')


def guard_main():
    run('command_guard')
