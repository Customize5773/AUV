#include <chrono>
#include <csignal>
#include <atomic>
#include <stdexcept>
#include "managed_bridge.hpp"

namespace {
std::atomic<bool> stopping{false};
static_assert(std::atomic<bool>::is_always_lock_free);
void stop(int) { stopping.store(true, std::memory_order_relaxed); }
}

int main(int argc, char **argv) {
  rclcpp::init(argc, argv, rclcpp::InitOptions{}, rclcpp::SignalHandlerOptions::None);
  std::signal(SIGINT, stop);
  std::signal(SIGTERM, stop);
  auto bridge = std::make_shared<ManagedBridge>();
  int result = 0;
  try {
    if (bridge->get_parameter("config_file").as_string().empty())
      throw std::runtime_error("sauvc_bridge requires a config_file YAML parameter");
    rclcpp::executors::SingleThreadedExecutor executor;
    executor.add_node(bridge);
    while (!stopping.load(std::memory_order_relaxed) && rclcpp::ok())
      executor.spin_once(std::chrono::milliseconds(50));
    executor.remove_node(bridge);
  } catch (const std::exception &error) {
    RCLCPP_ERROR(bridge->get_logger(), "%s", error.what());
    result = 1;
  }
  bridge->release_endpoints();
  bridge.reset();
  rclcpp::shutdown();
  return result;
}
