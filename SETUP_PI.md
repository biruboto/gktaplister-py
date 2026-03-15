# Raspberry Pi Setup

This file is the human-readable deployment checklist for a fresh Taplister Pi.

## Target OS

- Raspberry Pi OS Lite
- Debian 12 "Bookworm"
- 64-bit recommended

`Trixie` caused SDL/libudev issues in this project, so `Bookworm` is the known-good target.

## Device Assumptions

- Raspberry Pi 4
- 1080p display
- Raspberry Pi stays powered on full-time
- Taplister repo lives at `~/gktaplister-py`
- The Pi can reach the bar server over the local network

## What The Pi Should Do

- Boot automatically into the kiosk without manual login/commands
- Run the taplist during open hours
- Run the `game-over.py` screen after close
- Sit idle overnight without rendering the taplist 24/7

## Current Known-Good Display Path

- X11 path
- Not direct `kmsdrm` systemd rendering

The direct SDL/KMS service path was unreliable on this hardware/software stack. The X11 kiosk path is the known-good route.

## Required Packages

Installed by `scripts/bootstrap-pi-kiosk.sh`:

- `xserver-xorg`
- `xinit`
- `openbox`
- `x11-xserver-utils`
- `python3-pygame`
- `python3-requests`
- `librsvg2-bin`

## One-Time Setup On A Fresh Pi

1. Install Raspberry Pi OS Lite Bookworm.
2. Copy this repo to:
   - `~/gktaplister-py`
3. Run:

```bash
cd ~/gktaplister-py
./scripts/bootstrap-pi-kiosk.sh red
```

Use `blue` instead of `red` on the blue-side Pi.

4. Reboot:

```bash
sudo reboot
```

## What The Bootstrap Script Configures

- Installs system packages
- Enables autologin on `tty1`
- Starts X automatically from `tty1`
- Launches the side-specific scheduled kiosk runner
- Disables older direct-display services so they do not compete

## Schedule Defaults

Current defaults in the X11 scheduled runner:

- Open: `11:30`
- Close: `23:30`
- Game over ends: `00:15`

These are currently supplied through environment variables in:

- `scripts/run-red-scheduled-x11.sh`
- `scripts/run-blue-scheduled-x11.sh`

## Relevant Scripts

- `scripts/bootstrap-pi-kiosk.sh`
- `scripts/install-red-x11-autostart.sh`
- `scripts/install-blue-x11-autostart.sh`
- `scripts/start-red-scheduled-x11.sh`
- `scripts/start-blue-scheduled-x11.sh`
- `scripts/run-red-scheduled-x11.sh`
- `scripts/run-blue-scheduled-x11.sh`

## Notes

- The taplist uses HTTP polling against the bar server.
- Polling is lightweight now: metadata check first, full JSON fetch only when content changes.
- If the Pi is in the overnight idle window, seeing no taplist is expected behavior.
- Quiet boot can be enabled separately through `/boot/firmware/cmdline.txt`.
