#!/usr/bin/env bash
# Optional native ArduSub build; no firmware is uploaded to a physical board.
set -euo pipefail
SITL_CACHE="${HYDROSHIPS_SITL_CACHE:-$HOME/.cache/hydroships}"
SITL_SOURCE="$SITL_CACHE/ardupilot-sub45"
SITL_PYTHON="$SITL_CACHE/sitl-venv/bin/python"
SITL_COMMIT=abe1721cf52535af6eb2340e5cabed430dac76b5
mkdir -p "$SITL_CACHE"
if [ ! -d "$SITL_SOURCE" ]; then
    git init "$SITL_SOURCE"
    git -C "$SITL_SOURCE" remote add origin https://github.com/ArduPilot/ardupilot.git
    git -C "$SITL_SOURCE" fetch --depth 1 origin "$SITL_COMMIT"
    git -C "$SITL_SOURCE" checkout --detach FETCH_HEAD
fi
if [ "$(git -C "$SITL_SOURCE" rev-parse HEAD)" != "$SITL_COMMIT" ]; then
    echo "Cache source berbeda versi. Gunakan HYDROSHIPS_SITL_CACHE lain." >&2
    exit 1
fi
git -C "$SITL_SOURCE" diff --quiet
git -C "$SITL_SOURCE" submodule update --init --depth 1 modules/waf modules/mavlink \
    modules/DroneCAN/libcanard modules/DroneCAN/dronecan_dsdlc modules/DroneCAN/DSDL
if [ ! -x "$SITL_PYTHON" ]; then python3 -m venv "$SITL_CACHE/sitl-venv"; fi
env -u PYTHONPATH "$SITL_PYTHON" -m pip install empy==3.3.4 future==1.0.0 \
    pexpect==4.9.0 lxml==6.1.3 pymavlink==2.4.50 dronecan==1.0.27
cd "$SITL_SOURCE"
env -u PYTHONPATH "$SITL_PYTHON" waf configure --board sitl --disable-tests
env -u PYTHONPATH "$SITL_PYTHON" waf sub -j4
echo "SITL binary: $SITL_SOURCE/build/sitl/bin/ardusub"
