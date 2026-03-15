#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SETTINGS_FILE="$ROOT_DIR/settings.py"

if [[ ! -f "$SETTINGS_FILE" ]]; then
  echo "settings.py not found at: $SETTINGS_FILE" >&2
  exit 1
fi

current_base="$(sed -n 's/^SERVER_BASE = "\(.*\)".*/\1/p' "$SETTINGS_FILE")"
current_hostport="${current_base#http://}"
current_hostport="${current_hostport%/}"
current_ip="${current_hostport%%:*}"
current_port="${current_hostport##*:}"

read -r -p "Server IP [$current_ip]: " input_ip
read -r -p "Server port [$current_port]: " input_port

ip="${input_ip:-$current_ip}"
port="${input_port:-$current_port}"

if [[ ! "$ip" =~ ^([0-9]{1,3}\.){3}[0-9]{1,3}$ ]]; then
  echo "Invalid IP address: $ip" >&2
  exit 1
fi

IFS='.' read -r o1 o2 o3 o4 <<< "$ip"
for octet in "$o1" "$o2" "$o3" "$o4"; do
  if (( octet < 0 || octet > 255 )); then
    echo "Invalid IP address: $ip" >&2
    exit 1
  fi
done

if [[ ! "$port" =~ ^[0-9]{1,5}$ ]] || (( port < 1 || port > 65535 )); then
  echo "Invalid port: $port" >&2
  exit 1
fi

new_base="http://$ip:$port/"
escaped_base="${new_base//\//\\/}"

sed -i "s/^SERVER_BASE = \".*\"  # your bar server/SERVER_BASE = \"$escaped_base\"  # your bar server/" "$SETTINGS_FILE"

echo "Updated SERVER_BASE to $new_base"
