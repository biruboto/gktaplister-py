# systems/logos.py — rsvg-only, fully headless
import os
import shutil
import subprocess
import tempfile
import pygame
from pathlib import Path
import xml.etree.ElementTree as ET
from systems.fetch import is_url, fetch_binary
from settings import SERVER_BASE
from urllib.parse import urlparse

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

def _logo_stem(logo: str) -> str:
    # Use the original filename (not the hashed cache path)
    if is_url(logo):
        name = Path(urlparse(logo).path).name
    else:
        name = Path(logo).name
    return Path(name).stem  # strip ".svg"

def ensure_cache_dir():
    os.makedirs(LOGO_CACHE_FOLDER, exist_ok=True)


def _force_color_on_el(el: ET.Element, hexcol: str, stroke_mode: str = "none"):
    """
    Force a solid theme color onto an element via both style="" and presentation attrs.
    stroke_mode: "none" (default) or "color" to set stroke = fill color.
    """
    el.set("fill", hexcol)
    el.set("stroke", "none" if stroke_mode == "none" else hexcol)

    style_str = el.get("style", "")
    style_parts = {}
    for part in style_str.split(";"):
        if ":" in part:
            k, v = part.split(":", 1)
            style_parts[k.strip().lower()] = v.strip()
    style_parts["fill"] = hexcol
    style_parts["stroke"] = "none" if stroke_mode == "none" else hexcol
    el.set("style", ";".join(f"{k}:{v}" for k, v in style_parts.items()))

    if el.get("fill", "").startswith("url("):
        el.set("fill", hexcol)
    if el.get("stroke", "").startswith("url("):
        el.set("stroke", "none" if stroke_mode == "none" else hexcol)

    if "class" in el.attrib:
        del el.attrib["class"]


def _rewrite_svg_with_color(src_svg: str, hexcol: str, stroke_mode: str = "none") -> str:
    """
    Make a temp SVG where every drawable element (and groups) is forced to hexcol.
    Returns path to the temp SVG file.
    """
    tree = ET.parse(src_svg)
    root = tree.getroot()

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
    Export SVG -> PNG at exact size using rsvg-convert (headless).
    If color_rgb is given, rewrite a temp SVG with that fill/stroke baked in first.
    """
    rsvg = shutil.which("rsvg-convert")
    if not rsvg:
        raise RuntimeError(
            "rsvg-convert not found. Install with: sudo apt install librsvg2-bin"
        )

    os.makedirs(os.path.dirname(out_png_path), exist_ok=True)

    src = svg_path
    if color_rgb is not None:
        hexcol = f"#{color_rgb[0]:02x}{color_rgb[1]:02x}{color_rgb[2]:02x}"
        tmp_svg = _rewrite_svg_with_color(svg_path, hexcol, stroke_mode="none")
        src = tmp_svg

    try:
        # -w: output width (px), aspect ratio preserved; -b none: transparent BG
        cmd = [rsvg, "-w", str(int(size_px)), "-b", "none", "-o", out_png_path, src]
        subprocess.run(cmd, check=True)
    finally:
        # Clean up temp if we made one
        if src != svg_path:
            try:
                os.unlink(src)
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
                rasterize_svg_to_cache(full_path, cached_png, box_px, color_rgb=color)
                os.utime(cached_png, None)

            surf = pygame.image.load(cached_png).convert_alpha()
            return surf

        # Bitmap path
        surf = pygame.image.load(full_path).convert_alpha()
        return _fit_bitmap(surf, box_px)

    except Exception as e:
        print(f"[logo] failed to load {filename}: {e}")
        return None


def build_logo_cache(beerdb: list[dict], size_px: int, theme):
    """
    Preload one Surface per beer. Pull SVGs from server if needed, rasterize to PNG cache,
    and return a dict keyed by beer['id'].
    """
    cache: dict[str, pygame.Surface] = {}
    fill_rgb = getattr(theme, "accent", None)

    for b in beerdb:
        beer_id = b.get("id")
        logo = b.get("logoPath")
        if not beer_id or not logo:
            continue

        # Resolve to a local SVG path first when possible; only fetch remote as fallback.
        local_candidates: list[Path] = []
        remote_url: str | None = None

        if is_url(logo):
            remote_url = logo
            parsed_path = urlparse(logo).path.lstrip("/")
            if parsed_path:
                local_candidates.append(Path(parsed_path))
                local_candidates.append(Path("logos") / Path(parsed_path).name)
        else:
            path_part = logo.lstrip("./").lstrip("/")
            if "/" not in path_part:
                path_part = f"logos/{path_part}"
            local_candidates.append(Path(path_part))
            remote_url = f"{SERVER_BASE.rstrip('/')}/{path_part}"

        svg_path: Path | None = None
        for cand in local_candidates:
            if cand.exists():
                svg_path = cand
                break

        if svg_path is None and remote_url:
            try:
                local_svg = fetch_binary(remote_url, subdir="logos")
                svg_path = Path(local_svg)
            except Exception as e:
                print(f"[logo] fetch failed {logo}: {e}")
                continue

        if svg_path is None:
            print(f"[logo] missing logo source for {logo}")
            continue

        # PNG cache name and render
        stem = _logo_stem(logo)
        cached_png = Path("logos/_cache") / f"{stem}_{theme.name}_{size_px}.png"

        cached_png.parent.mkdir(parents=True, exist_ok=True)

        if not cached_png.exists():
            rasterize_svg_to_cache(str(svg_path), str(cached_png), size_px, color_rgb=fill_rgb)

        surf = pygame.image.load(str(cached_png)).convert_alpha()
        cache[beer_id] = surf

    return cache
