#!/usr/bin/env bash
set -euo pipefail

# Stop any kiosk-related process chain started by start-red-kiosk.sh
pkill -f "run-red-kiosk-x11.sh" || true
pkill -f "python3 red-side.py" || true
pkill -f "startx .*run-red-kiosk-x11.sh" || true
pkill -f "xinit .*run-red-kiosk-x11.sh" || true
pkill -f "Xorg :0" || true

echo "Kiosk stop requested."
