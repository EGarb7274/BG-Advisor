# Early Combo Advisor Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a curated 2-card early-combo advisor to BG-Advisor, surfaced in a new "EARLY COMBOS" tab alongside the existing "LATE GAME" comp recommendations, filtered by active tribes, with clickable comp links that jump to the matched comp card.

**Architecture:** A new `combos.json` data file (mirrors `comps.json`) and a `combo_recommender.py` module (mirrors `recommender.py`) handle data. `overlay.py` gains three new widgets (`TabBar`, `ComboCard`, `ComboList`), a small addition to `CompList`, and `BgOverlay` is updated to use a `QStackedWidget` for tab switching with a comp-link signal chain.

**Tech Stack:** Python 3.x, PyQt6, JSON, pytest

---

## File Map

| File | Action | Responsibility |
|------|--------|----------------|
| `combos.json` | Create | Curated 2-card combo data (~25 entries) |
| `combo_recommender.py` | Create | `load_combos()` + `filter_combos()` |
| `tests/test_combo_recommender.py` | Create | Unit tests for above |
| `overlay.py` | Modify | Add `TabBar`, `ComboCard`, `ComboList`; update `CompList`; refactor `BgOverlay` |

---

## Task 1: Create `combos.json`

**Files:**
- Create: `combos.json`

- [ ] **Step 1: Write the file**

Create `C:\Users\egarb\Projects\BG-Advisor\combos.json` with this exact content:

```json
[
  {
    "cards": ["Lurking Leviathan", "Sewer Lord"],
    "tribes": ["Beast"],
    "tiers": [4, 3],
    "synergy": "Sewer Lord spawns rat tokens every shop phase — each one passively stacks Leviathan's +1/+1 buff without spending any actions.",
    "leads_to": "Beasts - Leviathan"
  },
  {
    "cards": ["Titus Rivendare", "Goldrinn, The Great Wolf"],
    "tribes": ["Beast"],
    "tiers": [5, 4],
    "synergy": "Goldrinn gives all Beasts +5 attack on death — Titus doubles the trigger to +10. One death buffs your whole Beast army catastrophically.",
    "leads_to": "Beasts - Summons"
  },
  {
    "cards": ["Rylak Metalhead", "Hunting Tiger Shark"],
    "tribes": ["Beast"],
    "tiers": [4, 3],
    "synergy": "Every Beast attack triggers Tiger Shark's +2/+2 buff. Monstrous Macaw chains these triggers — stack them both early to ramp exponentially.",
    "leads_to": "Beasts - RDU"
  },
  {
    "cards": ["Darkgaze Elder", "Prickly Piper"],
    "tribes": ["Quillboar"],
    "tiers": [2, 1],
    "synergy": "Darkgaze makes each blood gem worth +2/+2 instead of +1/+1. Prickly Piper applies every gem to all friendly minions — your whole board scales off a single gem.",
    "leads_to": "Quilboar - Darkgaze"
  },
  {
    "cards": ["Gem Smuggler", "Titus Rivendare"],
    "tribes": ["Quillboar"],
    "tiers": [2, 5],
    "synergy": "Gem Smuggler discovers a blood gem each time you play a Quilboar. Titus doubles that to two gems per Quilboar — flood the board with gems every turn.",
    "leads_to": "Quilboar - Smuggler"
  },
  {
    "cards": ["Gem Smuggler", "Moon-bacon Jazzer"],
    "tribes": ["Quillboar"],
    "tiers": [2, 3],
    "synergy": "Gem Smuggler generates gems on each Quilboar played. Moon-bacon Jazzer applies each gem to a random Quilboar — combine with Prickly Piper to spread gems to everyone.",
    "leads_to": "Quilboar - Smuggler"
  },
  {
    "cards": ["Bristlebach", "Prickly Piper"],
    "tribes": ["Quillboar"],
    "tiers": [1, 1],
    "synergy": "Bristlebach generates a blood gem every time it attacks in combat. Prickly Piper turns that single gem into a buff for every friendly minion — passive board-wide scaling.",
    "leads_to": "Quilboar - Combat Scaling"
  },
  {
    "cards": ["Handless Forsaken", "Drustfallen Butcher"],
    "tribes": ["Undead"],
    "tiers": [2, 4],
    "synergy": "Butchering doubles the attack of all Undeads. Handless Forsaken spawns the summons that carry those doubled attacks — commit once both are in hand.",
    "leads_to": "Undead - Attack Scaling"
  },
  {
    "cards": ["Leeroy the Reckless", "Bile Spitter"],
    "tribes": ["Undead"],
    "tiers": [4, 2],
    "synergy": "Bile Spitter gives a friendly minion Poisonous. Give it to Leeroy — he one-shots anything he touches and deals overflow damage directly to the enemy hero.",
    "leads_to": "Undead - Overflow"
  },
  {
    "cards": ["Titus Rivendare", "Cadaver Caretaker"],
    "tribes": ["Murloc"],
    "tiers": [5, 3],
    "synergy": "Cadaver Caretaker has a reborn death rattle. Titus doubles death rattle triggers — pair with Monstrous Macaw to chain reborn loops that rebuild your board each combat.",
    "leads_to": "Murlocs - Reborn Loop"
  },
  {
    "cards": ["Magicfin Mycologist", "Primitive Painter"],
    "tribes": ["Murloc"],
    "tiers": [3, 2],
    "synergy": "Mycologist summons a random Murloc each time you play a Murloc. Primitive Painter buffs all Murlocs in hand and board — each chain play buffs an ever-growing swarm.",
    "leads_to": "Murlocs - APM"
  },
  {
    "cards": ["Brann Bronzebeard", "Magicfin Mycologist"],
    "tribes": ["Murloc"],
    "tiers": [4, 3],
    "synergy": "Brann doubles Mycologist's battlecry summon — each Murloc you play summons two random Murlocs instead of one. The board floods in a single shop phase.",
    "leads_to": "Murlocs - APM"
  },
  {
    "cards": ["Bile Spitter", "Diremuck Forager"],
    "tribes": ["Murloc"],
    "tiers": [2, 3],
    "synergy": "Bile Spitter gives a friendly Murloc Poisonous. Diremuck Forager gives divine shield — protect your poisonous attacker so it survives long enough to one-shot the enemy's best minion.",
    "leads_to": "Murlocs - Venom Scam"
  },
  {
    "cards": ["Groundbreaker", "Darkcrest Strategist"],
    "tribes": ["Naga"],
    "tiers": [2, 3],
    "synergy": "Groundbreaker gains +2/+2 per spell cast during your turn. Darkcrest Strategist generates and reduces spell costs — more spells per turn means faster scaling.",
    "leads_to": "Nagas - Groundbreaker"
  },
  {
    "cards": ["Brann Bronzebeard", "Groundbreaker"],
    "tribes": ["Naga"],
    "tiers": [4, 2],
    "synergy": "Brann doubles Groundbreaker's +2/+2 spell buff to +4/+4 per spell. A cheap spell engine with Brann in play can grow Groundbreaker into a 20/20+ threat in a few turns.",
    "leads_to": "Nagas - Groundbreaker"
  },
  {
    "cards": ["Ruthless Queensguard", "Maelstrom Emergent"],
    "tribes": ["Naga"],
    "tiers": [4, 3],
    "synergy": "Queensguard gains +1 attack each time she attacks. Maelstrom Emergent gives adjacent Nagas +2 attack when they attack — position them together and the scaling compounds every hit.",
    "leads_to": "Nagas - Combat Scaling"
  },
  {
    "cards": ["Living Azerite", "Leyline Surfacer"],
    "tribes": ["Elemental"],
    "tiers": [3, 2],
    "synergy": "Living Azerite buffs all Elementals in the shop each turn. Leyline Surfacer moves those shop buffs onto your board Elementals — repeat every turn for infinite scaling.",
    "leads_to": "Elementals - Shop Buff"
  },
  {
    "cards": ["Persistent Poet", "Fire-forged Evoker"],
    "tribes": ["Dragon"],
    "tiers": [3, 2],
    "synergy": "Fire-forged Evoker reduces spell costs, letting you cast more spells per turn. Each spell buffs Persistent Poet and triggers discovers — a self-feeding spell loop.",
    "leads_to": "Dragons - Spells"
  },
  {
    "cards": ["Ring Bearer", "Persistent Poet"],
    "tribes": ["Dragon"],
    "tiers": [4, 3],
    "synergy": "Ring Bearer gains +2/+2 each time you cast a spell. Persistent Poet generates spells and discovers more — the loop is self-sustaining and Ring Bearer grows exponentially.",
    "leads_to": "Dragons - Shiny Ring"
  },
  {
    "cards": ["Nightbane, Ignited", "Draconic Warden"],
    "tribes": ["Dragon"],
    "tiers": [4, 2],
    "synergy": "Draconic Warden gains +2/+2 each time you play a battlecry Dragon. Nightbane gains stats from battlecries too — play one Dragon per turn and both scale simultaneously.",
    "leads_to": "Dragons - Battlecries"
  },
  {
    "cards": ["Sky Admiral Rogers", "Proud Privateer"],
    "tribes": ["Pirate"],
    "tiers": [0, 2],
    "synergy": "Rogers' hero power cycles the shop cheaply, enabling you to play multiple Pirates per turn. Proud Privateer and Brazen Buccaneer accumulate bounty with each Pirate played.",
    "leads_to": "Pirates - Bounty APM"
  },
  {
    "cards": ["Malchezaar, Prince of Dance", "Ashen Corruptor"],
    "tribes": ["Demon"],
    "tiers": [5, 4],
    "synergy": "Ashen Corruptor rewinds damage so you can cycle cards without taking shop board hits. Pair with Brann to double the cycle value and fuel Twisted Wrathguard fodder generation.",
    "leads_to": "Demons - Shop Buff"
  },
  {
    "cards": ["Ancestral Automaton", "Kangor's Apprentice"],
    "tribes": ["Mech"],
    "tiers": [4, 5],
    "synergy": "Automaton copies itself on death — a permanent board presence. Kangor's Apprentice resurrects two mechs with divine shield and taunt each time one dies. Your board rebuilds faster than enemies can clear it.",
    "leads_to": "Mechs - Automaton"
  },
  {
    "cards": ["Cataclysmic Harbinger", "Drakkari Enchanter"],
    "tribes": ["Neutral"],
    "tiers": [5, 3],
    "synergy": "Cataclysmic Harbinger generates Back to Back spells every turn. Drakkari Enchanter doubles end-of-turn effects — more Back to Back charges per turn to scale your premium units.",
    "leads_to": "Back to Back"
  },
  {
    "cards": ["Cataclysmic Harbinger", "Felfire Conjurer"],
    "tribes": ["Neutral"],
    "tiers": [5, 3],
    "synergy": "Felfire Conjurer scales spell power, making each Back to Back bigger. Cataclysmic Harbinger generates them every turn — combine with Balinda Stonehearth to double the scaling.",
    "leads_to": "Back to Back"
  }
]
```

- [ ] **Step 2: Commit**

```bash
git add combos.json
git commit -m "feat: add curated early combo database"
```

---

## Task 2: `combo_recommender.py` (TDD)

**Files:**
- Create: `combo_recommender.py`
- Create: `tests/test_combo_recommender.py`

- [ ] **Step 1: Write the failing tests**

Create `C:\Users\egarb\Projects\BG-Advisor\tests\test_combo_recommender.py`:

```python
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
```

- [ ] **Step 2: Run tests — expect failure**

```bash
pytest tests/test_combo_recommender.py -v
```

Expected: `ImportError: No module named 'combo_recommender'`

- [ ] **Step 3: Write the implementation**

Create `C:\Users\egarb\Projects\BG-Advisor\combo_recommender.py`:

```python
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
```

- [ ] **Step 4: Run tests — expect all pass**

```bash
pytest tests/test_combo_recommender.py -v
```

Expected: 9 passed

- [ ] **Step 5: Commit**

```bash
git add combo_recommender.py tests/test_combo_recommender.py
git commit -m "feat: add combo_recommender module with tests"
```

---

## Task 3: Add `TabBar` to `overlay.py`

**Files:**
- Modify: `overlay.py` (add `TabBar` class after the `CompList` class, before `ErrorBanner`)

- [ ] **Step 1: Add `TabBar` class**

In `overlay.py`, locate the `# ── Error Banner` comment (currently around line 530). Insert the following block immediately before it:

```python
# ── Tab Bar ────────────────────────────────────────────────────────────────────

class TabBar(QFrame):
    tab_changed = pyqtSignal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._active = 0
        self._build()

    def _build(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)
        self._btns: list[QPushButton] = []
        for i, label in enumerate(("EARLY COMBOS", "LATE GAME")):
            btn = QPushButton(label)
            btn.setCheckable(True)
            btn.setChecked(i == 0)
            btn.setStyleSheet(
                f"QPushButton {{"
                f"  background: {BG_CHIP_IDLE}; color: {COLOR_DIM};"
                f"  border-radius: 4px; padding: 4px 8px;"
                f"  font-family: 'Segoe UI', sans-serif;"
                f"  font-size: 10px; font-weight: bold; letter-spacing: 1px;"
                f"  border: 1px solid #2a1e10;"
                f"}}"
                f"QPushButton:checked {{"
                f"  background: {BG_CHIP_ACTIVE}; color: #fff;"
                f"  border: 1px solid #d4a030;"
                f"}}"
                f"QPushButton:hover {{ background: rgba(55, 42, 26, 220); color: {COLOR_BODY}; }}"
                f"QPushButton:checked:hover {{ background: #c8922a; }}"
            )
            idx = i
            btn.clicked.connect(lambda _checked, i=idx: self._on_click(i))
            layout.addWidget(btn)
            self._btns.append(btn)

    def _on_click(self, index: int):
        if index == self._active:
            return
        self._active = index
        for i, btn in enumerate(self._btns):
            btn.setChecked(i == index)
        self.tab_changed.emit(index)

    def set_active(self, index: int):
        self._on_click(index)
```

- [ ] **Step 2: Run the full test suite to confirm no regressions**

```bash
pytest tests/ -v
```

Expected: all existing tests still pass (TabBar has no unit tests — it requires a running QApplication)

- [ ] **Step 3: Commit**

```bash
git add overlay.py
git commit -m "feat: add TabBar widget to overlay"
```

---

## Task 4: Add `ComboCard` to `overlay.py`

**Files:**
- Modify: `overlay.py` (add `ComboCard` class after `CompCard`, before `CompList`)

- [ ] **Step 1: Add `ComboCard` class**

In `overlay.py`, locate the `# ── Comp List` comment (currently around line 491). Insert the following block immediately before it:

```python
# ── Combo Card ─────────────────────────────────────────────────────────────────

class ComboCard(QFrame):
    comp_link_clicked = pyqtSignal(str)

    def __init__(self, combo: dict, parent=None):
        super().__init__(parent)
        self._expanded = False
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setStyleSheet(
            f"QFrame {{ background: {BG_CARD}; border-radius: 5px;"
            f"  border: 1px solid #2a1e10; margin: 1px; }}"
        )

        root = QVBoxLayout(self)
        root.setContentsMargins(10, 8, 10, 8)
        root.setSpacing(0)

        cards = combo.get("cards", ["?", "?"])
        tiers = combo.get("tiers", [0, 0])
        tier_text = f"T{tiers[0]} / T{tiers[1]}" if len(tiers) == 2 else ""

        # ── Header row (always visible) ──
        header_row = QHBoxLayout()
        header_row.setSpacing(6)

        name_lbl = QLabel(" + ".join(cards))
        name_lbl.setStyleSheet(
            f"color: #e8d8c0; font-family: 'Palatino Linotype', Georgia, serif;"
            f"font-size: 12px; font-weight: bold; background: transparent;"
        )
        name_lbl.setWordWrap(True)
        tier_lbl = QLabel(tier_text)
        tier_lbl.setStyleSheet(
            f"color: {COLOR_DIM}; font-size: 10px; background: transparent;"
        )
        self._arrow = QLabel("▶")
        self._arrow.setStyleSheet(
            f"color: {COLOR_MUTED}; font-size: 9px; background: transparent;"
        )
        header_row.addWidget(name_lbl, stretch=1)
        header_row.addWidget(tier_lbl)
        header_row.addWidget(self._arrow)
        root.addLayout(header_row)

        # ── Expanded detail panel (hidden by default) ──
        self._detail = QFrame()
        self._detail.setStyleSheet(
            f"QFrame {{ background: transparent; border-top: 1px solid #3a2c1a; }}"
        )
        detail_layout = QVBoxLayout(self._detail)
        detail_layout.setContentsMargins(0, 6, 0, 2)
        detail_layout.setSpacing(4)

        if cards:
            detail_layout.addWidget(_detail_section("Cards", cards, clickable=True))

        synergy = combo.get("synergy", "")
        if synergy:
            detail_layout.addWidget(_detail_section("Synergy", synergy))

        leads_to = combo.get("leads_to", "")
        if leads_to:
            leads_frame = QFrame()
            leads_frame.setStyleSheet("QFrame { background: transparent; }")
            leads_layout = QVBoxLayout(leads_frame)
            leads_layout.setContentsMargins(0, 4, 0, 0)
            leads_layout.setSpacing(2)

            leads_lbl = QLabel("LEADS TO")
            leads_lbl.setStyleSheet(
                f"color: {COLOR_GOLD}; font-family: 'Segoe UI', sans-serif;"
                f"font-size: 9px; font-weight: bold; letter-spacing: 1px; background: transparent;"
            )
            leads_layout.addWidget(leads_lbl)

            link_btn = QPushButton(leads_to)
            link_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            link_btn.setStyleSheet(
                f"QPushButton {{ background: transparent; color: {COLOR_BODY};"
                f"  font-family: 'Segoe UI', sans-serif; font-size: 10px;"
                f"  border: none; padding: 1px 0; text-align: left;"
                f"  text-decoration: underline; }}"
                f"QPushButton:hover {{ color: {COLOR_GOLD}; }}"
            )
            link_btn.clicked.connect(lambda: self.comp_link_clicked.emit(leads_to))
            leads_layout.addWidget(link_btn)
            detail_layout.addWidget(leads_frame)

        self._detail.hide()
        root.addWidget(self._detail)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._expanded = not self._expanded
            self._detail.setVisible(self._expanded)
            self._arrow.setText("▼" if self._expanded else "▶")
```

- [ ] **Step 2: Run tests — confirm no regressions**

```bash
pytest tests/ -v
```

Expected: all existing tests still pass

- [ ] **Step 3: Commit**

```bash
git add overlay.py
git commit -m "feat: add ComboCard widget to overlay"
```

---

## Task 5: Add `ComboList` + update `CompList`

**Files:**
- Modify: `overlay.py` (add `ComboList` class after `TabBar`; add `_comp_cards` dict and `get_comp_card` method to `CompList`)

- [ ] **Step 1: Add `_comp_cards` tracking to `CompList`**

In `overlay.py`, find `class CompList(QFrame):`. Replace the entire class with this updated version that tracks `CompCard` widgets by comp name:

```python
class CompList(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(4)
        self._comp_cards: dict[str, CompCard] = {}
        self._show_empty("No tribes active")

    def _show_empty(self, message: str):
        lbl = QLabel(message)
        lbl.setStyleSheet(
            f"color: {COLOR_MUTED}; font-size: 11px;"
            f"font-family: 'Segoe UI', sans-serif; padding: 4px;"
        )
        self._layout.addWidget(lbl)

    def update_comps(self, comps: list[dict]):
        while self._layout.count():
            item = self._layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        self._comp_cards = {}

        if not comps:
            self._show_empty("No matching comps")
            return

        title = QLabel("RECOMMENDED COMPS")
        title.setStyleSheet(
            f"color: {COLOR_GOLD}; font-family: 'Palatino Linotype', Georgia, serif;"
            f"font-size: 10px; font-weight: bold; letter-spacing: 2px; padding-bottom: 2px;"
        )
        self._layout.addWidget(title)
        for comp in comps:
            card = CompCard(comp)
            self._comp_cards[comp["name"]] = card
            self._layout.addWidget(card)
        self._layout.addStretch()

    def get_comp_card(self, name: str) -> 'CompCard | None':
        return self._comp_cards.get(name)
```

- [ ] **Step 2: Add `ComboList` class**

In `overlay.py`, locate the `# ── Tab Bar` comment added in Task 3. Insert the following block immediately after the `TabBar` class (before `# ── Error Banner`):

```python
# ── Combo List ─────────────────────────────────────────────────────────────────

class ComboList(QFrame):
    comp_link_clicked = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(4)
        self._show_empty("No tribes active")

    def _show_empty(self, message: str):
        lbl = QLabel(message)
        lbl.setStyleSheet(
            f"color: {COLOR_MUTED}; font-size: 11px;"
            f"font-family: 'Segoe UI', sans-serif; padding: 4px;"
        )
        self._layout.addWidget(lbl)

    def update_combos(self, combos: list[dict]):
        while self._layout.count():
            item = self._layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        if not combos:
            self._show_empty("No matching combos")
            return

        title = QLabel("EARLY COMBOS")
        title.setStyleSheet(
            f"color: {COLOR_GOLD}; font-family: 'Palatino Linotype', Georgia, serif;"
            f"font-size: 10px; font-weight: bold; letter-spacing: 2px; padding-bottom: 2px;"
        )
        self._layout.addWidget(title)
        for combo in combos:
            card = ComboCard(combo)
            card.comp_link_clicked.connect(self.comp_link_clicked)
            self._layout.addWidget(card)
        self._layout.addStretch()
```

- [ ] **Step 3: Run tests — confirm no regressions**

```bash
pytest tests/ -v
```

Expected: all existing tests still pass

- [ ] **Step 4: Commit**

```bash
git add overlay.py
git commit -m "feat: add ComboList widget and update CompList with comp card tracking"
```

---

## Task 6: Update `BgOverlay` — tab switcher + signal chain

**Files:**
- Modify: `overlay.py` (imports, `BgOverlay._build_ui`, `_on_tribes_changed`, plus two new methods)

- [ ] **Step 1: Add `QStackedWidget` to imports**

In `overlay.py`, find this line near the top:

```python
from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QPushButton, QFrame, QScrollArea,
)
```

Replace it with:

```python
from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QPushButton, QFrame, QScrollArea, QStackedWidget,
)
```

- [ ] **Step 2: Replace the scroll area block in `BgOverlay._build_ui`**

In `BgOverlay._build_ui`, find this block (currently around lines 675–686):

```python
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet(
            "QScrollArea { border: none; background: transparent; }"
            "QScrollBar:vertical { background: rgba(20,14,8,180); width: 5px; border-radius: 2px; }"
            f"QScrollBar::handle:vertical {{ background: {COLOR_MUTED}; border-radius: 2px; }}"
            "QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0px; }"
        )
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self._comp_list = CompList()
        scroll.setWidget(self._comp_list)
        body.addWidget(scroll, stretch=1)
```

Replace it with:

```python
        self._tab_bar = TabBar()
        self._tab_bar.tab_changed.connect(self._on_tab_changed)
        body.addWidget(self._tab_bar)

        _scroll_style = (
            "QScrollArea { border: none; background: transparent; }"
            "QScrollBar:vertical { background: rgba(20,14,8,180); width: 5px; border-radius: 2px; }"
            f"QScrollBar::handle:vertical {{ background: {COLOR_MUTED}; border-radius: 2px; }}"
            "QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0px; }"
        )

        combo_scroll = QScrollArea()
        combo_scroll.setWidgetResizable(True)
        combo_scroll.setStyleSheet(_scroll_style)
        combo_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self._combo_list = ComboList()
        self._combo_list.comp_link_clicked.connect(self._on_comp_link)
        combo_scroll.setWidget(self._combo_list)

        self._comp_scroll = QScrollArea()
        self._comp_scroll.setWidgetResizable(True)
        self._comp_scroll.setStyleSheet(_scroll_style)
        self._comp_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self._comp_list = CompList()
        self._comp_scroll.setWidget(self._comp_list)

        self._stack = QStackedWidget()
        self._stack.addWidget(combo_scroll)    # index 0 — Early Combos
        self._stack.addWidget(self._comp_scroll)  # index 1 — Late Game
        body.addWidget(self._stack, stretch=1)
```

- [ ] **Step 3: Replace `_on_tribes_changed`**

Find the existing `_on_tribes_changed` method in `BgOverlay`:

```python
    def _on_tribes_changed(self, active: set):
        from recommender import load_comps, filter_comps
        comps = load_comps()
        self._comp_list.update_comps(filter_comps(comps, active))
```

Replace it with:

```python
    def _on_tribes_changed(self, active: set):
        from recommender import load_comps, filter_comps
        from combo_recommender import load_combos, filter_combos as filter_combo_list
        comps = load_comps()
        self._comp_list.update_comps(filter_comps(comps, active))
        combos = load_combos()
        self._combo_list.update_combos(filter_combo_list(combos, active))
```

- [ ] **Step 4: Add `_on_tab_changed` and `_on_comp_link` methods**

Inside `BgOverlay`, add these two methods after `_on_rescan`:

```python
    def _on_tab_changed(self, index: int):
        self._stack.setCurrentIndex(index)

    def _on_comp_link(self, name: str):
        self._tab_bar.set_active(1)   # switches stack to index 1 via tab_changed signal
        card = self._comp_list.get_comp_card(name)
        if card:
            self._comp_scroll.ensureWidgetVisible(card)
```

- [ ] **Step 5: Run full test suite**

```bash
pytest tests/ -v
```

Expected: all tests pass

- [ ] **Step 6: Manual smoke test — launch the app**

```bash
python main.py
```

Verify:
1. Overlay launches; a tab bar appears with "EARLY COMBOS" (active, gold) and "LATE GAME" (dim) tabs
2. Click "LATE GAME" — comp list appears as before; click "EARLY COMBOS" — combo list appears
3. Toggle some tribes (e.g., Beast, Naga) — both lists update; Early Combos shows Beast and Naga combos only
4. Expand a combo card — synergy text appears; both card names are clickable and open the card popup
5. Click a "LEADS TO" comp name — tab switches to "LATE GAME" and scrolls to the matching comp card
6. Click a "LEADS TO" name for a tribe not currently active — tab still switches to Late Game (no crash)
7. Press F8 / rescan — tribes auto-populate; both panels update correctly

- [ ] **Step 7: Commit**

```bash
git add overlay.py
git commit -m "feat: wire BgOverlay tab switcher, combo filtering, and comp-link scroll"
```

---

## Self-Review Checklist

- [x] **combos.json** — Task 1 creates it with 25 entries; all `leads_to` values verified against `comps.json` name fields
- [x] **combo_recommender.py** — Task 2 implements and tests `load_combos` + `filter_combos`; mirrors recommender.py exactly
- [x] **TabBar** — Task 3; `tab_changed` signal, `set_active` method, gold/idle styling
- [x] **ComboCard** — Task 4; expands on click, `CardChip` for card names, "LEADS TO" link button emits `comp_link_clicked`
- [x] **CompList.get_comp_card** — Task 5; `_comp_cards` dict rebuilt each `update_comps` call
- [x] **ComboList** — Task 5; re-emits `comp_link_clicked` from child `ComboCard` widgets
- [x] **BgOverlay._build_ui** — Task 6; `QStackedWidget` with two scroll areas, `TabBar` wired up
- [x] **BgOverlay._on_tribes_changed** — Task 6; updates both `CompList` and `ComboList`
- [x] **BgOverlay._on_comp_link** — Task 6; calls `set_active(1)` (stack switches via signal), then scrolls to `CompCard`
- [x] **Edge case: comp filtered out** — `get_comp_card` returns `None`, `if card:` guard prevents crash, tab still switches
- [x] **Type consistency** — `comp_link_clicked = pyqtSignal(str)` in both `ComboCard` and `ComboList`; `get_comp_card(name: str) -> CompCard | None` referenced correctly in `_on_comp_link`
- [x] **No placeholders** — all steps contain complete code
