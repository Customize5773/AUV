#!/bin/bash
# Reproduce the Jetson-only frontend. Run compose up --force-recreate afterwards.
set -euo pipefail
profile_dir=$(cd "$(dirname "$0")" && pwd)
bun_bin=${BUN_BIN:-bun}
if [ "$("$bun_bin" --version)" != "1.3.14" ]; then
    echo 'Requires Bun 1.3.14 (same version as upstream BlueOS Dockerfile).' >&2
    exit 1
fi
build_dir=$(mktemp -d /tmp/blueos-jetson-build.XXXXXX)
echo "Build source retained at: $build_dir"
git clone --depth 1 --branch 1.4.6 https://github.com/bluerobotics/BlueOS.git "$build_dir/source"
test "$(git -C "$build_dir/source" rev-parse HEAD)" = 9b9e1643bc8cd2ca5ed843c0addde3d723475290
git -C "$build_dir/source" -c submodule.core/frontend/src/PX4-parameters.url=https://github.com/patrickelectric/PX4-parameters.git submodule update --init --depth 1 core/frontend/src/PX4-parameters core/frontend/src/components/vue-tour core/frontend/src/libs/MAVLink2Rest/mavlink2rest-ts
# Use the parameter data shipped with the exact base image, including its compression.
image=bluerobotics/blueos-core:1.4.6@sha256:729e10290212c4ec5b3d2978afac8fe6973d8b5e4a45dd26d73ba7d5fe8567a3
asset_container=$(docker create "$image")
trap 'docker rm "$asset_container" >/dev/null' EXIT
docker cp "$asset_container:/home/pi/frontend/assets/ArduPilot-Parameter-Repository/." "$build_dir/source/core/frontend/public/assets/ArduPilot-Parameter-Repository/"
python3 - "$build_dir/source/core/frontend/public/assets/ArduPilot-Parameter-Repository" <<'PY'
import gzip,sys
from pathlib import Path
for path in Path(sys.argv[1]).rglob('*.json.gz'):
    path.with_suffix('').write_bytes(gzip.decompress(path.read_bytes()))
PY
git -C "$build_dir/source" apply --check "$profile_dir/frontend.patch"
git -C "$build_dir/source" apply "$profile_dir/frontend.patch"
cd "$build_dir/source/core/frontend"
"$bun_bin" install --frozen-lockfile
VITE_APP_GIT_DESCRIBE=jetson-bench/1.4.6-0-g9b9e1643 NODE_OPTIONS=--max-old-space-size=6144 "$bun_bin" --bun run build
if [ -e "$profile_dir/frontend-dist" ]; then
    mv "$profile_dir/frontend-dist" "$build_dir/frontend-dist.previous"
fi
cp -a dist "$profile_dir/frontend-dist"
echo 'Frontend built. Recreate the container to activate this directory.'
