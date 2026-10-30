import json
import math
import time
from types import SimpleNamespace
from sauvc_sim.dynamics import PropulsionController
from sauvc_sim.physical_runtime import PhysicalRuntime
from sauvc_sim.runtime import Runtime
from sauvc_sim.state_estimation import StateEstimator


class Publisher:
    def __init__(self):self.messages=[]
    def publish(self,msg):self.messages.append(msg.data)


def propulsion():
    return SimpleNamespace(role='propulsion',surface_hold=True,hold_target=None,
        pose=(2.,3.,-.06,math.pi/2),active=True,disarmed=False,valid=True,
        last_received=time.monotonic(),cmd_time=time.monotonic(),desired=[0.]*4,
        measured=[0.]*4,z=-.06,controller=PropulsionController(),
        thrusters=Publisher(),hold_status=Publisher())


def test_hold_is_opt_in_and_stale_feedback_latches_motor_off():
    node=propulsion();node.surface_hold=False
    PhysicalRuntime.state(node,SimpleNamespace(data='STOP'))
    assert node.disarmed and node.hold_target is None
    node=propulsion();PhysicalRuntime.state(node,SimpleNamespace(data='STOP'))
    assert node.hold_target==node.pose
    node.pose=(2.1,3.,-.06,math.pi/2)
    PhysicalRuntime.tick(node)
    assert json.loads(node.hold_status.messages[-1])['active']
    assert any(abs(float(x))>0 for x in node.thrusters.messages[-1].split())
    node.last_received-=1
    PhysicalRuntime.tick(node)
    assert node.disarmed and all(float(x)==0 for x in node.thrusters.messages[-1].split())
    node.last_received=time.monotonic();node.cmd_time=time.monotonic()
    PhysicalRuntime.state(node,SimpleNamespace(data='DONE'));PhysicalRuntime.tick(node)
    assert all(float(x)==0 for x in node.thrusters.messages[-1].split())


def test_hold_guard_fault_and_abort_latch_off():
    for stop in ('guard','state'):
        node=propulsion();PhysicalRuntime.state(node,SimpleNamespace(data='STOP'))
        if stop=='guard':PhysicalRuntime.guard_fault(node,SimpleNamespace(data='stale_camera'))
        else:PhysicalRuntime.state(node,SimpleNamespace(data='ABORT'))
        PhysicalRuntime.tick(node)
        assert node.disarmed and all(float(x)==0 for x in node.thrusters.messages[-1].split())


def test_guard_still_publishes_fault_after_done():
    node=SimpleNamespace(terminal=True,fault_latched=False,fault_pub=Publisher(),get_logger=lambda:SimpleNamespace(error=lambda text:None))
    Runtime.trip(node,'stale_command');Runtime.trip(node,'stale_command')
    assert node.fault_pub.messages==['stale_command']


def test_integral_rejects_constant_disturbance_only_in_hold_mode():
    hold=PropulsionController();normal=PropulsionController()
    for _ in range(100):
        hold.command([0.]*4,[-.02,0.,0.,0.],-.095,.02,station_keeping=True)
        normal.command([0.]*4,[-.02,0.,0.,0.],-.095,.02)
    assert hold.integral[0]>.03 and normal.integral[0]==0
    assert hold.command([0.]*4,[0.]*4,-.095,.02,armed=False,station_keeping=True)==[0.]*7


def test_camera_gate_corrects_prior_with_age_compensation():
    e=StateEstimator(edition='2027',lane=1,prior_error=(.1,-.1))
    e.x=7.1;e.y=3.4;e.integration_velocity=[.8,0.,0.]
    for i in range(25):
        e.last=1.+i*.1
        e.observe_gate(dict(distance=2.76,bearing=0.),e.last-.1)
    assert abs(e.x-7.)<.002 and abs(e.y-3.5)<.002
    assert e.gate_corrections==23
    old=e.pose();assert not e.observe_gate(dict(distance=2.76,bearing=0.),e.last-.1)
    assert e.pose()==old


def test_camera_gate_rejects_stale_wrong_lane_and_return_view():
    e=StateEstimator(edition='2027');e.x=7.;e.y=10.;e.last=10.
    assert not e.observe_gate(dict(distance=2.68,bearing=0.),9.9)
    assert e.gate_corrections==0
    e.y=3.5;e.last=11.
    assert not e.observe_gate(dict(distance=2.68,bearing=0.),10.)
    e.yaw=math.pi
    assert not e.observe_gate(dict(distance=2.68,bearing=0.),10.95)
    e.arena='finals';e.yaw=0.;e.last=12.
    assert not e.observe_gate(dict(distance=2.68,bearing=0.),11.95)


def test_nonfinite_hold_pose_disarms_before_clamping_commands():
    node=propulsion();PhysicalRuntime.state(node,SimpleNamespace(data='STOP'))
    node.pose=(float('nan'),3.,-.06,0.)
    PhysicalRuntime.tick(node)
    assert node.disarmed and all(float(x)==0 for x in node.thrusters.messages[-1].split())


def test_initial_pose_uses_first_complete_sensor_set_after_partial_packets():
    e=StateEstimator();yaw=.4
    assert not e.update(dict(time=1.,gyro=[0.,0.,0.],accel=[0.,0.,9.81],mag=[20*math.cos(yaw),-20*math.sin(yaw),-45.]))
    assert not e.initialized
    assert e.update(dict(time=1.05,dvl=[0.,0.,0.],pressure_pa=101325+1000*9.81*.6))
    assert e.initialized and abs(e.z+.6)<1e-9 and abs(e.yaw-yaw)<1e-9


def test_arena_stop_distinguishes_active_hold_from_motor_off():
    from geometry_msgs.msg import Twist
    from sauvc_sim.arena_runtime import ArenaRuntime
    for hold in (False,True):
        node=SimpleNamespace(surface_hold=hold,physical=True,command_zero=True,force_zero=True,
                             judge=SimpleNamespace(thrust=lambda t,active:None))
        ArenaRuntime.dynamics(node,SimpleNamespace(data=json.dumps(dict(time=1.,force_n=[1.]*7))))
        assert node.zero==hold and not node.force_zero
        command=Twist();command.linear.x=.1
        ArenaRuntime.actual_command(node,command)
        assert not node.zero
        command.linear.x=0.;ArenaRuntime.actual_command(node,command)
        assert node.zero==hold
        ArenaRuntime.dynamics(node,SimpleNamespace(data=json.dumps(dict(time=2.,force_n=[0.]*7))))
        assert node.zero and node.force_zero
