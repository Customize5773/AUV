"""Host metrics, not container metrics; unavailable values remain null."""
import platform
import time
from pathlib import Path

import psutil


def system_snapshot(data_dir):
    memory = psutil.virtual_memory()
    disk = psutil.disk_usage(data_dir)
    sensors = []
    for zone in sorted(Path("/sys/class/thermal").glob("thermal_zone*")):
        try:
            value = int((zone / "temp").read_text().strip()) / 1000
            if -40 <= value <= 150:
                sensors.append({"name": (zone / "type").read_text().strip(), "celsius": value})
        except (OSError, ValueError):
            continue
    model_file = Path("/proc/device-tree/model")
    try:
        model = model_file.read_text().rstrip("\0\n")
    except OSError:
        model = platform.machine()
    return {"model": model, "hostname": platform.node(), "kernel": platform.release(),
            "os": platform.freedesktop_os_release().get("PRETTY_NAME", platform.system()),
            "cpu_percent": psutil.cpu_percent(), "cpu_count": psutil.cpu_count(),
            "memory": {"used": memory.used, "total": memory.total, "percent": memory.percent},
            "disk": {"used": disk.used, "total": disk.total, "percent": disk.percent},
            "temperatures": sensors, "uptime": time.time() - psutil.boot_time(),
            "process_memory": psutil.Process().memory_info().rss, "ts": time.time()}
