#!/usr/bin/env bash
set -euo pipefail

# Usage:
#   ./scripts/set-red-driver.sh kmsdrm
#   ./scripts/set-red-driver.sh offscreen
driver="${1:-}"
if [[ "$driver" != "kmsdrm" && "$driver" != "offscreen" ]]; then
  echo "Usage: $0 [kmsdrm|offscreen]"
  exit 2
fi

service_name="gk-taplister-red.service"
service_path="/etc/systemd/system/${service_name}"

if [[ ! -f "$service_path" ]]; then
  echo "Missing ${service_path}. Run ./scripts/install-red-service.sh first."
  exit 1
fi

sudo sed -i "s/^Environment=SDL_VIDEODRIVER=.*/Environment=SDL_VIDEODRIVER=${driver}/" "$service_path"
sudo systemctl daemon-reload
sudo systemctl restart "$service_name"
echo "Set SDL_VIDEODRIVER=${driver} and restarted ${service_name}"
systemctl status "$service_name" --no-pager --lines=8 || true
