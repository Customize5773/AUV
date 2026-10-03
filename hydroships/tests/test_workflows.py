"""Protocol and persistence checks; mock results are not hardware/SITL evidence."""
import json
import tempfile
import time
from contextlib import contextmanager
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from pymavlink import mavutil

from hydroships.app import create_app
from hydroships.storage import Storage
from hydroships.vehicle import Vehicle, VehicleError, parameter_value


def until(predicate, seconds=5):
    end = time.monotonic() + seconds
    while time.monotonic() < end:
        result = predicate()
        if result:
            return result
        time.sleep(.03)
    raise AssertionError("Condition did not become true before deadline")


@contextmanager
def connected_vehicle(**options):
    with tempfile.TemporaryDirectory() as directory:
        storage = Storage(Path(directory))
        vehicle = Vehicle(storage, **options)
        vehicle.start()
        try:
            vehicle.submit("connect", spec={"kind": "demo"}).result(3)
            until(lambda: vehicle.snapshot()["write_allowed"] and vehicle.param_state == "complete")
            yield vehicle, storage
        finally:
            vehicle.stop()
            storage.close()


def write(vehicle, name="PILOT_SPEED_DN", value=42, **overrides):
    args = dict(name=name, value=value, expected=vehicle.params[name]["value"], session=vehicle.session)
    args.update(overrides)
    return vehicle.submit("write", **args)


def test_mavlink_read_write_and_recording():
    with connected_vehicle() as (v, storage):
        assert v.snapshot()["identity"]["mode"] == "MANUAL"
        assert v.snapshot()["fields"]["voltage"]["value"] == 15.8
        result = write(v).result(3)
        assert result["value"] == 42
        assert v.params["PILOT_SPEED_DN"]["value"] == 42
        assert any(e["kind"] == "parameter.confirmed" for e in storage.events())
        logs = storage.log_list()
        assert logs
        record = json.loads((storage.logs / logs[0]["name"]).read_text().splitlines()[0])
        assert record["source"]["kind"] == "demo"


def test_missing_parameter_is_retried_by_index():
    with connected_vehicle() as (v, _):
        v.demo.drop_parameter_index = 2
        v.submit("download").result(2)
        until(lambda: v.param_state == "complete")
        assert len(v.params) == 6
        assert v.params["PILOT_SPEED_UP"]["index"] == 2


def test_rejection_timeout_and_no_automatic_write_retry():
    with connected_vehicle(write_timeout=.4) as (v, _):
        v.demo.reject_writes = True
        with pytest.raises(VehicleError, match="nilai berbeda"):
            write(v).result(3)
        assert len(v.demo.writes) == 1
        v.demo.reject_writes = False
        v.demo.silent_writes = True
        with pytest.raises(VehicleError, match="Timeout"):
            write(v).result(3)
        # The device may have applied it despite the lost response. Never resend.
        assert len(v.demo.writes) == 2
        assert v.demo.params["PILOT_SPEED_DN"][0] == 42
        v.submit("download").result(2)
        until(lambda: v.param_state == "complete")
        assert v.params["PILOT_SPEED_DN"]["value"] == 42


def test_armed_stale_session_and_concurrent_edit_are_rejected():
    with connected_vehicle() as (v, _):
        with pytest.raises(VehicleError, match="Sesi berubah"):
            write(v, session="old-session").result(2)
        with pytest.raises(VehicleError, match="Nilai sudah berubah"):
            write(v, expected=-1).result(2)
        v.demo.armed = True
        until(lambda: v.snapshot()["identity"].get("armed"))
        with pytest.raises(VehicleError, match="disarmed"):
            write(v).result(2)
        assert v.demo.writes == []


def test_disconnect_cancels_pending_and_does_not_replay_on_reconnect():
    with connected_vehicle() as (v, _):
        v.demo.silent_writes = True
        old_session = v.session
        pending = write(v)
        until(lambda: v.pending is not None)
        v.submit("disconnect").result(3)
        with pytest.raises(VehicleError, match="dibatalkan"):
            pending.result(3)
        assert not v.params and not v.fields
        assert v.session != old_session
        v.submit("connect", spec={"kind": "demo"}).result(3)
        until(lambda: v.param_state == "complete")
        assert v.demo.writes == []
        with pytest.raises(VehicleError, match="Sesi berubah"):
            write(v, session=old_session).result(2)


def test_heartbeat_loss_invalidates_session_then_recovers():
    with connected_vehicle(heartbeat_timeout=.8) as (v, _):
        old = v.session
        v.demo.paused.set()
        until(lambda: v.status == "reconnecting")
        assert v.session != old
        assert not v.snapshot()["write_allowed"]
        assert v.parameter_snapshot()["items"] == []
        until(lambda: v.status == "connected" and v.param_state == "complete", seconds=5)
        assert v.demo.writes == []


def test_foreign_system_cannot_overwrite_selected_vehicle():
    with connected_vehicle() as (v, _):
        port = v.link.port.getsockname()[1]
        rogue = mavutil.mavlink_connection(f"udpout:127.0.0.1:{port}", source_system=99, source_component=1)
        try:
            rogue.mav.heartbeat_send(12, 3, 129, 19, 3)
            rogue.mav.param_value_send(b"PILOT_SPEED_DN", 999, 9, 6, 1)
            time.sleep(.15)
            assert v.params["PILOT_SPEED_DN"]["value"] == 50
            assert v.identity["system_id"] == 42
            assert not v.identity["armed"]
        finally:
            rogue.close()


def test_parameter_numeric_boundaries():
    for value, typ in [(float("nan"), 9), (float("inf"), 9), (1e100, 9), (1.5, 6), (256, 1), (16777217, 6), (3, 7), (True, 9)]:
        with pytest.raises(VehicleError):
            parameter_value(value, typ)
    assert parameter_value(255, 1) == 255
    assert parameter_value(-2147483648, 6) == -2147483648


def test_storage_survives_reopen_and_rotates_with_limit():
    with tempfile.TemporaryDirectory() as directory:
        path = Path(directory)
        storage = Storage(path, max_log_bytes=250, max_logs=3)
        storage.save("name", "HydroShips test")
        storage.event("test", "persist")
        for i in range(30):
            storage.record({"value": i, "missing": float("nan")}, "demo")
        assert len(storage.log_list()) == 3
        for log in storage.log_list():
            assert log["bytes"] <= 250
        storage.close()
        storage = Storage(path)
        assert storage.setting("name") == "HydroShips test"
        assert storage.events()[0]["message"] == "persist"
        storage.close()


def test_api_workflow_boundaries_exports_and_restart():
    with tempfile.TemporaryDirectory() as directory:
        app = create_app(directory)
        headers = {"X-Hydroships-Client": "dashboard"}
        with TestClient(app, base_url="http://127.0.0.1:8081") as client:
            assert client.get("/api/health").json()["ok"]
            assert client.post("/api/connection", json={"kind": "demo"}).status_code == 403
            assert client.post("/api/connection", json={"kind": "demo"}, headers={**headers, "Origin": "https://evil.example"}).status_code == 403
            assert client.post("/api/connection", json={"kind": "serial", "endpoint": "/etc/passwd"}, headers=headers).status_code == 409
            assert client.post("/api/connection", json={"kind": "udp", "endpoint": "0.0.0.0:14550"}, headers=headers).status_code == 409
            assert client.post("/api/connection", json={"kind": "demo"}, headers=headers).status_code == 200
            until(lambda: client.get("/api/state").json()["vehicle"]["write_allowed"])
            until(lambda: client.get("/api/parameters").json()["state"] == "complete")
            params = client.get("/api/parameters").json()
            result = client.put("/api/parameters/PILOT_SPEED_DN", json={"session": params["session"], "expected": 50, "value": 35}, headers=headers)
            assert result.status_code == 200, result.text
            export = client.get("/api/parameters/export")
            assert export.status_code == 200 and "PILOT_SPEED_DN\t35\t9" in export.text
            assert client.get("/api/logs/not-a-log").status_code == 404
            filename = client.get("/api/logs").json()["items"][0]["name"]
            assert client.get("/api/logs/"+filename).status_code == 200
            with client.websocket_connect("ws://127.0.0.1:8081/api/live", headers={"Origin": "http://127.0.0.1:8081"}) as ws:
                assert ws.receive_json()["vehicle"]["status"] == "connected"
            assert client.put("/api/settings", json={"name": "Persistence check"}, headers=headers).status_code == 200
        with TestClient(create_app(directory), base_url="http://127.0.0.1:8081") as client:
            assert client.get("/api/settings").json()["name"] == "Persistence check"
            assert client.get("/api/state").json()["vehicle"]["status"] == "disconnected"
            assert client.get("/api/settings").json()["connection"]["kind"] == "demo"
