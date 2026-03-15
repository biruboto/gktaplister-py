#!/usr/bin/env bash
set -euo pipefail

side="${1:-}"
if [[ "$side" != "red" && "$side" != "blue" ]]; then
  echo "Usage: $0 [red|blue]"
  exit 2
fi

repo_root="$(cd "$(dirname "$0")/.." && pwd)"
cd "$repo_root"

echo "[bootstrap] installing apt dependencies"
sudo apt update
sudo apt install -y --no-install-recommends \
  xserver-xorg \
  xinit \
  openbox \
  x11-xserver-utils \
  python3-pygame \
  python3-requests \
  librsvg2-bin

echo "[bootstrap] enabling ${side} X11 scheduled autostart"
"${repo_root}/scripts/install-${side}-x11-autostart.sh"

echo
echo "[bootstrap] complete"
echo "Next step: sudo reboot"
