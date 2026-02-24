#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"
SDL_VIDEODRIVER=kmsdrm SDL_KMSDRM_DEVICE_INDEX="${SDL_KMSDRM_DEVICE_INDEX:-0}" python3 redscreen-test.py
