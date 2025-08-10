# systems/logos.py
import os
import re
import shutil
import subprocess
import tempfile
import pygame

LOGO_FOLDER = "logos"
LOGO_CACHE_FOLDER = os.path.join(LOGO_FOLDER, "_cache")

def ensure_cache_dir():
    os.makedirs(LOGO_CACHE_FOLDER, exist_ok=True)

def inkscape_path():
    return shutil.which("inkscape")

def _hex(rgb):
    r, g, b = rgb
    return f"#{r:02x}{g:02x}{b:02x}"

def _colorize_svg_to_temp(svg_path: str, color_rgb: tuple[int,int,int]) -> str:
    """
    Create a temp SVG with fills/strokes changed to the given color.
    - We rewrite only explicit color values (hex/rgb), leave 'none' alone.
    - If a path had no fill/stroke specified, we'll also inject a CSS override.
    """
    with open(svg_path, "r", encoding="utf-8") as f:
        data = f.read()

    hexcol = _hex(color_rgb)

    # Replace explicit color values but DO NOT touch 'none'
    # fill="#xxxxxx"  or  fill="rgb(...)"
    data = re.sub(r'fill="(#[0-9A-Fa-f]{3,6}|rgb\([^)]+\))"',
                  f'fill="{hexcol}"', data)
    data = re.sub(r'stroke="(#[0-9A-Fa-f]{3,6}|rgb\([^)]+\))"',
                  f'stroke="{hexcol}"', data)

    # Also inject a CSS override to catch elements with default fills (black)
    # but preserve explicit 'fill="none"' via :not([fill="none"])
    # (Some SVG renderers ignore attribute selectors on presentation attrs, but Inkscape honors this.)
    style_tag = (
        "<style>"
        f"*{{color:{hexcol};}}"
        f'*:not([fill="none"]){{fill:{hexcol} !important;}}'
        f'*:not([stroke="none"]){{stroke:{hexcol} !important;}}'
        "</style>"
    )

    # Insert style right after opening <svg ...>
    m = re.search(r"<svg\b[^>]*>", data, flags=re.IGNORECASE)
    if m:
        insert_at = m.end()
        data = data[:insert_at] + style_tag + data[insert_at:]
    else:
        # Fallback: just prepend
        data = style_tag + data

    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".svg")
    with open(tmp.name, "w", encoding="utf-8") as f:
        f.write(data)
    return tmp.name

def rasterize_svg_to_cache(svg_path: str, out_png_path: str, size_px: int,
                           color_rgb: tuple[int,int,int] | None,
                           ):
    ink = inkscape_path()
    if not ink:
        raise RuntimeError("Inkscape not found in PATH")

    os.makedirs(os.path.dirname(out_png_path), exist_ok=True)

    # If a color is provided, make a temp colorized SVG
    svg_to_use = svg_path
    temp_created = False
    if color_rgb is not None:
        svg_to_use = _colorize_svg_to_temp(svg_path, color_rgb)
        temp_created = True

    try:
        subprocess.run([
            ink, svg_to_use,
            f"--export-width={size_px}",
            f"--export-filename={out_png_path}",
            "--export-type=png",
            "--export-background-opacity=0",
            "--export-area-drawing",
        ], check=True)
    finally:
        if temp_created and os.path.exists(svg_to_use):
            try:
                os.unlink(svg_to_use)
            except Exception:
                pass

def _fit_bitmap(surface: pygame.Surface, box_px: int) -> pygame.Surface | None:
    w, h = surface.get_size()
    if not w or not h:
        return None
    scale = min(box_px / w, box_px / h)
    new_size = (max(1, int(w*scale)), max(1, int(h*scale)))
    return pygame.transform.smoothscale(surface, new_size) if new_size != (w,h) else surface

def load_logo_surface(filename: str, box_px: int, theme=None) -> pygame.Surface | None:
    """
    Load a logo as a pygame Surface.
    - PNG/JPG: load and fit to box.
    - SVG: colorize to theme.accent (if theme given), rasterize to persistent cache:
        logos/_cache/<name>_<theme.name>_<box_px>.png
      If theme is None, file name is <name>_<box_px>.png
    """
    ensure_cache_dir()
    full_path = os.path.join(LOGO_FOLDER, filename)
    base, ext = os.path.splitext(os.path.basename(filename))
    ext_lower = ext.lower()

    try:
        if ext_lower == ".svg":
            # Theme-aware cache filename
            theme_tag = theme.name if theme else "default"
            cached_png = os.path.join(LOGO_CACHE_FOLDER, f"{base}_{theme_tag}_{box_px}.png")

            svg_mtime = os.path.getmtime(full_path)
            regenerate = True
            if os.path.exists(cached_png):
                png_mtime = os.path.getmtime(cached_png)
                regenerate = svg_mtime > png_mtime + 0.0001

            if regenerate:
                color = theme.accent if theme else None
                rasterize_svg_to_cache(full_path, cached_png, box_px, color_rgb=color)
                os.utime(cached_png, None)

            surf = pygame.image.load(cached_png).convert_alpha()
            return surf  # IMPORTANT: do not resample SVGs again
        else:
            # Bitmap path
            surf = pygame.image.load(full_path).convert_alpha()
            return _fit_bitmap(surf, box_px)
    except Exception as e:
        print(f"[logo] failed to load {filename}: {e}")
        return None

def build_logo_cache(beerdb: list[dict], size_px: int, theme) -> dict[str, pygame.Surface | None]:
    """Preload and cache one Surface per distinct logo file at the given size and theme."""
    cache: dict[str, pygame.Surface | None] = {}
    for beer in beerdb:
        logo_file = beer.get("logoPath")
        if logo_file and logo_file not in cache:
            cache[logo_file] = load_logo_surface(logo_file, size_px, theme=theme)
    return cache
