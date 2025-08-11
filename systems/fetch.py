from pathlib import Path
from urllib.parse import urlparse, urljoin
import requests, hashlib, time

def is_url(s: str) -> bool:
    try:
        return urlparse(s).scheme in ("http", "https")
    except Exception:
        return False

CACHE_ROOT = Path(".cache_remote")
CACHE_ROOT.mkdir(exist_ok=True)

def _cache_path(url: str, subdir: str, ext_hint: str | None = None) -> Path:
    h = hashlib.sha1(url.encode("utf-8")).hexdigest()[:16]
    name = Path(urlparse(url).path).name or "file"
    if ext_hint and not name.lower().endswith(ext_hint):
        name += ext_hint
    p = CACHE_ROOT / subdir
    p.mkdir(parents=True, exist_ok=True)
    return p / f"{h}_{name}"

def fetch_text(url: str, ttl=15) -> Path:
    dest = _cache_path(url, "json", ".json")
    if dest.exists() and (time.time() - dest.stat().st_mtime) < ttl:
        return dest
    r = requests.get(url, timeout=10)
    r.raise_for_status()
    dest.write_text(r.text, encoding="utf-8")
    return dest

def fetch_binary(url: str, subdir="assets", ttl=300) -> Path:
    dest = _cache_path(url, subdir, None)
    if dest.exists() and (time.time() - dest.stat().st_mtime) < ttl:
        return dest
    r = requests.get(url, timeout=15)
    r.raise_for_status()
    dest.write_bytes(r.content)
    return dest
