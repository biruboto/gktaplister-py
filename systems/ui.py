import math, pygame

# cache for header logo across frames
_HEADER_TEXT = None
_HEADER_THEME = None

WHITE = (255,255,255)

# --- NeonTextFX v2: outline + shadow + MASKED shimmer ---
import math, pygame

class NeonTextFX:
    def __init__(self, font: pygame.font.Font, text: str,
                 base_color=(255,255,255),
                 outline_color=(255,255,255),
                 shadow_color=(0,0,0), shadow_alpha=140,
                 outline_px=2, shadow_offset=(3,4),
                 shimmer=True, shimmer_speed=90,          # px/sec
                 shimmer_color=None):                     # defaults to base_color
        # Render base white (keeps edges crisp)
        base_white = font.render(text, True, (255,255,255)).convert_alpha()
        tw, th = base_white.get_size()
        pad = max(2, outline_px + 2)
        self.pad = pad
        self.text_w, self.text_h = tw, th

        # Colorize base to chosen color
        base = base_white.copy()
        base.fill((*base_color,255), special_flags=pygame.BLEND_RGBA_MULT)
        self.base = base

        # Outline (mask dilate)
        mask = pygame.mask.from_surface(base_white)
        outline = pygame.Surface((tw + pad*2, th + pad*2), pygame.SRCALPHA).convert_alpha()
        offsets = [(dx,dy) for dx in range(-outline_px, outline_px+1)
                            for dy in range(-outline_px, outline_px+1)
                            if dx*dx+dy*dy <= outline_px*outline_px]
        stamp = mask.to_surface(setcolor=(255,255,255,255), unsetcolor=(0,0,0,0)).convert_alpha()
        for dx, dy in offsets:
            outline.blit(stamp, (pad+dx, pad+dy))
        outline.fill((*outline_color,255), special_flags=pygame.BLEND_RGBA_MULT)
        self.outline = outline

        # Shadow (reuse outline)
        shadow = outline.copy()
        shadow.fill((*shadow_color,255), special_flags=pygame.BLEND_RGBA_MULT)
        shadow.set_alpha(shadow_alpha)
        self.shadow = shadow
        self.shadow_offset = shadow_offset

        # ---- MASKED SHIMMER SETUP ----
        self.shimmer = shimmer
        self.shimmer_speed = shimmer_speed  # pixels per second

        # Build a vertical white gradient bar then rotate it a bit (e.g., 20°)
        stripe_w = 12
        bar = pygame.Surface((stripe_w, th * 2), pygame.SRCALPHA).convert_alpha()
        for x in range(stripe_w):
            t = 1.0 - abs((x - (stripe_w-1)/2) / max(1, (stripe_w-1)/2))
            a = int(220 * (t*t))  # bright center
            pygame.draw.line(bar, (255, 255, 255, a), (x, 0), (x, th * 2 - 1))

        self.stripe = pygame.transform.rotate(bar, -20)  # slight diagonal
        self.mask_surf = mask.to_surface(setcolor=(255,255,255,255), unsetcolor=(0,0,0,0)).convert_alpha()
        self.sweep = pygame.Surface((tw, th), pygame.SRCALPHA).convert_alpha()

        # internal timer for smooth motion (don’t rely on external t)
        self._span = tw + self.stripe.get_width()
        self._phase_px = 0.0
        self._last_ticks = pygame.time.get_ticks()


        # Precompute a glyph mask surface we can use to clip the shimmer
        self.mask_surf = mask.to_surface(setcolor=(255,255,255,255), unsetcolor=(0,0,0,0)).convert_alpha()
        # A per-frame scratch buffer for the masked sweep (same size as text)
        self.sweep = pygame.Surface((tw, th), pygame.SRCALPHA).convert_alpha()

    def draw(self, screen, x, y, t_seconds=None):  # t_seconds ignored; we self-time
            # 1) shadow & outline
        screen.blit(self.shadow, (x - self.pad + self.shadow_offset[0],
                                y - self.pad + self.shadow_offset[1]))
        screen.blit(self.outline, (x - self.pad, y - self.pad))

        # 2) base text (solid)
        screen.blit(self.base, (x, y))

        # 3) masked shimmer ON TOP (smooth internal timing)
        if self.shimmer:
            now = pygame.time.get_ticks()
            dt = (now - self._last_ticks) / 1000.0
            self._last_ticks = now
            self._phase_px = (self._phase_px + self.shimmer_speed * dt) % self._span

            self.sweep.fill((0, 0, 0, 0))
            pos_x = int(self._phase_px) - self.stripe.get_width()
            # slight vertical offset so the diagonal bar covers the text height
            pos_y = -self.stripe.get_height() // 4
            self.sweep.blit(self.stripe, (pos_x, pos_y))
            # clip to glyphs
            self.sweep.blit(self.mask_surf, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
            # overlay normally (alpha) so it’s visible over any color
            screen.blit(self.sweep, (x, y))


# --- end NeonTextFX v2 ---

def get_font(size, font_path=None, fallback=None):
    try:
        if font_path:
            return pygame.font.Font(font_path, size)
        return pygame.font.SysFont(fallback or pygame.font.get_default_font(), size)
    except Exception as e:
        print("Font error, using default:", e)
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
            if dx*dx + dy*dy < glow_size*glow_size:
                glow = font.render(text, True, color)
                glow.set_alpha(36)
                screen.blit(glow, (x + dx, y + dy))
    label = font.render(text, True, color)
    screen.blit(label, (x, y))

def draw_logo_placeholder(screen, x, y, size, color):
    pygame.draw.rect(screen, color, (x, y, size, size),
                     border_radius=int(size * 0.22), width=2)
    pygame.draw.line(screen, color, (x+8, y+size//2), (x+size-8, y+size//2), width=2)

def draw_taplist(screen, beers, logo_cache, theme, screen_w, screen_h,
                 beer_font_path, info_font_path, header_font_path="fonts/WtfNewStrike.ttf"):
    LOGO_SIZE = theme.logo_size
    CARD_HEIGHT = 130
    ROW_PADDING = 18
    COLUMN_COUNT = 2
    LOGO_MARGIN = 0
    DIM_WHITE = theme.dim_white
    ACCENT = theme.accent

    global _HEADER_TEXT, _HEADER_THEME

    # pick the header font path (fallback to beer font if None)
    hf_path = header_font_path or beer_font_path
    max_header_w = screen_w - 62 - 20  # left margin 62, ~20px right padding

    # rebuild cached header text if theme or font path changed
    if _HEADER_TEXT is None or _HEADER_THEME != (theme.name, hf_path):
        try:
            header_font = get_fitting_font("TAP LIST", max_header_w, hf_path, start_size=88, min_size=32)
            _HEADER_TEXT = NeonTextFX(
                font=header_font,
                text="TAP LIST",
                base_color=ACCENT,                # theme accent (red/blue)
                outline_color=(255,255,255),
                shadow_color=(0,0,0), shadow_alpha=140,
                outline_px=2, shadow_offset=(3,4),
                shimmer=True, shimmer_speed=90,
                # Or try a gradient fill:
                # use_gradient=True, grad_top=(255,220,220), grad_bottom=ACCENT,
            )
            _HEADER_THEME = (theme.name, hf_path)
        except Exception as e:
            print("Header text init failed:", e)
            _HEADER_TEXT = None

    # draw header
    t_seconds = pygame.time.get_ticks() / 1000.0
    if _HEADER_TEXT:
        _HEADER_TEXT.draw(screen, 62, 30, t_seconds)
    else:
        # fallback uses the same header font path so you still get the custom font
        header_font = get_fitting_font("TAP LIST", max_header_w, hf_path, start_size=88, min_size=32)
        draw_neon_text(screen, "TAP LIST", 62, 30, header_font, ACCENT, 16)



    cards_per_col = (len(beers) + 1) // 2
    col_x = [20, screen_w // 2 + 16]

    for col in range(COLUMN_COUNT):
        for idx in range(cards_per_col):
            beer_idx = col * cards_per_col + idx
            if beer_idx >= len(beers):
                break
            beer = beers[beer_idx]
            top = 160 + idx * (CARD_HEIGHT + ROW_PADDING)
            left = col_x[col]

            # Logo
            surf = logo_cache.get(beer.get("id"))
            logo_box_x = left + LOGO_MARGIN
            logo_box_y = top + (CARD_HEIGHT - LOGO_SIZE) // 2
            logo_box_rect = pygame.Rect(logo_box_x, logo_box_y, LOGO_SIZE, LOGO_SIZE)

            if surf:
                logo_rect = surf.get_rect(center=logo_box_rect.center)
                screen.blit(surf, logo_rect)
            else:
                draw_logo_placeholder(screen, logo_box_x, logo_box_y, LOGO_SIZE, ACCENT)

            # Text
            x_text = left + LOGO_MARGIN + LOGO_SIZE + 22
            SPACING = 15
            max_text_width = (screen_w // 2 - 36) - (LOGO_MARGIN + LOGO_SIZE + 22) - 18

            brewery = beer['brewery'].upper()
            title   = beer['title'].upper()
            full_name = f"{brewery} {title}"

            # Fit one font for the whole line so combined width fits
            name_font = get_fitting_font(full_name, max_text_width, beer_font_path,
                                         start_size=72, min_size=22)

            info_line = f"{beer['style'].upper()} – {beer['abv']}% ABV – {beer['city'].upper()}, {beer['state'].upper()}"
            info_font_fitted = get_fitting_font(info_line, max_text_width, info_font_path,
                                                start_size=32, min_size=12)

            # Render brewery + beer name in different theme shades
            brewery_surf = name_font.render(brewery, True, theme.text_brewery)
            space_surf   = name_font.render(" ", True, theme.text_beer)
            title_surf   = name_font.render(title, True, theme.text_beer)

            info_surf = info_font_fitted.render(info_line, True, theme.text_info)

            name_ascent = name_font.get_ascent()
            info_ascent = info_font_fitted.get_ascent()
            block_height = name_ascent + SPACING + info_ascent
            block_top = top + (CARD_HEIGHT - block_height) // 2

            x = x_text
            screen.blit(brewery_surf, (x, block_top));  x += brewery_surf.get_width()
            screen.blit(space_surf,   (x, block_top));  x += space_surf.get_width()
            screen.blit(title_surf,   (x, block_top))

            screen.blit(info_surf, (x_text, block_top + name_ascent + SPACING))
