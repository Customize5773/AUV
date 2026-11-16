#pragma once
#include <rclcpp/rclcpp.hpp>
#include <ros_gz_bridge/ros_gz_bridge.hpp>

class ManagedBridge : public ros_gz_bridge::RosGzBridge {
public:
  void release_endpoints() {
    // Humble handles retain their owner; break that cycle while ROS is still alive.
    if (heartbeat_timer_) heartbeat_timer_->cancel();
    heartbeat_timer_.reset();
    handles_.clear();
    services_.clear();
    gz_node_.reset();
  }
};
