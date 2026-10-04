"""Real ROS 2 transport with a labelled synthetic task driver; no motion outputs."""
import argparse
import collections
import ctypes
import json
import os
import queue
import signal
import sys
import threading
import time
import uuid

import rclpy
from rclpy.executors import SingleThreadedExecutor
from rclpy.node import Node
from rclpy.qos import qos_profile_sensor_data
from std_msgs.msg import String

from .core import MissionEngine

PREFIX = '/auv2027'


def publish(publisher, value):
    publisher.publish(String(data=json.dumps(value, allow_nan=False)))


def decode(message):
    if len(message.data) > 65536:
        raise ValueError('Pesan terlalu besar.')
    data = json.loads(message.data, parse_constant=lambda value: (_ for _ in ()).throw(ValueError(value)))
    if not isinstance(data, dict):
        raise ValueError('Pesan harus berupa object JSON.')
    return data


class MissionNode(Node):
    def __init__(self):
        super().__init__('mission_executor', namespace=PREFIX, start_parameter_services=False)
        self.engine = MissionEngine()
        self.executor_id = str(uuid.uuid4())
        self.acks = collections.OrderedDict()
        self.state_pub = self.create_publisher(String, PREFIX + '/mission/state', 10)
        self.ack_pub = self.create_publisher(String, PREFIX + '/mission/ack', 10)
        self.request_pub = self.create_publisher(String, PREFIX + '/tasks/request', 10)
        self.cancel_pub = self.create_publisher(String, PREFIX + '/tasks/cancel', 10)
        self.create_subscription(String, PREFIX + '/mission/command', self.command, 10)
        self.create_subscription(String, PREFIX + '/tasks/result', self.result, 10)
        self.create_timer(.05, self.tick)
        self.create_timer(.5, self.state)

    def command(self, message):
        try:
            data = decode(message)
            identifier = data.get('command_id')
            if not isinstance(identifier, str) or not 1 <= len(identifier) <= 64:
                return
            if identifier in self.acks:
                publish(self.ack_pub, self.acks[identifier]); return
            try:
                if data.get('action') == 'start' and data.get('mode') == 'software_test':
                    if not isinstance(data.get('run_id'), str):
                        raise ValueError('ID eksekusi harus berupa UUID.')
                    uuid.UUID(data['run_id'])
                    self.engine.start(data['run_id'], data['plan'], data['scenario'], data['revision'])
                elif data.get('action') == 'abort':
                    self.engine.abort(data.get('run_id'))
                else:
                    raise ValueError('Hanya eksekusi uji software dan abort yang tersedia.')
                ack = {'command_id': identifier, 'accepted': True, 'run_id': data['run_id']}
            except (KeyError, TypeError, ValueError) as exc:
                ack = {'command_id': identifier, 'accepted': False, 'error': str(exc)[:300]}
            self.acks[identifier] = ack
            if len(self.acks) > 64:
                self.acks.popitem(last=False)
            self.flush()
            self.state()
            publish(self.ack_pub, ack)
        except (ValueError, TypeError):
            pass

    def result(self, message):
        try:
            self.engine.result(decode(message))
            self.flush()
            self.state()
        except (TypeError, ValueError):
            pass

    def tick(self):
        self.engine.tick()
        self.flush()

    def flush(self):
        while self.engine.outbox:
            kind, data = self.engine.outbox.pop(0)
            publish(self.request_pub if kind == 'request' else self.cancel_pub, data)

    def state(self):
        publish(self.state_pub, {'executor_id': self.executor_id, 'mission': self.engine.snapshot()})


class TestTasks(Node):
    """Synthetic acknowledgements exercise lifecycle, not navigation or physics."""
    def __init__(self):
        super().__init__('software_test_tasks', namespace=PREFIX, start_parameter_services=False)
        self.pending = None
        self.seen = collections.deque(maxlen=64)
        self.publisher = self.create_publisher(String, PREFIX + '/tasks/result', 10)
        self.create_subscription(String, PREFIX + '/tasks/request', self.request, 10)
        self.create_subscription(String, PREFIX + '/tasks/cancel', self.cancel, 10)
        self.create_timer(.05, self.tick)

    def request(self, message):
        try:
            data = decode(message)
            if data.get('mode') != 'software_test' or data.get('request_id') in self.seen:
                return
            if not all(isinstance(data.get(k), str) and len(data[k]) <= 64 for k in ('run_id', 'request_id')):
                return
            self.seen.append(data['request_id'])
            self.pending = (time.monotonic() + 1.5, data)
        except (ValueError, TypeError):
            pass

    def cancel(self, message):
        try:
            data = decode(message)
            if self.pending and data.get('request_id') == self.pending[1]['request_id']:
                self.pending = None
        except (ValueError, TypeError):
            pass

    def tick(self):
        if self.pending and time.monotonic() >= self.pending[0]:
            data = self.pending[1]; self.pending = None
            if data.get('scenario') == 'no_response':
                return
            publish(self.publisher, {'run_id': data['run_id'], 'request_id': data['request_id'],
                                    'status': 'failed' if data.get('scenario') == 'failure' else 'succeeded',
                                    'detail': 'Kegagalan sintetis dari modul uji.'})


class ConsoleBridge(Node):
    def __init__(self, console):
        super().__init__('console_bridge', namespace=PREFIX, start_parameter_services=False)
        self.console = console
        self.commands = queue.Queue(maxsize=16)
        self.eof = False
        self.mission = None
        self.mission_at = None
        self.legacy = None
        self.legacy_at = None
        self.graph = {'nodes': [], 'topics': []}
        self.publisher = self.create_publisher(String, PREFIX + '/mission/command', 10)
        self.create_subscription(String, PREFIX + '/mission/state', self.receive, 10)
        self.create_subscription(String, PREFIX + '/mission/ack', self.ack, 10)
        self.create_subscription(String, '/hydroships/mission/state', self.receive_legacy, qos_profile_sensor_data)
        self.create_timer(.05, self.send)
        self.create_timer(.5, self.snapshot)
        self.create_timer(2, self.discover)
        if console:
            threading.Thread(target=self.read, daemon=True).start()

    def emit(self, value):
        if self.console:
            print(json.dumps(value, allow_nan=False), flush=True)

    def read(self):
        try:
            for line in sys.stdin:
                if len(line) > 65536:
                    continue
                try:
                    data = json.loads(line)
                    if isinstance(data, dict): self.commands.put(data, timeout=1)
                except (ValueError, queue.Full):
                    continue
        finally:
            self.eof = True

    def send(self):
        try:
            publish(self.publisher, self.commands.get_nowait())
        except queue.Empty:
            pass

    def receive(self, message):
        try:
            self.mission = decode(message)
            self.mission_at = time.monotonic()
        except (ValueError, TypeError):
            pass

    def ack(self, message):
        try:
            self.emit({'kind': 'ack', 'data': decode(message)})
        except (ValueError, TypeError):
            pass

    def receive_legacy(self, message):
        self.legacy = message.data[:160]
        self.legacy_at = time.monotonic()

    def discover(self):
        self.graph = {
            'nodes': sorted(set((namespace.rstrip('/') + '/' + name) for name, namespace in self.get_node_names_and_namespaces()))[:128],
            'topics': [{'name': name, 'types': types[:4]} for name, types in sorted(self.get_topic_names_and_types())[:128]],
        }

    def snapshot(self):
        now = time.monotonic()
        self.emit({'kind': 'snapshot', 'graph': self.graph, 'executor': self.mission,
                   'executor_age': None if self.mission_at is None else now - self.mission_at,
                   'command_subscribers': self.publisher.get_subscription_count(),
                   'legacy': {'state': self.legacy, 'age': None if self.legacy_at is None else now - self.legacy_at}})


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--console', action='store_true')
    tasks = parser.add_mutually_exclusive_group()
    tasks.add_argument('--test-tasks', action='store_true')
    tasks.add_argument('--external-tasks', action='store_true')
    args, ros_args = parser.parse_known_args()
    if args.console:
        parent = os.getppid()
        ctypes.CDLL(None).prctl(1, signal.SIGTERM)
        if os.getppid() != parent:
            return
    rclpy.init(args=ros_args)
    nodes = [MissionNode()]
    if not args.external_tasks: nodes.append(TestTasks())
    nodes.append(ConsoleBridge(args.console))
    executor = SingleThreadedExecutor()
    for node in nodes: executor.add_node(node)
    try:
        while rclpy.ok() and not nodes[-1].eof:
            executor.spin_once(timeout_sec=.1)
    except (KeyboardInterrupt, rclpy.executors.ExternalShutdownException):
        pass
    finally:
        executor.shutdown()
        for node in nodes: node.destroy_node()
        if rclpy.ok(): rclpy.shutdown()


if __name__ == '__main__':
    main()
