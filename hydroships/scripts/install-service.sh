#!/usr/bin/env bash
set -euo pipefail
APP_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
test -x "$APP_DIR/.venv/bin/python"
test -f "$APP_DIR/frontend/dist/index.html"
mkdir -p "$HOME/.config/systemd/user"
export APP_DIR
python3 - <<'PY'
import os
from pathlib import Path
app = os.environ['APP_DIR'].replace('%', '%%').replace('"', '\\"')
unit = f'''[Unit]
Description=HydroShips Jetson vehicle console
After=network.target

[Service]
Type=simple
WorkingDirectory={app}
ExecStart=/usr/bin/env -u PYTHONPATH "{app}/.venv/bin/python" -m hydroships
Environment=PYTHONNOUSERSITE=1
Environment=HYDROSHIPS_HOST=127.0.0.1
Environment=HYDROSHIPS_PORT=8081
Environment=HYDROSHIPS_ROS_ENABLED=1
Restart=on-failure
RestartSec=3
TimeoutStopSec=15
UMask=0077
NoNewPrivileges=true

[Install]
WantedBy=default.target
'''
(Path.home()/'.config/systemd/user/hydroships.service').write_text(unit)
PY
systemctl --user daemon-reload
systemctl --user enable --now hydroships.service
systemctl --user --no-pager status hydroships.service
