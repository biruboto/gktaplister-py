#!/usr/bin/env bash
set -euo pipefail

# Stop any kiosk-related process chain started by start-blue-kiosk.sh
pkill -f "run-blue-kiosk-x11.sh" || true
pkill -f "python3 blue-side.py" || true
pkill -f "startx .*run-blue-kiosk-x11.sh" || true
pkill -f "xinit .*run-blue-kiosk-x11.sh" || true
pkill -f "Xorg :0" || true

echo "Blue kiosk stop requested."
