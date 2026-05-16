import re
import json
import logging
import urllib.request
import urllib.error

logger = logging.getLogger(__name__)

BASE_URL = "https://hsbg.cards"
_API_BASE = f"{BASE_URL}/api/v1/cards"

_cache: dict[str, dict | None] = {}


def slugify(name: str) -> str:
    s = name.lower()
    s = re.sub(r"[',\.]", "", s)
    s = re.sub(r"[^a-z0-9]+", "-", s)
    return s.strip("-")


def fetch_card(name: str) -> dict | None:
    slug = slugify(name)
    if slug in _cache:
        return _cache[slug]
    try:
        url = f"{_API_BASE}/{slug}"
        req = urllib.request.Request(url, headers={"Accept": "application/json"})
        with urllib.request.urlopen(req, timeout=6) as r:
            data = json.loads(r.read())
        card = data.get("data")
        _cache[slug] = card
        return card
    except urllib.error.HTTPError as e:
        if e.code != 404:
            logger.warning(f"API error for '{name}' (slug: {slug}): {e}")
        _cache[slug] = None
        return None
    except Exception as e:
        logger.warning(f"Failed to fetch card '{name}': {e}")
        return None


def fetch_image_bytes(path: str) -> bytes | None:
    try:
        with urllib.request.urlopen(BASE_URL + path, timeout=10) as r:
            return r.read()
    except Exception as e:
        logger.warning(f"Failed to fetch image '{path}': {e}")
        return None
