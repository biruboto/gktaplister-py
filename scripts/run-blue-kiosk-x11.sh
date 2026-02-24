#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "$0")/.." && pwd)"
cd "$repo_root"

# Keep the display awake and blanking disabled for kiosk behavior.
xset -dpms || true
xset s off || true
xset s noblank || true

# Force the first connected display to 1080p50 when available.
output_name="$(xrandr --query | awk '/ connected/{print $1; exit}')"
if [[ -n "$output_name" ]]; then
  forced_rate=""
  if xrandr --query | awk -v out="$output_name" '
    $1==out && $2=="connected" {in_output=1; next}
    in_output && $1 !~ /^ / {in_output=0}
    in_output && $1=="1920x1080" && $0 ~ /(^|[[:space:]])50(\.00)?([*+ ]|$)/ {found=1}
    END {exit !found}
  '; then
    if xrandr --output "$output_name" --mode 1920x1080 --rate 50; then
      forced_rate="50"
    fi
  fi

  if [[ -z "$forced_rate" ]]; then
    best_rate="$(
      xrandr --query | awk -v out="$output_name" '
        $1==out && $2=="connected" {in_output=1; next}
        in_output && $1 !~ /^ / {in_output=0}
        in_output && $1=="1920x1080" {
          for (i=2; i<=NF; i++) {
            r=$i
            gsub(/[^0-9.]/, "", r)
            if (r+0 > best+0) best=r
          }
        }
        END { if (best != "") print best }
      '
    )"
    if [[ -n "$best_rate" ]]; then
      if ! xrandr --output "$output_name" --mode 1920x1080 --rate "$best_rate"; then
        echo "[kiosk] failed to force 1920x1080@${best_rate}"
      fi
    else
      echo "[kiosk] no 1920x1080 mode found for ${output_name}"
    fi
  fi
fi

active_rate=""
if [[ -n "$output_name" ]]; then
  active_rate="$(
    xrandr --current | awk -v out="$output_name" '
      $1==out && $2=="connected" {in_output=1; next}
      in_output && $1 !~ /^ / {in_output=0}
      in_output && /\*/ {
        for (i=1; i<=NF; i++) {
          if ($i ~ /\*/) {
            gsub("\\*", "", $i)
            print $i
            exit
          }
        }
      }
    '
  )"
fi
echo "[kiosk] output=${output_name:-unknown} refresh=${active_rate:-unknown}Hz"

# Kiosk defaults: avoid accidental shell drop and match observed 50Hz scanout.
export GK_ALLOW_ESCAPE=0
export GK_PI_PERF_MODE=1
export GK_LEGACY_PARITY_MODE=0
export GK_RENDER_SCALE=1.0
export GK_TARGET_FPS=50
export GK_USE_VSYNC=1
export GK_ANGLE_STEP_DEFAULT=3
export GK_ANGLE_STEP_BROKEN=1
export GK_UI_FULL_BLIT=1
export GK_SHOW_FPS=0
export PYTHONUNBUFFERED=1

log_file="${repo_root}/logs/blue-kiosk.log"
mkdir -p "$(dirname "$log_file")"
echo "[kiosk] logging app output to ${log_file}"

while true; do
  python3 blue-side.py 2>&1 | tee -a "$log_file"
  sleep 1
done
