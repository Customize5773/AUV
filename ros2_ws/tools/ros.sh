#!/usr/bin/env bash
# Humble requires Python 3.10 on this host; never load the KKI overlay.
set -e
task_ws="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$task_ws"
unset PYTHONHOME PYTHONPATH AMENT_PREFIX_PATH COLCON_PREFIX_PATH CMAKE_PREFIX_PATH
unset LD_LIBRARY_PATH GTK_PATH GTK_EXE_PREFIX GTK_IM_MODULE_FILE GIO_MODULE_DIR
export PYTHONNOUSERSITE=1
source /opt/ros/humble/setup.bash
task_default_python=/usr/bin/python3.10
if [[ -x .venv-ros310/bin/python ]]; then
    task_default_python="$task_ws/.venv-ros310/bin/python"
fi
task_python="${SAUVC_PYTHON:-$task_default_python}"
# ROS executables use /usr/bin/env python3; keep children in this interpreter too.
export PATH="$(dirname "$task_python"):$PATH"
"$task_python" -c 'import sys; assert sys.version_info[:2] == (3, 10), "Humble needs Python 3.10"'
export ROS_DOMAIN_ID="${ROS_DOMAIN_ID:-86}"
# Gazebo also needs isolation from any running KKI simulation.
export IGN_PARTITION="${IGN_PARTITION:-sauvc_practice}"
export ROS_LOG_DIR="$task_ws/log/ros"
mkdir -p "$ROS_LOG_DIR"
if [[ "${1:-}" == build ]]; then
    shift
    "$task_python" tools/build_contact_monitor.py
    exec "$task_python" /usr/bin/colcon --log-base log build \
        --base-paths src --build-base build --install-base install "$@"
fi
if [[ ! -f install/local_setup.bash ]]; then
    echo 'Build first: bash tools/ros.sh build --symlink-install' >&2
    exit 1
fi
source install/local_setup.bash
if [[ "${1:-}" == python ]]; then
    shift
    exec "$task_python" "$@"
fi
exec "$task_python" /opt/ros/humble/bin/ros2 "$@"
