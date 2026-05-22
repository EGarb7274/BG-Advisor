import json
from pathlib import Path

COMBOS_PATH = Path(__file__).parent / "combos.json"


def load_combos(path: Path = COMBOS_PATH) -> list[dict]:
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        return data if isinstance(data, list) else []
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        return []


def filter_combos(combos: list[dict], active_tribes: set[str]) -> list[dict]:
    if not active_tribes:
        return []
    return [
        c for c in combos
        if set(c.get("tribes", [])).issubset(active_tribes)
    ]
