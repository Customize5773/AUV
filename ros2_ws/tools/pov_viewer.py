"""Display one annotated camera in a single Qt/ROS process with graceful shutdown."""
import argparse
import signal
import sys

import rclpy
from rclpy.qos import qos_profile_sensor_data
from rclpy.signals import SignalHandlerOptions
from sensor_msgs.msg import Image
from python_qt_binding.QtCore import Qt, QTimer
from python_qt_binding.QtGui import QImage, QPixmap
from python_qt_binding.QtWidgets import QApplication, QLabel
from sauvc_sim.gate_detection import decode_rgb


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('camera',choices=['front','bottom'])
    camera=parser.parse_args().camera
    app=QApplication(sys.argv[:1])
    app.setApplicationName('sauvc_pov')
    label=QLabel('Waiting for camera…')
    label.setWindowTitle('SAUVC POV '+camera)
    label.setAlignment(Qt.AlignCenter)
    label.resize(640,480)
    rclpy.init(signal_handler_options=SignalHandlerOptions.NO)
    node=rclpy.create_node('sauvc_pov_'+camera)

    def image(msg):
        rgb=decode_rgb(msg.data,msg.width,msg.height,msg.step,msg.encoding)
        if rgb is None:
            label.setText('INVALID CAMERA IMAGE')
            return
        pixels=rgb.tobytes()
        frame=QImage(pixels,msg.width,msg.height,msg.width*3,QImage.Format_RGB888)
        label.setPixmap(QPixmap.fromImage(frame).scaled(label.size(),Qt.KeepAspectRatio,Qt.FastTransformation))

    node.create_subscription(Image,'/sauvc/perception/'+camera+'/image_annotated',image,qos_profile_sensor_data)
    timer=QTimer()
    timer.timeout.connect(lambda:rclpy.spin_once(node,timeout_sec=0.))
    timer.start(20)
    for sig in (signal.SIGINT,signal.SIGTERM):
        signal.signal(sig,lambda *_:app.quit())
    label.show()
    try:
        return app.exec_()
    finally:
        timer.stop()
        node.destroy_node()
        rclpy.shutdown()


if __name__=='__main__':
    sys.exit(main())
