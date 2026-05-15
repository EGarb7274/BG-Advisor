import json
from pathlib import Path

COMPS_PATH = Path(__file__).parent / "comps.json"


def load_comps(path: Path = COMPS_PATH) -> list[dict]:
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        return data if isinstance(data, list) else []
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        return []


def filter_comps(comps: list[dict], active_tribes: set[str]) -> list[dict]:
    if not active_tribes:
        return []
    matching = [
        c for c in comps
        if set(c.get("tribes", [])).issubset(active_tribes)
    ]
    return sorted(matching, key=lambda c: c.get("tier", 0), reverse=True)
