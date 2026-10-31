"""Test-only loss injection, timed from the first nonzero mission command."""
import json
import math


class FaultSchedule:
    def __init__(self, fault, delay, log):
        self.fault=fault;self.delay=delay;self.log=log
        self.started=None;self.injected=None

    def observe(self, command, stamp):
        values=(command.linear.x,command.linear.y,command.linear.z,command.angular.z)
        if self.started is None and all(math.isfinite(v) for v in values) and any(abs(v)>1e-6 for v in values):
            self.started=stamp

    def drop(self, key, stamp):
        due=self.fault==key+'_loss' and self.started is not None and stamp-self.started>self.delay
        if due and self.injected is None:
            self.injected=stamp
            self.log('FAULT_INJECTED '+json.dumps(dict(fault=self.fault,started_s=self.started,injected_s=stamp)))
        return due
