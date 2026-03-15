#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "$0")/.." && pwd)"
cd "$repo_root"

# Keep the display awake while X is active. When the scheduler is idle,
# X remains up and the root window stays black instead of dropping to tty.
xset -dpms || true
xset s off || true
xset s noblank || true

if command -v unclutter >/dev/null 2>&1; then
  unclutter -idle 0 -root -grab >/dev/null 2>&1 &
fi

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
      xrandr --output "$output_name" --mode 1920x1080 --rate "$best_rate" || true
    fi
  fi
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
export GK_SCHEDULE_LOG_FILE="${GK_SCHEDULE_LOG_FILE:-${repo_root}/logs/red-scheduler.log}"
export PYTHONUNBUFFERED=1

mkdir -p "${repo_root}/logs"
echo "[kiosk] starting red scheduled X11 runner"

exec python3 kiosk_scheduler.py red 2>&1 | tee -a "${repo_root}/logs/red-kiosk.log"
