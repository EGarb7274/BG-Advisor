import json
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from config import load_config, DEFAULT_CONFIG


def test_load_config_returns_defaults_when_file_missing(tmp_path):
    cfg = load_config(tmp_path / "config.json")
    assert cfg["hotkey_scan"] == "f8"
    assert cfg["hotkey_toggle"] == "f9"
    assert cfg["hotkey_calibrate"] == "shift+f8"
    assert cfg["opacity"] == 0.85
    assert cfg["crop_region"] is None


def test_load_config_reads_existing_values(tmp_path):
    cfg_file = tmp_path / "config.json"
    cfg_file.write_text(json.dumps({
        "hotkey_scan": "f6",
        "opacity": 0.5,
        "crop_region": [100, 200, 300, 400]
    }))
    cfg = load_config(cfg_file)
    assert cfg["hotkey_scan"] == "f6"
    assert cfg["opacity"] == 0.5
    assert cfg["crop_region"] == [100, 200, 300, 400]


def test_load_config_merges_missing_keys_with_defaults(tmp_path):
    cfg_file = tmp_path / "config.json"
    cfg_file.write_text(json.dumps({"hotkey_scan": "f6"}))
    cfg = load_config(cfg_file)
    assert cfg["hotkey_scan"] == "f6"
    assert cfg["opacity"] == 0.85


def test_load_config_returns_defaults_on_bad_json(tmp_path):
    cfg_file = tmp_path / "config.json"
    cfg_file.write_text("not valid json {{")
    cfg = load_config(cfg_file)
    assert cfg["hotkey_scan"] == "f8"


from config import save_config


def test_save_config_writes_json_file(tmp_path):
    cfg_file = tmp_path / "config.json"
    save_config({"hotkey_scan": "f6", "crop_region": [10, 20, 300, 400]}, cfg_file)
    data = json.loads(cfg_file.read_text())
    assert data["hotkey_scan"] == "f6"
    assert data["crop_region"] == [10, 20, 300, 400]


def test_save_config_creates_parent_dirs(tmp_path):
    cfg_file = tmp_path / "subdir" / "config.json"
    save_config({"opacity": 0.7}, cfg_file)
    assert cfg_file.exists()
    assert json.loads(cfg_file.read_text())["opacity"] == 0.7
