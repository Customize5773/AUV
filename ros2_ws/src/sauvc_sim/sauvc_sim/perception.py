"""Camera-only perception topics; a missing camera clears its last detections."""
import json
import signal
import time

import rclpy
from rclpy.node import Node
from rclpy.qos import qos_profile_sensor_data
from rclpy.signals import SignalHandlerOptions
from sensor_msgs.msg import Image
from std_msgs.msg import String

from sauvc_sim.object_detection import detect_objects


class Perception(Node):
    def __init__(self):
        super().__init__('sauvc_perception')
        self.declare_parameter('arena', 'qualification')
        self.arena = self.get_parameter('arena').value
        if self.arena not in ('qualification', 'finals'):
            raise ValueError('unknown arena')
        self.last_received = {}
        self.publishers_by_camera = {}
        for camera in ('front', 'bottom'):
            self.publishers_by_camera[camera] = self.create_publisher(
                String, '/sauvc/perception/'+camera, 10)
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
        result.update(camera=camera, arena=self.arena, fresh=True,
                      stamp={'sec': msg.header.stamp.sec, 'nanosec': msg.header.stamp.nanosec},
                      frame_id=msg.header.frame_id, width=msg.width, height=msg.height,
                      processing_ms=(time.monotonic()-start)*1000)
        self.publish(camera, result)

    def expire(self):
        now = time.monotonic()
        for camera in self.publishers_by_camera:
            age = now-self.last_received.get(camera, now-2)
            if age > 1:
                self.publish(camera, dict(camera=camera, arena=self.arena, fresh=False,
                                          valid_image=False, detections=[], age_seconds=age))


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
