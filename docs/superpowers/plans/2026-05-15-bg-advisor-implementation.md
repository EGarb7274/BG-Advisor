# BG-Advisor Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a Windows overlay that OCR-scans Hearthstone Battlegrounds tribe panels on hotkey press and recommends endgame compositions in a semi-transparent always-on-top PyQt6 window.

**Architecture:** Five focused modules — `config.py` manages persistent settings, `recommender.py` is pure logic filtering `comps.json`, `ocr.py` handles screenshot→crop→winrt OCR→fuzzy matching, `overlay.py` owns all PyQt6 UI (tribe chips + comp list + error banner), and `main.py` wires hotkeys to the pipeline.

**Tech Stack:** Python 3.11+, PyQt6, Pillow, keyboard, winsdk (winrt), pytest, difflib (stdlib)

---

## File Map

| File | Responsibility |
|---|---|
| `requirements.txt` | Pinned dependencies |
| `config.py` | Load/save `config.json` with defaults |
| `recommender.py` | Load `comps.json`, filter comps by active tribes, sort by tier |
| `ocr.py` | Screenshot, crop, winrt OCR, fuzzy tribe matching |
| `overlay.py` | All PyQt6 UI: tribe chip panel, comp list, error banner |
| `calibrate.py` | Fullscreen crosshair selector for crop region |
| `main.py` | Entry point: hotkeys, wires OCR → overlay → recommender |
| `comps.json` | Comp database (manually maintained) |
| `config.json` | User config (auto-created with defaults on first run) |
| `bg.log` | Error/event log (auto-created) |
| `tests/test_config.py` | Unit tests for config module |
| `tests/test_recommender.py` | Unit tests for recommender module |
| `tests/test_ocr.py` | Unit tests for OCR module (winrt mocked) |

---

### Task 1: Environment Setup

**Files:**
- Create: `requirements.txt`
- Create: `tests/__init__.py`

- [ ] **Step 1: Create requirements.txt**

```
PyQt6>=6.6.0
Pillow>=10.0.0
keyboard>=0.13.5
winsdk>=1.0.0b10
pytest>=8.0.0
```

- [ ] **Step 2: Install dependencies**

Run: `pip install -r requirements.txt`
Expected: All packages install without errors. Verify with `python -c "import PyQt6, PIL, keyboard, winrt; print('OK')"`.

- [ ] **Step 3: Create tests directory**

```bash
mkdir tests
touch tests/__init__.py
```

- [ ] **Step 4: Commit**

```bash
git add requirements.txt tests/__init__.py
git commit -m "chore: project setup and dependencies"
```

---

### Task 2: Seed comps.json

**Files:**
- Create: `comps.json`

- [ ] **Step 1: Create comps.json**

```json
[
  {
    "name": "Murloc Flood",
    "tier": 3,
    "tribes": ["Murloc"],
    "key_minions": ["Murloc Warleader", "Toxfin", "Old Murk-Eye", "Tidecaller"]
  },
  {
    "name": "Mech Divine Shield",
    "tier": 3,
    "tribes": ["Mech"],
    "key_minions": ["Deflecto Bot", "Kangor's Apprentice", "Zilliax Deluxe"]
  },
  {
    "name": "Dragon Scaling",
    "tier": 3,
    "tribes": ["Dragon"],
    "key_minions": ["Murozond", "Kalecgos", "Nadina the Red"]
  },
  {
    "name": "Mech-Pirate Menace",
    "tier": 3,
    "tribes": ["Mech", "Pirate"],
    "key_minions": ["Navigator", "Salty Looter", "Deflecto Bot"]
  },
  {
    "name": "Pirate Aggro",
    "tier": 2,
    "tribes": ["Pirate"],
    "key_minions": ["Peggy Brittlebone", "Yohoho", "Soulsplitter"]
  },
  {
    "name": "Elemental Tavern",
    "tier": 2,
    "tribes": ["Elemental"],
    "key_minions": ["Nomi Kitchen Nightmare", "Lil Rag", "Tavern Tempest"]
  },
  {
    "name": "Quillboar Gems",
    "tier": 2,
    "tribes": ["Quillboar"],
    "key_minions": ["Aggem Thorncurse", "Bristleback Knight", "Roadboar"]
  },
  {
    "name": "Undead Value",
    "tier": 2,
    "tribes": ["Undead"],
    "key_minions": ["Titus Rivendare", "Baron Rivendare", "Recurring Nightmare"]
  },
  {
    "name": "Naga Spell Synergy",
    "tier": 2,
    "tribes": ["Naga"],
    "key_minions": ["Viper", "Tarecgosa", "Coilfang Constrictor"]
  },
  {
    "name": "Beast Buddy",
    "tier": 2,
    "tribes": ["Beast"],
    "key_minions": ["Mama Bear", "Pack Leader", "Bannerboar"]
  },
  {
    "name": "Demon Warlock",
    "tier": 2,
    "tribes": ["Demon"],
    "key_minions": ["Wrath Weaver", "Soul Juggler", "Mal'Ganis"]
  }
]
```

- [ ] **Step 2: Commit**

```bash
git add comps.json
git commit -m "data: seed comps.json with initial comp data"
```

---

### Task 3: Config Module — Load

**Files:**
- Create: `config.py`
- Create: `tests/test_config.py`

- [ ] **Step 1: Write failing tests**

```python
# tests/test_config.py
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
    # Provided key overrides default
    assert cfg["hotkey_scan"] == "f6"
    # Missing keys fall back to defaults
    assert cfg["opacity"] == 0.85


def test_load_config_returns_defaults_on_bad_json(tmp_path):
    cfg_file = tmp_path / "config.json"
    cfg_file.write_text("not valid json {{")
    cfg = load_config(cfg_file)
    assert cfg["hotkey_scan"] == "f8"
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_config.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'config'`

- [ ] **Step 3: Implement config.py**

```python
# config.py
import json
from pathlib import Path

CONFIG_PATH = Path(__file__).parent / "config.json"

DEFAULT_CONFIG: dict = {
    "hotkey_scan": "f8",
    "hotkey_toggle": "f9",
    "hotkey_calibrate": "shift+f8",
    "crop_region": None,
    "opacity": 0.85,
}


def load_config(path: Path = CONFIG_PATH) -> dict:
    if not path.exists():
        return dict(DEFAULT_CONFIG)
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        cfg = dict(DEFAULT_CONFIG)
        cfg.update(data)
        return cfg
    except (json.JSONDecodeError, OSError):
        return dict(DEFAULT_CONFIG)
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/test_config.py -v`
Expected: PASS (4 tests)

- [ ] **Step 5: Commit**

```bash
git add config.py tests/test_config.py
git commit -m "feat: config load with defaults and merge"
```

---

### Task 4: Config Module — Save

**Files:**
- Modify: `config.py`
- Modify: `tests/test_config.py`

- [ ] **Step 1: Write failing tests**

Add to `tests/test_config.py`:

```python
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
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_config.py::test_save_config_writes_json_file -v`
Expected: FAIL with `ImportError: cannot import name 'save_config'`

- [ ] **Step 3: Add save_config to config.py**

Append to `config.py`:

```python
def save_config(cfg: dict, path: Path = CONFIG_PATH) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(cfg, f, indent=2)
```

- [ ] **Step 4: Run all config tests**

Run: `pytest tests/test_config.py -v`
Expected: PASS (6 tests)

- [ ] **Step 5: Commit**

```bash
git add config.py tests/test_config.py
git commit -m "feat: config save_config"
```

---

### Task 5: Recommender — Load Comps

**Files:**
- Create: `recommender.py`
- Create: `tests/test_recommender.py`

- [ ] **Step 1: Write failing tests**

```python
# tests/test_recommender.py
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
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_recommender.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'recommender'`

- [ ] **Step 3: Implement recommender.py**

```python
# recommender.py
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
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/test_recommender.py -v`
Expected: PASS (4 tests)

- [ ] **Step 5: Commit**

```bash
git add recommender.py tests/test_recommender.py
git commit -m "feat: recommender load_comps"
```

---

### Task 6: Recommender — Filter and Sort

**Files:**
- Modify: `recommender.py`
- Modify: `tests/test_recommender.py`

- [ ] **Step 1: Write failing tests**

Add to `tests/test_recommender.py`:

```python
from recommender import filter_comps

SAMPLE_COMPS = [
    {"name": "Murloc Flood",   "tier": 3, "tribes": ["Murloc"],          "key_minions": ["Warleader"]},
    {"name": "Mech Shields",   "tier": 3, "tribes": ["Mech"],            "key_minions": ["Deflecto"]},
    {"name": "Mech-Pirate",    "tier": 3, "tribes": ["Mech", "Pirate"],  "key_minions": ["Navigator"]},
    {"name": "Dragon Value",   "tier": 2, "tribes": ["Dragon"],          "key_minions": ["Murozond"]},
]


def test_filter_returns_single_tribe_match():
    results = filter_comps(SAMPLE_COMPS, {"Murloc", "Dragon"})
    names = [c["name"] for c in results]
    assert "Murloc Flood" in names
    assert "Dragon Value" in names
    assert "Mech Shields" not in names
    assert "Mech-Pirate" not in names


def test_filter_multi_tribe_comp_requires_all_tribes_active():
    results = filter_comps(SAMPLE_COMPS, {"Mech", "Pirate"})
    assert "Mech-Pirate" in [c["name"] for c in results]

    results = filter_comps(SAMPLE_COMPS, {"Mech"})
    assert "Mech-Pirate" not in [c["name"] for c in results]
    assert "Mech Shields" in [c["name"] for c in results]


def test_filter_results_sorted_by_tier_descending():
    results = filter_comps(SAMPLE_COMPS, {"Murloc", "Dragon"})
    tiers = [c["tier"] for c in results]
    assert tiers == sorted(tiers, reverse=True)


def test_filter_empty_active_set_returns_nothing():
    assert filter_comps(SAMPLE_COMPS, set()) == []


def test_filter_empty_comps_returns_nothing():
    assert filter_comps([], {"Murloc"}) == []
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_recommender.py -k filter -v`
Expected: FAIL with `ImportError: cannot import name 'filter_comps'`

- [ ] **Step 3: Add filter_comps to recommender.py**

Append to `recommender.py`:

```python
def filter_comps(comps: list[dict], active_tribes: set[str]) -> list[dict]:
    if not active_tribes:
        return []
    matching = [
        c for c in comps
        if set(c.get("tribes", [])).issubset(active_tribes)
    ]
    return sorted(matching, key=lambda c: c.get("tier", 0), reverse=True)
```

- [ ] **Step 4: Run all recommender tests**

Run: `pytest tests/test_recommender.py -v`
Expected: PASS (9 tests)

- [ ] **Step 5: Commit**

```bash
git add recommender.py tests/test_recommender.py
git commit -m "feat: filter_comps with tribe subset matching and tier sort"
```

---

### Task 7: OCR Module — Screenshot and Crop

**Files:**
- Create: `ocr.py`
- Create: `tests/test_ocr.py`

- [ ] **Step 1: Write failing tests**

```python
# tests/test_ocr.py
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock
sys.path.insert(0, str(Path(__file__).parent.parent))

from ocr import capture_crop


def test_capture_crop_crops_to_region():
    mock_img = MagicMock()
    mock_img.crop.return_value = mock_img
    with patch("ocr.ImageGrab.grab", return_value=mock_img):
        result = capture_crop([100, 200, 300, 400])
    mock_img.crop.assert_called_once_with((100, 200, 400, 600))  # x,y,x+w,y+h
    assert result is mock_img


def test_capture_crop_none_returns_full_screen():
    mock_img = MagicMock()
    with patch("ocr.ImageGrab.grab", return_value=mock_img):
        result = capture_crop(None)
    mock_img.crop.assert_not_called()
    assert result is mock_img
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_ocr.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'ocr'`

- [ ] **Step 3: Create ocr.py with capture_crop**

```python
# ocr.py
import asyncio
import difflib
import logging
from PIL import ImageGrab, Image

logger = logging.getLogger(__name__)

ALL_TRIBES = [
    "Murloc", "Beast", "Mech", "Demon", "Dragon",
    "Elemental", "Pirate", "Naga", "Undead", "Quillboar",
]

FUZZY_THRESHOLD = 0.75


def capture_crop(crop_region: list | None) -> Image.Image:
    img = ImageGrab.grab()
    if crop_region:
        x, y, w, h = crop_region
        img = img.crop((x, y, x + w, y + h))
    return img
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/test_ocr.py -v`
Expected: PASS (2 tests)

- [ ] **Step 5: Commit**

```bash
git add ocr.py tests/test_ocr.py
git commit -m "feat: ocr capture_crop"
```

---

### Task 8: OCR Module — winrt OCR and Fuzzy Matching

**Files:**
- Modify: `ocr.py`
- Modify: `tests/test_ocr.py`

- [ ] **Step 1: Write failing tests**

Add to `tests/test_ocr.py`:

```python
from ocr import run_ocr, match_tribes, scan_tribes, ALL_TRIBES


def test_run_ocr_returns_text_from_lines():
    mock_img = MagicMock()
    mock_result = MagicMock()
    mock_result.lines = [MagicMock(text="Murloc"), MagicMock(text="Pirates")]
    with patch("ocr.asyncio.run", return_value=mock_result):
        lines = run_ocr(mock_img)
    assert "Murloc" in lines
    assert "Pirates" in lines


def test_run_ocr_returns_empty_on_exception():
    mock_img = MagicMock()
    with patch("ocr.asyncio.run", side_effect=Exception("OCR failed")):
        lines = run_ocr(mock_img)
    assert lines == []


def test_match_tribes_exact_match():
    matched, unmatched = match_tribes(["Murloc", "Mech"], ALL_TRIBES)
    assert "Murloc" in matched
    assert "Mech" in matched
    assert unmatched == []


def test_match_tribes_fuzzy_corrects_typo():
    # OCR commonly misreads Murloc as "Murioc" or "Murlo c"
    matched, unmatched = match_tribes(["Murioc", "Mechs"], ALL_TRIBES)
    assert "Murloc" in matched
    assert "Mech" in matched


def test_match_tribes_flags_unrecognized_tokens():
    matched, unmatched = match_tribes(["XyzGarbage123"], ALL_TRIBES)
    assert matched == []
    assert "XyzGarbage123" in unmatched


def test_match_tribes_no_duplicates():
    # Two OCR tokens fuzzy-matching to same tribe should not produce duplicates
    matched, _ = match_tribes(["Murioc", "Murlo c"], ALL_TRIBES)
    assert matched.count("Murloc") == 1


def test_scan_tribes_integrates_capture_and_ocr():
    mock_img = MagicMock()
    mock_result = MagicMock()
    mock_result.lines = [MagicMock(text="Murloc"), MagicMock(text="Dragon")]
    with patch("ocr.ImageGrab.grab", return_value=mock_img), \
         patch("ocr.asyncio.run", return_value=mock_result):
        matched, unmatched = scan_tribes(None)
    assert "Murloc" in matched
    assert "Dragon" in matched
    assert unmatched == []
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_ocr.py -k "run_ocr or match_tribes or scan_tribes" -v`
Expected: FAIL with `ImportError: cannot import name 'run_ocr'`

- [ ] **Step 3: Add run_ocr, match_tribes, scan_tribes to ocr.py**

Append to `ocr.py`:

```python
def run_ocr(img: Image.Image) -> list[str]:
    try:
        import winrt.windows.media.ocr as win_ocr
        import winrt.windows.graphics.imaging as imaging
        import winrt.windows.storage.streams as streams
        import io

        async def _recognize():
            engine = win_ocr.OcrEngine.try_create_from_user_profile_languages()
            buf = io.BytesIO()
            img.save(buf, format="BMP")
            buf.seek(0)
            data = buf.read()
            stream = streams.InMemoryRandomAccessStream()
            writer = streams.DataWriter(stream)
            writer.write_bytes(list(data))
            await writer.store_async()
            stream.seek(0)
            decoder = await imaging.BitmapDecoder.create_async(stream)
            bitmap = await decoder.get_software_bitmap_async()
            return await engine.recognize_async(bitmap)

        result = asyncio.run(_recognize())
        return [line.text for line in result.lines]
    except Exception as e:
        logger.error(f"OCR failed: {e}")
        return []


def match_tribes(
    ocr_tokens: list[str],
    known_tribes: list[str] = ALL_TRIBES,
) -> tuple[list[str], list[str]]:
    matched: list[str] = []
    unmatched: list[str] = []
    for token in ocr_tokens:
        close = difflib.get_close_matches(token, known_tribes, n=1, cutoff=FUZZY_THRESHOLD)
        if close:
            tribe = close[0]
            if tribe not in matched:
                matched.append(tribe)
        else:
            unmatched.append(token)
    return matched, unmatched


def scan_tribes(crop_region: list | None) -> tuple[list[str], list[str]]:
    img = capture_crop(crop_region)
    tokens = run_ocr(img)
    return match_tribes(tokens)
```

- [ ] **Step 4: Run all OCR tests**

Run: `pytest tests/test_ocr.py -v`
Expected: PASS (all tests)

- [ ] **Step 5: Commit**

```bash
git add ocr.py tests/test_ocr.py
git commit -m "feat: ocr run_ocr, match_tribes, scan_tribes with fuzzy matching"
```

---

### Task 9: Overlay — Base Window

**Files:**
- Create: `overlay.py`

> PyQt6 UI cannot be unit tested without a display. Verify each UI task manually with a `_test_overlay.py` temp file.

- [ ] **Step 1: Create overlay.py with base BgOverlay window**

```python
# overlay.py
import sys
import logging
from PyQt6.QtWidgets import QApplication, QWidget, QVBoxLayout, QFrame
from PyQt6.QtCore import Qt, QPoint

logger = logging.getLogger(__name__)


class BgOverlay(QWidget):
    def __init__(self, config: dict):
        super().__init__()
        self._config = config
        self._drag_pos = QPoint()
        self._setup_window()
        self._build_ui()

    def _setup_window(self):
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setWindowOpacity(self._config.get("opacity", 0.85))
        self.setMinimumWidth(280)
        self.resize(280, 500)
        screen = QApplication.primaryScreen().geometry()
        self.move(screen.width() - 300, 100)

    def _build_ui(self):
        self._container = QFrame(self)
        self._container.setStyleSheet(
            "QFrame { background: rgba(20, 20, 20, 210); border-radius: 8px; }"
        )
        self._main_layout = QVBoxLayout(self._container)
        self._main_layout.setContentsMargins(10, 10, 10, 10)
        self._main_layout.setSpacing(8)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(self._container)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.MouseButton.LeftButton and self._drag_pos:
            self.move(event.globalPosition().toPoint() - self._drag_pos)

    def toggle_visibility(self):
        self.setVisible(not self.isVisible())
```

- [ ] **Step 2: Verify window opens**

Create `_test_overlay.py`:

```python
import sys
from PyQt6.QtWidgets import QApplication
from overlay import BgOverlay

app = QApplication(sys.argv)
w = BgOverlay({"opacity": 0.9})
w.show()
sys.exit(app.exec())
```

Run: `python _test_overlay.py`
Expected: A small dark rounded window appears anchored to the right side of the screen. Draggable. Close terminal with Ctrl+C.

- [ ] **Step 3: Clean up and commit**

```bash
rm _test_overlay.py
git add overlay.py
git commit -m "feat: base overlay window (always-on-top, translucent, draggable)"
```

---

### Task 10: Overlay — Tribe Panel

**Files:**
- Modify: `overlay.py`

- [ ] **Step 1: Add TribeChip and TribePanel classes to overlay.py**

Add after the imports block in `overlay.py`:

```python
from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QPushButton, QFrame, QScrollArea,
)
from PyQt6.QtCore import Qt, QPoint, pyqtSignal

ALL_TRIBES = [
    "Murloc", "Beast", "Mech", "Demon", "Dragon",
    "Elemental", "Pirate", "Naga", "Undead", "Quillboar",
]


class TribeChip(QPushButton):
    def __init__(self, name: str, parent=None):
        super().__init__(name, parent)
        self.setCheckable(True)
        self.toggled.connect(lambda checked: self._apply_style(checked))
        self._apply_style(False)

    def _apply_style(self, active: bool):
        if active:
            self.setStyleSheet(
                "QPushButton { background: #4a9eff; color: white; border-radius: 4px;"
                " padding: 4px 8px; font-size: 12px; font-weight: bold; border: none; }"
            )
        else:
            self.setStyleSheet(
                "QPushButton { background: #333; color: #777; border-radius: 4px;"
                " padding: 4px 8px; font-size: 12px; border: none; }"
            )


class TribePanel(QFrame):
    tribes_changed = pyqtSignal(set)

    def __init__(self, on_rescan, parent=None):
        super().__init__(parent)
        self._chips: dict[str, TribeChip] = {}
        self._on_rescan = on_rescan
        self._warning_label = None
        self._build()

    def _build(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)

        # Header row
        header = QHBoxLayout()
        title = QLabel("TRIBES")
        title.setStyleSheet("color: #bbb; font-size: 11px; font-weight: bold; letter-spacing: 1px;")
        header.addWidget(title)
        header.addStretch()
        rescan = QPushButton("↺")
        rescan.setFixedSize(24, 24)
        rescan.setStyleSheet(
            "QPushButton { background: #555; color: #eee; border-radius: 4px; font-size: 14px; border: none; }"
            "QPushButton:hover { background: #777; }"
        )
        rescan.clicked.connect(self._on_rescan)
        header.addWidget(rescan)
        layout.addLayout(header)

        # Tribe chip grid (3 columns)
        grid = QGridLayout()
        grid.setSpacing(4)
        for i, tribe in enumerate(ALL_TRIBES):
            chip = TribeChip(tribe)
            chip.toggled.connect(self._emit_change)
            self._chips[tribe] = chip
            grid.addWidget(chip, i // 3, i % 3)
        layout.addLayout(grid)

        # Warning label for unrecognized OCR tokens (hidden by default)
        self._warning_label = QLabel("")
        self._warning_label.setStyleSheet(
            "QLabel { color: #e07000; font-size: 10px; padding: 2px; }"
        )
        self._warning_label.setWordWrap(True)
        self._warning_label.hide()
        layout.addWidget(self._warning_label)

    def _emit_change(self):
        self.tribes_changed.emit(self.active_tribes())

    def active_tribes(self) -> set:
        return {name for name, chip in self._chips.items() if chip.isChecked()}

    def set_active_tribes(self, tribes: list[str], flagged_tokens: list[str] | None = None):
        for name, chip in self._chips.items():
            chip.blockSignals(True)
            chip.setChecked(name in tribes)
            chip.blockSignals(False)

        if flagged_tokens:
            self._warning_label.setText(f"⚠ Unrecognized: {', '.join(flagged_tokens)}")
            self._warning_label.show()
        else:
            self._warning_label.hide()

        self._emit_change()
```

- [ ] **Step 2: Add tribe panel to BgOverlay._build_ui**

Replace `_build_ui` in `BgOverlay`:

```python
def _build_ui(self):
    self._container = QFrame(self)
    self._container.setStyleSheet(
        "QFrame { background: rgba(20, 20, 20, 210); border-radius: 8px; }"
    )
    self._main_layout = QVBoxLayout(self._container)
    self._main_layout.setContentsMargins(10, 10, 10, 10)
    self._main_layout.setSpacing(8)

    self._tribe_panel = TribePanel(on_rescan=self._on_rescan)
    self._tribe_panel.tribes_changed.connect(self._on_tribes_changed)
    self._main_layout.addWidget(self._tribe_panel)

    divider = QFrame()
    divider.setFrameShape(QFrame.Shape.HLine)
    divider.setStyleSheet("QFrame { color: #444; }")
    self._main_layout.addWidget(divider)

    # Comp area placeholder (replaced in Task 11)
    self._comp_placeholder = QLabel("Select tribes to see recommendations")
    self._comp_placeholder.setStyleSheet("color: #666; font-size: 11px;")
    self._comp_placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
    self._main_layout.addWidget(self._comp_placeholder)

    outer = QVBoxLayout(self)
    outer.setContentsMargins(0, 0, 0, 0)
    outer.addWidget(self._container)

def _on_rescan(self):
    pass  # Wired in main.py via set_rescan_callback

def _on_tribes_changed(self, active: set):
    pass  # Wired in Task 11
```

- [ ] **Step 3: Verify tribe panel**

Create `_test_overlay.py`:

```python
import sys
from PyQt6.QtWidgets import QApplication
from overlay import BgOverlay

app = QApplication(sys.argv)
w = BgOverlay({"opacity": 0.9})
w._tribe_panel.set_active_tribes(["Murloc", "Mech"], flagged_tokens=["Dragnz"])
w.show()
sys.exit(app.exec())
```

Run: `python _test_overlay.py`
Expected: Overlay shows tribe chips — Murloc and Mech highlighted blue, others dim. Orange warning "⚠ Unrecognized: Dragnz" visible below the chips. ↺ button in header.

- [ ] **Step 4: Clean up and commit**

```bash
rm _test_overlay.py
git add overlay.py
git commit -m "feat: tribe panel with toggleable chips and OCR warning label"
```

---

### Task 11: Overlay — Comp List

**Files:**
- Modify: `overlay.py`

- [ ] **Step 1: Add CompCard and CompList classes to overlay.py**

Add before `BgOverlay` class:

```python
class CompCard(QFrame):
    def __init__(self, comp: dict, parent=None):
        super().__init__(parent)
        self.setStyleSheet(
            "QFrame { background: rgba(40, 40, 40, 180); border-radius: 6px; margin: 1px; }"
        )
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 6, 8, 6)
        layout.setSpacing(2)

        tier = comp.get("tier", 1)
        stars = "★" * tier + "☆" * (3 - tier)
        header = QLabel(f"{stars}  {comp['name']}")
        header.setStyleSheet("color: #eee; font-size: 13px; font-weight: bold;")
        layout.addWidget(header)

        key_minions = ", ".join(comp.get("key_minions", []))
        detail = QLabel(f"Key: {key_minions}")
        detail.setStyleSheet("color: #999; font-size: 11px;")
        detail.setWordWrap(True)
        layout.addWidget(detail)


class CompList(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(4)
        self._empty_label = QLabel("No tribes active")
        self._empty_label.setStyleSheet("color: #555; font-size: 11px;")
        self._layout.addWidget(self._empty_label)

    def update_comps(self, comps: list[dict]):
        while self._layout.count():
            item = self._layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        if not comps:
            lbl = QLabel("No matching comps")
            lbl.setStyleSheet("color: #555; font-size: 11px;")
            self._layout.addWidget(lbl)
            return

        comp_title = QLabel("COMPS")
        comp_title.setStyleSheet("color: #bbb; font-size: 11px; font-weight: bold; letter-spacing: 1px;")
        self._layout.addWidget(comp_title)
        for comp in comps:
            self._layout.addWidget(CompCard(comp))
        self._layout.addStretch()
```

- [ ] **Step 2: Wire CompList into BgOverlay**

Replace the comp placeholder block in `_build_ui` (remove `self._comp_placeholder`) and add after the divider:

```python
scroll = QScrollArea()
scroll.setWidgetResizable(True)
scroll.setStyleSheet(
    "QScrollArea { border: none; background: transparent; }"
    "QScrollBar:vertical { background: #222; width: 6px; border-radius: 3px; }"
    "QScrollBar::handle:vertical { background: #555; border-radius: 3px; }"
)
scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
self._comp_list = CompList()
scroll.setWidget(self._comp_list)
self._main_layout.addWidget(scroll, stretch=1)
```

Implement `_on_tribes_changed`:

```python
def _on_tribes_changed(self, active: set):
    from recommender import load_comps, filter_comps
    comps = load_comps()
    if not comps:
        self._comp_list.update_comps([])
        return
    self._comp_list.update_comps(filter_comps(comps, active))
```

- [ ] **Step 3: Verify comp list renders**

Create `_test_overlay.py`:

```python
import sys
from PyQt6.QtWidgets import QApplication
from overlay import BgOverlay

app = QApplication(sys.argv)
w = BgOverlay({"opacity": 0.9})
w._tribe_panel.set_active_tribes(["Murloc", "Mech", "Pirate"])
w.show()
sys.exit(app.exec())
```

Run: `python _test_overlay.py`
Expected: Overlay shows tribe panel with Murloc/Mech/Pirate highlighted, and comp list below showing Mech Divine Shield (★★★), Mech-Pirate Menace (★★★), Murloc Flood (★★★), Pirate Aggro (★★), each with tier stars, name, and key minions. Scroll works if list overflows.

- [ ] **Step 4: Clean up and commit**

```bash
rm _test_overlay.py
git add overlay.py
git commit -m "feat: comp list with tier cards and scroll"
```

---

### Task 12: main.py — Hotkeys and Integration

**Files:**
- Create: `main.py`

- [ ] **Step 1: Create main.py**

```python
# main.py
import sys
import logging
import keyboard
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QTimer

from config import load_config, save_config
from ocr import scan_tribes
from overlay import BgOverlay

logging.basicConfig(
    filename="bg.log",
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
)
logger = logging.getLogger(__name__)


def main():
    cfg = load_config()
    app = QApplication(sys.argv)
    overlay = BgOverlay(cfg)
    overlay.show()

    def on_scan():
        try:
            matched, flagged = scan_tribes(cfg.get("crop_region"))
            if not matched and not flagged:
                overlay.show_error(
                    "No tribes detected — hover over the tribe panel in Hearthstone, then press F8"
                )
            else:
                overlay.clear_error()
            overlay._tribe_panel.set_active_tribes(matched, flagged or None)
            logger.info(f"Scan complete: matched={matched} flagged={flagged}")
        except Exception as e:
            overlay.show_error(f"Scan error: {e}")
            logger.error(f"Scan failed: {e}")

    def on_toggle():
        overlay.toggle_visibility()

    def on_calibrate():
        from calibrate import run_calibration
        region = run_calibration()
        if region:
            cfg["crop_region"] = region
            save_config(cfg)
            logger.info(f"Crop region saved: {region}")

    # Wire rescan button in overlay to same handler as F8
    overlay._tribe_panel._on_rescan = lambda: QTimer.singleShot(0, on_scan)

    try:
        keyboard.add_hotkey(cfg["hotkey_scan"],      lambda: QTimer.singleShot(0, on_scan))
        keyboard.add_hotkey(cfg["hotkey_toggle"],    lambda: QTimer.singleShot(0, on_toggle))
        keyboard.add_hotkey(cfg["hotkey_calibrate"], lambda: QTimer.singleShot(0, on_calibrate))
        logger.info("BG-Advisor started")
    except Exception as e:
        overlay.show_error(f"Hotkey registration failed: {e}")
        logger.error(f"Hotkey registration failed: {e}")

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Add show_error / clear_error to BgOverlay**

Add to `overlay.py` (before `_setup_window`):

```python
# Add ErrorBanner class before BgOverlay:

class ErrorBanner(QLabel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWordWrap(True)
        self.setStyleSheet(
            "QLabel { background: #7a1a1a; color: #ffcccc; padding: 6px;"
            " border-radius: 4px; font-size: 11px; }"
        )
        self.hide()

    def show_error(self, message: str):
        self.setText(message)
        self.show()

    def clear_error(self):
        self.hide()
        self.setText("")
```

Add `ErrorBanner` to `_build_ui` at the top of `self._main_layout`:

```python
self._error_banner = ErrorBanner()
self._main_layout.insertWidget(0, self._error_banner)
```

Add public methods to `BgOverlay`:

```python
def show_error(self, message: str):
    self._error_banner.show_error(message)

def clear_error(self):
    self._error_banner.clear_error()
```

- [ ] **Step 3: Verify full integration**

Run: `python main.py`
Expected:
- Overlay appears on right side of screen
- F9 hides/shows overlay
- F8 without a crop region calibrated → scans full screen → likely shows "No tribes detected" error banner
- F8 while hovering over Hearthstone tribe panel (crop region set) → tribe chips update, comp list updates
- `bg.log` is created in project root with `INFO BG-Advisor started`

- [ ] **Step 4: Commit**

```bash
git add main.py overlay.py
git commit -m "feat: main.py hotkeys, error banner, full pipeline integration"
```

---

### Task 13: Calibration Mode

**Files:**
- Create: `calibrate.py`

- [ ] **Step 1: Create calibrate.py**

```python
# calibrate.py
import sys
from PyQt6.QtWidgets import QApplication, QWidget
from PyQt6.QtCore import Qt, QRect, QPoint
from PyQt6.QtGui import QPainter, QColor, QPen, QFont


class CalibrationOverlay(QWidget):
    def __init__(self):
        super().__init__()
        self.result: list | None = None
        self._start = QPoint()
        self._end = QPoint()
        self._selecting = False
        self._setup()

    def _setup(self):
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setGeometry(QApplication.primaryScreen().geometry())
        self.setCursor(Qt.CursorShape.CrossCursor)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._start = event.pos()
            self._selecting = True

    def mouseMoveEvent(self, event):
        if self._selecting:
            self._end = event.pos()
            self.update()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton and self._selecting:
            self._end = event.pos()
            self._selecting = False
            rect = QRect(self._start, self._end).normalized()
            self.result = [rect.x(), rect.y(), rect.width(), rect.height()]
            self.close()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Escape:
            self.result = None
            self.close()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.fillRect(self.rect(), QColor(0, 0, 0, 90))
        if self._selecting:
            rect = QRect(self._start, self._end).normalized()
            painter.setPen(QPen(QColor(80, 160, 255), 2))
            painter.drawRect(rect)
            painter.fillRect(rect, QColor(80, 160, 255, 30))
        font = QFont("Arial", 14)
        painter.setFont(font)
        painter.setPen(QPen(QColor(255, 255, 255, 220)))
        painter.drawText(
            self.rect(),
            Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignHCenter,
            "\nDrag to select the tribe panel area    ESC to cancel",
        )


def run_calibration() -> list | None:
    app = QApplication.instance() or QApplication(sys.argv)
    w = CalibrationOverlay()
    w.show()
    w.activateWindow()
    app.exec()
    return w.result
```

- [ ] **Step 2: Verify calibration**

Create `_test_calibrate.py`:

```python
from calibrate import run_calibration

region = run_calibration()
print(f"Selected region: {region}")
```

Run: `python _test_calibrate.py`
Expected: Screen dims with instruction text at top. Crosshair cursor. Drag to draw blue selection box. On release, `[x, y, w, h]` prints to console. ESC prints `None`.

- [ ] **Step 3: Clean up and commit**

```bash
rm _test_calibrate.py
git add calibrate.py
git commit -m "feat: calibration overlay for crop region selection"
```

---

### Task 14: Backfill Tracking Folder

**Files:**
- Create: `C:\Users\egarb\.claude\project\BG-Advisor\project-info.md`
- Copy: design spec to `C:\Users\egarb\.claude\project\BG-Advisor\docs\`

- [ ] **Step 1: Create project-info.md**

Write `C:\Users\egarb\.claude\project\BG-Advisor\project-info.md`:

```markdown
# BG-Advisor

**Created:** 2026-05-15
**Project Root:** C:\Users\egarb\Projects\BG-Advisor

## Overview
Windows overlay for Hearthstone Battlegrounds. On hotkey press (F8), OCR-scans
the tribe panel, displays toggleable tribe chips in a semi-transparent overlay,
and recommends endgame compositions filtered to the active tribes.

## Tech Stack
- Python 3.11+, PyQt6, Pillow, keyboard, winsdk (winrt), pytest

## Key Files
- `main.py` — entry point, hotkey wiring (F8/F9/Shift+F8)
- `ocr.py` — screenshot → crop → winrt OCR → fuzzy tribe name matching
- `recommender.py` — pure logic: filters comps.json by active tribes, sorts by tier
- `overlay.py` — all PyQt6 UI: TribePanel, CompList, ErrorBanner, BgOverlay
- `calibrate.py` — fullscreen crosshair selector for crop region
- `comps.json` — manually maintained comp database (update after patches)
- `config.json` — user settings (hotkeys, crop_region, opacity)

## Design Docs
See docs/2026-05-15-bg-advisor-design.md
```

- [ ] **Step 2: Copy design spec to tracking docs**

```bash
cp "C:/Users/egarb/Projects/BG-Advisor/docs/superpowers/specs/2026-05-15-bg-advisor-design.md" \
   "C:/Users/egarb/.claude/project/BG-Advisor/docs/2026-05-15-bg-advisor-design.md"
```

- [ ] **Step 3: Final commit**

```bash
git add -A
git commit -m "docs: backfill project tracking folder and final plan"
```

---

## Self-Review

**Spec coverage:**
| Requirement | Task |
|---|---|
| Hotkey F8 scan | Task 12 |
| Hotkey F9 toggle | Task 12 |
| Hotkey Shift+F8 calibrate | Task 12, 13 |
| Pillow screenshot + crop | Task 7 |
| winrt OCR | Task 8 |
| difflib fuzzy matching | Task 8 |
| Tribe chips (all tribes, toggleable) | Task 10 |
| OCR sets initial active state | Task 12 (on_scan → set_active_tribes) |
| User can override chip state | Task 10 (chips are toggleable buttons) |
| Rescan button | Task 10 (↺ button → on_rescan) |
| Unrecognized tokens flagged orange | Task 10 (warning label) |
| Comp recommender filters by active tribes | Task 6 |
| Multi-tribe comps require both active | Task 6 |
| Sorted by tier descending | Task 6 |
| PyQt6 always-on-top translucent window | Task 9 |
| Draggable | Task 9 |
| Semi-transparent (opacity configurable) | Task 9, config |
| comps.json schema | Task 2 |
| config.json schema | Task 3, 4 |
| Calibration mode (crosshair selector) | Task 13 |
| No tribes detected → error message | Task 12 (on_scan) |
| comps.json missing → empty comp list (no crash) | Task 5 (load_comps returns []) |
| config.json missing → defaults | Task 3 |
| Hotkey conflict → logged | Task 12 |
| bg.log | Task 12 |
