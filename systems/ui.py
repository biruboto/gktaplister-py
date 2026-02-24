import math
import os

import pygame

TEXT_ANTIALIAS = True

# Header effect cache across frames
_HEADER_TEXT = None
_HEADER_THEME = None
_HEADER_POS = (62, 30)


class NeonTextFX:
    def __init__(
        self,
        font: pygame.font.Font,
        text: str,
        base_color=(255, 255, 255),
        outline_color=(255, 255, 255),
        shadow_color=(0, 0, 0),
        shadow_alpha=140,
        outline_px=2,
        shadow_offset=(3, 4),
        shimmer=False,
        shimmer_speed=90,
        extrusion_px=0,
        extrusion_color=(0, 0, 0),
        wave=True,
        wave_amplitude=4,
        wave_wavelength=120,
        wave_speed=3.2,
        wave_step=2,
        bounce_phase_step=0.7,
        pair_kerning=None,
    ):
        base_white = font.render(text, True, (255, 255, 255)).convert_alpha()
        tw, th = base_white.get_size()
        pad = max(2, outline_px + 2) if outline_px > 0 else 0
        self.pad = pad
        self.has_outline = outline_px > 0

        base = base_white.copy()
        base.fill((*base_color, 255), special_flags=pygame.BLEND_RGBA_MULT)
        self.base = base
        self.text = text
        self.font = font
        self.base_color = base_color
        self.shadow_color = shadow_color
        self.shadow_alpha = shadow_alpha

        mask = pygame.mask.from_surface(base_white)
        stamp = mask.to_surface(setcolor=(255, 255, 255, 255), unsetcolor=(0, 0, 0, 0)).convert_alpha()

        if self.has_outline:
            outline = pygame.Surface((tw + pad * 2, th + pad * 2), pygame.SRCALPHA).convert_alpha()
            offsets = [
                (dx, dy)
                for dx in range(-outline_px, outline_px + 1)
                for dy in range(-outline_px, outline_px + 1)
                if dx * dx + dy * dy <= outline_px * outline_px
            ]
            for dx, dy in offsets:
                outline.blit(stamp, (pad + dx, pad + dy))
            outline.fill((*outline_color, 255), special_flags=pygame.BLEND_RGBA_MULT)
            self.outline = outline
            shadow = outline.copy()
        else:
            self.outline = None
            shadow = stamp.copy()

        shadow.fill((*shadow_color, 255), special_flags=pygame.BLEND_RGBA_MULT)
        shadow.set_alpha(shadow_alpha)
        self.shadow = shadow
        self.shadow_offset = shadow_offset
        self.extrusion_px = max(0, int(extrusion_px))
        self.extrusion_color = extrusion_color
        self.extrusion = None
        if self.extrusion_px > 0:
            self.extrusion = stamp.copy()
            self.extrusion.fill((*extrusion_color, 255), special_flags=pygame.BLEND_RGBA_MULT)

        self.shimmer = shimmer
        self.shimmer_speed = shimmer_speed

        stripe_w = 12
        bar = pygame.Surface((stripe_w, th * 2), pygame.SRCALPHA).convert_alpha()
        for x in range(stripe_w):
            t = 1.0 - abs((x - (stripe_w - 1) / 2) / max(1, (stripe_w - 1) / 2))
            a = int(220 * (t * t))
            pygame.draw.line(bar, (255, 255, 255, a), (x, 0), (x, th * 2 - 1))

        self.stripe = pygame.transform.rotate(bar, -20)
        self.mask_surf = mask.to_surface(setcolor=(255, 255, 255, 255), unsetcolor=(0, 0, 0, 0)).convert_alpha()
        self.sweep = pygame.Surface((tw, th), pygame.SRCALPHA).convert_alpha()

        self._span = tw + self.stripe.get_width()
        self._phase_px = 0.0
        self._last_ticks = pygame.time.get_ticks()

        self.wave = wave
        self.wave_amplitude = max(0, int(wave_amplitude))
        self.wave_wavelength = max(1, float(wave_wavelength))
        self.wave_speed = float(wave_speed)  # radians / sec
        self.wave_step = max(1, int(wave_step))
        self._wave_phase = 0.0
        self._wave_buffer = pygame.Surface(
            (tw, th + self.wave_amplitude * 2), pygame.SRCALPHA
        ).convert_alpha()
        self.bounce_phase_step = float(bounce_phase_step)
        self._char_surfs = []
        self._char_shadow_surfs = []
        self._char_x = []
        self.pair_kerning = pair_kerning or {}
        char_x = 0
        for i, ch in enumerate(text):
            if i > 0:
                pair = text[i - 1] + ch
                char_x += int(round(self.pair_kerning.get(pair, 0)))
            ch_white = font.render(ch, True, (255, 255, 255)).convert_alpha()
            ch_base = ch_white.copy()
            ch_base.fill((*base_color, 255), special_flags=pygame.BLEND_RGBA_MULT)
            ch_shadow = ch_white.copy()
            ch_shadow.fill((*shadow_color, 255), special_flags=pygame.BLEND_RGBA_MULT)
            ch_shadow.set_alpha(shadow_alpha)
            self._char_surfs.append(ch_base)
            self._char_shadow_surfs.append(ch_shadow)
            self._char_x.append(char_x)
            char_x += ch_base.get_width()

    def draw_base(self, screen, x, y):
        if self.extrusion:
            # Fake 3D depth by stacking a few offset layers behind the glyphs.
            for i in range(self.extrusion_px, 0, -1):
                screen.blit(self.extrusion, (x + i, y + i))
        screen.blit(self.shadow, (x - self.pad + self.shadow_offset[0], y - self.pad + self.shadow_offset[1]))
        if self.outline:
            screen.blit(self.outline, (x - self.pad, y - self.pad))
        screen.blit(self.base, (x, y))

    def draw_shimmer(self, screen, x, y):
        return

        now = pygame.time.get_ticks()
        dt = (now - self._last_ticks) / 1000.0
        self._last_ticks = now
        self._phase_px = (self._phase_px + self.shimmer_speed * dt) % self._span

        self.sweep.fill((0, 0, 0, 0))
        pos_x = int(self._phase_px) - self.stripe.get_width()
        pos_y = -self.stripe.get_height() // 4
        self.sweep.blit(self.stripe, (pos_x, pos_y))
        self.sweep.blit(self.mask_surf, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
        screen.blit(self.sweep, (x, y))

    def draw(self, screen, x, y):
        self.draw_base(screen, x, y)
        self.draw_shimmer(screen, x, y)

    def draw_wave(self, screen, x, y):
        # Character bounce effect: each glyph moves vertically by a phase-shifted sine.
        if not self.wave:
            self.draw_base(screen, x, y)
            return

        now = pygame.time.get_ticks()
        dt = (now - self._last_ticks) / 1000.0
        self._last_ticks = now
        self._wave_phase += self.wave_speed * dt

        for i, glyph in enumerate(self._char_surfs):
            y_off_f = math.sin(self._wave_phase + i * self.bounce_phase_step) * self.wave_amplitude
            y_off = int(round(y_off_f))
            gx = x + self._char_x[i]
            gy = y + y_off
            screen.blit(
                self._char_shadow_surfs[i],
                (gx + self.shadow_offset[0], gy + self.shadow_offset[1]),
            )
            screen.blit(glyph, (gx, gy))


def draw_taplist_overlay(screen):
    if _HEADER_TEXT is None:
        return
    # Animate only the header glyphs each frame; everything else stays cached/static.
    _HEADER_TEXT.draw_wave(screen, _HEADER_POS[0], _HEADER_POS[1])


def get_font(size, font_path=None, fallback=None):
    try:
        if font_path:
            return pygame.font.Font(font_path, size)
        return pygame.font.SysFont(fallback or pygame.font.get_default_font(), size)
    except Exception as exc:
        print("Font error, using default:", exc)
        return pygame.font.SysFont(fallback or pygame.font.get_default_font(), size)


def get_fitting_font(text, max_width, font_path, start_size=64, min_size=16):
    size = start_size
    while size > min_size:
        font = get_font(size, font_path)
        if font.size(text)[0] <= max_width:
            return font
        size -= 1
    return get_font(min_size, font_path)


def draw_neon_text(screen, text, x, y, font, color, glow_size=12):
    for dx in range(-glow_size, glow_size + 1, 2):
        for dy in range(-glow_size, glow_size + 1, 2):
            if dx * dx + dy * dy < glow_size * glow_size:
                glow = font.render(text, TEXT_ANTIALIAS, color)
                glow.set_alpha(36)
                screen.blit(glow, (x + dx, y + dy))
    label = font.render(text, TEXT_ANTIALIAS, color)
    screen.blit(label, (x, y))


def draw_logo_placeholder(screen, x, y, size, color):
    pygame.draw.rect(screen, color, (x, y, size, size), border_radius=int(size * 0.22), width=2)
    pygame.draw.line(screen, color, (x + 8, y + size // 2), (x + size - 8, y + size // 2), width=2)

def desaturate_color(color, amount=0.45):
    # Blend toward luminance to get a "muted" version, not flat gray.
    r, g, b = color
    lum = int(0.299 * r + 0.587 * g + 0.114 * b)
    return (
        int(r + (lum - r) * amount),
        int(g + (lum - g) * amount),
        int(b + (lum - b) * amount),
    )


def draw_taplist_static(
    screen,
    beers,
    logo_cache,
    theme,
    screen_w,
    screen_h,
    beer_font_path,
    info_font_path,
    header_font_path="fonts/WtfNewStrike.ttf",
    draw_panels=False,
    panel_color=(0, 0, 0),
    panel_border=(80, 80, 80),
):
    logo_size = theme.logo_size
    card_height = 130
    row_padding = 18
    column_count = 2
    logo_margin = 0
    accent = theme.accent
    dirty_rects = []

    global _HEADER_TEXT, _HEADER_THEME
    global _HEADER_POS

    hf_path = header_font_path or beer_font_path
    max_header_w = screen_w - 20

    if _HEADER_TEXT is None or _HEADER_THEME != (theme.name, hf_path):
        try:
            header_font = get_fitting_font("TAP LIST", max_header_w, hf_path, start_size=220, min_size=88)
            _HEADER_TEXT = NeonTextFX(
                font=header_font,
                text="TAP LIST",
                base_color=accent,
                outline_color=(255, 255, 255),
                shadow_color=(0, 0, 0),
                shadow_alpha=0,
                outline_px=0,
                shadow_offset=(0, 0),
                shimmer=False,
                wave=True,
                wave_amplitude=4,
                wave_wavelength=145,
                wave_speed=2.0,
                wave_step=2,
                bounce_phase_step=0.62,
                extrusion_px=0,
                pair_kerning={"TA": -16},
            )
            _HEADER_THEME = (theme.name, hf_path)
        except Exception as exc:
            print("Header text init failed:", exc)
            _HEADER_TEXT = None

    if _HEADER_TEXT:
        header_x = (screen_w - _HEADER_TEXT.base.get_width()) // 2
        header_h = _HEADER_TEXT.base.get_height()
    else:
        header_font = get_fitting_font("TAP LIST", max_header_w, hf_path, start_size=220, min_size=88)
        header_w = header_font.size("TAP LIST")[0]
        header_x = (screen_w - header_w) // 2
        header_h = header_font.get_height()

    rows = (len(beers) + 1) // 2
    if theme.name == "blue":
        list_h = rows * card_height + max(0, rows - 1) * row_padding
        header_gap = 20
        block_h = header_h + header_gap + list_h
        try:
            blue_block_offset = int(os.getenv("GK_BLUE_BLOCK_Y_OFFSET", "0"))
        except Exception:
            blue_block_offset = 0
        block_top = max(0, (screen_h - block_h) // 2 + blue_block_offset)
        header_y = block_top
        list_top = header_y + header_h + header_gap
    else:
        header_y = 18
        list_top = 160

    _HEADER_POS = (header_x, header_y)
    col_x = [20, screen_w // 2 + 16]

    for col in range(column_count):
        for idx in range(rows):
            # Row-major order to match editor layout:
            # 0=L row1, 1=R row1, 2=L row2, 3=R row2, ...
            beer_idx = idx * column_count + col
            if beer_idx >= len(beers):
                break

            beer = beers[beer_idx]
            top = list_top + idx * (card_height + row_padding)
            left = col_x[col]

            if draw_panels:
                card_rect = pygame.Rect(left - 8, top + 2, screen_w // 2 - 24, card_height - 4)
                pygame.draw.rect(screen, panel_color, card_rect, border_radius=14)
                pygame.draw.rect(screen, panel_border, card_rect, width=2, border_radius=14)
                dirty_rects.append(card_rect.copy())

            surf = logo_cache.get(beer.get("id"))
            logo_box_x = left + logo_margin
            logo_box_y = top + (card_height - logo_size) // 2
            logo_box_rect = pygame.Rect(logo_box_x, logo_box_y, logo_size, logo_size)

            if surf:
                logo_rect = surf.get_rect(center=logo_box_rect.center)
                screen.blit(surf, logo_rect)
                dirty_rects.append(logo_rect.copy())
            else:
                draw_logo_placeholder(screen, logo_box_x, logo_box_y, logo_size, accent)
                dirty_rects.append(logo_box_rect.copy())

            x_text = left + logo_margin + logo_size + 22
            spacing = 15
            max_text_width = (screen_w // 2 - 36) - (logo_margin + logo_size + 22) - 18

            brewery = beer["brewery"].upper()
            title = beer["title"].upper()
            full_name = f"{brewery} {title}"

            name_font = get_fitting_font(full_name, max_text_width, beer_font_path, start_size=72, min_size=22)

            sold_out = beer.get("soldOut", False)
            info_line = (
                "-TEMPORARILY SOLD OUT-"
                if sold_out
                else f"{beer['style'].upper()} - {beer['abv']}% ABV - "
                f"{beer['city'].upper()}, {beer['state'].upper()}"
            )
            info_font_fitted = get_fitting_font(
                info_line,
                max_text_width,
                info_font_path,
                start_size=32,
                min_size=12,
            )

            brewery_color = desaturate_color(theme.text_brewery) if sold_out else theme.text_brewery
            beer_color = desaturate_color(theme.text_beer) if sold_out else theme.text_beer
            info_color = desaturate_color(theme.text_info) if sold_out else theme.text_info

            brewery_surf = name_font.render(brewery, TEXT_ANTIALIAS, brewery_color)
            space_surf = name_font.render(" ", TEXT_ANTIALIAS, beer_color)
            title_surf = name_font.render(title, TEXT_ANTIALIAS, beer_color)
            info_surf = info_font_fitted.render(info_line, TEXT_ANTIALIAS, info_color)

            name_ascent = name_font.get_ascent()
            info_ascent = info_font_fitted.get_ascent()
            block_height = name_ascent + spacing + info_ascent
            block_top = top + (card_height - block_height) // 2

            x = x_text
            b_rect = screen.blit(brewery_surf, (x, block_top))
            dirty_rects.append(b_rect)
            x += brewery_surf.get_width()
            s_rect = screen.blit(space_surf, (x, block_top))
            dirty_rects.append(s_rect)
            x += space_surf.get_width()
            t_rect = screen.blit(title_surf, (x, block_top))
            dirty_rects.append(t_rect)

            if sold_out:
                strike_y = block_top + int(name_ascent * 0.55)
                strike_start = x_text
                strike_end = x_text + brewery_surf.get_width() + space_surf.get_width() + title_surf.get_width()
                pygame.draw.line(screen, beer_color, (strike_start, strike_y), (strike_end, strike_y), 3)
                dirty_rects.append(
                    pygame.Rect(
                        strike_start,
                        strike_y - 2,
                        max(1, strike_end - strike_start),
                        5,
                    )
                )

            info_x = x_text
            if sold_out:
                info_x = x_text + max(0, (max_text_width - info_surf.get_width()) // 2)
            i_rect = screen.blit(info_surf, (info_x, block_top + name_ascent + spacing))
            dirty_rects.append(i_rect)

    return dirty_rects
