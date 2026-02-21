import json
import math
import random
import threading
import time
from pathlib import Path

import pygame

from battlefield_js_port import ArcadeBattlefield
from settings import SERVER_BASE
from systems.fetch import fetch_text, is_url
from systems.logos import build_logo_cache
from systems.ui import draw_taplist_overlay, draw_taplist_static

BEERDB_FILE = "json/beer-database.json"
TARGET_FPS = 60
TOKEN_POLL_SECONDS = 0.75
BATTLEFIELD_RENDER_SCALE = 0.75
PERF_LOG_FILE = "perf.log"
USE_VSYNC = False
UI_COLORKEY = (1, 0, 1)
UI_USE_COLORKEY_CACHE = True
UI_FONT_PATH = "fonts/EightBit Atari-Fat3.ttf"
UI_OPAQUE_PANELS = False
UI_FULL_BLIT = True


def urlify(path_or_url: str) -> str:
    if is_url(path_or_url):
        return path_or_url
    return f"{SERVER_BASE.rstrip('/')}/{path_or_url.lstrip('./').lstrip('/')}"


def load_json(src: str, ttl: int = 15, timeout_s: float = 10):
    if is_url(src):
        local_path = fetch_text(src, ttl=ttl, timeout_s=timeout_s)
        return json.loads(Path(local_path).read_text(encoding="utf-8"))

    # For relative paths, prefer the server source of truth, then fall back to local file.
    try:
        local_path = fetch_text(urlify(src), ttl=ttl, timeout_s=timeout_s)
        return json.loads(Path(local_path).read_text(encoding="utf-8"))
    except Exception:
        local = Path(src)
        if local.exists():
            return json.loads(local.read_text(encoding="utf-8"))
        raise


def merge_taplist_with_db(taplist: dict, beerdb: list[dict]) -> list[dict]:
    db_by_id = {b["id"]: b for b in beerdb}
    out = []
    for slot in taplist.get("beers", []):
        beer = db_by_id.get(slot.get("id"))
        if not beer:
            continue
        entry = beer.copy()
        entry["soldOut"] = slot.get("soldOut", False)
        out.append(entry)
    return out


def force_spawn_mode(arcade_field: ArcadeBattlefield, mode: str):
    battle = arcade_field.battle
    if mode not in ("normal", "broken", "combat"):
        return

    battle.ship["active"] = True
    battle.ship["mode"] = mode
    battle.ship["scale"] = float(random.randint(1, 4))
    if mode == "combat":
        battle.alien.update(
            {"active": True, "scale": int(battle.ship["scale"]), "frame": 0, "ticker": 0.0}
        )
    else:
        battle.alien.update({"active": False, "x": -9999, "y": -9999, "frame": 0})

    margin = 100
    edge = random.randint(0, 3)
    if edge == 0:
        sx, sy = random.random() * battle.w, -margin
    elif edge == 1:
        sx, sy = battle.w + margin, random.random() * battle.h
    elif edge == 2:
        sx, sy = random.random() * battle.w, battle.h + margin
    else:
        sx, sy = -margin, random.random() * battle.h
    battle.ship["x"], battle.ship["y"] = sx, sy

    cx, cy = battle.w / 2, battle.h / 2
    spread = min(battle.w, battle.h) * 0.25
    tx = cx + (random.random() - 0.5) * spread
    ty = cy + (random.random() - 0.5) * spread
    w = battle.ship_w * battle.ship["scale"]
    h = battle.ship_h * battle.ship["scale"]
    dx = tx - (battle.ship["x"] + w / 2)
    dy = ty - (battle.ship["y"] + h / 2)
    dist = math.hypot(dx, dy) or 1.0
    if mode == "broken":
        base_speed = (0.8 + random.random() * 0.8) * 60.0
    else:
        base_speed = (2 + random.random() * 6) * 60.0

    battle.ship["vx"] = dx / dist * base_speed
    battle.ship["vy"] = dy / dist * base_speed
    battle.ship["angle"] = math.degrees(math.atan2(battle.ship["vy"], battle.ship["vx"]))
    battle.ship["timer"] = 0.0


def run(theme):
    pygame.init()
    pygame.mouse.set_visible(False)
    pygame.event.set_blocked(
        [pygame.MOUSEMOTION, pygame.MOUSEBUTTONDOWN, pygame.MOUSEBUTTONUP]
    )

    display_flags = pygame.FULLSCREEN | pygame.DOUBLEBUF
    if USE_VSYNC:
        screen = pygame.display.set_mode((0, 0), display_flags, vsync=1)
    else:
        screen = pygame.display.set_mode((0, 0), display_flags)
    width, height = screen.get_size()
    clock = pygame.time.Clock()

    taplist = load_json(theme.json_path, ttl=0)
    beerdb = load_json(BEERDB_FILE, ttl=0)
    beers = merge_taplist_with_db(taplist, beerdb)
    current_refresh_token = taplist.get("refreshToken")

    logo_cache = build_logo_cache(beers, theme.logo_size, theme)
    battle_w = max(640, int(width * BATTLEFIELD_RENDER_SCALE))
    battle_h = max(360, int(height * BATTLEFIELD_RENDER_SCALE))
    battlefield = ArcadeBattlefield(battle_w, battle_h, bg_color=theme.bg_color)
    battlefield_surface = pygame.Surface((battle_w, battle_h)).convert()
    debug_font = pygame.font.SysFont(None, 24)

    if UI_USE_COLORKEY_CACHE:
        ui_static = pygame.Surface((width, height)).convert()
        ui_static.set_colorkey(UI_COLORKEY, pygame.RLEACCEL)
    else:
        ui_static = pygame.Surface((width, height), pygame.SRCALPHA).convert_alpha()
    ui_dirty = True
    ui_rects = []
    draw_starfield = True
    draw_battle = True
    draw_ui = True
    perf_logging = True

    perf_acc = {
        "update_ms": 0.0,
        "draw_ms": 0.0,
        "scale_ms": 0.0,
        "ui_ms": 0.0,
        "flip_ms": 0.0,
        "frame_ms": 0.0,
        "frames": 0,
    }
    last_perf_report = time.perf_counter()

    # Start a fresh perf log per run.
    try:
        Path(PERF_LOG_FILE).write_text("", encoding="utf-8")
    except Exception:
        pass

    def log_debug(line: str):
        print(line)
        try:
            with Path(PERF_LOG_FILE).open("a", encoding="utf-8") as f:
                f.write(line + "\n")
        except Exception:
            pass

    log_debug(f"[debug] vsync={USE_VSYNC} target_fps={TARGET_FPS}")

    poll_lock = threading.Lock()
    stop_poll = threading.Event()
    poll_state = {"pending": None}

    def poll_worker():
        last_seen_token = current_refresh_token
        while not stop_poll.wait(TOKEN_POLL_SECONDS):
            try:
                latest_taplist = load_json(theme.json_path, ttl=0, timeout_s=0.5)
                latest_token = latest_taplist.get("refreshToken")
                if latest_token == last_seen_token:
                    continue
                latest_beerdb = load_json(BEERDB_FILE, ttl=0, timeout_s=0.8)
                merged = merge_taplist_with_db(latest_taplist, latest_beerdb)
                with poll_lock:
                    poll_state["pending"] = (latest_token, merged)
                last_seen_token = latest_token
            except Exception:
                # Keep rendering smooth even if network polling fails intermittently.
                pass

    poll_thread = threading.Thread(target=poll_worker, daemon=True)
    poll_thread.start()

    running = True
    while running:
        dt = clock.tick(TARGET_FPS if TARGET_FPS > 0 else 0) / 1000.0
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                elif event.key == pygame.K_c:
                    force_spawn_mode(battlefield, "combat")
                elif event.key == pygame.K_b:
                    force_spawn_mode(battlefield, "broken")
                elif event.key == pygame.K_n:
                    force_spawn_mode(battlefield, "normal")
                elif event.key == pygame.K_F1:
                    draw_starfield = not draw_starfield
                    log_debug(f"[debug] draw_starfield={draw_starfield}")
                elif event.key == pygame.K_F2:
                    draw_battle = not draw_battle
                    log_debug(f"[debug] draw_battle={draw_battle}")
                elif event.key == pygame.K_F3:
                    draw_ui = not draw_ui
                    log_debug(f"[debug] draw_ui={draw_ui}")
                elif event.key == pygame.K_F12:
                    perf_logging = not perf_logging
                    log_debug(f"[debug] perf_logging={perf_logging}")

        pending = None
        with poll_lock:
            if poll_state["pending"] is not None:
                pending = poll_state["pending"]
                poll_state["pending"] = None
        if pending:
            current_refresh_token, beers = pending
            logo_cache = build_logo_cache(beers, theme.logo_size, theme)
            ui_dirty = True

        frame_t0 = time.perf_counter()
        t0 = frame_t0
        battlefield.update(dt)
        t1 = time.perf_counter()

        if ui_dirty:
            if UI_USE_COLORKEY_CACHE:
                ui_static.fill(UI_COLORKEY)
            else:
                ui_static.fill((0, 0, 0, 0))
            ui_rects = draw_taplist_static(
                ui_static,
                beers,
                logo_cache,
                theme,
                width,
                height,
                beer_font_path=UI_FONT_PATH,
                info_font_path=UI_FONT_PATH,
                header_font_path=UI_FONT_PATH,
                draw_panels=UI_OPAQUE_PANELS,
                panel_color=tuple(max(0, c - 18) for c in theme.bg_color),
                panel_border=tuple(min(255, int(c * 0.55) + 30) for c in theme.accent),
            )
            ui_dirty = False

        battlefield.draw(
            battlefield_surface,
            draw_starfield=draw_starfield,
            draw_battle=draw_battle,
        )
        t2 = time.perf_counter()
        if battle_w == width and battle_h == height:
            screen.blit(battlefield_surface, (0, 0))
        else:
            pygame.transform.scale(battlefield_surface, (width, height), screen)
        t3 = time.perf_counter()
        if draw_ui:
            if UI_USE_COLORKEY_CACHE and UI_FULL_BLIT:
                screen.blit(ui_static, (0, 0))
            else:
                for rect in ui_rects:
                    screen.blit(ui_static, rect.topleft, rect)
            draw_taplist_overlay(screen)

        fps_text = debug_font.render(f"{clock.get_fps():.1f} FPS", True, (120, 255, 120))
        screen.blit(fps_text, (10, 8))
        t4 = time.perf_counter()
        pygame.display.flip()
        t5 = time.perf_counter()

        perf_acc["update_ms"] += (t1 - t0) * 1000.0
        perf_acc["draw_ms"] += (t2 - t1) * 1000.0
        perf_acc["scale_ms"] += (t3 - t2) * 1000.0
        perf_acc["ui_ms"] += (t4 - t3) * 1000.0
        perf_acc["flip_ms"] += (t5 - t4) * 1000.0
        perf_acc["frame_ms"] += (t5 - frame_t0) * 1000.0
        perf_acc["frames"] += 1

        now = time.perf_counter()
        if perf_logging and (now - last_perf_report) >= 2.0 and perf_acc["frames"] > 0:
            n = perf_acc["frames"]
            log_debug(
                "[perf] "
                f"fps={clock.get_fps():.1f} "
                f"frame={perf_acc['frame_ms']/n:.2f}ms "
                f"update={perf_acc['update_ms']/n:.2f}ms "
                f"draw={perf_acc['draw_ms']/n:.2f}ms "
                f"scale={perf_acc['scale_ms']/n:.2f}ms "
                f"ui={perf_acc['ui_ms']/n:.2f}ms "
                f"flip={perf_acc['flip_ms']/n:.2f}ms"
            )
            for k in perf_acc:
                perf_acc[k] = 0.0 if k != "frames" else 0
            last_perf_report = now

    stop_poll.set()
    pygame.quit()
