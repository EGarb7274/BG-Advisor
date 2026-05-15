import json
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from recommender import load_comps


def test_load_comps_returns_list(tmp_path):
    data = [{"name": "Test Comp", "tier": 3, "tribes": ["Murloc"], "key_minions": ["Card A"]}]
    f = tmp_path / "comps.json"
    f.write_text(json.dumps(data))
    result = load_comps(f)
    assert len(result) == 1
    assert result[0]["name"] == "Test Comp"


def test_load_comps_returns_empty_on_missing_file(tmp_path):
    assert load_comps(tmp_path / "missing.json") == []


def test_load_comps_returns_empty_on_bad_json(tmp_path):
    f = tmp_path / "comps.json"
    f.write_text("not valid json {{")
    assert load_comps(f) == []


def test_load_comps_returns_empty_on_non_list_json(tmp_path):
    f = tmp_path / "comps.json"
    f.write_text(json.dumps({"not": "a list"}))
    assert load_comps(f) == []


from recommender import filter_comps

SAMPLE_COMPS = [
    {"name": "Murloc Flood",  "tier": 3, "tribes": ["Murloc"],         "key_minions": ["Warleader"]},
    {"name": "Mech Shields",  "tier": 3, "tribes": ["Mech"],           "key_minions": ["Deflecto"]},
    {"name": "Mech-Pirate",   "tier": 3, "tribes": ["Mech", "Pirate"], "key_minions": ["Navigator"]},
    {"name": "Dragon Value",  "tier": 2, "tribes": ["Dragon"],         "key_minions": ["Murozond"]},
]


def test_filter_returns_single_tribe_match():
    results = filter_comps(SAMPLE_COMPS, {"Murloc", "Dragon"})
    names = [c["name"] for c in results]
    assert "Murloc Flood" in names
    assert "Dragon Value" in names
    assert "Mech Shields" not in names
    assert "Mech-Pirate" not in names


def test_filter_multi_tribe_requires_all_tribes_active():
    results = filter_comps(SAMPLE_COMPS, {"Mech", "Pirate"})
    assert "Mech-Pirate" in [c["name"] for c in results]

    results = filter_comps(SAMPLE_COMPS, {"Mech"})
    assert "Mech-Pirate" not in [c["name"] for c in results]
    assert "Mech Shields" in [c["name"] for c in results]


def test_filter_sorted_by_tier_descending():
    results = filter_comps(SAMPLE_COMPS, {"Murloc", "Dragon"})
    tiers = [c["tier"] for c in results]
    assert tiers == sorted(tiers, reverse=True)


def test_filter_empty_active_tribes_returns_nothing():
    assert filter_comps(SAMPLE_COMPS, set()) == []


def test_filter_empty_comps_returns_nothing():
    assert filter_comps([], {"Murloc"}) == []
