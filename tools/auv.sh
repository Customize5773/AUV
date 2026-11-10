#!/usr/bin/env bash
# Terminal operations; simulator commands never connect MAVLink hardware.
set -euo pipefail
root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
unit=auv-simulation.service
case "${1:-help}" in
  status)
    systemctl --user show "$unit" -p LoadState -p ActiveState -p SubState -p MainPID
    ;;
  devices)
    ip -brief address
    ls -l /dev/serial/by-id/ /dev/v4l/by-id/ 2>/dev/null || true
    ;;
  sim-start)
    case "${2:-}" in
      qualification) arena=qualification; extended=false ;;
      arena) arena=finals; extended=false ;;
      pinger) arena=finals; extended=true ;;
      *) echo 'Usage: bash tools/auv.sh sim-start qualification|arena|pinger' >&2; exit 2 ;;
    esac
    [[ -f "$root/ros2_ws/install/local_setup.bash" ]] || { echo 'Build ros2_ws first.' >&2; exit 1; }
    command -v ign >/dev/null || { echo "Gazebo Fortress is required; run simulation on the laptop." >&2; exit 1; }
    exec systemd-run --user --unit="$unit" --collect \
      --property=Restart=no --property=KillSignal=SIGINT --property=TimeoutStopSec=30 \
      --working-directory="$root/ros2_ws" \
      /usr/bin/bash "$root/ros2_ws/tools/ros.sh" launch sauvc_sim arena.launch.py \
      edition:=2027 headless:=true autonomous:=true "arena:=$arena" "extended:=$extended"
    ;;
  sim-stop) exec systemctl --user stop "$unit" ;;
  logs) exec journalctl --user -u "$unit" -n 80 -f ;;
  telemetry)
    shift
    exec "$root/.venv-vehicle/bin/python" "$root/tools/telemetry.py" "$@"
    ;;
  camera-check)
    [[ $# == 2 && "$2" == /dev/v4l/by-id/* && -c "$2" ]] || { echo 'Supply one stable /dev/v4l/by-id/ capture device.' >&2; exit 2; }
    exec timeout 20 v4l2-ctl --device="$2" --set-fmt-video=width=640,height=480,pixelformat=MJPG --set-parm=30 --stream-mmap --stream-count=60 --stream-to=/dev/null
    ;;
  help)
    echo 'status | devices | sim-start qualification|arena|pinger | sim-stop | logs'
    echo 'telemetry DEVICE [--seconds 10] | camera-check /dev/v4l/by-id/DEVICE'
    ;;
  *) echo 'Unknown operation; use help.' >&2; exit 2 ;;
esac
