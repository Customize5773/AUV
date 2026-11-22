// Native regression for the Fortress render-thread double join.
#include "../sauvc_sim/fortress_sensors/Sensors.cc"
#include <future>

int main()
{
  SensorsPrivate sensors;
  std::promise<void> release;
  auto ready = release.get_future();
  sensors.running = true;
  sensors.renderThread = std::thread([&] { ready.wait(); });
  std::thread first([&] { sensors.Stop(); });
  while (sensors.running)
    std::this_thread::yield();
  std::thread second([&] { sensors.Stop(); });
  std::this_thread::sleep_for(std::chrono::milliseconds(100));
  release.set_value();
  first.join();
  second.join();
  return sensors.renderThread.joinable() ? 1 : 0;
}
