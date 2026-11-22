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
#include <ignition/gazebo/components/LinearVelocityCmd.hh>
#include <ignition/gazebo/components/AngularVelocityCmd.hh>
#include <atomic>
#include <array>
#include <sstream>
#include <random>
#include <cmath>
#include <ignition/gazebo/components/DetachableJoint.hh>
#include <ignition/gazebo/components/Link.hh>
#include <algorithm>
#include <ignition/gazebo/components/Joint.hh>
#include <ignition/gazebo/components/JointPosition.hh>
#include <ignition/msgs/double.pb.h>

namespace sauvc {
using namespace ignition::gazebo;
static std::vector<Entity> observeHull(EntityComponentManager &ecm) {
  std::vector<Entity> parts;
  ecm.Each<components::Collision, components::Name>(
    [&](const Entity &entity, const components::Collision *, const components::Name *name) {
      if ((name->Data() == "hull" || name->Data() == "hull_upper") &&
          scopedName(entity, ecm, "::", false).find("sauvc_auv::") != std::string::npos) {
        parts.push_back(entity);
        if (!ecm.Component<components::ContactSensorData>(entity))
          ecm.CreateComponent(entity, components::ContactSensorData());
      }
      return true;
    });
  return parts;
}

class ContactMonitor : public System, public ISystemPreUpdate, public ISystemPostUpdate {
  ignition::transport::Node node;
  ignition::transport::Node::Publisher publisher;
  std::vector<Entity> hullParts;
  std::chrono::steady_clock::duration last{};
public:
  void PreUpdate(const UpdateInfo &, EntityComponentManager &ecm) override {
    if (!hullParts.empty()) return;
    hullParts = observeHull(ecm);
    if (!hullParts.empty())
      publisher = node.Advertise<ignition::msgs::Contacts>("/sauvc/contacts");
  }
  void PostUpdate(const UpdateInfo &info, const EntityComponentManager &ecm) override {
    if (info.paused || hullParts.empty()) return;
    ignition::msgs::Contacts message;
    for (auto part : hullParts) {
      const auto *data = ecm.Component<components::ContactSensorData>(part);
      if (data) for (const auto &contact : data->Data().contact())
        *message.add_contact() = contact;
    }
    if (!message.contact_size() && info.simTime-last < std::chrono::milliseconds(33)) return;
    auto ns = std::chrono::duration_cast<std::chrono::nanoseconds>(info.simTime).count();
    message.mutable_header()->mutable_stamp()->set_sec(ns / 1000000000);
    message.mutable_header()->mutable_stamp()->set_nsec(ns % 1000000000);
    publisher.Publish(message);
    last = info.simTime;
  }
};

// Training mechanism: a real hull/pole contact releases the supported ball.
// Gravity and collisions then move it; a release request alone never earns points.
class ArenaPhysics : public System, public ISystemConfigure, public ISystemPreUpdate, public ISystemPostUpdate {
  ignition::transport::Node node;
  ignition::transport::Node::Publisher publisher;
  std::atomic<bool> request{false}, gripRequest{false};
  Entity attachment{kNullEntity}, loadingJoint{kNullEntity}, pinger{kNullEntity};
  Entity gripper{kNullEntity};
  std::array<std::vector<Entity>,2> fingers;
  std::array<bool,2> jawContact{};
  bool pickupContact{false}, usePickupJoint{true}, bilateralWitness{false};
  double servoAngle{0};
  std::array<Entity,2> jaws{{kNullEntity,kNullEntity}};
  std::array<double,2> jawPosition{{0,0}},jawTarget{{0,0}};
  std::array<ignition::transport::Node::Publisher,2> jawPublishers;
  bool jawReady{false},jawsOpen{false};
  std::mt19937 rng{42};
  std::normal_distribution<double> acousticNoise{0,2e-7};
  ignition::transport::Node::Publisher acousticPublisher;
  Entity auv{kNullEntity}, payload{kNullEntity};
  std::vector<Entity> hullParts;
  std::array<Entity,3> balls{{kNullEntity,kNullEntity,kNullEntity}};
  std::array<bool,3> released{{false,false,false}};
  std::array<ignition::math::Pose3d,3> supports;
  const std::array<std::string,3> names{{"blue_flare","red_flare","yellow_flare"}};
  bool dropped{false}, configured{false};
  std::chrono::steady_clock::duration last{};
public:
  void Configure(const Entity &, const std::shared_ptr<const sdf::Element> &sdf,
                 EntityComponentManager &, EventManager &) override {
    usePickupJoint = sdf->Get<bool>("use_pickup_joint", true).first;
  }
  void PreUpdate(const UpdateInfo &info, EntityComponentManager &ecm) override {
    if (!configured) {
      publisher=node.Advertise<ignition::msgs::StringMsg>("/sauvc/arena/physics");
      node.Subscribe("/sauvc/payload/release", &ArenaPhysics::Release, this);
      node.Subscribe("/sauvc/payload/grip", &ArenaPhysics::Grip, this);
      acousticPublisher=node.Advertise<ignition::msgs::StringMsg>("/sauvc/acoustics");
      for (size_t i=0;i<2;++i)
        jawPublishers[i]=node.Advertise<ignition::msgs::Double>("/sauvc/gripper/"+std::to_string(i)+"/target");
      configured=true;
    }
    if (auv==kNullEntity || payload==kNullEntity || hullParts.empty() || gripper==kNullEntity || jaws[0]==kNullEntity || jaws[1]==kNullEntity) {
      if (hullParts.empty()) hullParts = observeHull(ecm);
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
        const auto scope=scopedName(e,ecm,"::",false);
        for (size_t i=0;i<fingers.size();++i) {
          const auto jawScope="sauvc_auv::pickup_jaw_"+std::to_string(i)+"::";
          auto &collisions=fingers[i];
          if (scope.find(jawScope)!=std::string::npos &&
              std::find(collisions.begin(),collisions.end(),e)==collisions.end()) {
            collisions.push_back(e);
            ecm.CreateComponent(e,components::ContactSensorData());
          }
        }
        return true;
      });
      ecm.Each<components::Joint,components::Name>([&](const Entity &e,const components::Joint *,const components::Name *n) {
        for (size_t i=0;i<2;++i) if (n->Data()=="pickup_hinge_"+std::to_string(i) && scopedName(e,ecm).find("sauvc_auv")!=std::string::npos) {
          jaws[i]=e;
          if (!ecm.Component<components::JointPosition>(e)) ecm.CreateComponent(e,components::JointPosition());
        }
        return true;
      });
      ecm.Each<components::Link,components::Name>([&](const Entity &e,const components::Link *,const components::Name *n) {
        if (n->Data()=="payload_gripper" && scopedName(e,ecm).find("sauvc_auv")!=std::string::npos) {
          gripper=e;
        }
        return true;
      });
    }
    if (info.paused || auv==kNullEntity || payload==kNullEntity || gripper==kNullEntity) return;
    jawReady=true;
    jawsOpen=true;
    for (size_t i=0;i<2;++i) {
      const double open=i==0?-.35:.35;
      jawTarget[i]=(request.load() && !gripRequest.load())?open:0.;
      const auto *position=jaws[i]==kNullEntity?nullptr:ecm.Component<components::JointPosition>(jaws[i]);
      const bool valid=position && !position->Data().empty() && std::isfinite(position->Data()[0]);
      jawPosition[i]=valid?position->Data()[0]:0.;
      jawReady=jawReady && valid;
      jawsOpen=jawsOpen && valid && std::abs(jawPosition[i]-open)<.015;
      if (info.simTime-last>=std::chrono::milliseconds(50)) {
        ignition::msgs::Double target;target.set_data(jawTarget[i]);jawPublishers[i].Publish(target);
      }
    }
    if (!dropped && loadingJoint==kNullEntity) {
      loadingJoint=ecm.CreateEntity();
      ecm.CreateComponent(loadingJoint,components::DetachableJoint({
        gripper,Model(payload).CanonicalLink(ecm),"fixed"}));
    }
    for (size_t i=0;i<3;++i) if (balls[i]!=kNullEntity) {
      if (!released[i]) Hold(balls[i],supports[i],ecm);
      else Free(balls[i],ecm);
    }
    // Ideal servo slew: 120 degrees in 0.4 s; no direct PWM/hardware control.
    if (request.load()) servoAngle=std::min(2.094395102,servoAngle+5.235987756*std::chrono::duration<double>(info.dt).count());
    if (!dropped) {
      if (servoAngle>=2.094395 && jawsOpen) {
        dropped=true;
        ecm.RequestRemoveEntity(loadingJoint);loadingJoint=kNullEntity;
        Free(payload,ecm);
      }
    } else Free(payload,ecm);
    jawContact.fill(false);
    for (size_t i=0;i<fingers.size();++i) for (auto finger:fingers[i]) {
      const auto *data=ecm.Component<components::ContactSensorData>(finger);
      if (data) for (const auto &c:data->Data().contact())
        if (c.collision1().name().find("payload_ball::")!=std::string::npos ||
            c.collision2().name().find("payload_ball::")!=std::string::npos) jawContact[i]=true;
    }
    pickupContact=jawContact[0] || jawContact[1];
    const bool gripping = gripRequest.load() && dropped && jawReady && !jawsOpen;
    const bool bilateral = gripping && jawContact[0] && jawContact[1];
    if (!usePickupJoint && gripper!=kNullEntity && payload!=kNullEntity) {
      const double gap=worldPose(gripper,ecm).Pos().Distance(worldPose(payload,ecm).Pos());
      bilateralWitness=gripping && gap<.075 && (bilateral || bilateralWitness);
    }
    if (usePickupJoint && bilateral && attachment==kNullEntity && gripper!=kNullEntity) {
      attachment=ecm.CreateEntity();
      ecm.CreateComponent(attachment,components::DetachableJoint({
        gripper,Model(payload).CanonicalLink(ecm),"fixed"}));
    }
    if (!gripRequest.load() && jawsOpen && attachment!=kNullEntity) {
      ecm.RequestRemoveEntity(attachment);attachment=kNullEntity;
    }
    for (auto part : hullParts) {
      const auto *contacts=ecm.Component<components::ContactSensorData>(part);
      if (contacts) for (const auto &c:contacts->Data().contact()) {
        auto a=c.collision1().name(),b=c.collision2().name();
        for (size_t i=0;i<3;++i) if (!released[i] && balls[i]!=kNullEntity &&
            (a.find(names[i]+"::")!=std::string::npos || b.find(names[i]+"::")!=std::string::npos)) {
          released[i]=true;
          Enable(balls[i],ecm,true);
        }
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
    if (info.paused || payload==kNullEntity || gripper==kNullEntity || info.simTime-last<std::chrono::milliseconds(50)) return;
    last=info.simTime;
    std::ostringstream out;
    const auto capture=worldPose(gripper,ecm).Pos();
    out<<"{\"time\":"<<std::chrono::duration<double>(info.simTime).count()
       <<",\"pickup_position\":["<<capture.X()<<','<<capture.Y()<<','<<capture.Z()<<']'
       <<",\"payload_released\":"<<(dropped?"true":"false")
       <<",\"servo_angle_rad\":"<<servoAngle
       <<",\"jaw_ready\":"<<(jawReady?"true":"false")
       <<",\"jaws_open\":"<<(jawsOpen?"true":"false")
       <<",\"jaw_position_rad\":["<<jawPosition[0]<<','<<jawPosition[1]<<']'
       <<",\"jaw_target_rad\":["<<jawTarget[0]<<','<<jawTarget[1]<<']'
       <<",\"unlatched_bilateral_grip\":"<<(bilateralWitness?"true":"false")
       <<",\"pickup_contact\":"<<(pickupContact?"true":"false")
       <<",\"payload_attached\":"<<(attachment!=kNullEntity || loadingJoint!=kNullEntity?"true":"false")<<",\"balls\":{";
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
                   sauvc::ArenaPhysics::ISystemConfigure, sauvc::ArenaPhysics::ISystemPreUpdate, sauvc::ArenaPhysics::ISystemPostUpdate)
