import asyncio
import contextlib
import fcntl
import os
import re
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Literal

from fastapi import FastAPI, HTTPException, Request, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse, Response
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, ConfigDict, Field
from starlette.middleware.trustedhost import TrustedHostMiddleware

from . import __version__
from .storage import Storage
from .system import system_snapshot
from .vehicle import Vehicle, VehicleError, serial_devices

ROOT = Path(__file__).resolve().parents[2]


class ConnectionRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    kind: Literal["demo", "serial", "udp"]
    endpoint: str = Field(default="", max_length=256)
    baud: Literal[57600, 115200, 230400, 460800, 921600] = 115200


class ParameterRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", allow_inf_nan=False)
    session: str = Field(min_length=1, max_length=64)
    expected: float = Field(strict=True)
    value: float = Field(strict=True)


class SettingsRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    name: str = Field(min_length=1, max_length=60)


def create_app(data_dir=None):
    directory = Path(data_dir or os.environ.get("HYDROSHIPS_DATA_DIR", ROOT / ".data"))

    @asynccontextmanager
    async def lifespan(app):
        directory.mkdir(parents=True, exist_ok=True, mode=0o700)
        with (directory / "runtime.lock").open("w") as lockfile:
            # One application process, including when started outside systemd.
            fcntl.flock(lockfile, fcntl.LOCK_EX | fcntl.LOCK_NB)
            app.state.storage = storage = Storage(directory)
            app.state.vehicle = vehicle = Vehicle(storage)
            app.state.system = system_snapshot(directory)
            vehicle.start()
            storage.event("service.started", "HydroShips dimulai.", version=__version__)

            async def monitor():
                while True:
                    app.state.system = await asyncio.to_thread(system_snapshot, directory)
                    await asyncio.sleep(2)

            task = asyncio.create_task(monitor())
            try:
                yield
            finally:
                task.cancel()
                with contextlib.suppress(asyncio.CancelledError):
                    await task
                await asyncio.to_thread(vehicle.stop)
                storage.event("service.stopped", "HydroShips dihentikan.")
                storage.close()

    app = FastAPI(title="HydroShips", version=__version__, lifespan=lifespan,
                  docs_url=None, redoc_url=None)
    hosts = os.environ.get("HYDROSHIPS_ALLOWED_HOSTS", "127.0.0.1,localhost").split(",")
    app.add_middleware(TrustedHostMiddleware, allowed_hosts=hosts)

    @app.middleware("http")
    async def browser_boundary(request: Request, call_next):
        if request.method not in ("GET", "HEAD", "OPTIONS"):
            origin = request.headers.get("origin")
            if request.headers.get("x-hydroships-client") != "dashboard" or (
                origin and origin.rstrip("/") != str(request.base_url).rstrip("/")
            ):
                return JSONResponse({"detail": "Permintaan harus berasal dari antarmuka HydroShips."}, status_code=403)
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["Referrer-Policy"] = "same-origin"
        response.headers["X-Frame-Options"] = "DENY"
        if request.url.path.startswith("/api/"):
            response.headers["Cache-Control"] = "no-store"
        return response

    async def command(action, **payload):
        future = app.state.vehicle.submit(action, **payload)
        try:
            return await asyncio.wait_for(asyncio.wrap_future(future), timeout=8)
        except VehicleError as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc
        except asyncio.TimeoutError as exc:
            raise HTTPException(status_code=504, detail="Operasi belum terkonfirmasi; periksa koneksi dan baca ulang data.") from exc

    def snapshot():
        return {"version": __version__, "vehicle": app.state.vehicle.snapshot(),
                "system": app.state.system, "name": app.state.storage.setting("name", "HydroShips"),
                "events": app.state.storage.events(8)}

    @app.get("/api/health")
    def health():
        alive = app.state.vehicle.thread.is_alive()
        return JSONResponse({"ok": alive, "version": __version__, "connection": app.state.vehicle.snapshot()["status"]},
                            status_code=200 if alive else 503)

    @app.get("/api/state")
    def state():
        return snapshot()

    @app.get("/api/ports")
    def ports():
        return {"items": serial_devices()}

    @app.get("/api/settings")
    def settings():
        return {"name": app.state.storage.setting("name", "HydroShips"),
                "connection": app.state.storage.setting("connection")}

    @app.put("/api/settings")
    def save_settings(body: SettingsRequest):
        app.state.storage.save("name", body.name)
        return {"name": body.name}

    @app.post("/api/connection")
    async def connect(body: ConnectionRequest):
        return await command("connect", spec=body.model_dump())

    @app.delete("/api/connection")
    async def disconnect():
        return await command("disconnect")

    @app.get("/api/parameters")
    def parameters():
        return app.state.vehicle.parameter_snapshot()

    @app.post("/api/parameters/refresh")
    async def refresh():
        return await command("download")

    @app.get("/api/parameters/export")
    def export():
        with app.state.vehicle.lock:
            data = app.state.vehicle.parameter_snapshot()
            identity = app.state.vehicle.identity
            if data["state"] != "complete":
                raise HTTPException(409, "Tunggu pembacaan parameter lengkap sebelum ekspor.")
            lines = ["# HydroShips parameter snapshot", f"# Session: {data['session']}",
                     "# sysid\tcompid\tname\tvalue\ttype"]
            for p in data["items"]:
                lines.append(f"{identity['system_id']}\t{identity['component_id']}\t{p['name']}\t{p['value']:.9g}\t{p['type']}")
        return Response("\n".join(lines)+"\n", media_type="text/plain",
                        headers={"Content-Disposition": 'attachment; filename="hydroships.params"'})

    @app.put("/api/parameters/{name}")
    async def write_parameter(name: str, body: ParameterRequest):
        if not re.fullmatch(r"[A-Z0-9_]{1,16}", name):
            raise HTTPException(422, "Nama parameter tidak valid.")
        return await command("write", name=name, **body.model_dump())

    @app.get("/api/events")
    def events(limit: int = 100, after: int = 0):
        return {"items": app.state.storage.events(max(1, min(limit, 10000)), max(0, after))}

    @app.get("/api/logs")
    def logs():
        return {"items": app.state.storage.log_list(), "max_bytes": 8*8*1024*1024}

    @app.get("/api/logs/{name}")
    def download_log(name: str):
        if not re.fullmatch(r"telemetry-[A-Za-z0-9-]+\.jsonl", name):
            raise HTTPException(404, "Log tidak ditemukan.")
        with app.state.storage.lock:
            try:
                content = (app.state.storage.logs / name).read_bytes()
            except FileNotFoundError as exc:
                raise HTTPException(404, "Log sudah dirotasi atau tidak ditemukan.") from exc
        return Response(content, media_type="application/x-ndjson",
                        headers={"Content-Disposition": f'attachment; filename="{name}"'})

    @app.websocket("/api/live")
    async def live(ws: WebSocket):
        origin = ws.headers.get("origin", "")
        expected = ("https" if ws.url.scheme == "wss" else "http") + "://" + ws.headers.get("host", "")
        if origin != expected:
            await ws.close(code=1008)
            return
        await ws.accept()
        try:
            while True:
                await ws.send_json(snapshot())
                await asyncio.sleep(.5)
        except (WebSocketDisconnect, OSError, RuntimeError):
            pass

    dist = ROOT / "frontend" / "dist"
    if dist.exists():
        app.mount("/", StaticFiles(directory=dist, html=True), name="frontend")
    else:
        @app.get("/")
        def unbuilt():
            return {"application": "HydroShips", "frontend": "Build frontend before starting the service."}
    return app
