#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "$0")/.." && pwd)"
cd "$repo_root"

xset -dpms || true
xset s off || true
xset s noblank || true

if command -v unclutter >/dev/null 2>&1; then
  unclutter -idle 0 -root -grab >/dev/null 2>&1 &
fi

output_name="$(xrandr --query | awk '/ connected/{print $1; exit}')"
if [[ -n "$output_name" ]]; then
  set_display_mode() {
    local mode="$1"
    local preferred_rate="$2"
    local rate=""

    if [[ -n "$preferred_rate" ]] && xrandr --query | awk -v out="$output_name" -v mode="$mode" -v rate="$preferred_rate" '
      $1==out && $2=="connected" {in_output=1; next}
      in_output && $1 !~ /^ / {in_output=0}
      in_output && $1==mode {
        for (i=2; i<=NF; i++) {
          r=$i
          gsub(/[^0-9.]/, "", r)
          if (r == rate || r == rate ".00") found=1
        }
      }
      END {exit !found}
    '; then
      if xrandr --output "$output_name" --mode "$mode" --rate "$preferred_rate"; then
        return 0
      fi
    fi

    rate="$(
      xrandr --query | awk -v out="$output_name" -v mode="$mode" '
        $1==out && $2=="connected" {in_output=1; next}
        in_output && $1 !~ /^ / {in_output=0}
        in_output && $1==mode {
          for (i=2; i<=NF; i++) {
            r=$i
            gsub(/[^0-9.]/, "", r)
            if (r+0 > best+0) best=r
          }
        }
        END { if (best != "") print best }
      '
    )"
    if [[ -n "$rate" ]]; then
      xrandr --output "$output_name" --mode "$mode" --rate "$rate"
      return $?
    fi

    return 1
  }

  set_display_mode 1920x1080 50 || set_display_mode 1280x720 60 || true
fi

export GK_ALLOW_ESCAPE=0
export GK_PI_PERF_MODE=1
export GK_LEGACY_PARITY_MODE=0
export GK_RENDER_SCALE=1.0
export GK_TARGET_FPS=50
export GK_GAMEOVER_FPS=50
export GK_USE_VSYNC=1
export GK_ANGLE_STEP_DEFAULT=3
export GK_ANGLE_STEP_BROKEN=1
export GK_UI_FULL_BLIT=1
export GK_SHOW_FPS=0
export GK_OPEN_TIME="${GK_OPEN_TIME:-11:30}"
export GK_CLOSE_TIME="${GK_CLOSE_TIME:-23:30}"
export GK_GAMEOVER_END="${GK_GAMEOVER_END:-00:15}"
export GK_IDLE_SLEEP_SECONDS="${GK_IDLE_SLEEP_SECONDS:-30}"
export GK_SCHEDULE_LOG_FILE="${GK_SCHEDULE_LOG_FILE:-${repo_root}/logs/blue-scheduler.log}"
export PYTHONUNBUFFERED=1

mkdir -p "${repo_root}/logs"
echo "[kiosk] starting blue scheduled X11 runner"

exec python3 kiosk_scheduler.py blue 2>&1 | tee -a "${repo_root}/logs/blue-kiosk.log"
