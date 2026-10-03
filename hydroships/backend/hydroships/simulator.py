"""Explicit demo vehicle speaking actual MAVLink. NOT ArduSub SITL or physics."""
import math
import threading
import time

from pymavlink import mavutil


class DemoVehicle:
    def __init__(self, endpoint, *, drop_parameter_index=None):
        self.endpoint = endpoint
        self.stopped = threading.Event()
        self.paused = threading.Event()
        self.reject_writes = False
        self.silent_writes = False
        self.armed = False
        self.drop_parameter_index = drop_parameter_index
        self.params = {"SYSID_THISMAV": (42.0, 4), "PILOT_SPEED_DN": (50.0, 9),
                       "PILOT_SPEED_UP": (50.0, 9), "WPNAV_SPEED": (100.0, 9),
                       "GCS_PID_MASK": (0.0, 6), "SURFACE_DEPTH": (-0.1, 9)}
        self.writes = []
        self.thread = threading.Thread(target=self.run, name="demo-autopilot", daemon=True)

    def start(self):
        self.thread.start()

    def stop(self):
        self.stopped.set()
        self.thread.join(timeout=3)

    def run(self):
        link = mavutil.mavlink_connection(self.endpoint, source_system=42, source_component=1)
        start = time.monotonic()
        last_hb = last_data = 0

        def send_parameter(name):
            value, typ = self.params[name]
            link.mav.param_value_send(name.encode(), value, typ, len(self.params), list(self.params).index(name))

        try:
            while not self.stopped.wait(.01):
                now = time.monotonic()
                if self.paused.is_set():
                    continue
                elapsed = now - start
                if now - last_hb >= .5:
                    mode = 1 | (128 if self.armed else 0)
                    link.mav.heartbeat_send(12, 3, mode, 19, 3)
                    # 4.5.0 official version field, with mock explicitly named in UI.
                    link.mav.autopilot_version_send(2, 0x04050000, 0, 0, 0,
                        [0]*8, [0]*8, [0]*8, 0, 0, 42)
                    last_hb = now
                if now - last_data >= .1:
                    link.mav.attitude_send(int(elapsed*1000), .08*math.sin(elapsed/3),
                        .05*math.cos(elapsed/4), math.radians((elapsed*3)%360), 0, 0, 0)
                    link.mav.sys_status_send(0, 0, 0, 230, 15800, 230, 82, 0, 0, 0, 0, 0, 0)
                    # SCALED_PRESSURE2: display water pressure, not an invented depth.
                    link.mav.scaled_pressure2_send(int(elapsed*1000), 1013.25+100*abs(math.sin(elapsed/20)), 0, 2700)
                    link.mav.vfr_hud_send(0, 0, int(elapsed*3)%360, 0, -1.2-.2*math.sin(elapsed/10), 0)
                    last_data = now
                for _ in range(30):
                    msg = link.recv_match(blocking=False)
                    if msg is None:
                        break
                    typ = msg.get_type()
                    if typ == "PARAM_REQUEST_LIST":
                        for i, name in enumerate(self.params):
                            if i != self.drop_parameter_index:
                                send_parameter(name)
                    elif typ == "PARAM_REQUEST_READ":
                        name = str(msg.param_id).rstrip("\0")
                        if msg.param_index >= 0 and msg.param_index < len(self.params):
                            name = list(self.params)[msg.param_index]
                        if name in self.params:
                            send_parameter(name)
                    elif typ == "PARAM_SET":
                        name = str(msg.param_id).rstrip("\0")
                        self.writes.append((name, msg.param_value))
                        if name in self.params:
                            if not self.reject_writes:
                                self.params[name] = (msg.param_value, self.params[name][1])
                            if not self.silent_writes:
                                send_parameter(name)
        finally:
            link.close()
