// Fortress publishes stock contact messages only on impact. Publish empty frames too.
#include <ignition/gazebo/System.hh>
#include <ignition/gazebo/EntityComponentManager.hh>
#include <ignition/gazebo/components/Collision.hh>
#include <ignition/gazebo/components/ContactSensorData.hh>
#include <ignition/gazebo/components/Name.hh>
#include <ignition/gazebo/Util.hh>
#include <ignition/plugin/Register.hh>
#include <ignition/transport/Node.hh>
#include <ignition/msgs/contacts.pb.h>

namespace sauvc {
using namespace ignition::gazebo;
class ContactMonitor : public System, public ISystemPreUpdate, public ISystemPostUpdate {
  ignition::transport::Node node;
  ignition::transport::Node::Publisher publisher;
  Entity hull{kNullEntity};
  std::chrono::steady_clock::duration last{};
public:
  void PreUpdate(const UpdateInfo &, EntityComponentManager &ecm) override {
    if (hull != kNullEntity) return;
    ecm.Each<components::Collision, components::Name>(
      [&](const Entity &entity, const components::Collision *, const components::Name *name) {
        if (name->Data() == "hull" && scopedName(entity, ecm).find("sauvc_auv") != std::string::npos) {
          hull = entity;
          ecm.CreateComponent(hull, components::ContactSensorData());
          publisher = node.Advertise<ignition::msgs::Contacts>("/sauvc/contacts");
          return false;
        }
        return true;
      });
  }
  void PostUpdate(const UpdateInfo &info, const EntityComponentManager &ecm) override {
    if (info.paused || hull == kNullEntity) return;
    const auto *data = ecm.Component<components::ContactSensorData>(hull);
    if (!data) return;
    if (data->Data().contact_size() == 0 && info.simTime-last < std::chrono::milliseconds(33)) return;
    auto message = data->Data();
    auto ns = std::chrono::duration_cast<std::chrono::nanoseconds>(info.simTime).count();
    message.mutable_header()->mutable_stamp()->set_sec(ns / 1000000000);
    message.mutable_header()->mutable_stamp()->set_nsec(ns % 1000000000);
    publisher.Publish(message);
    last = info.simTime;
  }
};
}
IGNITION_ADD_PLUGIN(sauvc::ContactMonitor, ignition::gazebo::System,
                   sauvc::ContactMonitor::ISystemPreUpdate, sauvc::ContactMonitor::ISystemPostUpdate)
