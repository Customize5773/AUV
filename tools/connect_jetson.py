#!/usr/bin/env python3
"""Laptop: activate AUV-Link, wait for SSH, then open the remote project."""
import shutil
import subprocess
import sys
import time


def run(*args):
    return subprocess.run(args, text=True, capture_output=True, timeout=25)


def connect():
    for command in ("nmcli", "ssh", "code"):
        if not shutil.which(command):
            raise RuntimeError(f"Perintah {command} belum tersedia di laptop.")
    active = run("nmcli", "-g", "GENERAL.CONNECTION", "device", "show", "wlp0s20f3")
    if active.returncode:
        raise RuntimeError(active.stderr.strip())
    if active.stdout.strip() != "AUV-Link":
        print("Mengaktifkan AUV-Link. Wi-Fi internet laptop akan terputus.", flush=True)
        result = run("nmcli", "--wait", "20", "connection", "up", "AUV-Link")
        if result.returncode:
            raise RuntimeError(result.stderr.strip())
    print("Menunggu SSH Jetson (maksimal sekitar 2 menit)...", flush=True)
    deadline = time.monotonic() + 120
    error = "Jetson belum merespons."
    while time.monotonic() < deadline:
        result = run(
            "ssh", "-o", "BatchMode=yes", "-o", "StrictHostKeyChecking=yes",
            "-o", "ConnectTimeout=5", "-o", "ConnectionAttempts=1",
            "-o", "HostName=10.42.77.2", "auv-wifi",
            "test -d /home/aero/AUV || exit 42",
        )
        if result.returncode == 0:
            print("SSH dan folder siap. Membuka VS Code.", flush=True)
            result = run("code", "--new-window", "--remote",
                         "ssh-remote+auv-wifi", "/home/aero/AUV")
            if result.returncode:
                raise RuntimeError(result.stderr.strip())
            return
        if result.returncode == 42:
            raise RuntimeError("SSH berhasil, tetapi folder /home/aero/AUV tidak tersedia.")
        error = result.stderr.strip()
        if "Permission denied" in error or "Host key verification failed" in error:
            raise RuntimeError(error)
        time.sleep(3)
    raise RuntimeError(
        f"{error}\nPastikan Jetson menyala dan profil boot sudah diterapkan. "
        "Gunakan Ethernet untuk diagnosis; jangan pindah Wi-Fi selama akses."
    )


def main():
    try:
        connect()
        return 0
    except (RuntimeError, OSError, subprocess.TimeoutExpired) as error:
        print(f"Gagal: {error}", file=sys.stderr)
        if sys.stdin.isatty():
            input("Tekan Enter untuk menutup...")
        return 1


if __name__ == "__main__":
    sys.exit(main())
