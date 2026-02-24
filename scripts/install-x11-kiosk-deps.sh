#!/usr/bin/env bash
set -euo pipefail

sudo apt update
sudo apt install -y --no-install-recommends \
  xserver-xorg \
  xinit \
  openbox \
  x11-xserver-utils \
  python3-pygame \
  python3-requests \
  librsvg2-bin
