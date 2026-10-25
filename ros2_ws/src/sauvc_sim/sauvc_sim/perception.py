"""Camera-only perception topics; a missing camera clears its last detections."""
import json
import signal
import time

import rclpy
from rclpy.node import Node
from rclpy.qos import qos_profile_sensor_data
from rclpy.signals import SignalHandlerOptions
from sensor_msgs.msg import Image, CameraInfo
from std_msgs.msg import String

from sauvc_sim.object_detection import detect_objects
from sauvc_sim.detection_overlay import annotate, unavailable_image
from sauvc_sim.camera_geometry import CameraModel
from sauvc_sim.tracking import Tracker


class Perception(Node):
    def __init__(self):
        super().__init__('sauvc_perception')
        self.declare_parameter('arena', 'qualification')
        self.arena = self.get_parameter('arena').value
        if self.arena not in ('qualification', 'finals'):
            raise ValueError('unknown arena')
        self.last_received = {}
        self.publishers_by_camera = {}
        self.annotated = {}
        self.info = {}
        self.trackers = {c:Tracker() for c in ('front','bottom')}
        for camera in ('front', 'bottom'):
            self.publishers_by_camera[camera] = self.create_publisher(
                String, '/sauvc/perception/'+camera, 10)
            self.annotated[camera] = self.create_publisher(
                Image, '/sauvc/perception/'+camera+'/image_annotated', qos_profile_sensor_data)
            self.info[camera] = self.create_publisher(
                CameraInfo, f'/sauvc/camera_{camera}/camera_info', qos_profile_sensor_data)
            self.create_subscription(Image, f'/sauvc/camera_{camera}/image_raw',
                                     lambda msg, c=camera: self.image(msg, c), qos_profile_sensor_data)
        self.create_timer(.2, self.expire)

    def publish(self, camera, result):
        self.publishers_by_camera[camera].publish(String(data=json.dumps(result)))

    def image(self, msg, camera):
        start = time.monotonic()
        self.last_received[camera] = start
        result = detect_objects(msg.data, msg.width, msg.height, msg.step,
                                msg.encoding, camera, self.arena)
        stamp = msg.header.stamp.sec+msg.header.stamp.nanosec*1e-9
        if result['valid_image']:
            model = CameraModel(msg.width,msg.height)
            for obj in result['detections']:
                metric = model.locate(obj,camera)
                if metric:
                    obj.update(metric)
            result['detections'] = self.trackers[camera].update(result['detections'],stamp)
            k = model.k
            self.info[camera].publish(CameraInfo(header=msg.header,width=msg.width,height=msg.height,
                distortion_model='plumb_bob',d=[0.]*5,k=k,r=[1.,0.,0.,0.,1.,0.,0.,0.,1.],
                p=[k[0],0.,k[2],0.,0.,k[4],k[5],0.,0.,0.,1.,0.]))
        else:
            self.trackers[camera].clear()
        result.update(camera=camera, arena=self.arena, fresh=True,
                      calibration_source='simulator_pinhole_zero_distortion',
                      stamp={'sec': msg.header.stamp.sec, 'nanosec': msg.header.stamp.nanosec},
                      frame_id=msg.header.frame_id, width=msg.width, height=msg.height,
                      processing_ms=(time.monotonic()-start)*1000)
        self.publish(camera, result)
        if self.annotated[camera].get_subscription_count():
            pixels = annotate(msg.data, msg.width, msg.height, msg.step, msg.encoding,
                              result['detections']) if result['valid_image'] else None
            if pixels is None:
                self.unavailable(camera, 'INVALID CAMERA IMAGE')
            else:
                self.annotated[camera].publish(Image(
                    header=msg.header, width=msg.width, height=msg.height,
                    encoding='rgb8', step=msg.width*3, data=pixels))

    def unavailable(self, camera, message):
        if self.annotated[camera].get_subscription_count():
            msg = Image(width=640, height=480, encoding='rgb8', step=640*3,
                        data=unavailable_image(message))
            msg.header.stamp = self.get_clock().now().to_msg()
            self.annotated[camera].publish(msg)

    def expire(self):
        now = time.monotonic()
        for camera in self.publishers_by_camera:
            age = now-self.last_received.get(camera, now-2)
            if age > 1:
                self.trackers[camera].clear()
                self.publish(camera, dict(camera=camera, arena=self.arena, fresh=False,
                                          valid_image=False, detections=[], age_seconds=age))
                self.unavailable(camera, 'CAMERA STALE - NO DETECTIONS')


def main():
    rclpy.init(signal_handler_options=SignalHandlerOptions.NO)
    stopping = False
    def stop(signum, frame):
        nonlocal stopping
        stopping = True
    signal.signal(signal.SIGINT, stop)
    signal.signal(signal.SIGTERM, stop)
    node = Perception()
    executor = rclpy.executors.SingleThreadedExecutor()
    executor.add_node(node)
    try:
        while not stopping:
            executor.spin_once(timeout_sec=.1)
    finally:
        signal.signal(signal.SIGINT, signal.SIG_IGN)
        executor.shutdown()
        node.destroy_node()
        rclpy.try_shutdown()
