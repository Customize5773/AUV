"""One worker owns all MAVLink I/O. No actuator or mode commands are exposed."""
import copy
import math
import queue
import re
import struct
import threading
import time
import uuid
from concurrent.futures import Future
from pathlib import Path

from pymavlink import mavutil
from serial.tools import list_ports

from .simulator import DemoVehicle


class VehicleError(Exception):
    pass


def serial_devices():
    aliases = {}
    for alias in Path("/dev/serial/by-id").glob("*"):
        aliases[str(alias.resolve())] = str(alias)
    return [{"path": aliases.get(port.device, port.device), "device": port.device,
             "description": port.description, "serial": port.serial_number,
             "vid": port.vid, "pid": port.pid, "stable": port.device in aliases}
            for port in list_ports.comports()]


def parameter_value(value, typ):
    if isinstance(value, bool):
        raise VehicleError("Nilai harus berupa angka, bukan boolean.")
    try:
        value = float(value)
        encoded = struct.unpack("<f", struct.pack("<f", value))[0]
    except (TypeError, ValueError, OverflowError, struct.error):
        raise VehicleError("Nilai tidak dapat dikirim sebagai float32.")
    if not math.isfinite(value) or not math.isfinite(encoded):
        raise VehicleError("Nilai harus berupa angka finite.")
    bounds = {1: (0, 255), 2: (-128, 127), 3: (0, 65535), 4: (-32768, 32767),
              5: (0, 4294967295), 6: (-2147483648, 2147483647)}
    if typ in bounds:
        low, high = bounds[typ]
        if not value.is_integer() or not low <= value <= high or encoded != value:
            raise VehicleError("Nilai integer di luar rentang atau tidak dapat diwakili tepat.")
    elif typ != 9:
        raise VehicleError("Tipe parameter ini belum didukung untuk perubahan.")
    return encoded


class Vehicle:
    def __init__(self, storage, heartbeat_timeout=3.0, write_timeout=3.0):
        self.storage = storage
        self.heartbeat_timeout = heartbeat_timeout
        self.write_timeout = write_timeout
        self.lock = threading.RLock()
        self.commands = queue.Queue(maxsize=64)
        self.stopped = threading.Event()
        self.thread = threading.Thread(target=self._run, name="mavlink-owner", daemon=True)
        self.link = None
        self.demo = None
        self.spec = None
        self.status = "disconnected"
        self.error = None
        self.session = str(uuid.uuid4())
        self.target = None
        self.expected_target = None
        self.identity = {}
        self.fields = {}
        self.params = {}
        self.param_count = 0
        self.param_indices = set()
        self.param_state = "idle"
        self.download_started = 0
        self.last_param_request = 0
        self.retry_index = 0
        self.pending = None
        self.last_heartbeat = None
        self.opened_at = 0
        self.next_open = 0
        self.received = 0
        self.started_at = time.time()

    def start(self):
        self.thread.start()

    def stop(self):
        self.stopped.set()
        self.thread.join(timeout=5)
        if self.thread.is_alive():
            raise RuntimeError("MAVLink worker did not stop")

    def submit(self, action, **payload):
        future = Future()
        try:
            self.commands.put_nowait((action, payload, future))
        except queue.Full:
            future.set_exception(VehicleError("Antrean penuh. Coba lagi setelah operasi selesai."))
        return future

    def snapshot(self):
        with self.lock:
            now = time.monotonic()
            fields = {key: {**value, "age": max(0, now-value["_mono"]),
                           "stale": self.status != "connected" or now-value["_mono"] > 3}
                      for key, value in self.fields.items()}
            for value in fields.values():
                value.pop("_mono", None)
            return {"status": self.status, "error": self.error, "session": self.session,
                    "connection": copy.deepcopy(self.spec), "identity": copy.deepcopy(self.identity),
                    "heartbeat_age": None if self.last_heartbeat is None else now-self.last_heartbeat,
                    "fields": fields, "received": self.received,
                    "parameters": {"count": len(self.params), "expected": self.param_count,
                                   "state": self.param_state, "writing": self.pending is not None},
                    "write_allowed": self._write_allowed(), "worker_alive": self.thread.is_alive()}

    def parameter_snapshot(self):
        with self.lock:
            return {"session": self.session, "state": self.param_state, "expected": self.param_count,
                    "items": [copy.deepcopy(self.params[k]) for k in sorted(self.params)]}

    def _write_allowed(self):
        return (self.status == "connected" and self.last_heartbeat is not None
                and time.monotonic()-self.last_heartbeat < self.heartbeat_timeout
                and self.identity.get("autopilot") == 3 and self.identity.get("vehicle_type") == 12
                and self.identity.get("firmware") is not None and self.identity.get("armed") is False)

    def _field(self, key, value, unit, source):
        if value is None or not math.isfinite(value):
            return
        self.fields[key] = {"value": value, "unit": unit, "source": source,
                            "ts": time.time(), "_mono": time.monotonic()}

    def _fail_pending(self, reason):
        if self.pending:
            pending, self.pending = self.pending, None
            self.storage.event("parameter.failed", reason, "warning", name=pending["name"],
                               requested=pending["value"], session=self.session)
            if not pending["future"].done():
                pending["future"].set_exception(VehicleError(reason))

    def _close(self, reason):
        self._fail_pending(reason)
        if self.link:
            self.link.close()
            self.link = None
        if self.demo:
            self.demo.stop()
            self.demo = None
        self.target = None
        self.last_heartbeat = None
        self.identity = {}
        self.fields = {}
        self.params = {}
        self.param_indices = set()
        self.param_count = 0
        self.param_state = "idle"
        self.session = str(uuid.uuid4())

    def _configure(self, spec):
        kind = spec.get("kind")
        if kind not in ("demo", "serial", "udp"):
            raise VehicleError("Jenis koneksi tidak dikenal.")
        if kind == "serial":
            devices = serial_devices()
            device = next((d for d in devices if d["path"] == spec.get("endpoint")), None)
            if not device:
                raise VehicleError("Pilih perangkat dari daftar port yang terdeteksi.")
            spec["fingerprint"] = {k: device[k] for k in ("serial", "vid", "pid")}
            spec["reconnect"] = device["stable"] and bool(device["serial"])
        if kind == "udp":
            # Listen only; never create an outgoing arbitrary network connection.
            if not re.fullmatch(r"127\.0\.0\.1:[0-9]{4,5}", spec.get("endpoint", "")):
                raise VehicleError("Endpoint UDP harus 127.0.0.1:PORT.")
            port = int(spec["endpoint"].split(":")[1])
            if not 1024 <= port <= 65535:
                raise VehicleError("Port UDP harus antara 1024 dan 65535.")
            spec["reconnect"] = True
        if kind == "demo":
            spec.update(endpoint="internal", reconnect=True)
        self._close("Koneksi diganti; perubahan yang tertunda dibatalkan.")
        self.expected_target = None
        self.spec = spec
        self.status = "connecting"
        self.error = None
        self.next_open = 0
        self.storage.save("connection", spec)
        self.storage.event("connection.request", "Membuka koneksi " + kind, connection=spec)

    def _open(self):
        spec = self.spec
        if spec["kind"] == "serial":
            device = next((d for d in serial_devices() if d["path"] == spec["endpoint"]), None)
            if not device or any(device[k] != v for k, v in spec["fingerprint"].items()):
                raise VehicleError("Perangkat pilihan belum tersedia atau identitasnya berubah.")
            endpoint = spec["endpoint"]
        elif spec["kind"] == "demo":
            endpoint = "udpin:127.0.0.1:0"
        else:
            endpoint = "udpin:" + spec["endpoint"]
        self.link = mavutil.mavlink_connection(endpoint, baud=spec.get("baud", 115200),
                    source_system=250, source_component=191, autoreconnect=False)
        if spec["kind"] == "serial" and hasattr(self.link.port, "exclusive"):
            self.link.port.exclusive = True
        if spec["kind"] == "demo":
            port = self.link.port.getsockname()[1]
            self.demo = DemoVehicle(f"udpout:127.0.0.1:{port}")
            self.demo.start()
        self.opened_at = time.monotonic()
        self.error = None

    def _download(self):
        if self.status != "connected" or not self.target:
            raise VehicleError("Hubungkan autopilot terlebih dahulu.")
        if self.pending:
            raise VehicleError("Tunggu perubahan parameter selesai.")
        self.params = {}
        self.param_indices = set()
        self.param_count = 0
        self.param_state = "loading"
        self.download_started = self.last_param_request = time.monotonic()
        self.retry_index = 0
        self.link.mav.param_request_list_send(*self.target)
        self.storage.event("parameters.read", "Meminta daftar parameter.")

    def _command(self, action, payload, future):
        if action == "connect":
            self._configure(dict(payload["spec"]))
        elif action == "disconnect":
            self._close("Koneksi diputus; perubahan tertunda dibatalkan.")
            self.spec = None
            self.expected_target = None
            self.status = "disconnected"
            self.error = None
            self.storage.event("connection.closed", "Koneksi diputus oleh pengguna.")
        elif action == "download":
            self._download()
        elif action == "write":
            if not self._write_allowed():
                raise VehicleError("Perubahan memerlukan ArduSub teridentifikasi, terhubung, dan disarmed.")
            if payload["session"] != self.session:
                raise VehicleError("Sesi berubah. Muat ulang parameter sebelum mengubahnya.")
            name = payload["name"]
            parameter = self.params.get(name)
            if parameter is None or self.param_state != "complete":
                raise VehicleError("Daftar parameter harus selesai dibaca terlebih dahulu.")
            if self.pending:
                raise VehicleError("Masih ada perubahan parameter yang menunggu respons.")
            if parameter["value"] != payload["expected"]:
                raise VehicleError("Nilai sudah berubah. Muat ulang dan periksa nilai terbaru.")
            value = parameter_value(payload["value"], parameter["type"])
            self.storage.event("parameter.request", "Mengirim perubahan parameter.", name=name,
                               old=parameter["value"], requested=value, session=self.session)
            self.pending = {"name": name, "value": value, "old": parameter["value"],
                            "type": parameter["type"], "future": future,
                            "deadline": time.monotonic()+self.write_timeout}
            self.link.mav.param_set_send(*self.target, name.encode("ascii"), value, parameter["type"])
            return
        else:
            raise VehicleError("Operasi tidak tersedia.")
        if not future.done():
            future.set_result({"ok": True})

    def _receive(self, msg):
        typ = msg.get_type()
        source = (msg.get_srcSystem(), msg.get_srcComponent())
        if typ == "BAD_DATA":
            return
        if typ == "HEARTBEAT" and self.target is None:
            if msg.autopilot == mavutil.mavlink.MAV_AUTOPILOT_INVALID or msg.type == mavutil.mavlink.MAV_TYPE_GCS:
                return
            if self.expected_target is not None and source != self.expected_target:
                return
            self.target = self.expected_target = source
            self.status = "connected"
            self.error = None
            self.identity = {"system_id": source[0], "component_id": source[1],
                             "autopilot": msg.autopilot, "vehicle_type": msg.type, "firmware": None}
            self.storage.event("connection.ready", "Heartbeat autopilot diterima.", target=source,
                               source=self.spec["kind"])
            self.link.mav.command_long_send(*source, mavutil.mavlink.MAV_CMD_REQUEST_MESSAGE, 0,
                                            mavutil.mavlink.MAVLINK_MSG_ID_AUTOPILOT_VERSION, 0, 0, 0, 0, 0, 0)
            self.link.mav.request_data_stream_send(*source, mavutil.mavlink.MAV_DATA_STREAM_ALL, 10, 1)
            self._download()
        if self.target is None or source != self.target:
            return
        self.received += 1
        self.storage.record(msg.to_dict(), {"kind": self.spec["kind"], "system": source[0],
                                           "component": source[1], "session": self.session})
        if typ == "HEARTBEAT":
            self.last_heartbeat = time.monotonic()
            self.identity.update(armed=bool(msg.base_mode & mavutil.mavlink.MAV_MODE_FLAG_SAFETY_ARMED),
                                 mode=mavutil.mode_string_v10(msg), custom_mode=msg.custom_mode)
            if self.identity["armed"]:
                self._fail_pending("Autopilot menjadi armed; hasil perubahan tidak dapat dikonfirmasi.")
        elif typ == "AUTOPILOT_VERSION":
            version = msg.flight_sw_version
            self.identity.update(firmware=f"{version >> 24}.{(version >> 16) & 255}.{(version >> 8) & 255}",
                                 capabilities=msg.capabilities, uid=str(msg.uid))
        elif typ == "ATTITUDE":
            for key in ("roll", "pitch", "yaw"):
                value = math.degrees(getattr(msg, key))
                self._field(key, value % 360 if key == "yaw" else value, "°", typ)
        elif typ == "SYS_STATUS":
            if msg.voltage_battery != 65535:
                self._field("voltage", msg.voltage_battery/1000, "V", typ)
            if msg.current_battery != -1:
                self._field("current", msg.current_battery/100, "A", typ)
            if 0 <= msg.battery_remaining <= 100:
                self._field("battery", msg.battery_remaining, "%", typ)
        elif typ == "SCALED_PRESSURE2":
            self._field("pressure", msg.press_abs, "hPa", typ)
            self._field("water_temperature", msg.temperature/100, "°C", typ)
        elif typ == "VFR_HUD":
            self._field("heading", msg.heading, "°", typ)
            self._field("altitude", msg.alt, "m", typ)
        elif typ == "PARAM_VALUE":
            name = msg.param_id
            if isinstance(name, bytes):
                name = name.decode("ascii", errors="replace")
            name = name.rstrip("\0")
            if not re.fullmatch(r"[A-Z0-9_]{1,16}", name) or not math.isfinite(msg.param_value):
                return
            self.params[name] = {"name": name, "value": msg.param_value, "type": msg.param_type,
                                 "index": msg.param_index, "updated": time.time()}
            if 0 < msg.param_count <= 10000:
                if self.param_state == "complete" and self.param_count != msg.param_count:
                    self.param_state = "incomplete"
                    self.storage.event("parameters.changed", "Jumlah parameter berubah; baca ulang daftar parameter.", "warning")
                self.param_count = msg.param_count
                if 0 <= msg.param_index < self.param_count:
                    self.param_indices.add(msg.param_index)
                if self.param_state == "loading" and len(self.param_indices) == self.param_count:
                    self.param_state = "complete"
                    self.storage.event("parameters.ready", "Daftar parameter selesai dibaca.", count=len(self.params))
            if self.pending and self.pending["name"] == name:
                pending = self.pending
                matches = (msg.param_value == pending["value"] if pending["type"] != 9
                           else math.isclose(msg.param_value, pending["value"], rel_tol=1e-6, abs_tol=1e-8))
                if time.monotonic() > pending["deadline"]:
                    self._fail_pending("Respons terlambat; baca ulang nilai parameter untuk memastikan keadaan perangkat.")
                elif msg.param_type == pending["type"] and matches:
                    self.pending = None
                    self.storage.event("parameter.confirmed", "Nilai parameter dikonfirmasi autopilot.",
                                       name=name, old=pending["old"], value=msg.param_value, session=self.session)
                    if not pending["future"].done():
                        pending["future"].set_result({"ok": True, "name": name, "value": msg.param_value})
                else:
                    self._fail_pending("Autopilot mengembalikan nilai berbeda; perubahan belum terkonfirmasi.")
        elif typ == "STATUSTEXT":
            text = msg.text.decode(errors="replace") if isinstance(msg.text, bytes) else msg.text
            self.storage.event("autopilot.message", text.rstrip("\0")[:500], "warning" if msg.severity <= 4 else "info")

    def _tick(self):
        now = time.monotonic()
        if self.pending and (self.pending["future"].cancelled() or now > self.pending["deadline"]):
            self._fail_pending("Timeout: nilai belum terkonfirmasi. Baca ulang sebelum mencoba lagi.")
        if self.link and now - (self.last_heartbeat or self.opened_at) > self.heartbeat_timeout:
            raise VehicleError("Heartbeat autopilot tidak diterima.")
        if self.param_state == "loading":
            if now - self.download_started > 60:
                self.param_state = "incomplete"
                self.storage.event("parameters.incomplete", "Pembacaan parameter belum lengkap; ulangi pembacaan.", "warning")
            elif now - self.last_param_request > .5:
                if self.param_count:
                    missing = sorted(set(range(self.param_count)) - self.param_indices)
                    if missing:
                        start = self.retry_index % len(missing)
                        batch = (missing[start:] + missing[:start])[:10]
                        for index in batch:
                            self.link.mav.param_request_read_send(*self.target, b"", index)
                        self.retry_index += len(batch)
                else:
                    self.link.mav.param_request_list_send(*self.target)
                self.last_param_request = now

    def _run(self):
        try:
            while not self.stopped.wait(.02):
                with self.lock:
                    # Commands only ever execute on this worker.
                    for _ in range(8):
                        try:
                            action, payload, future = self.commands.get_nowait()
                        except queue.Empty:
                            break
                        if future.cancelled():
                            continue
                        try:
                            self._command(action, payload, future)
                        except Exception as exc:
                            if not future.done():
                                future.set_exception(VehicleError(str(exc)))
                    if not self.spec:
                        continue
                    try:
                        if self.link is None and time.monotonic() >= self.next_open:
                            self._open()
                        if self.link:
                            for _ in range(150):
                                msg = self.link.recv_match(blocking=False)
                                if msg is None:
                                    break
                                self._receive(msg)
                            self._tick()
                    except Exception as exc:
                        reason = str(exc)
                        changed = self.error != reason
                        self._close(reason)
                        self.error = reason
                        self.status = "reconnecting" if self.spec.get("reconnect") else "disconnected"
                        if changed:
                            self.storage.event("connection.lost", reason, "warning")
                        if not self.spec.get("reconnect"):
                            self.spec = None
                        self.next_open = time.monotonic()+2
        finally:
            with self.lock:
                self._close("Layanan dihentikan; perubahan tertunda dibatalkan.")
                self.status = "disconnected"
                while not self.commands.empty():
                    _, _, future = self.commands.get_nowait()
                    if not future.done():
                        future.set_exception(VehicleError("Layanan telah dihentikan."))
