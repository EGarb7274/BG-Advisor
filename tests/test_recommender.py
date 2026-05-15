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
