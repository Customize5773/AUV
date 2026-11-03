// Record image metadata before the ROS bridge; never copy pixels to the log.
#include <ignition/transport/Node.hh>
#include <ignition/msgs/image.pb.h>
#include <csignal>
#include <fstream>
#include <iomanip>
#include <mutex>
#include <thread>
#include <chrono>
#include <ctime>

static volatile std::sig_atomic_t stopping = 0;
static void stop(int) { stopping = 1; }
static double wall() {
  timespec t; clock_gettime(CLOCK_MONOTONIC, &t);
  return t.tv_sec + t.tv_nsec * 1e-9;
}

int main(int argc, char **argv) {
  if (argc != 2) return 2;
  std::ofstream out(argv[1]);
  if (!out) return 2;
  out << std::setprecision(17);
  std::mutex mutex;
  ignition::transport::Node node;
  for (const std::string camera : {"front", "bottom"}) {
    std::function<void(const ignition::msgs::Image &)> callback =
      [&, camera](const ignition::msgs::Image &msg) {
        const double received = wall();
        std::lock_guard<std::mutex> lock(mutex);
        out << "{\"kind\":\"native_image\",\"camera\":\"" << camera
            << "\",\"wall_s\":" << received << ",\"sim_s\":"
            << msg.header().stamp().sec() + msg.header().stamp().nsec() * 1e-9
            << ",\"width\":" << msg.width() << ",\"height\":" << msg.height()
            << ",\"bytes\":" << msg.data().size() << "}\n";
      };
    if (!node.Subscribe("/sauvc/camera_" + camera + "/image_raw", callback)) return 3;
  }
  std::signal(SIGINT, stop); std::signal(SIGTERM, stop);
  while (!stopping) {
    {
      std::lock_guard<std::mutex> lock(mutex);
      out << "{\"kind\":\"heartbeat\",\"wall_s\":" << wall() << "}\n";
      out.flush();
      if (!out) return 4;
    }
    std::this_thread::sleep_for(std::chrono::milliseconds(100));
  }
}
