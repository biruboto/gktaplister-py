import pygame
import json
import os
import sys
import math
import subprocess
import shutil
from collections import defaultdict

# ======== CONFIG ==========
# Keep global defaults as a fallback; theme will override at runtime
TAPLIST_FILE = "./json/red-beers.json"
BEERDB_FILE = "./json/beer-database.json"
LOGO_FOLDER = "logos"
LOGO_CACHE_FOLDER = os.path.join(LOGO_FOLDER, "_cache")  # persistent raster cache
SCREEN_WIDTH = 1920
SCREEN_HEIGHT = 1080
FPS = 40

BG_COLOR = (24, 2, 6)       # Near-black with a hint of red
NEON_RED = (255, 36, 56)    # Red glow for header and borders
WHITE = (255, 255, 255)
DIM_WHITE = (180, 180, 180)
SOLDOUT_OVERLAY = (40, 40, 40, 180)  # RGBA for sold out beers

# ----- FONT CONFIG -----
HEADER_FONT_PATH = None
BEER_FONT_PATH = "./fonts/MagistralBold.otf"
INFO_FONT_PATH = "./fonts/Orbitron.otf"
DEFAULT_HEADER_FONT = pygame.font.get_default_font()

# Beer card layout
COLUMN_COUNT = 2
ROW_PADDING = 18
COL_PADDING = 20
CARD_HEIGHT = 130
LOGO_SIZE = 130
LOGO_MARGIN = 0

# Starfield config
STAR_COUNT = 90
STAR_COLORS = [
    (255, 80, 120), (255, 255, 255), (180, 50, 80),
    (200, 120, 140), (255, 200, 200)
]

# =========================

def load_json(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)

def ensure_cache_dir():
    os.makedirs(LOGO_CACHE_FOLDER, exist_ok=True)

def inkscape_path():
    return shutil.which("inkscape")

def rasterize_svg_to_cache(svg_path, out_png_path, box_px):
    ink = inkscape_path()
    if not ink:
        raise RuntimeError("Inkscape not found in PATH")
    os.makedirs(os.path.dirname(out_png_path), exist_ok=True)
    subprocess.check_call([
        ink, svg_path,
        "--export-type=png",
        f"--export-filename={out_png_path}",
        f"--export-width={box_px}",      # exact final width
        "--export-background-opacity=0", # true transparent background
        "--export-area-drawing"          # crop to artwork bounds
    ])

def load_logo_surface(filename, box_px=LOGO_SIZE):
    """
    Load a logo as a pygame Surface.
    - If PNG/JPG: load and fit to box.
    - If SVG: use persistent cache logos/_cache/<name>_<box_px>.png;
      regenerate via Inkscape if stale/missing.
    """
    try:
        full_path = os.path.join(LOGO_FOLDER, filename)
        base, ext = os.path.splitext(os.path.basename(filename))
        ext_lower = ext.lower()

        def fit(surface):
            w, h = surface.get_size()
            if w == 0 or h == 0:
                return None
            scale = min(box_px / w, box_px / h)
            new_size = (max(1, int(w * scale)), max(1, int(h * scale)))
            return pygame.transform.smoothscale(surface, new_size) if new_size != (w, h) else surface

        if ext_lower == ".svg":
            ensure_cache_dir()
            cached_png = os.path.join(LOGO_CACHE_FOLDER, f"{base}_{box_px}.png")
            svg_mtime = os.path.getmtime(full_path)
            need_regen = True
            if os.path.exists(cached_png):
                png_mtime = os.path.getmtime(cached_png)
                need_regen = svg_mtime > png_mtime + 0.0001

            if need_regen:
                try:
                    rasterize_svg_to_cache(full_path, cached_png, box_px)
                    os.utime(cached_png, None)
                except Exception as e:
                    print(f"[logo] Inkscape rasterization failed for {filename}: {e}")
                    return None

            try:
                surf = pygame.image.load(cached_png).convert_alpha()
            except Exception as e:
                print(f"[logo] Failed to load cached PNG {cached_png}: {e}")
                return None

            # IMPORTANT: no second resample in Python for SVGs
            return surf

        else:
            surf = pygame.image.load(full_path).convert_alpha()
            return fit(surf)

    except Exception as e:
        print(f"[logo] failed to load {filename}: {e}")
        return None

def get_fitting_font(text, max_width, font_path, start_size=64, min_size=16):
    size = start_size
    while size > min_size:
        font = get_font(size, font_path)
        if font.size(text)[0] <= max_width:
            return font
        size -= 1
    return get_font(min_size, font_path)

def merge_taplist_with_db(taplist, beerdb):
    db_by_id = {b['id']: b for b in beerdb}
    result = []
    for beer in taplist["beers"]:
        b = db_by_id.get(beer["id"])
        if b:
            b = b.copy()
            b['soldOut'] = beer.get('soldOut', False)
            result.append(b)
    return result

def make_starfield(w, h):
    stars = []
    for i in range(STAR_COUNT):
        x = int(os.urandom(1)[0] / 255.0 * w)
        y = int(os.urandom(1)[0] / 255.0 * h)
        speed = 0.12 + (os.urandom(1)[0] / 255.0) * 0.7
        size = 1 + int(os.urandom(1)[0] / 220.0 * 3)
        color = STAR_COLORS[i % len(STAR_COLORS)]
        twinkle = (os.urandom(1)[0] / 255.0) * math.pi * 2
        stars.append({"x": x, "y": y, "speed": speed, "size": size, "color": color, "tw": twinkle})
    return stars

def draw_starfield(screen, stars, t, screen_h):
    for s in stars:
        offset = math.sin(t * s["speed"] + s["tw"]) * 1.5
        col = [min(255, max(0, int(c + offset * 32))) for c in s["color"]]
        pygame.draw.circle(screen, col, (int(s["x"]), int((s["y"] + offset) % screen_h)), s["size"])

def get_font(size, font_path=None, fallback=None):
    try:
        if font_path:
            return pygame.font.Font(font_path, size)
        else:
            return pygame.font.SysFont(fallback or DEFAULT_HEADER_FONT, size)
    except Exception as e:
        print("Font error, using default:", e)
        return pygame.font.SysFont(fallback or DEFAULT_HEADER_FONT, size)

def draw_neon_text(screen, text, x, y, font, color, glow_size=12):
    for dx in range(-glow_size, glow_size + 1, 2):
        for dy in range(-glow_size, glow_size + 1, 2):
            if dx*dx + dy*dy < glow_size*glow_size:
                glow = font.render(text, True, color)
                glow.set_alpha(36)
                screen.blit(glow, (x + dx, y + dy))
    label = font.render(text, True, color)
    screen.blit(label, (x, y))

def draw_logo_placeholder(screen, x, y, size, color):
    pygame.draw.rect(screen, color, (x, y, size, size),
                     border_radius=int(size * 0.22), width=2)
    pygame.draw.line(screen, color,
                     (x+8, y+size//2), (x+size-8, y+size//2), width=2)

def run(theme):
    """Entry point used by the tiny launchers."""
    # Pull runtime config from theme (small, safe changes)
    taplist_file = theme.json_path
    logo_size = theme.logo_size
    bg_color = theme.bg_color
    accent = theme.accent
    dim_white = theme.dim_white

    pygame.init()
    screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
    pygame.display.set_caption(f"GK Taplist - {theme.name.capitalize()} Side")
    clock = pygame.time.Clock()

    global SCREEN_WIDTH, SCREEN_HEIGHT
    SCREEN_WIDTH, SCREEN_HEIGHT = screen.get_size()

    taplist = load_json(taplist_file)
    beerdb = load_json(BEERDB_FILE)
    beers = merge_taplist_with_db(taplist, beerdb)

    # Build logo cache at the theme's size
    logo_cache = {}
    for beer in beerdb:
        logo_file = beer.get("logoPath")
        if logo_file and logo_file not in logo_cache:
            logo_cache[logo_file] = load_logo_surface(logo_file, logo_size)

    header_font = get_font(88, HEADER_FONT_PATH)
    beer_font = get_font(38, BEER_FONT_PATH)
    info_font = get_font(22, INFO_FONT_PATH)

    stars = make_starfield(SCREEN_WIDTH, SCREEN_HEIGHT)
    start_time = pygame.time.get_ticks()

    running = True
    while running:
        t = (pygame.time.get_ticks() - start_time) / 1000.0
        for event in pygame.event.get():
            if event.type == pygame.QUIT or (
                event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):
                running = False

        screen.fill(bg_color)
        draw_starfield(screen, stars, t, SCREEN_HEIGHT)
        draw_neon_text(screen, "TAP LIST", 62, 30, header_font, accent, 16)

        cards_per_col = (len(beers) + 1) // 2
        col_x = [20, SCREEN_WIDTH // 2 + 16]
        for col in range(COLUMN_COUNT):
            for idx in range(cards_per_col):
                beer_idx = col * cards_per_col + idx
                if beer_idx >= len(beers):
                    break
                beer = beers[beer_idx]
                top = 160 + idx * (CARD_HEIGHT + ROW_PADDING)
                left = col_x[col]

                # Logos
                logo_file = beer.get("logoPath")
                surf = logo_cache.get(logo_file)
                logo_box_x = left + LOGO_MARGIN
                logo_box_y = top + (CARD_HEIGHT - logo_size) // 2
                logo_box_rect = pygame.Rect(logo_box_x, logo_box_y, logo_size, logo_size)

                if surf:
                    logo_rect = surf.get_rect(center=logo_box_rect.center)
                    screen.blit(surf, logo_rect)
                else:
                    draw_logo_placeholder(screen, logo_box_x, logo_box_y, logo_size, accent)

                # Beer info
                x_text = left + LOGO_MARGIN + logo_size + 22
                SPACING = 15
                full_name = f"{beer['brewery']} {beer['title']}".upper()
                max_text_width = (SCREEN_WIDTH // 2 - 36) - (LOGO_MARGIN + logo_size + 22) - 18
                name_font = get_fitting_font(full_name, max_text_width, BEER_FONT_PATH, start_size=72, min_size=22)

                style = beer['style'].upper()
                abv = f"{beer['abv']}% ABV"
                city = f"{beer['city'].upper()}, {beer['state'].upper()}"
                info = f"{style} – {abv} – {city}"
                info_font_fitted = get_fitting_font(info, max_text_width, INFO_FONT_PATH, start_size=32, min_size=12)

                name_surf = name_font.render(full_name, True, WHITE)
                info_surf = info_font_fitted.render(info, True, dim_white)

                name_ascent = name_font.get_ascent()
                info_ascent = info_font_fitted.get_ascent()
                block_height = name_ascent + SPACING + info_ascent
                block_top = top + (CARD_HEIGHT - block_height) // 2

                screen.blit(name_surf, (x_text, block_top))
                screen.blit(info_surf, (x_text, block_top + name_ascent + SPACING))

                if beer.get("soldOut", False):
                    soldout_overlay = pygame.Surface((SCREEN_WIDTH//2-96, CARD_HEIGHT), pygame.SRCALPHA)
                    soldout_overlay.fill(SOLDOUT_OVERLAY)
                    screen.blit(soldout_overlay, (left, top))
                    soldout_text = info_font.render("SOLD OUT", True, accent)
                    screen.blit(soldout_text, (x_text, top + CARD_HEIGHT//2 - 10))

        pygame.display.flip()
        clock.tick(FPS)

    pygame.quit()
