#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF'
Usage:
  bash scripts/set-kiosk-schedule.sh
  bash scripts/set-kiosk-schedule.sh [red|blue|both] OPEN_TIME CLOSE_TIME GAMEOVER_END

Times must be 24-hour HH:MM values.

Examples:
  bash scripts/set-kiosk-schedule.sh
  bash scripts/set-kiosk-schedule.sh blue 11:30 23:30 00:15
  bash scripts/set-kiosk-schedule.sh both 12:00 00:00 00:30
EOF
}

supports_color() {
  [[ -t 1 ]] && command -v tput >/dev/null 2>&1
}

if supports_color; then
  faint="$(tput dim 2>/dev/null || true)"
  normal="$(tput sgr0 2>/dev/null || true)"
else
  faint=""
  normal=""
fi

validate_hhmm() {
  local label="$1"
  local value="$2"

  if [[ ! "$value" =~ ^[0-9]{2}:[0-9]{2}$ ]]; then
    echo "Invalid ${label}: ${value} (expected HH:MM)" >&2
    return 1
  fi

  local hour="${value%%:*}"
  local minute="${value##*:}"
  if (( 10#$hour > 23 || 10#$minute > 59 )); then
    echo "Invalid ${label}: ${value} (expected 00:00 through 23:59)" >&2
    return 1
  fi
}

prompt_time() {
  local label="$1"
  local prompt="$2"
  local value

  while true; do
    echo >&2
    echo "$prompt" >&2
    echo "${faint}Format: 00:00, 24 hour time${normal}" >&2
    printf "> " >&2
    read -r value
    if validate_hhmm "$label" "$value"; then
      printf '%s\n' "$value"
      return 0
    fi
  done
}

run_interactive() {
  local choice confirm

  echo "GK Taplister schedule setup"
  echo
  echo "Which side do you want to set?"
  echo "  1) Red side"
  echo "  2) Blue side"
  echo "  3) Both sides"

  while true; do
    read -r -p "> " choice
    case "$choice" in
      1|red|Red|RED)
        side="red"
        break
        ;;
      2|blue|Blue|BLUE)
        side="blue"
        break
        ;;
      3|both|Both|BOTH)
        side="both"
        break
        ;;
      *)
        echo "Please enter 1, 2, 3, red, blue, or both."
        ;;
    esac
  done

  open_time="$(prompt_time "taplist turn-on time" "When should the tap list turn on?")"
  close_time="$(prompt_time "game-over display time" "When should the Game Over screen be displayed?")"
  gameover_end="$(prompt_time "sleep time" "When should the system go to sleep?")"

  echo
  echo "Ready to update:"
  echo "  Side: ${side}"
  echo "  Tap list on: ${open_time}"
  echo "  Game Over: ${close_time}"
  echo "  Sleep: ${gameover_end}"
  echo
  read -r -p "Save this schedule? [y/N] " confirm
  case "$confirm" in
    y|Y|yes|YES|Yes) ;;
    *)
      echo "Canceled. No schedule changes were made."
      exit 0
      ;;
  esac
}

if [[ "${1:-}" == "-h" || "${1:-}" == "--help" ]]; then
  usage
  exit 0
fi

if [[ $# -eq 0 ]]; then
  run_interactive
elif [[ $# -ne 4 ]]; then
  usage >&2
  exit 2
else
  side="$1"
  open_time="$2"
  close_time="$3"
  gameover_end="$4"
fi

case "$side" in
  red|blue|both) ;;
  *)
    echo "Invalid side: $side" >&2
    usage >&2
    exit 2
    ;;
esac

validate_hhmm "open time" "$open_time"
validate_hhmm "close time" "$close_time"
validate_hhmm "game-over end time" "$gameover_end"

repo_root="$(cd "$(dirname "$0")/.." && pwd)"

python_bin="${PYTHON_BIN:-}"
if [[ -z "$python_bin" ]]; then
  for candidate in python3 python py; do
    if command -v "$candidate" >/dev/null 2>&1 && "$candidate" -c 'import sys' >/dev/null 2>&1; then
      python_bin="$candidate"
      break
    fi
  done
fi

if [[ -z "$python_bin" ]]; then
  echo "Could not find a working Python interpreter. Set PYTHON_BIN=/path/to/python and retry." >&2
  exit 1
fi

runner_paths=()
if [[ "$side" == "red" || "$side" == "both" ]]; then
  runner_paths+=("${repo_root}/scripts/run-red-scheduled-x11.sh")
fi
if [[ "$side" == "blue" || "$side" == "both" ]]; then
  runner_paths+=("${repo_root}/scripts/run-blue-scheduled-x11.sh")
fi

for runner in "${runner_paths[@]}"; do
  if [[ ! -f "$runner" ]]; then
    echo "Missing runner: $runner" >&2
    exit 1
  fi

  "$python_bin" - "$runner" "$open_time" "$close_time" "$gameover_end" <<'PY'
import re
import sys
from pathlib import Path

path = Path(sys.argv[1])
values = {
    "GK_OPEN_TIME": sys.argv[2],
    "GK_CLOSE_TIME": sys.argv[3],
    "GK_GAMEOVER_END": sys.argv[4],
}

text = path.read_text(encoding="utf-8")
missing = []

for name, value in values.items():
    pattern = rf'export {name}="\$\{{{name}:-[^}}]*\}}"'
    replacement = f'export {name}="${{{name}:-{value}}}"'
    text, count = re.subn(pattern, replacement, text)
    if count != 1:
        missing.append(name)

if missing:
    joined = ", ".join(missing)
    raise SystemExit(f"{path}: could not update expected schedule line(s): {joined}")

path.write_text(text, encoding="utf-8")
PY

  echo "Updated ${runner}"
done

echo "Schedule defaults set: open=${open_time} close=${close_time} gameover_end=${gameover_end}"
echo "Restart the kiosk or reboot the Pi for the new defaults to take effect."
