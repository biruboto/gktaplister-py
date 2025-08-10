import os, shutil, subprocess, pygame

LOGO_FOLDER = "logos"
LOGO_CACHE_FOLDER = os.path.join(LOGO_FOLDER, "_cache")

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
        f"--export-width={box_px}",
        "--export-background-opacity=0",
        "--export-area-drawing"
    ])

def load_logo_surface(filename, box_px):
    full_path = os.path.join(LOGO_FOLDER, filename)
    base, ext = os.path.splitext(os.path.basename(filename))
    ext_lower = ext.lower()

    def fit(surface):
        w, h = surface.get_size()
        if w == 0 or h == 0:
            return None
        scale = min(box_px / w, box_px / h)
        new_size = (max(1,int(w*scale)), max(1,int(h*scale)))
        return pygame.transform.smoothscale(surface, new_size) if new_size != (w,h) else surface

    try:
        if ext_lower == ".svg":
            ensure_cache_dir()
            cached_png = os.path.join(LOGO_CACHE_FOLDER, f"{base}_{box_px}.png")
            svg_mtime = os.path.getmtime(full_path)
            need_regen = True
            if os.path.exists(cached_png):
                png_mtime = os.path.getmtime(cached_png)
                need_regen = svg_mtime > png_mtime + 0.0001
            if need_regen:
                rasterize_svg_to_cache(full_path, cached_png, box_px)
                os.utime(cached_png, None)
            surf = pygame.image.load(cached_png).convert_alpha()
            return surf  # important: no second resample for SVGs
        else:
            surf = pygame.image.load(full_path).convert_alpha()
            return fit(surf)
    except Exception as e:
        print(f"[logo] failed to load {filename}: {e}")
        return None

def build_logo_cache(beerdb, size):
    cache = {}
    for beer in beerdb:
        logo_file = beer.get("logoPath")
        if logo_file and logo_file not in cache:
            cache[logo_file] = load_logo_surface(logo_file, size)
    return cache
