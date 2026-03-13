import os
import random
import math
from pathlib import Path

import pygame


def _env_bool(name: str, default: bool) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in ("1", "true", "yes", "on")


def _env_int(name: str, default: int) -> int:
    raw = os.getenv(name)
    if raw is None:
        return default
    try:
        return int(raw.strip())
    except Exception:
        return default


TARGET_FPS = max(0, _env_int("GK_GAMEOVER_FPS", 60))
ALLOW_ESCAPE = _env_bool("GK_ALLOW_ESCAPE", True)
USE_VSYNC = _env_bool("GK_USE_VSYNC", False)
SPRITES_DIR = Path("sprites")
IMAGES_DIR = Path("images")
FONTS_DIR = Path("fonts")
BG_FILE = "gameoverbg.png"
URF_FILE = "urf.png"
ASTRO_LEFT_FILE = "astronaut1.png"
ASTRO_RIGHT_FILE = "astronaut2.png"
GK_LOGO_FILE = "gklogosprite.png"
GAME_OVER_FONT_FILE = "Precinct 90.ttf"
SUBTITLE_FONT_FILE = "Fusion Drive Bold.ttf"
BITMAP_NATIVE_PX = 8
ASTRO_MAX_ALPHA = 204  # 80%
ASTRO_FADE_SECONDS = 24.0


def load_sprite(name: str):
    path = SPRITES_DIR / name
    if not path.exists():
        return None
    try:
        return pygame.image.load(str(path)).convert_alpha()
    except Exception:
        return None


def load_image_sprite(name: str):
    path = IMAGES_DIR / name
    if not path.exists():
        return None
    try:
        return pygame.image.load(str(path)).convert_alpha()
    except Exception:
        return None


def load_font(name: str, size: int):
    path = FONTS_DIR / name
    try:
        if path.exists():
            return pygame.font.Font(str(path), size)
    except Exception:
        pass
    return pygame.font.SysFont(None, size)


def build_star_layer(world_w: int, world_h: int):
    layer = pygame.Surface((world_w, world_h), pygame.SRCALPHA).convert_alpha()
    area = world_w * world_h

    white_count = max(80, area // 18000)
    blue_cross_count = max(20, area // 60000)
    yellow_count = max(10, area // 110000)
    twinkle_ratio = 0.20
    twinkle_stars = []

    # Sparse single white stars at roughly 50% opacity.
    for _ in range(white_count):
        x = random.randint(0, world_w - 1)
        y = random.randint(0, world_h - 1)
        layer.set_at((x, y), (255, 255, 255, 128))

    # Blue-white stars with a blue cross (top/bottom/left/right).
    for _ in range(blue_cross_count):
        x = random.randint(1, world_w - 2)
        y = random.randint(1, world_h - 2)
        layer.set_at((x, y), (214, 236, 255, 220))
        if random.random() < twinkle_ratio:
            twinkle_stars.append(
                {
                    "x": x,
                    "y": y,
                    "phase": random.random() * math.tau,
                    "speed": random.uniform(1.2, 2.4),
                }
            )
        else:
            layer.set_at((x, y - 1), (116, 160, 255, 170))
            layer.set_at((x, y + 1), (116, 160, 255, 170))
            layer.set_at((x - 1, y), (116, 160, 255, 170))
            layer.set_at((x + 1, y), (116, 160, 255, 170))

    # Small amount of yellow stars.
    for _ in range(yellow_count):
        x = random.randint(0, world_w - 1)
        y = random.randint(0, world_h - 1)
        layer.set_at((x, y), (255, 224, 152, 200))

    return layer, twinkle_stars


def draw_twinkle_stars(screen, twinkle_stars, t: float, view_x: int, view_y: int, width: int, height: int):
    for s in twinkle_stars:
        wave = 0.5 + 0.5 * math.sin(t * s["speed"] + s["phase"])
        if wave < 0.25:
            continue
        if wave > 0.78:
            arm_color = (164, 196, 255, 225)
        else:
            arm_color = (116, 160, 255, 170)

        x = s["x"] - view_x
        y = s["y"] - view_y
        if x <= 0 or x >= width - 1 or y <= 0 or y >= height - 1:
            continue
        screen.set_at((x, y - 1), arm_color)
        screen.set_at((x, y + 1), arm_color)
        screen.set_at((x - 1, y), arm_color)
        screen.set_at((x + 1, y), arm_color)


def build_integer_scaled_to_width(sprite, target_width: int):
    if sprite is None:
        return None
    src_w = max(1, sprite.get_width())
    src_h = max(1, sprite.get_height())
    full_scale = max(1, math.ceil(target_width / src_w))
    scale = max(1, (full_scale + 1) // 2)
    return pygame.transform.scale(sprite, (src_w * scale, src_h * scale))


def build_background_surface(bg, width: int, height: int):
    if bg is None:
        surf = pygame.Surface((width, height)).convert()
        surf.fill((0, 0, 0))
        return surf
    if bg.get_width() < width or bg.get_height() < height:
        scale = max(
            width / max(1, bg.get_width()),
            height / max(1, bg.get_height()),
        )
        return pygame.transform.scale(
            bg,
            (int(bg.get_width() * scale), int(bg.get_height() * scale)),
        )
    return bg


def build_integer_scaled_fixed(sprite, scale: int = 2):
    if sprite is None:
        return None
    src_w = max(1, sprite.get_width())
    src_h = max(1, sprite.get_height())
    scale = max(1, int(scale))
    return pygame.transform.scale(sprite, (src_w * scale, src_h * scale))


def draw_wavy_sprite(
    screen,
    sprite,
    x: int,
    y: int,
    t: float,
    phase: float,
    amp_px: float = 6.0,
    wavelength_px: float = 14.0,
    speed: float = 2.1,
    bob_px: float = 5.0,
    row_step: int = 1,
):
    if sprite is None:
        return

    w = sprite.get_width()
    h = sprite.get_height()
    base_y = y + int(math.sin(t * 0.85 + phase) * bob_px)
    step = max(1, int(row_step))
    for row in range(0, h, step):
        native_row = row // step
        dx = int(math.sin((native_row / wavelength_px) + t * speed + phase) * amp_px)
        band_h = min(step, h - row)
        screen.blit(sprite, (x + dx, base_y + row), area=(0, row, w, band_h))


def build_title_glyphs(font, text: str, color):
    glyphs = []
    space_advance = max(1, font.size(" ")[0])
    for ch in text:
        surf = font.render(ch, False, color).convert_alpha()
        bounds = surf.get_bounding_rect()
        if bounds.width > 0 and bounds.height > 0:
            tight = pygame.Surface((bounds.width, bounds.height), pygame.SRCALPHA).convert_alpha()
            tight.blit(surf, (0, 0), bounds)
            glyphs.append({"surf": tight, "advance": tight.get_width()})
        else:
            blank = pygame.Surface((space_advance, 1), pygame.SRCALPHA).convert_alpha()
            glyphs.append({"surf": blank, "advance": space_advance})
    return glyphs


def calc_glyph_run_width(glyphs, spacing: int):
    if not glyphs:
        return 0
    return sum(g["advance"] for g in glyphs) + spacing * (len(glyphs) - 1)


def draw_pulse_wave_text(
    screen,
    glyphs,
    x: int,
    y: int,
    t: float,
    spacing: int = 0,
    float_px: float = 5.0,
    float_speed: float = 1.1,
    pulse_period: float = 2.8,
    pulse_px: float = 34.0,
    pulse_width: float = 0.9,
    pulse_speed_chars: float = 5.2,
):
    if not glyphs:
        return

    pulse_time = t % pulse_period
    pulse_center = pulse_time * pulse_speed_chars - 2.0
    cursor_x = x
    for i, glyph in enumerate(glyphs):
        float_y = math.sin(t * float_speed + i * 0.45) * float_px
        pulse_dist = (i - pulse_center) / max(0.1, pulse_width)
        pulse_main = math.exp(-(pulse_dist * pulse_dist)) * pulse_px
        trail_dist = (i - (pulse_center - 0.55)) / max(0.1, pulse_width * 1.35)
        pulse_trail = math.exp(-(trail_dist * trail_dist)) * (pulse_px * 0.35)
        pulse_y = pulse_main - pulse_trail
        glyph_y = y + int(float_y - pulse_y)
        screen.blit(glyph["surf"], (cursor_x, glyph_y))
        cursor_x += glyph["advance"] + spacing


def draw_float_text(
    screen,
    glyphs,
    x: int,
    y: int,
    t: float,
    spacing: int = 0,
    float_px: float = 5.0,
    float_speed: float = 1.1,
):
    if not glyphs:
        return

    cursor_x = x
    for i, glyph in enumerate(glyphs):
        float_y = math.sin(t * float_speed + i * 0.45) * float_px
        glyph_y = y + int(float_y)
        screen.blit(glyph["surf"], (cursor_x, glyph_y))
        cursor_x += glyph["advance"] + spacing


def main():
    pygame.display.init()
    pygame.font.init()
    pygame.event.set_allowed([pygame.QUIT, pygame.KEYDOWN])

    flags = pygame.FULLSCREEN | pygame.DOUBLEBUF
    if USE_VSYNC:
        screen = pygame.display.set_mode((0, 0), flags, vsync=1)
    else:
        screen = pygame.display.set_mode((0, 0), flags)
    pygame.display.set_caption("GK Taplister - Game Over")
    try:
        pygame.mouse.set_visible(False)
    except Exception:
        pass

    width, height = screen.get_size()
    clock = pygame.time.Clock()

    bg = load_sprite(BG_FILE)
    bg_scaled = build_background_surface(bg, width, height)
    bg_extra_x = max(0, bg_scaled.get_width() - width)
    bg_extra_y = max(0, bg_scaled.get_height() - height)
    bg_base_x = -(bg_extra_x // 2)
    bg_base_y = -(bg_extra_y // 2)
    bg_pan_y = min(bg_extra_y // 2, max(0, int(height * 0.04)))
    bg_pan_seconds = 160.0

    urf = load_sprite(URF_FILE)
    if urf is not None:
        urf = pygame.transform.flip(urf, False, True)
    urf_scaled = build_integer_scaled_to_width(urf, width)
    if urf_scaled is not None:
        urf_x = 0
        # Flipped motion: start above screen, move down into view.
        urf_start_y = -urf_scaled.get_height()
        # Stop when top edge aligns with top of screen.
        urf_end_y = 0
        urf_rise_seconds = 140.0

    astro_left = build_integer_scaled_fixed(load_sprite(ASTRO_LEFT_FILE), scale=4)
    astro_right = build_integer_scaled_fixed(load_sprite(ASTRO_RIGHT_FILE), scale=4)
    gk_logo = build_integer_scaled_fixed(load_image_sprite(GK_LOGO_FILE), scale=3)
    game_over_font_size = 160
    subtitle_font_size = 64
    game_over_font = load_font(GAME_OVER_FONT_FILE, game_over_font_size)
    game_over_glyphs = build_title_glyphs(game_over_font, "GAME OVER", (255, 255, 255))
    subtitle_font = load_font(SUBTITLE_FONT_FILE, subtitle_font_size)
    subtitle_glyphs = build_title_glyphs(subtitle_font, "See You Next Time!", (255, 255, 255))
    if astro_left is not None:
        astro_left = astro_left.copy()
        astro_left.set_alpha(0)
    if astro_right is None and astro_left is not None:
        astro_right = pygame.transform.flip(astro_left, True, False)
    elif astro_right is not None:
        astro_right = astro_right.copy()
        astro_right.set_alpha(0)

    stars_world, twinkle_stars = build_star_layer(bg_scaled.get_width(), bg_scaled.get_height())

    running = True
    t = 0.0
    while running:
        dt = clock.tick(TARGET_FPS if TARGET_FPS > 0 else 0) / 1000.0
        t += dt

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE and ALLOW_ESCAPE:
                running = False

        bg_progress = min(1.0, t / bg_pan_seconds)
        bg_x = bg_base_x
        bg_y = bg_base_y - int(bg_pan_y * bg_progress)
        bg_x = min(0, max(-bg_extra_x, bg_x))
        bg_y = min(0, max(-bg_extra_y, bg_y))
        view_x = -bg_x
        view_y = -bg_y
        view_rect = pygame.Rect(view_x, view_y, width, height)
        screen.blit(bg_scaled, (0, 0), view_rect)
        screen.blit(stars_world, (0, 0), view_rect)
        draw_twinkle_stars(screen, twinkle_stars, t, view_x, view_y, width, height)
        astro_alpha = int(ASTRO_MAX_ALPHA * min(1.0, t / ASTRO_FADE_SECONDS))
        if astro_left is not None:
            astro_left.set_alpha(astro_alpha)
        if astro_right is not None:
            astro_right.set_alpha(astro_alpha)
        margin_x = max(12, int(width * 0.018))
        margin_y = max(8, int(height * 0.02))
        if astro_left is not None:
            draw_wavy_sprite(
                screen,
                astro_left,
                margin_x,
                height - astro_left.get_height() - margin_y,
                t,
                phase=0.0,
                amp_px=4.0,
                wavelength_px=20.0,
                speed=0.9,
                bob_px=2.0,
                row_step=4,
            )
        if astro_right is not None:
            draw_wavy_sprite(
                screen,
                astro_right,
                width - astro_right.get_width() - margin_x,
                height - astro_right.get_height() - margin_y,
                t,
                phase=1.9,
                amp_px=4.0,
                wavelength_px=20.0,
                speed=1.0,
                bob_px=2.0,
                row_step=4,
            )
        if urf_scaled is not None:
            progress = min(1.0, t / urf_rise_seconds)
            eased = math.sin((progress * math.pi) / 2.0)
            urf_y = urf_start_y + (urf_end_y - urf_start_y) * eased
            screen.blit(urf_scaled, (urf_x, int(urf_y)))
        if gk_logo is not None:
            logo_x = (width - gk_logo.get_width()) // 2
            logo_y = 100
            screen.blit(gk_logo, (logo_x, logo_y))
        title_spacing = max(1, game_over_font_size // BITMAP_NATIVE_PX)
        title_width = calc_glyph_run_width(game_over_glyphs, title_spacing)
        text_x = (width - title_width) // 2
        text_y = 330
        draw_pulse_wave_text(screen, game_over_glyphs, text_x, text_y, t, spacing=title_spacing)
        subtitle_spacing = max(1, subtitle_font_size // BITMAP_NATIVE_PX)
        subtitle_width = calc_glyph_run_width(subtitle_glyphs, subtitle_spacing)
        subtitle_x = (width - subtitle_width) // 2
        subtitle_y = 500
        draw_float_text(screen, subtitle_glyphs, subtitle_x, subtitle_y, t, spacing=subtitle_spacing, float_px=4.0, float_speed=1.0)

        pygame.display.flip()

    pygame.font.quit()
    pygame.display.quit()


if __name__ == "__main__":
    main()
