import pygame
import json
import os
import sys
import math
from collections import defaultdict

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
    
def load_logo(filename):
    try:
        # Loads SVG or PNG just fine, as long as SDL_image supports SVG
        surf = pygame.image.load(os.path.join(LOGO_FOLDER, filename)).convert_alpha()
        return surf
    except Exception as e:
        print(f"Could not load logo {filename}: {e}")
        return None  # Or a default image
    
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

def draw_starfield(screen, stars, t):
    for s in stars:
        offset = math.sin(t * s["speed"] + s["tw"]) * 1.5
        col = [min(255, max(0, int(c + offset * 32))) for c in s["color"]]
        pygame.draw.circle(screen, col, (int(s["x"]), int((s["y"] + offset) % SCREEN_HEIGHT)), s["size"])

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

    # Load data
    taplist = load_json(TAPLIST_FILE)
    beerdb = load_json(BEERDB_FILE)
    beers = merge_taplist_with_db(taplist, beerdb)

    # Build a cache of scaled logos once
    logo_cache = {}
    for beer in beerdb:
        logo_file = beer.get("logoPath")
        if logo_file and logo_file not in logo_cache:
            img = load_logo(logo_file)
            if img:
                ow, oh = img.get_size()
                scale = LOGO_SIZE / max(ow, oh)
                nw, nh = int(ow*scale), int(oh*scale)
            else:
                logo_cache[logo_file] = None

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
        draw_starfield(screen, stars, t)

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
                # Card BG (optional: make it glow if you want)
                #pygame.draw.rect(screen, (36, 12, 20), (left, top, SCREEN_WIDTH//2-36, CARD_HEIGHT), border_radius=6)
                # Logos
                logo_file = beer.get("logoPath")
                logo_img = logo_cache.get(logo_file)
                if logo_img:
                    orig_width, orig_height = logo_img.get_size()
                    scale = LOGO_SIZE / max(orig_width, orig_height)
                    new_width = int(orig_width * scale)
                    new_height = int(orig_height * scale)
                    logo_img_scaled = logo_cache[beer["logoPath"]]

                    # Compute the rect of the container (center of logo box)
                    logo_box_x = left + LOGO_MARGIN
                    logo_box_y = top + (CARD_HEIGHT - LOGO_SIZE) // 2
                    logo_box_rect = pygame.Rect(logo_box_x, logo_box_y, LOGO_SIZE, LOGO_SIZE)

                    # Use get_rect to center the scaled logo in the box
                    logo_rect = logo_img_scaled.get_rect(center=logo_box_rect.center)
                    screen.blit(logo_img_scaled, logo_rect)

                else:
                    draw_logo_placeholder(screen, left + LOGO_MARGIN, top + (CARD_HEIGHT-LOGO_SIZE)//2, LOGO_SIZE, NEON_RED)

                # Beer info
                x_text = left + LOGO_MARGIN + LOGO_SIZE + 22
                # ---- BEER CARD: Concatenated Name (ALL CAPS, fits width) + Info Line ----
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
