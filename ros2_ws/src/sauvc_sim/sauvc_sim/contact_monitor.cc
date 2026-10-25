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
#include <random>
#include <cmath>
#include <ignition/gazebo/components/DetachableJoint.hh>

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
  std::atomic<bool> request{false}, gripRequest{false};
  Entity attachment{kNullEntity}, pinger{kNullEntity};
  std::vector<Entity> fingers;
  bool pickupContact{false};
  double servoAngle{0};
  std::mt19937 rng{42};
  std::normal_distribution<double> acousticNoise{0,2e-7};
  ignition::transport::Node::Publisher acousticPublisher;
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
      node.Subscribe("/sauvc/payload/grip", &ArenaPhysics::Grip, this);
      acousticPublisher=node.Advertise<ignition::msgs::StringMsg>("/sauvc/acoustics");
      configured=true;
    }
    if (auv==kNullEntity || payload==kNullEntity || hull==kNullEntity) {
      ecm.Each<components::Model,components::Name>([&](const Entity &e,const components::Model *,const components::Name *n) {
        if (n->Data()=="sauvc_auv") auv=e;
        if (n->Data()=="payload_ball") payload=e;
        if (n->Data()=="pinger_source") pinger=e;
        for (size_t i=0;i<3;++i) if (n->Data()==names[i]+"_ball" && balls[i]==kNullEntity) {
          balls[i]=e;supports[i]=worldPose(e,ecm);
        }
        return true;
      });
      ecm.Each<components::Collision,components::Name>([&](const Entity &e,const components::Collision *,const components::Name *n) {
        if (n->Data()=="hull" && scopedName(e,ecm).find("sauvc_auv")!=std::string::npos) hull=e;
        if (n->Data().find("pickup_")==0 && scopedName(e,ecm).find("sauvc_auv")!=std::string::npos) {
          fingers.push_back(e);
          ecm.CreateComponent(e,components::ContactSensorData());
        }
        return true;
      });
    }
    if (info.paused || auv==kNullEntity || payload==kNullEntity) return;
    for (size_t i=0;i<3;++i) if (balls[i]!=kNullEntity) {
      if (!released[i]) Hold(balls[i],supports[i],ecm);
      else Free(balls[i],ecm);
    }
    // Ideal servo slew: 120 degrees in 0.4 s; no direct PWM/hardware control.
    if (request.load()) servoAngle=std::min(2.094395102,servoAngle+5.235987756*std::chrono::duration<double>(info.dt).count());
    if (!dropped) {
      if (servoAngle>=2.094395) {
        dropped=true;
        Free(payload,ecm);
      } else {
        auto pose=worldPose(auv,ecm);
        pose.Pos()+=pose.Rot().RotateVector(ignition::math::Vector3d(.2,0,-.18));
        Hold(payload,pose,ecm);
      }
    } else Free(payload,ecm);
    pickupContact=false;
    for (auto finger:fingers) {
      const auto *data=ecm.Component<components::ContactSensorData>(finger);
      if (data) for (const auto &c:data->Data().contact())
        if (c.collision1().name().find("payload_ball::")!=std::string::npos ||
            c.collision2().name().find("payload_ball::")!=std::string::npos) pickupContact=true;
    }
    if (gripRequest.load() && dropped && pickupContact && attachment==kNullEntity) {
      attachment=ecm.CreateEntity();
      ecm.CreateComponent(attachment,components::DetachableJoint({
        Model(auv).CanonicalLink(ecm),Model(payload).CanonicalLink(ecm),"fixed"}));
    }
    if (!gripRequest.load() && attachment!=kNullEntity) {
      ecm.RequestRemoveEntity(attachment);attachment=kNullEntity;
    }
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
  void Grip(const ignition::msgs::Boolean &msg) { gripRequest.store(msg.data()); }
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
       <<",\"payload_released\":"<<(dropped?"true":"false")
       <<",\"servo_angle_rad\":"<<servoAngle
       <<",\"pickup_contact\":"<<(pickupContact?"true":"false")
       <<",\"payload_attached\":"<<(attachment!=kNullEntity?"true":"false")<<",\"balls\":{";
    auto emit=[&](const std::string &name,Entity e,bool freed) {
      const auto p=worldPose(e,ecm).Pos();
      out<<'"'<<name<<"\":{\"position\":["<<p.X()<<','<<p.Y()<<','<<p.Z()
         <<"],\"released\":"<<(freed?"true":"false")<<'}';
    };
    emit("payload",payload,dropped);
    for (size_t i=0;i<3;++i) if (balls[i]!=kNullEntity) { out<<',';emit(names[i],balls[i],released[i]); }
    out<<"}}";
    ignition::msgs::StringMsg msg;msg.set_data(out.str());publisher.Publish(msg);
    if (pinger!=kNullEntity) {
      const auto pose=worldPose(auv,ecm);
      const auto source=worldPose(pinger,ecm).Pos();
      const std::array<ignition::math::Vector3d,4> hydro{{{.1,0,0},{-.1,0,0},{0,.1,0},{0,-.1,0}}};
      double distances[4];
      for (size_t i=0;i<4;++i) distances[i]=(source-(pose.Pos()+pose.Rot().RotateVector(hydro[i]))).Length();
      std::ostringstream packet;
      packet.precision(12);
      packet<<"{\"time\":"<<std::chrono::duration<double>(info.simTime).count()<<",\"frequency_hz\":45000,\"tdoa_s\":[0";
      for (size_t i=1;i<4;++i) packet<<','<<(distances[i]-distances[0])/1500.+acousticNoise(rng);
      packet<<"]}";
      ignition::msgs::StringMsg ping;ping.set_data(packet.str());acousticPublisher.Publish(ping);
    }
  }
};
}
IGNITION_ADD_PLUGIN(sauvc::ContactMonitor, ignition::gazebo::System,
                   sauvc::ContactMonitor::ISystemPreUpdate, sauvc::ContactMonitor::ISystemPostUpdate)
IGNITION_ADD_PLUGIN(sauvc::ArenaPhysics, ignition::gazebo::System,
                   sauvc::ArenaPhysics::ISystemPreUpdate, sauvc::ArenaPhysics::ISystemPostUpdate)
