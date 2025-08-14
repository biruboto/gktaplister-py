# systems/logos.py
import os
import shutil
import subprocess
import tempfile
import pygame
import sys
from pathlib import Path
import xml.etree.ElementTree as ET
from systems.fetch import is_url, fetch_binary
from settings import SERVER_BASE
from urllib.parse import urljoin

LOGO_FOLDER = "logos"
LOGO_CACHE_FOLDER = os.path.join(LOGO_FOLDER, "_cache")

SVG_NS = "http://www.w3.org/2000/svg"
ET.register_namespace("", SVG_NS)

# Tags we consider "drawable" and will force color on
_DRAW_TAGS = {
    f"{{{SVG_NS}}}{t}" for t in [
        "path", "rect", "circle", "ellipse",
        "polygon", "polyline", "line", "text"
    ]
}
_GROUP_TAG = f"{{{SVG_NS}}}g"


def ensure_cache_dir():
    os.makedirs(LOGO_CACHE_FOLDER, exist_ok=True)

def inkscape_path():
    # Prefer console binary on Windows to avoid GUI popups
    if os.name == "nt":
        p = shutil.which("inkscape.com")
        if p: return p
    return shutil.which("inkscape")

# Small helper to run Inkscape headlessly on Windows
def run_inkscape(cmd):
    if os.name == "nt":
        CREATE_NO_WINDOW = 0x08000000
        return subprocess.run(cmd, check=True, creationflags=CREATE_NO_WINDOW)
    else:
        return subprocess.run(cmd, check=True)

def run_inkscape(cmd):
    if os.name == "nt":
        CREATE_NO_WINDOW = 0x08000000
        return subprocess.run(cmd, check=True, creationflags=CREATE_NO_WINDOW)
    else:
        return subprocess.run(cmd, check=True)


def _force_color_on_el(el: ET.Element, hexcol: str, stroke_mode: str = "none"):
    """
    Force a solid theme color onto an element via both style="" and presentation attrs.
    stroke_mode: "none" (default) or "color" to set stroke = fill color.
    """
    # Override presentation attributes
    el.set("fill", hexcol)
    el.set("stroke", "none" if stroke_mode == "none" else hexcol)

    # Normalize/override style=""
    style_str = el.get("style", "")
    style_parts = {}
    for part in style_str.split(";"):
        if ":" in part:
            k, v = part.split(":", 1)
            style_parts[k.strip().lower()] = v.strip()
    style_parts["fill"] = hexcol
    style_parts["stroke"] = "none" if stroke_mode == "none" else hexcol
    el.set("style", ";".join(f"{k}:{v}" for k, v in style_parts.items()))

    # Kill gradients like url(#grad)
    if el.get("fill", "").startswith("url("):
        el.set("fill", hexcol)
    if el.get("stroke", "").startswith("url("):
        el.set("stroke", "none" if stroke_mode == "none" else hexcol)

    # Remove classes so CSS can't override later (defensive)
    if "class" in el.attrib:
        del el.attrib["class"]


def _rewrite_svg_with_color(src_svg: str, hexcol: str, stroke_mode: str = "none") -> str:
    """
    Make a temp SVG where every drawable element (and groups) is forced to hexcol.
    Returns path to the temp SVG file.
    """
    tree = ET.parse(src_svg)
    root = tree.getroot()

    # Walk and force color on drawables and groups (groups so inheritance is covered)
    for el in root.iter():
        tag = el.tag
        if tag in _DRAW_TAGS or tag == _GROUP_TAG:
            _force_color_on_el(el, hexcol, stroke_mode)

    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".svg")
    tree.write(tmp.name, encoding="utf-8", xml_declaration=True)
    tmp.close()
    return tmp.name


def rasterize_svg_to_cache(svg_path: str, out_png_path: str, size_px: int,
                           color_rgb: tuple[int, int, int] | None):
    """
    Export SVG -> PNG at exact size.
    If color_rgb is given, rewrite a temp SVG with that fill/stroke baked in, then export.
    """
    ink = inkscape_path()
    if not ink:
        raise RuntimeError("Inkscape not found in PATH")

    os.makedirs(os.path.dirname(out_png_path), exist_ok=True)

    if color_rgb is None:
        # Export as-is
        run_inkscape([
            ink, svg_path,
            "--batch-process",
            "--export-type=png",
            f"--export-filename={out_png_path}",
            f"--export-width={size_px}",
            "--export-background-opacity=0",
            "--export-area-drawing",
        ])
        return

    # Color path
    hexcol = f"#{color_rgb[0]:02x}{color_rgb[1]:02x}{color_rgb[2]:02x}"
    tmp_svg = _rewrite_svg_with_color(svg_path, hexcol, stroke_mode="none")
    try:
        run_inkscape([
            ink, tmp_svg,
            "--batch-process",
            "--export-type=png",
            f"--export-filename={out_png_path}",
            f"--export-width={size_px}",
            "--export-background-opacity=0",
            "--export-area-drawing",
        ])
    finally:
        try:
            os.unlink(tmp_svg)
        except Exception:
            pass

def _fit_bitmap(surface: pygame.Surface, box_px: int) -> pygame.Surface | None:
    w, h = surface.get_size()
    if not w or not h:
        return None
    scale = min(box_px / w, box_px / h)
    new_size = (max(1, int(w * scale)), max(1, int(h * scale)))
    return pygame.transform.smoothscale(surface, new_size) if new_size != (w, h) else surface


def load_logo_surface(filename: str, box_px: int, theme=None) -> pygame.Surface | None:
    """
    Load a logo Surface.
      - SVG: colorize to theme.accent, cache at logos/_cache/<name>_<theme>_<size>.png
             (no Python resample afterward)
      - PNG/JPG: load and fit to box
    """
    ensure_cache_dir()
    full_path = os.path.join(LOGO_FOLDER, filename)
    base, ext = os.path.splitext(os.path.basename(filename))
    ext_lower = ext.lower()

    try:
        if ext_lower == ".svg":
            theme_tag = theme.name if theme else "default"
            cached_png = os.path.join(LOGO_CACHE_FOLDER, f"{base}_{theme_tag}_{box_px}.png")

            svg_mtime = os.path.getmtime(full_path)
            regenerate = True
            if os.path.exists(cached_png):
                png_mtime = os.path.getmtime(cached_png)
                regenerate = svg_mtime > png_mtime + 0.0001

            if regenerate:
                color = theme.accent if theme else None
                # Debug (optional): print("[logo] rasterize", filename, "color:", color, "->", cached_png)
                rasterize_svg_to_cache(full_path, cached_png, box_px, color_rgb=color)
                os.utime(cached_png, None)

            surf = pygame.image.load(cached_png).convert_alpha()
            return surf  # IMPORTANT: no second resample for SVGs

        # Bitmap path
        surf = pygame.image.load(full_path).convert_alpha()
        return _fit_bitmap(surf, box_px)

    except Exception as e:
        print(f"[logo] failed to load {filename}: {e}")
        return None


def build_logo_cache(beerdb: list[dict], size_px: int, theme):
    """
    Preload one Surface per beer. Assumes your existing rasterize flow:
    - you have something like rasterize_svg_to_cache(svg_path, out_png_path, size_px, color_rgb=theme.accent)
    - you load the resulting PNG into pygame and store by beer['id']
    """
    cache: dict[str, pygame.Surface] = {}
    fill_rgb = getattr(theme, "accent", None)

    for b in beerdb:
        beer_id = b.get("id")
        logo = b.get("logoPath")
        if not beer_id or not logo:
            continue

        # --- NEW: resolve remote/local to a local svg path ---
        if is_url(logo):
            remote_url = logo
        else:
            # Strip leading ./ or / just in case
            path_part = logo.lstrip("./").lstrip("/")
            # If it’s just a filename (no slash), serve it from /logos/
            if "/" not in path_part:
                path_part = f"logos/{path_part}"
            remote_url = f"{SERVER_BASE.rstrip('/')}/{path_part}"

        print("[logo fetch]", remote_url)  # <- remove later if noisy
        local_svg = fetch_binary(remote_url, subdir="logos")
        svg_path = Path(local_svg)

        # --- your existing PNG cache naming/export/load flow below ---
        stem = svg_path.stem
        cached_png = Path("logos/_cache") / f"{stem}_{theme.name}_{size_px}.png"
        cached_png.parent.mkdir(parents=True, exist_ok=True)

        # Regenerate if missing (keep your existing mtime logic if you have it)
        if not cached_png.exists():
            rasterize_svg_to_cache(str(svg_path), str(cached_png), size_px, color_rgb=fill_rgb)

        surf = pygame.image.load(str(cached_png)).convert_alpha()
        cache[beer_id] = surf

    return cache
