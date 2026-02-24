#!/usr/bin/env bash
set -euo pipefail

# Usage:
#   ./scripts/install-red-service.sh            # defaults to kmsdrm
#   ./scripts/install-red-service.sh offscreen  # fallback path
driver="${1:-kmsdrm}"
if [[ "$driver" != "kmsdrm" && "$driver" != "offscreen" ]]; then
  echo "Usage: $0 [kmsdrm|offscreen]"
  exit 2
fi

app_dir="$(cd "$(dirname "$0")/.." && pwd)"
user_name="$(id -un)"
service_name="gk-taplister-red.service"
service_path="/etc/systemd/system/${service_name}"

sudo tee "$service_path" >/dev/null <<EOF
[Unit]
Description=GK Taplister Red
After=network-online.target
Wants=network-online.target

[Service]
User=${user_name}
WorkingDirectory=${app_dir}
Environment=PYTHONUNBUFFERED=1
Environment=SDL_VIDEODRIVER=${driver}
Environment=SDL_KMSDRM_DEVICE_INDEX=0
Environment=GK_USE_VSYNC=1
ExecStart=/usr/bin/python3 ${app_dir}/red-side.py
Restart=always
RestartSec=2
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable --now "$service_name"
sudo systemctl restart "$service_name"
echo "Installed ${service_name} with SDL_VIDEODRIVER=${driver}"
systemctl status "$service_name" --no-pager --lines=8 || true
