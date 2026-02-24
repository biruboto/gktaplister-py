#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "$0")/.." && pwd)"
runner="${repo_root}/scripts/run-blue-kiosk-x11.sh"

if [[ ! -x "$runner" ]]; then
  echo "Missing executable runner: $runner"
  exit 1
fi

exec startx "$runner" -- :0 vt"$(fgconsole)" -keeptty -nolisten tcp
