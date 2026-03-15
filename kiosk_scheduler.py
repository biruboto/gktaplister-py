import os
import signal
import subprocess
import sys
import time
from dataclasses import dataclass
from datetime import datetime, time as dt_time
from pathlib import Path


def _env_float(name: str, default: float) -> float:
    raw = os.getenv(name)
    if raw is None:
        return default
    try:
        return float(raw.strip())
    except Exception:
        return default


def _env_str(name: str, default: str) -> str:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip()


def parse_hhmm(value: str) -> dt_time:
    hour_str, minute_str = value.strip().split(":", 1)
    return dt_time(hour=int(hour_str), minute=int(minute_str))


def time_in_window(now: dt_time, start: dt_time, end: dt_time) -> bool:
    if start <= end:
        return start <= now < end
    return now >= start or now < end


def log_line(message: str):
    line = f"[scheduler] {message}"
    print(line, flush=True)
    log_file = os.getenv("GK_SCHEDULE_LOG_FILE", "").strip()
    if not log_file:
        return
    try:
        path = Path(log_file)
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8") as f:
            f.write(line + "\n")
    except Exception:
        pass


@dataclass(frozen=True)
class ScheduleConfig:
    open_time: dt_time
    close_time: dt_time
    gameover_end: dt_time
    idle_sleep_seconds: float


class KioskScheduler:
    def __init__(self, side: str, app_root: Path, config: ScheduleConfig):
        self.side = side
        self.app_root = app_root
        self.config = config
        self.current_mode = None
        self.child = None
        self.running = True
        self.python = sys.executable or "/usr/bin/python3"

    def desired_mode(self, now: dt_time) -> str:
        if time_in_window(now, self.config.open_time, self.config.close_time):
            return "taplist"
        if time_in_window(now, self.config.close_time, self.config.gameover_end):
            return "gameover"
        return "idle"

    def command_for_mode(self, mode: str) -> list[str] | None:
        if mode == "taplist":
            return [self.python, str(self.app_root / f"{self.side}-side.py")]
        if mode == "gameover":
            return [self.python, str(self.app_root / "game-over.py")]
        return None

    def stop_child(self):
        if self.child is None:
            return
        proc = self.child
        self.child = None
        log_line(f"stopping mode={self.current_mode} pid={proc.pid}")
        try:
            proc.terminate()
            proc.wait(timeout=8)
        except subprocess.TimeoutExpired:
            proc.kill()
            proc.wait(timeout=3)
        except Exception as exc:
            log_line(f"stop warning: {exc}")
        self.current_mode = None

    def start_mode(self, mode: str):
        cmd = self.command_for_mode(mode)
        if cmd is None:
            self.current_mode = "idle"
            return
        log_line(f"starting mode={mode} cmd={' '.join(cmd)}")
        self.child = subprocess.Popen(cmd, cwd=str(self.app_root))
        self.current_mode = mode

    def tick(self):
        now = datetime.now().time()
        desired = self.desired_mode(now)

        if self.child is not None:
            return_code = self.child.poll()
            if return_code is not None:
                log_line(f"mode={self.current_mode} exited rc={return_code}")
                self.child = None
                self.current_mode = None

        if desired != self.current_mode:
            self.stop_child()
            self.start_mode(desired)

        if desired == "idle":
            time.sleep(self.config.idle_sleep_seconds)
        else:
            time.sleep(5.0)

    def shutdown(self, *_args):
        self.running = False
        self.stop_child()

    def run(self):
        signal.signal(signal.SIGTERM, self.shutdown)
        signal.signal(signal.SIGINT, self.shutdown)

        log_line(
            f"boot side={self.side} open={self.config.open_time.strftime('%H:%M')} "
            f"close={self.config.close_time.strftime('%H:%M')} "
            f"gameover_end={self.config.gameover_end.strftime('%H:%M')}"
        )

        while self.running:
            self.tick()


def main():
    if len(sys.argv) != 2 or sys.argv[1] not in ("red", "blue"):
        print("Usage: python3 kiosk_scheduler.py [red|blue]", file=sys.stderr)
        raise SystemExit(2)

    side = sys.argv[1]
    app_root = Path(__file__).resolve().parent
    config = ScheduleConfig(
        open_time=parse_hhmm(_env_str("GK_OPEN_TIME", "11:30")),
        close_time=parse_hhmm(_env_str("GK_CLOSE_TIME", "23:30")),
        gameover_end=parse_hhmm(_env_str("GK_GAMEOVER_END", "00:15")),
        idle_sleep_seconds=max(5.0, _env_float("GK_IDLE_SLEEP_SECONDS", 30.0)),
    )
    KioskScheduler(side=side, app_root=app_root, config=config).run()


if __name__ == "__main__":
    main()
