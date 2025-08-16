import pygame

WHITE = (255,255,255)

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
                 beer_font_path, info_font_path):
    LOGO_SIZE = theme.logo_size
    CARD_HEIGHT = 130
    ROW_PADDING = 18
    COLUMN_COUNT = 2
    LOGO_MARGIN = 0
    DIM_WHITE = theme.dim_white
    ACCENT = theme.accent

    header_font = get_font(88, None)
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
            full_name = f"{beer['brewery']} {beer['title']}".upper()
            max_text_width = (screen_w // 2 - 36) - (LOGO_MARGIN + LOGO_SIZE + 22) - 18

            name_font = get_fitting_font(full_name, max_text_width, beer_font_path, start_size=72, min_size=22)
            info_line = f"{beer['style'].upper()} – {beer['abv']}% ABV – {beer['city'].upper()}, {beer['state'].upper()}"
            info_font_fitted = get_fitting_font(info_line, max_text_width, info_font_path, start_size=32, min_size=12)

            name_surf = name_font.render(full_name, True, WHITE)
            info_surf = info_font_fitted.render(info_line, True, DIM_WHITE)

            name_ascent = name_font.get_ascent()
            info_ascent = info_font_fitted.get_ascent()
            block_height = name_ascent + SPACING + info_ascent
            block_top = top + (CARD_HEIGHT - block_height) // 2

            screen.blit(name_surf, (x_text, block_top))
            screen.blit(info_surf, (x_text, block_top + name_ascent + SPACING))
