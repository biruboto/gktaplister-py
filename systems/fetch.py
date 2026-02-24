import hashlib
import time
from pathlib import Path
from urllib.parse import urlparse

import requests

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

def fetch_text(url: str, ttl=15, timeout_s=10, allow_stale_on_error=True) -> Path:
    dest = _cache_path(url, "json", ".json")
    if dest.exists() and (time.time() - dest.stat().st_mtime) < ttl:
        return dest
    try:
        r = requests.get(url, timeout=timeout_s)
        r.raise_for_status()
    except Exception:
        if allow_stale_on_error and dest.exists():
            # Keep the display alive with stale data during temporary network/server failures.
            return dest
        raise
    dest.write_text(r.text, encoding="utf-8")
    return dest

def fetch_binary(url: str, subdir="assets", ttl=300, timeout_s=15) -> Path:
    dest = _cache_path(url, subdir, None)
    if dest.exists() and (time.time() - dest.stat().st_mtime) < ttl:
        return dest
    try:
        r = requests.get(url, timeout=timeout_s)
        r.raise_for_status()
    except Exception:
        if dest.exists():
            return dest
        raise
    dest.write_bytes(r.content)
    return dest
