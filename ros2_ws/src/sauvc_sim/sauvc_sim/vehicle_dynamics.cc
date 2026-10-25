// Force-driven plant and synthetic instruments. Truth is confined to the simulator.
#include <ignition/gazebo/System.hh>
#include <ignition/gazebo/Model.hh>
#include <ignition/gazebo/Link.hh>
#include <ignition/gazebo/Util.hh>
#include <ignition/gazebo/components/Model.hh>
#include <ignition/gazebo/components/Name.hh>
#include <ignition/plugin/Register.hh>
#include <ignition/transport/Node.hh>
#include <ignition/msgs/stringmsg.pb.h>
#include <array>
#include <algorithm>
#include <cmath>
#include <mutex>
#include <random>
#include <sstream>

namespace sauvc {
using namespace ignition::gazebo;
using V=ignition::math::Vector3d;
class VehicleDynamics : public System, public ISystemConfigure,
                        public ISystemPreUpdate, public ISystemPostUpdate {
  ignition::transport::Node node;
  ignition::transport::Node::Publisher sensors,telemetry;
  Entity model{kNullEntity},link{kNullEntity};
  std::mutex mutex;
  std::array<double,6> requested{},forces{};
  std::array<V,6> positions{{V(.2,.15,0),V(.2,-.15,0),V(-.2,.15,0),V(-.2,-.15,0),V(.18,0,0),V(-.18,0,0)}};
  const double c=std::sqrt(.5);
  std::array<V,6> axes{{V(c,-c,0),V(c,c,0),V(c,c,0),V(c,-c,0),V(0,0,1),V(0,0,1)}};
  double rho=1000,g=9.81,volume=.02005,height=.1336666667,cb=.03,tau=.15,hmax=20,vmax=40;
  double pn=20,dn=.003,gn=.0008,mn=.05,buoyancy=0,now=0,last_sensor=-1,last_slow=-1;
  V linear{8,12,80},quadratic{25,35,40},angular{1.5,1.5,.4},angular2{.8,.8,.8},current{},previous_velocity{};
  std::chrono::steady_clock::time_point last_command{};
  bool received=false,timed_out=false;
  std::string fault;
  std::mt19937 generator{42};
  std::normal_distribution<double> gaussian{0,1};
public:
  void Configure(const Entity &,const std::shared_ptr<const sdf::Element> &sdf,
                 EntityComponentManager &,EventManager &) override {
    rho=sdf->Get<double>("density");g=sdf->Get<double>("gravity");
    volume=sdf->Get<double>("volume");height=sdf->Get<double>("buoyancy_height");cb=sdf->Get<double>("buoyancy_z");
    tau=sdf->Get<double>("thruster_tau");hmax=sdf->Get<double>("horizontal_thrust");vmax=sdf->Get<double>("vertical_thrust");
    linear=sdf->Get<V>("linear_drag");quadratic=sdf->Get<V>("quadratic_drag");
    angular=sdf->Get<V>("angular_linear_drag");angular2=sdf->Get<V>("angular_quadratic_drag");current=sdf->Get<V>("current");
    pn=sdf->Get<double>("pressure_noise_pa");dn=sdf->Get<double>("dvl_noise");
    gn=sdf->Get<double>("gyro_noise");mn=sdf->Get<double>("mag_noise_ut");
    fault=sdf->Get<std::string>("fault");generator.seed(sdf->Get<unsigned int>("seed"));
    sensors=node.Advertise<ignition::msgs::StringMsg>("/sauvc/sensors");
    telemetry=node.Advertise<ignition::msgs::StringMsg>("/sauvc/dynamics/telemetry");
    node.Subscribe("/sauvc/thrusters",&VehicleDynamics::Command,this);
  }
  void Command(const ignition::msgs::StringMsg &msg) {
    std::istringstream in(msg.data());std::array<double,6> values{};
    for (auto &v:values) if (!(in>>v) || !std::isfinite(v) || std::abs(v)>1) return;
    std::string extra;if (in>>extra) return;
    std::lock_guard<std::mutex> lock(mutex);
    requested=values;last_command=std::chrono::steady_clock::now();received=true;
  }
  void PreUpdate(const UpdateInfo &info,EntityComponentManager &ecm) override {
    if (link==kNullEntity) {
      ecm.Each<components::Model,components::Name>([&](const Entity &e,const components::Model *,const components::Name *n) {
        if (n->Data()=="sauvc_auv") { model=e;link=Model(e).CanonicalLink(ecm);Link(link).EnableVelocityChecks(ecm);return false; }
        return true;
      });
    }
    if (info.paused || link==kNullEntity) return;
    now=std::chrono::duration<double>(info.simTime).count();
    double dt=std::chrono::duration<double>(info.dt).count();
    if (dt<=0) return;
    const auto pose=worldPose(link,ecm);
    auto vel=Link(link).WorldLinearVelocity(ecm),omega=Link(link).WorldAngularVelocity(ecm);
    if (!vel || !omega) return;
    V v=pose.Rot().RotateVectorReverse(*vel-current),w=pose.Rot().RotateVectorReverse(*omega);
    std::array<double,6> u{};
    {
      std::lock_guard<std::mutex> lock(mutex);
      timed_out=received && (std::chrono::duration<double>(std::chrono::steady_clock::now()-last_command).count()>.5 || (fault=="actuator_loss" && now>12));
      if (received && !timed_out) u=requested;
    }
    V force{},torque{};
    for (size_t i=0;i<6;++i) {
      double target=(i<4?hmax:vmax)*u[i]*std::abs(u[i]);
      forces[i]+=(1-std::exp(-dt/tau))*(target-forces[i]);
      V f=axes[i]*forces[i];force+=f;torque+=positions[i].Cross(f);
    }
    for (size_t i=0;i<3;++i) {
      force[i]-=linear[i]*v[i]+quadratic[i]*v[i]*std::abs(v[i]);
      torque[i]-=angular[i]*w[i]+angular2[i]*w[i]*std::abs(w[i]);
    }
    double fraction=std::clamp((height*.5-(pose.Pos().Z()+cb))/height,0.,1.);
    buoyancy=rho*g*volume*fraction;
    V up(0,0,buoyancy);
    V offset=pose.Rot().RotateVector(V(0,0,cb-height*(1-fraction)*.5));
    Link(link).AddWorldWrench(ecm,pose.Rot().RotateVector(force)+up,
                             pose.Rot().RotateVector(torque)+offset.Cross(up));
  }
  double noise(double sigma) { return sigma*gaussian(generator); }
  void PostUpdate(const UpdateInfo &info,const EntityComponentManager &ecm) override {
    if (info.paused || link==kNullEntity) return;
    double t=std::chrono::duration<double>(info.simTime).count();
    const auto pose=worldPose(link,ecm);
    auto vel=Link(link).WorldLinearVelocity(ecm),omega=Link(link).WorldAngularVelocity(ecm);
    if (!vel || !omega) return;
    double dt=std::chrono::duration<double>(info.dt).count();
    V accel=pose.Rot().RotateVectorReverse((*vel-previous_velocity)/std::max(dt,1e-6)+V(0,0,g));
    previous_velocity=*vel;
    if (t-last_sensor<.01) return;
    last_sensor=t;
    V gyro=pose.Rot().RotateVectorReverse(*omega),mag=pose.Rot().RotateVectorReverse(V(20,0,-45));
    V dvl=pose.Rot().RotateVectorReverse(*vel);
    std::ostringstream out;out.precision(12);
    out<<"{\"time\":"<<t<<",\"actuator_timeout\":"<<(timed_out?"true":"false");
    auto vector=[&](const char *key,V v,double sigma) {
      out<<",\""<<key<<"\":["<<v.X()+noise(sigma)<<','<<v.Y()+noise(sigma)<<','<<v.Z()+noise(sigma)<<']';
    };
    if (!(fault=="imu_loss" && t>12)) {
      vector("gyro",gyro+V(0,0,.001),gn);vector("accel",accel,.02);vector("mag",mag,mn);
    }
    if (t-last_slow>=.05) {
      last_slow=t;
      if (!(fault=="pressure_loss" && t>12))
        out<<",\"pressure_pa\":"<<101325+rho*g*std::max(0.,-pose.Pos().Z())+10+noise(pn);
      if (!(fault=="dvl_loss" && t>12)) vector("dvl",dvl+V(.001,-.001,.0005),dn);
    }
    out<<'}';ignition::msgs::StringMsg msg;msg.set_data(out.str());sensors.Publish(msg);
    std::ostringstream state;state<<"{\"time\":"<<t<<",\"buoyancy_n\":"<<buoyancy
      <<",\"timed_out\":"<<(timed_out?"true":"false")<<",\"force_n\":[";
    for (size_t i=0;i<6;++i) state<<(i?",":"")<<forces[i];
    state<<"]}";msg.set_data(state.str());telemetry.Publish(msg);
  }
};
}
IGNITION_ADD_PLUGIN(sauvc::VehicleDynamics,ignition::gazebo::System,
                   sauvc::VehicleDynamics::ISystemConfigure,sauvc::VehicleDynamics::ISystemPreUpdate,
                   sauvc::VehicleDynamics::ISystemPostUpdate)
