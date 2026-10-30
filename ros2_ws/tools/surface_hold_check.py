"""Independent hold-window measurements followed by a deliberate emergency stop."""
import copy
import math
import time
import rclpy
from std_msgs.msg import String
from sauvc_sim.runtime import STATUS_QOS


def verify_hold(node, observed):
    trajectory=observed['trajectory'];end=trajectory[-1][0]
    window=[p for p in trajectory if p[0]>=end-30.]
    drift=max(math.dist(p[1:3],window[0][1:3]) for p in window)
    depth=max(abs(p[3]-window[0][3]) for p in window)
    forces=[p for p in observed['dynamics'] if p['time']>=end-30.]
    active=bool(observed['hold_status']) and observed['hold_status'][-1]['active']
    powered=any(abs(f)>.05 for p in forces for f in p['force_n'])
    proof=dict(duration_s=window[-1][0]-window[0][0],max_xy_drift_m=drift,max_depth_change_m=depth,
               active=active,powered=powered,passed=window[-1][0]-window[0][0]>=29. and drift<.10 and depth<.03 and active and powered)
    completion=copy.deepcopy(observed['result'])
    pub=node.create_publisher(String,'/sauvc/guard/fault',STATUS_QOS)
    # Allow discovery, then exercise the actual fault subscription and thruster decay.
    until=time.monotonic()+.5
    while time.monotonic()<until:rclpy.spin_once(node,timeout_sec=.02)
    pub.publish(String(data='verification_surface_hold_stop'))
    until=time.monotonic()+3.
    while time.monotonic()<until:rclpy.spin_once(node,timeout_sec=.02)
    proof['abort_disarmed']=bool(observed['hold_status']) and observed['hold_status'][-1]['disarmed'] and not observed['hold_status'][-1]['active']
    proof['abort_thrusters_zero']=len(observed['dynamics'])>=10 and all(abs(f)<.05 for p in observed['dynamics'][-10:] for f in p['force_n'])
    proof['passed']=proof['passed'] and proof['abort_disarmed'] and proof['abort_thrusters_zero']
    proof['result_after_injected_abort']=observed['result']
    observed['result']=completion
    node.destroy_publisher(pub)
    return proof
