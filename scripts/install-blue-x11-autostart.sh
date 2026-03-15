#!/usr/bin/env bash
set -euo pipefail

app_dir="$(cd "$(dirname "$0")/.." && pwd)"
user_name="$(id -un)"
override_dir="/etc/systemd/system/getty@tty1.service.d"
override_file="${override_dir}/autologin.conf"
profile_file="${HOME}/.bash_profile"
launcher="${app_dir}/scripts/start-blue-scheduled-x11.sh"

if [[ ! -x "$launcher" ]]; then
  echo "Missing executable launcher: $launcher"
  exit 1
fi

sudo mkdir -p "$override_dir"
sudo tee "$override_file" >/dev/null <<EOF
[Service]
ExecStart=
ExecStart=-/sbin/agetty --autologin ${user_name} --noclear %I \$TERM
EOF

touch "$profile_file"
if ! grep -Fq "$launcher" "$profile_file"; then
  cat >>"$profile_file" <<EOF

# GK blue kiosk autostart
if [[ -z "\${DISPLAY:-}" && "\$(tty)" == "/dev/tty1" ]]; then
  exec "${launcher}"
fi
EOF
fi

sudo systemctl disable --now gk-blue-kiosk.service 2>/dev/null || true
sudo systemctl disable --now gk-taplister-blue.service 2>/dev/null || true
sudo systemctl daemon-reload
sudo systemctl restart getty@tty1.service

echo "Configured tty1 autologin + blue X11 scheduled kiosk."
echo "Reboot to test, or switch to tty1 and log out."
