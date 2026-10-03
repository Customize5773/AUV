#!/bin/bash
set -e
/usr/bin/start-blueos-core
# Match the upstream service lifecycle, while keeping this adapter independent.
tmux new-session -d -s jetson_monitor 'while true; do python3 /opt/jetson/monitor.py; sleep 2; done'
sleep infinity
