#!/usr/bin/env bash
set -euo pipefail

app_dir="$(cd "$(dirname "$0")/.." && pwd)"
user_name="$(id -un)"
service_name="gk-red-kiosk.service"
service_path="/etc/systemd/system/${service_name}"

sudo systemctl disable --now gk-taplister-red.service 2>/dev/null || true

sudo tee "$service_path" >/dev/null <<EOF
[Unit]
Description=GK Red Kiosk Scheduler
After=network-online.target time-sync.target
Wants=network-online.target time-sync.target

[Service]
User=${user_name}
WorkingDirectory=${app_dir}
Environment=PYTHONUNBUFFERED=1
Environment=SDL_VIDEODRIVER=kmsdrm
Environment=SDL_KMSDRM_DEVICE_INDEX=0
Environment=GK_USE_VSYNC=1
Environment=GK_RENDER_SCALE=1.0
Environment=GK_TARGET_FPS=50
Environment=GK_GAMEOVER_FPS=50
Environment=GK_UI_FULL_BLIT=1
Environment=GK_SHOW_FPS=0
Environment=GK_ALLOW_ESCAPE=0
Environment=GK_OPEN_TIME=11:30
Environment=GK_CLOSE_TIME=23:30
Environment=GK_GAMEOVER_END=00:15
Environment=GK_IDLE_SLEEP_SECONDS=30
Environment=GK_SCHEDULE_LOG_FILE=${app_dir}/logs/red-scheduler.log
ExecStart=/usr/bin/python3 ${app_dir}/kiosk_scheduler.py red
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
echo "Installed ${service_name}"
systemctl status "$service_name" --no-pager --lines=12 || true
