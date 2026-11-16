#include <atomic>
#include <chrono>
#include <cstdlib>
#include <functional>
#include <iostream>
#include <thread>
#include <ignition/msgs/stringmsg.pb.h>
#include <std_msgs/msg/string.hpp>
#include "../src/managed_bridge.hpp"

bool check(ros_gz_bridge::BridgeDirection direction, int index) {
  std::atomic<bool> ros_seen{false}, gz_seen{false};
  ignition::transport::Node native;
  auto bridge = std::make_shared<ManagedBridge>();
  auto observer = std::make_shared<rclcpp::Node>("bridge_observer");
  ros_gz_bridge::BridgeConfig config;
  config.ros_topic_name = "/sauvc_lifetime/ros" + std::to_string(index);
  config.gz_topic_name = "/sauvc_lifetime/gz" + std::to_string(index);
  config.ros_type_name = "std_msgs/msg/String";
  config.gz_type_name = "ignition.msgs.StringMsg";
  config.direction = direction;
  bridge->add_bridge(config);
  auto pub = observer->create_publisher<std_msgs::msg::String>(config.ros_topic_name, 10);
  auto sub = observer->create_subscription<std_msgs::msg::String>(config.ros_topic_name, 10,
    [&](std_msgs::msg::String::ConstSharedPtr msg) { if (msg->data == "native") ros_seen = true; });
  std::function<void(const ignition::msgs::StringMsg &)> callback =
    [&](const ignition::msgs::StringMsg &msg) { if (msg.data() == "ros") gz_seen = true; };
  bool subscribed = native.Subscribe(config.gz_topic_name, callback);
  bool need_ros = direction != ros_gz_bridge::BridgeDirection::ROS_TO_GZ;
  bool need_gz = direction != ros_gz_bridge::BridgeDirection::GZ_TO_ROS;
  bool publisher_ok = true;
  rclcpp::executors::SingleThreadedExecutor executor;
  executor.add_node(bridge); executor.add_node(observer);
  auto deadline = std::chrono::steady_clock::now() + std::chrono::seconds(8);
  while (((need_ros && !ros_seen) || (need_gz && !gz_seen)) &&
      std::chrono::steady_clock::now() < deadline) {
    std_msgs::msg::String ros_message; ros_message.data = "ros"; pub->publish(ros_message);
    // The bridge ignores local Gazebo messages; publish from a separate process.
    if (need_ros) {
      auto command = "ign topic -t " + config.gz_topic_name +
        " -m ignition.msgs.StringMsg -p 'data: \"native\"'";
      publisher_ok = (std::system(command.c_str()) == 0) && publisher_ok;
    }
    executor.spin_some(std::chrono::milliseconds(5));
    std::this_thread::sleep_for(std::chrono::milliseconds(20));
  }
  bool delivered = subscribed && publisher_ok && (!need_ros || ros_seen) && (!need_gz || gz_seen);
  executor.remove_node(observer); executor.remove_node(bridge);
  pub.reset(); sub.reset(); observer.reset();
  std::weak_ptr<ManagedBridge> weak = bridge;
  std::cout << "direction=" << index << " delivered=" << delivered
            << " references_before_release=" << bridge.use_count() << std::endl;
  bridge->release_endpoints(); bridge->release_endpoints(); bridge.reset();
  bool released = weak.expired();
  std::cout << "released=" << released << std::endl;
  native.Unsubscribe(config.gz_topic_name);
  return delivered && released;
}

int main(int argc, char **argv) {
  rclcpp::init(argc, argv);
  bool passed = true;
  for (int index = 1; index <= 3; ++index)
    passed = check(static_cast<ros_gz_bridge::BridgeDirection>(index), index) && passed;
  rclcpp::shutdown();
  return passed ? 0 : 1;
}
