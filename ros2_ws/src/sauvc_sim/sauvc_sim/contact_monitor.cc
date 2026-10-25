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
#include <ignition/msgs/boolean.pb.h>
#include <ignition/msgs/stringmsg.pb.h>
#include <ignition/gazebo/Model.hh>
#include <ignition/gazebo/Link.hh>
#include <ignition/gazebo/components/Model.hh>
#include <ignition/gazebo/components/Gravity.hh>
#include <ignition/gazebo/components/LinearVelocityCmd.hh>
#include <ignition/gazebo/components/AngularVelocityCmd.hh>
#include <atomic>
#include <array>
#include <sstream>

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

// Training mechanism: a real hull/pole contact releases the supported ball.
// Gravity and collisions then move it; a release request alone never earns points.
class ArenaPhysics : public System, public ISystemPreUpdate, public ISystemPostUpdate {
  ignition::transport::Node node;
  ignition::transport::Node::Publisher publisher;
  std::atomic<bool> request{false};
  Entity auv{kNullEntity}, hull{kNullEntity}, payload{kNullEntity};
  std::array<Entity,3> balls{{kNullEntity,kNullEntity,kNullEntity}};
  std::array<bool,3> released{{false,false,false}};
  std::array<ignition::math::Pose3d,3> supports;
  const std::array<std::string,3> names{{"blue_flare","red_flare","yellow_flare"}};
  bool dropped{false}, configured{false};
  std::chrono::steady_clock::duration last{};
public:
  void PreUpdate(const UpdateInfo &info, EntityComponentManager &ecm) override {
    if (!configured) {
      publisher=node.Advertise<ignition::msgs::StringMsg>("/sauvc/arena/physics");
      node.Subscribe("/sauvc/payload/release", &ArenaPhysics::Release, this);
      configured=true;
    }
    if (auv==kNullEntity || payload==kNullEntity || hull==kNullEntity) {
      ecm.Each<components::Model,components::Name>([&](const Entity &e,const components::Model *,const components::Name *n) {
        if (n->Data()=="sauvc_auv") auv=e;
        if (n->Data()=="payload_ball") payload=e;
        for (size_t i=0;i<3;++i) if (n->Data()==names[i]+"_ball" && balls[i]==kNullEntity) {
          balls[i]=e;supports[i]=worldPose(e,ecm);
        }
        return true;
      });
      ecm.Each<components::Collision,components::Name>([&](const Entity &e,const components::Collision *,const components::Name *n) {
        if (n->Data()=="hull" && scopedName(e,ecm).find("sauvc_auv")!=std::string::npos) hull=e;
        return true;
      });
    }
    if (info.paused || auv==kNullEntity || payload==kNullEntity) return;
    for (size_t i=0;i<3;++i) if (balls[i]!=kNullEntity) {
      if (!released[i]) Hold(balls[i],supports[i],ecm);
      else Free(balls[i],ecm);
    }
    if (!dropped) {
      if (request.load()) {
        dropped=true;
        Free(payload,ecm);
      } else {
        auto pose=worldPose(auv,ecm);
        pose.Pos()+=pose.Rot().RotateVector(ignition::math::Vector3d(.2,0,-.18));
        Hold(payload,pose,ecm);
      }
    } else Free(payload,ecm);
    const auto *contacts=ecm.Component<components::ContactSensorData>(hull);
    if (contacts) for (const auto &c:contacts->Data().contact()) {
      auto a=c.collision1().name(),b=c.collision2().name();
      for (size_t i=0;i<3;++i) if (!released[i] && balls[i]!=kNullEntity &&
          (a.find(names[i]+"::")!=std::string::npos || b.find(names[i]+"::")!=std::string::npos)) {
        released[i]=true;
        Enable(balls[i],ecm,true);
      }
    }
  }
  void Release(const ignition::msgs::Boolean &msg) { if (msg.data()) request.store(true); }
  void Hold(Entity e,const ignition::math::Pose3d &pose,EntityComponentManager &ecm) {
    Model(e).SetWorldPoseCmd(ecm,pose);
    auto link=Model(e).CanonicalLink(ecm);
    Link(link).SetLinearVelocity(ecm,ignition::math::Vector3d::Zero);
    Link(link).SetAngularVelocity(ecm,ignition::math::Vector3d::Zero);
  }
  void Free(Entity e,EntityComponentManager &ecm) {
    // Fortress retains a zeroed velocity command, which otherwise cancels gravity.
    auto link=Model(e).CanonicalLink(ecm);
    ecm.RemoveComponent<components::LinearVelocityCmd>(link);
    ecm.RemoveComponent<components::AngularVelocityCmd>(link);
  }
  void Enable(Entity entity,EntityComponentManager &ecm,bool nudge) {
    auto link=Model(entity).CanonicalLink(ecm);
    if (nudge) Link(link).SetLinearVelocity(ecm,ignition::math::Vector3d(.2,0,0));
  }
  void PostUpdate(const UpdateInfo &info,const EntityComponentManager &ecm) override {
    if (info.paused || payload==kNullEntity || info.simTime-last<std::chrono::milliseconds(50)) return;
    last=info.simTime;
    std::ostringstream out;
    out<<"{\"time\":"<<std::chrono::duration<double>(info.simTime).count()
       <<",\"payload_released\":"<<(dropped?"true":"false")<<",\"balls\":{";
    auto emit=[&](const std::string &name,Entity e,bool freed) {
      const auto p=worldPose(e,ecm).Pos();
      out<<'"'<<name<<"\":{\"position\":["<<p.X()<<','<<p.Y()<<','<<p.Z()
         <<"],\"released\":"<<(freed?"true":"false")<<'}';
    };
    emit("payload",payload,dropped);
    for (size_t i=0;i<3;++i) if (balls[i]!=kNullEntity) { out<<',';emit(names[i],balls[i],released[i]); }
    out<<"}}";
    ignition::msgs::StringMsg msg;msg.set_data(out.str());publisher.Publish(msg);
  }
};
}
IGNITION_ADD_PLUGIN(sauvc::ContactMonitor, ignition::gazebo::System,
                   sauvc::ContactMonitor::ISystemPreUpdate, sauvc::ContactMonitor::ISystemPostUpdate)
IGNITION_ADD_PLUGIN(sauvc::ArenaPhysics, ignition::gazebo::System,
                   sauvc::ArenaPhysics::ISystemPreUpdate, sauvc::ArenaPhysics::ISystemPostUpdate)
