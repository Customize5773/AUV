"""Bounded physical camera -> ROS -> existing perception check; no vehicle control.

Run with ROS sourced, sauvc_sim on PYTHONPATH and an isolated ROS_DOMAIN_ID.
Image timestamps mark the end of VideoCapture.read(), not sensor exposure.
"""
import argparse
from array import array
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import time

import cv2
import numpy as np
import rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile, ReliabilityPolicy
from sensor_msgs.msg import Image
from std_msgs.msg import String


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('device')
    parser.add_argument('--seconds', type=int, default=30)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    if not 5 <= args.seconds <= 120:
        parser.error('seconds must be 5..120')
    if not args.device.startswith('/dev/v4l/by-id/') or not Path(args.device).is_char_device():
        parser.error('use an existing stable /dev/v4l/by-id/ capture device')
    if os.environ.get('ROS_DOMAIN_ID') != '187' or os.environ.get('ROS_LOCALHOST_ONLY') != '1':
        parser.error('requires ROS_DOMAIN_ID=187 ROS_LOCALHOST_ONLY=1 for isolated testing')
    owned = subprocess.run(['fuser', args.device], capture_output=True)
    if owned.returncode != 1:
        raise RuntimeError('camera busy or ownership check failed')
    rclpy.init()
    node = Node('physical_camera_check')
    qos = QoSProfile(depth=1, reliability=ReliabilityPolicy.BEST_EFFORT)
    pub = node.create_publisher(Image, '/physical_test/front/image_raw', qos)
    ages, processing, results, stale = [], [], [], []
    def receive(msg):
        data = json.loads(msg.data)
        if not data.get('fresh'):
            stale.append(time.monotonic())
            assert not data.get('detections'), 'stale target retained'
            return
        results.append(data)
        stamp = data['stamp']['sec'] + data['stamp']['nanosec'] * 1e-9
        ages.append(node.get_clock().now().nanoseconds / 1e9 - stamp)
        processing.append(data['processing_ms'])
    node.create_subscription(String, '/physical_test/front/detections', receive, 10)
    remaps = ['-r', '/sauvc/camera_front/image_raw:=/physical_test/front/image_raw',
              '-r', '/sauvc/perception/front:=/physical_test/front/detections',
              '-r', '/sauvc/camera_front/camera_info:=/physical_test/unvalidated_camera_info']
    child, cap, published, read_failures, exit_code = None, None, 0, 0, None
    passed = False
    started = time.monotonic()
    try:
        child = subprocess.Popen([sys.executable, '-c',
            'from sauvc_sim.perception import main; main()', '--ros-args',
            '-p', 'arena:=finals', '-p', 'use_sim_time:=false', *remaps])
        cap = cv2.VideoCapture(args.device, cv2.CAP_V4L2)
        if not cap.isOpened():
            raise RuntimeError('cannot open camera')
        while pub.get_subscription_count() == 0 and time.monotonic() - started < 15:
            if child.poll() is not None:
                raise RuntimeError('perception exited during startup')
            rclpy.spin_once(node, timeout_sec=.1)
        if not pub.get_subscription_count():
            raise RuntimeError('perception subscriber missing')
        capture_start = time.monotonic()
        while time.monotonic() - capture_start < args.seconds:
            if child.poll() is not None:
                raise RuntimeError('perception exited during capture')
            ok, frame = cap.read()
            stamp = node.get_clock().now().to_msg()
            if not ok:
                read_failures += 1
                raise RuntimeError('camera read failed')
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            height, width = rgb.shape[:2]
            msg = Image(height=height, width=width, encoding='rgb8', step=width * 3,
                        data=array('B', rgb.tobytes()))
            msg.header.stamp, msg.header.frame_id = stamp, 'uncalibrated_physical_front'
            pub.publish(msg)
            published += 1
            until = time.monotonic() + .1
            while time.monotonic() < until:
                rclpy.spin_once(node, timeout_sec=.01)
        cap.release()
        cap = None
        stopped = time.monotonic()
        while time.monotonic() - stopped < 3:
            rclpy.spin_once(node, timeout_sec=.05)
        assert ages and all(x['valid_image'] for x in results), 'no valid processed images'
        assert any(t > stopped + 1 for t in stale), 'camera loss did not expire detections'
        passed = True
    finally:
        if cap is not None:
            cap.release()
        if child is not None:
            child.send_signal(signal.SIGINT)
            try:
                exit_code = child.wait(timeout=10)
            except subprocess.TimeoutExpired:
                child.kill()
                child.wait()
                exit_code = -9
        report = dict(accepted=passed and exit_code == 0, published=published, processed=len(ages), read_failures=read_failures,
            frame_age_ms={str(p): float(np.percentile(ages, p)*1000) for p in (50, 95, 100)} if ages else {},
            processing_ms={str(p): float(np.percentile(processing, p)) for p in (50, 95, 100)} if processing else {},
            stale_messages=len(stale), perception_exit=exit_code,
            timestamp_basis='host_after_read_not_exposure', metric_geometry_validated=False,
            outbound_vehicle_messages=0)
        args.output.write_text(json.dumps(report, indent=2)+'\n')
        node.destroy_node()
        rclpy.try_shutdown()
    assert exit_code == 0, 'perception shutdown failed'
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
