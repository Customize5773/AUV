"""Bounded local storage. This module never connects to an autopilot."""
import json
import math
import sqlite3
import threading
import time
from datetime import datetime, timezone
from pathlib import Path


def clean(value):
    if isinstance(value, float) and not math.isfinite(value):
        return None
    if isinstance(value, (bytes, bytearray)):
        return value.decode("utf-8", errors="replace").rstrip("\0")
    if isinstance(value, dict):
        return {str(k): clean(v) for k, v in value.items()}
    if isinstance(value, (tuple, list)):
        return [clean(v) for v in value]
    return value


class Storage:
    def __init__(self, directory: Path, max_log_bytes=8 * 1024 * 1024, max_logs=8):
        self.directory = directory
        directory.mkdir(parents=True, exist_ok=True, mode=0o700)
        self.logs = directory / "telemetry"
        self.logs.mkdir(exist_ok=True)
        self.lock = threading.RLock()
        self.db = sqlite3.connect(directory / "hydroships.sqlite3", check_same_thread=False)
        self.db.execute("PRAGMA journal_mode=WAL")
        self.db.executescript("""
          CREATE TABLE IF NOT EXISTS settings(key TEXT PRIMARY KEY, value TEXT NOT NULL);
          CREATE TABLE IF NOT EXISTS events(id INTEGER PRIMARY KEY, ts REAL NOT NULL,
            level TEXT NOT NULL, kind TEXT NOT NULL, message TEXT NOT NULL, detail TEXT NOT NULL);
        """)
        self.db.commit()
        self.max_log_bytes = max_log_bytes
        self.max_logs = max_logs
        self.current_log = None
        self.log_size = 0
        self.log_sequence = 0
        self.started = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")

    def setting(self, key, default=None):
        with self.lock:
            row = self.db.execute("SELECT value FROM settings WHERE key=?", (key,)).fetchone()
            return json.loads(row[0]) if row else default

    def save(self, key, value):
        with self.lock, self.db:
            self.db.execute("INSERT OR REPLACE INTO settings VALUES (?,?)", (key, json.dumps(clean(value))))

    def event(self, kind, message, level="info", **detail):
        with self.lock, self.db:
            self.db.execute("INSERT INTO events(ts,level,kind,message,detail) VALUES (?,?,?,?,?)",
                            (time.time(), level, kind, message, json.dumps(clean(detail))))
            self.db.execute("DELETE FROM events WHERE id <= (SELECT MAX(id)-10000 FROM events)")

    def events(self, limit=100, after=0):
        with self.lock:
            rows = self.db.execute("SELECT id,ts,level,kind,message,detail FROM events WHERE id>? ORDER BY id DESC LIMIT ?",
                                   (after, limit)).fetchall()
        return [dict(id=r[0], ts=r[1], level=r[2], kind=r[3], message=r[4], detail=json.loads(r[5])) for r in rows]

    def record(self, message, source):
        record = {"ts": time.time(), "source": source, "message": clean(message)}
        line = (json.dumps(record, allow_nan=False, separators=(",", ":")) + "\n").encode()
        with self.lock:
            if self.current_log is None or self.log_size + len(line) > self.max_log_bytes:
                self.log_sequence += 1
                self.current_log = self.logs / f"telemetry-{self.started}-{self.log_sequence:04d}.jsonl"
                self.log_size = 0
                self.current_log.touch()
                # Keep the active file even if the host clock moved backwards.
                files = sorted(p for p in self.logs.glob("telemetry-*.jsonl") if p != self.current_log)
                for path in files[:max(0, len(files) - (self.max_logs - 1))]:
                    path.unlink(missing_ok=True)
            with self.current_log.open("ab") as stream:
                stream.write(line)
            self.log_size += len(line)

    def log_list(self):
        with self.lock:
            return [dict(name=p.name, bytes=p.stat().st_size, modified=p.stat().st_mtime)
                    for p in sorted(self.logs.glob("telemetry-*.jsonl"), reverse=True)]

    def close(self):
        with self.lock:
            self.db.close()
