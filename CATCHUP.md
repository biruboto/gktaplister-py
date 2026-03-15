# Taplister Catch-Up

This is the short re-familiarization file for future work on Taplister.

## What This System Is

Taplister is a digital taplist system for a retro arcade bar.

- A local server hosts JSON, logos, editors, and save endpoints.
- Two Raspberry Pi 4 clients display the taplists:
  - `red`
  - `blue`
- The Pis are display clients only. They poll the server and render signage.
- The editors run on the server side and write JSON that the Pis read.

## Current Architecture

### Display Clients

- `red-side.py`
- `blue-side.py`
- Shared runtime in `main.py`
- Shared battlefield/starfield renderer in `systems/battle.py`
- Shared taplist UI rendering in `systems/ui.py`
- `game-over.py` is the after-hours screen

### Editors

- `red-side-editor.html`
- `blue-side-editor.html`
- `beer-db-editor.html`

### Data

- `json/red-beers.json`
- `json/blue-beers.json`
- `json/beer-database.json`

### Logos

- `logos/` contains the available brewery logo library
- The beer DB editor needs the full logo library, even if some logos are not currently assigned

## Deployment / Pi State

See `SETUP_PI.md` for full setup.

Known-good Pi setup:

- Raspberry Pi OS Lite
- Debian 12 `Bookworm`
- Pi 4
- X11 path, not direct `kmsdrm`

We explicitly tried the lower-level direct SDL/KMS path and ran into stack issues. The known-good path is:

- autologin on `tty1`
- start X from `tty1`
- run scheduled kiosk launcher inside X

Relevant scripts:

- `scripts/bootstrap-pi-kiosk.sh`
- `scripts/install-red-x11-autostart.sh`
- `scripts/install-blue-x11-autostart.sh`
- `scripts/run-red-scheduled-x11.sh`
- `scripts/run-blue-scheduled-x11.sh`

## Scheduling

Current desired schedule:

- Taplist starts: `11:30 AM`
- Game over starts: `11:30 PM`
- Idle begins: `12:15 AM`

The kiosk scheduler is:

- `kiosk_scheduler.py`

## Important Operational Note

`tty1` is now an autologin kiosk path.

If local shell access is needed on the Pi:

- switch to `tty2` or another VT with `Ctrl+Alt+F2`
- do admin/setup work there

This matters for network setup and emergency recovery.

## Current UI / Editor State

### Red / Blue Side Editors

- Only show active beers from the beer database
- Layout is intentionally 2-column to match the taplist visually
- Blue side has fewer taps than red by design

### Beer Database Editor

Recent important behavior:

- beers now support an `archived` flag
- `show all beers` is split into:
  - `Active Beers`
  - `Archived Beers`
- rows can be moved between those sections
- tap assignment editors only show non-archived beers

There was a regression during this work:

- the top beer dropdown broke
- root cause was an `await` inside a non-`async` function
- final fix was to keep the top selector as a native `<select>` and avoid unnecessary custom dropdown work

## Rendering / Performance Lessons

This project has been stubbornly heavy on the Pi relative to how visually simple it looks.

### What We Tried

- original HTML/CSS/JS version
- `pygame`
- `pyglet`
- `kivy`

Across multiple approaches, we still saw frustrating smoothness/perf issues, which is why we suspected stack-level causes at several points.

### What We Confirmed

- The current Python display path can sit around one full CPU core on the Pi
- That does **not** mean the whole Pi is maxed out, but it is still heavier than expected
- The taplist UI compositing is more expensive than the battle layer looks
- The animated `TAP LIST` header alone cost about 10 FPS in testing

### Current Performance Conclusions

- The `TAP LIST` header is now static again
- We added an `F` key toggle for FPS display in `main.py`
- Multiple optimization experiments were tried and then intentionally backed out when they did not produce worthwhile gains
- A full internal `1280x720` render experiment did **not** produce a meaningful frame-rate improvement and was reverted

### Aesthetic Change Kept

- Ship exhaust particles in `systems/battle.py` were changed to square/pixel-style particles because the circular/glowy version was not preferred visually

## Why This Still Feels Heavy

Likely reasons:

- software-rendered 2D composition in Python
- 1080p full-screen signage with transparent/text-heavy overlay work
- pygame/X11 path still doing more CPU-side work than intuition suggests

Even when the battle scene looks simple, the signage UI itself is a significant render cost.

## Rewrite Thoughts For Later

If this is ever rewritten for a more final production renderer, the most promising direction is probably:

- a native SDL2 client in `C++` or `Rust`

Why that idea came up:

- simpler stack than browser/Python/UI frameworks
- better control over fullscreen render loop
- better fit for fixed-function signage:
  - logos
  - text
  - simple sprite animation
  - deterministic output

Important nuance:

- this would be a real rewrite, not a quick optimization pass
- but it is probably the cleanest long-term architecture if the goal is "smooth and reliable Pi signage appliance"

## Files To Reopen First Next Time

If resuming work later, start with:

- `SETUP_PI.md`
- `main.py`
- `systems/ui.py`
- `systems/battle.py`
- `kiosk_scheduler.py`
- `scripts/run-red-scheduled-x11.sh`
- `scripts/run-blue-scheduled-x11.sh`
- `beer-db-editor.html`

## Current Mental Model

This project is working and deployable, even if the frame rate never got to the ideal target.

The practical state is:

- editors work
- Pi boot path works
- red/blue scheduled kiosk path works
- game over path works
- network/server settings are manageable
- performance is acceptable enough to operate, but still imperfect

If future work resumes, it should probably be either:

1. leave the current system alone and ship it as-is
2. do a serious renderer rewrite rather than endless micro-optimization
