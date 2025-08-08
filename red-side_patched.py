import pygame
import json
import os
import sys
import math
from collections import defaultdict
from io import BytesIO
import cairosvg

# ======== CONFIG ==========
TAPLIST_FILE = "./json/red-beers.json"
BEERDB_FILE = "./json/beer-database.json"
LOGO_FOLDER = "logos"
SCREEN_WIDTH = 1920
SCREEN_HEIGHT = 1080
FPS = 40

BG_COLOR = (24, 2, 6)       # Near-black with a hint of red
NEON_RED = (255, 36, 56)    # Red glow for header and borders
WHITE = (255, 255, 255)
DIM_WHITE = (180, 180, 180)
SOLDOUT_OVERLAY = (40, 40, 40, 180)  # RGBA for sold out beers

# ----- FONT CONFIG -----
# Plug in your custom fonts below (must be TTF)
HEADER_FONT_PATH = None # e.g. "MagistralBold.ttf"
BEER_FONT_PATH = "./fonts/MagistralBold.otf"   # e.g. "Orbitron.ttf"
INFO_FONT_PATH = "./fonts/Orbitron.otf"   # e.g. "Orbitron.ttf"
DEFAULT_HEADER_FONT = pygame.font.get_default_font()
DEFAULT_BEER_FONT = pygame.font.get_default_font()

# Beer card layout
COLUMN_COUNT = 2
ROW_PADDING = 18
COL_PADDING = 20
CARD_HEIGHT = 130
LOGO_SIZE = 130
LOGO_MARGIN = 0

# Starfield config
STAR_COUNT = 90
STAR_COLORS = [(255, 80, 120), (255, 255, 255), (180, 50, 80), (200, 120, 140), (255, 200, 200)]

# =========================

def load_json(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)

def load_logo_surface(filename, box_px=LOGO_SIZE):
    """
    Load a logo as a pygame Surface. If it's an SVG, rasterize with CairoSVG.
    Then scale once to fit inside a square box of size box_px, preserving aspect.
    Returns a Surface or None on failure.
    """
    try:
        full_path = os.path.join(LOGO_FOLDER, filename)
        if filename.lower().endswith(".svg"):
            # Rasterize SVG to PNG bytes at roughly our target width
            png_bytes = cairosvg.svg2png(url=full_path, output_width=box_px)
            surf = pygame.image.load(BytesIO(png_bytes)).convert_alpha()
        else:
            surf = pygame.image.load(full_path).convert_alpha()
    except Exception as e:
        print(f"Could not load logo {filename}: {e}")
        return None

    # One-time fit into LOGO_SIZE square (keep aspect)
    w, h = surf.get_size()
    if w == 0 or h == 0:
        return None
    scale = min(box_px / w, box_px / h)
    new_size = (max(1, int(w * scale)), max(1, int(h * scale)))
    if new_size != (w, h):
        surf = pygame.transform.smoothscale(surf, new_size)
    return surf

def get_fitting_font(text, max_width, font_path, start_size=64, min_size=16):
    size = start_size
    while size > min_size:
        font = get_font(size, font_path)
        if font.size(text)[0] <= max_width:
            return font
        size -= 1
    # If nothing fits, return smallest font
    return get_font(min_size, font_path)

def merge_taplist_with_db(taplist, beerdb):
    db_by_id = {b['id']: b for b in beerdb}
    result = []
    for beer in taplist["beers"]:
        b = db_by_id.get(beer["id"], None)
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
    # Outer glow
    for dx in range(-glow_size, glow_size + 1, 2):
        for dy in range(-glow_size, glow_size + 1, 2):
            if dx*dx + dy*dy < glow_size*glow_size:
                glow = font.render(text, True, color)
                glow.set_alpha(36)
                screen.blit(glow, (x + dx, y + dy))
    # Solid text
    label = font.render(text, True, color)
    screen.blit(label, (x, y))

def draw_logo_placeholder(screen, x, y, size, color):
    # Just a rounded rectangle for now
    pygame.draw.rect(screen, color, (x, y, size, size), border_radius=int(size * 0.22), width=2)
    pygame.draw.line(screen, color, (x+8, y+size//2), (x+size-8, y+size//2), width=2)

def main():
    pygame.init()
    screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
    pygame.display.set_caption("GK Taplist - Red Side")
    clock = pygame.time.Clock()

    # Use real screen size for layout and starfield
    global SCREEN_WIDTH, SCREEN_HEIGHT
    SCREEN_WIDTH, SCREEN_HEIGHT = screen.get_size()

    # Load data
    taplist = load_json(TAPLIST_FILE)
    beerdb = load_json(BEERDB_FILE)
    beers = merge_taplist_with_db(taplist, beerdb)

    # Build a cache of pre-scaled logos once (PNG/JPG/SVG all end up as Surfaces sized for LOGO_SIZE)
    logo_cache = {}
    for beer in beerdb:
        logo_file = beer.get("logoPath")
        if logo_file and logo_file not in logo_cache:
            logo_cache[logo_file] = load_logo_surface(logo_file, LOGO_SIZE)

    # Fonts (swap your TTFs here!)
    header_font = get_font(88, HEADER_FONT_PATH)
    beer_font = get_font(38, BEER_FONT_PATH)
    info_font = get_font(22, INFO_FONT_PATH)

    # Starfield
    stars = make_starfield(SCREEN_WIDTH, SCREEN_HEIGHT)
    start_time = pygame.time.get_ticks()

    running = True
    while running:
        t = (pygame.time.get_ticks() - start_time) / 1000.0
        for event in pygame.event.get():
            if event.type == pygame.QUIT or (
                event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):
                running = False

        screen.fill(BG_COLOR)
        draw_starfield(screen, stars, t, SCREEN_HEIGHT)

        # Header
        draw_neon_text(screen, "TAP LIST", 62, 30, header_font, NEON_RED, 16)

        # Layout: two columns
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
                logo_box_y = top + (CARD_HEIGHT - LOGO_SIZE) // 2
                logo_box_rect = pygame.Rect(logo_box_x, logo_box_y, LOGO_SIZE, LOGO_SIZE)

                if surf:
                    logo_rect = surf.get_rect(center=logo_box_rect.center)
                    screen.blit(surf, logo_rect)
                else:
                    draw_logo_placeholder(screen, logo_box_x, logo_box_y, LOGO_SIZE, NEON_RED)

                # Beer info
                x_text = left + LOGO_MARGIN + LOGO_SIZE + 22
                SPACING = 15

                # 1. Concatenate brewery and title, all caps
                full_name = f"{beer['brewery']} {beer['title']}".upper()

                # 2. Compute max width for name (adjust as needed for your layout)
                max_text_width = (SCREEN_WIDTH // 2 - 36) - (LOGO_MARGIN + LOGO_SIZE + 22) - 18

                # 3. Get font that fits the name in the space
                name_font = get_fitting_font(full_name, max_text_width, BEER_FONT_PATH, start_size=72, min_size=22)

                # 4. Prepare info string (all caps)
                style = beer['style'].upper()
                abv = f"{beer['abv']}% ABV"
                city = f"{beer['city'].upper()}, {beer['state'].upper()}"
                info = f"{style} – {abv} – {city}"

                # 5. Get the font that fits the container width for info
                info_font_fitted = get_fitting_font(info, max_text_width, INFO_FONT_PATH, start_size=32, min_size=12)

                # 6. Render surfaces for both lines
                name_surf = name_font.render(full_name, True, WHITE)
                info_surf = info_font_fitted.render(info, True, DIM_WHITE)

                # 7. Vertical alignment calculation
                name_ascent = name_font.get_ascent()
                info_ascent = info_font_fitted.get_ascent()
                block_height = name_ascent + SPACING + info_ascent
                block_top = top + (CARD_HEIGHT - block_height) // 2

                # 8. Blit (draw) text, vertically centered in the card
                screen.blit(name_surf, (x_text, block_top))
                screen.blit(info_surf, (x_text, block_top + name_ascent + SPACING))

                # Sold Out?
                if beer.get("soldOut", False):
                    soldout_overlay = pygame.Surface((SCREEN_WIDTH//2-96, CARD_HEIGHT), pygame.SRCALPHA)
                    soldout_overlay.fill(SOLDOUT_OVERLAY)
                    screen.blit(soldout_overlay, (left, top))
                    soldout_text = info_font.render("SOLD OUT", True, NEON_RED)
                    screen.blit(soldout_text, (x_text, top + CARD_HEIGHT//2 - 10))

        pygame.display.flip()
        clock.tick(FPS)

    pygame.quit()

if __name__ == "__main__":
    main()
