import json
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from combo_recommender import load_combos, filter_combos


SAMPLE_COMBOS = [
    {
        "cards": ["Lurking Leviathan", "Sewer Lord"],
        "tribes": ["Beast"],
        "tiers": [4, 3],
        "synergy": "Passive stacking.",
        "leads_to": "Beasts - Leviathan",
    },
    {
        "cards": ["Groundbreaker", "Darkcrest Strategist"],
        "tribes": ["Naga"],
        "tiers": [2, 3],
        "synergy": "Spell scaling.",
        "leads_to": "Nagas - Groundbreaker",
    },
    {
        "cards": ["Cataclysmic Harbinger", "Drakkari Enchanter"],
        "tribes": ["Neutral"],
        "tiers": [5, 3],
        "synergy": "End-of-turn doubling.",
        "leads_to": "Back to Back",
    },
]


def test_load_combos_returns_list(tmp_path):
    p = tmp_path / "combos.json"
    p.write_text(json.dumps(SAMPLE_COMBOS), encoding="utf-8")
    result = load_combos(p)
    assert isinstance(result, list)
    assert len(result) == 3


def test_load_combos_missing_file(tmp_path):
    assert load_combos(tmp_path / "missing.json") == []


def test_load_combos_invalid_json(tmp_path):
    p = tmp_path / "combos.json"
    p.write_text("not valid json {{", encoding="utf-8")
    assert load_combos(p) == []


def test_load_combos_non_list_json(tmp_path):
    p = tmp_path / "combos.json"
    p.write_text(json.dumps({"not": "a list"}), encoding="utf-8")
    assert load_combos(p) == []


def test_filter_combos_matching_tribe():
    result = filter_combos(SAMPLE_COMBOS, {"Beast"})
    assert len(result) == 1
    assert result[0]["leads_to"] == "Beasts - Leviathan"


def test_filter_combos_multiple_tribes():
    result = filter_combos(SAMPLE_COMBOS, {"Beast", "Naga", "Neutral"})
    assert len(result) == 3


def test_filter_combos_empty_tribes_returns_nothing():
    assert filter_combos(SAMPLE_COMBOS, set()) == []


def test_filter_combos_no_match():
    assert filter_combos(SAMPLE_COMBOS, {"Demon"}) == []


def test_filter_combos_empty_list():
    assert filter_combos([], {"Beast"}) == []
