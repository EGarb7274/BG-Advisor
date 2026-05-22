# Early Combo Advisor — Design Spec

**Date:** 2026-05-22  
**Status:** Approved

---

## Overview

Add a new "Early Combos" feature to BG-Advisor that surfaces powerful 2-card synergy pairs available in tavern tiers 1–4. These combos serve as mid-game pivots that guide the player toward a specific late-game composition. The feature lives in a new tab alongside the existing late-game comp recommendations.

---

## Goals

- Show the player which 2-card pairs to look for early (tiers 1–4) that naturally transition into a strong late-game build.
- Filter combos by currently active tribes, same as existing comp recommendations.
- Let the player click a combo's destination comp to jump directly to it in the Late Game tab.
- Reuse existing UI patterns (`CardChip`, `CardPopup`, palette constants) to keep the overlay visually consistent.

---

## Architecture

### New files

| File | Purpose |
|------|---------|
| `combos.json` | Curated list of ~25–30 2-card combo entries |
| `combo_recommender.py` | `load_combos()` + `filter_combos()` — mirrors `recommender.py` |

### Modified files

| File | Changes |
|------|---------|
| `overlay.py` | Add `TabBar`, `ComboCard`, `ComboList`; update `BgOverlay` to use `QStackedWidget` + tab switching + comp-link scroll |

### Unchanged

`recommender.py`, `api.py`, `main.py`, `config.py`, `ocr.py`

---

## Data: `combos.json`

Each entry is a JSON object with these fields:

```json
{
  "cards": ["Lurking Leviathan", "Sewer Lord"],
  "tribes": ["Beast"],
  "tiers": [4, 3],
  "synergy": "Sewer Lord spawns rats every shop phase — each one passively stacks Leviathan's +1/+1 buff without spending any actions.",
  "leads_to": "Beasts - Leviathan"
}
```

| Field | Type | Description |
|-------|------|-------------|
| `cards` | `list[str]` | Exactly 2 card names. Must be valid hsbg.cards slugifiable names. |
| `tribes` | `list[str]` | Tribes required for this combo to appear. Uses same values as `comps.json`. |
| `tiers` | `list[int]` | Tavern tier each card first appears at (display only, index matches `cards`). |
| `synergy` | `str` | 1–2 sentence explanation of what makes the pair powerful. |
| `leads_to` | `str` | Must exactly match a `name` field in `comps.json`. Used to resolve the clickable comp link. |

**Filtering rule:** A combo appears when `set(combo["tribes"]).issubset(active_tribes)` — identical to how `filter_comps` works in `recommender.py`.

---

## New Module: `combo_recommender.py`

```python
COMBOS_PATH = Path(__file__).parent / "combos.json"

def load_combos(path: Path = COMBOS_PATH) -> list[dict]: ...
def filter_combos(combos: list[dict], active_tribes: set[str]) -> list[dict]: ...
```

`filter_combos` returns combos where `tribes` is a subset of `active_tribes`. No sorting — combos are browsed, not ranked. Returns `[]` when `active_tribes` is empty.

---

## UI Components

### `TabBar` (new widget in `overlay.py`)

- `QFrame` containing two `QPushButton` pills: **"EARLY COMBOS"** and **"LATE GAME"**
- Active tab styled with `BG_CHIP_ACTIVE` (gold); inactive with `BG_CHIP_IDLE`
- Emits `tab_changed = pyqtSignal(int)` (0 = Early Combos, 1 = Late Game)
- Sits between the tribe panel divider and the scroll area in `BgOverlay`

### `ComboCard` (new widget in `overlay.py`)

Mirrors `CompCard` structure:

- **Collapsed header:** both card names joined by " + ", a tier badge (e.g., "T3 / T4"), no arrow expand hint
- **Expanded detail** (click to toggle):
  - Two `CardChip` instances (one per card) — clicking opens the existing `CardPopup`
  - "SYNERGY" section: plain text label with the synergy description
  - "LEADS TO" section: a `QPushButton` styled as a dim underlined link with the comp name
- Clicking "LEADS TO" emits `comp_link_clicked = pyqtSignal(str)` with the exact comp name string

### `ComboList` (new widget in `overlay.py`)

- Mirrors `CompList`
- `update_combos(combos: list[dict])` clears and rebuilds the list
- Shows "EARLY COMBOS" header label at top
- Shows "No matching combos" empty-state when filtered list is empty
- Re-emits `comp_link_clicked` from any child `ComboCard` upward to `BgOverlay`

---

## `BgOverlay` Changes

### Tab switcher

- `TabBar` inserted between the tribe-panel divider and the scroll region
- `QStackedWidget` replaces the single `QScrollArea`:
  - Index 0: scroll area containing `ComboList`
  - Index 1: scroll area containing `CompList`
- `TabBar.tab_changed` → `BgOverlay._on_tab_changed(index)` → `self._stack.setCurrentIndex(index)`

### Tribe change handler

`_on_tribes_changed(active)` updates **both** panels regardless of which tab is visible:

```python
def _on_tribes_changed(self, active: set):
    comps = load_comps()
    filtered_comps = filter_comps(comps, active)
    self._comp_list.update_comps(filtered_comps)
    self._comp_cards = {c["name"]: card_widget for c, card_widget in zip(filtered_comps, ...)}

    combos = load_combos()
    self._combo_list.update_combos(filter_combos(combos, active))
```

### Comp-link scroll

`BgOverlay` maintains `self._comp_cards: dict[str, CompCard]` — populated each time `_on_tribes_changed` runs — mapping comp name → its `CompCard` widget.

`_on_comp_link(name: str)`:
1. Switch `TabBar` active button to "LATE GAME" and `_stack` to index 1
2. Look up `self._comp_cards.get(name)`
3. If found: `QScrollArea.ensureWidgetVisible(comp_card)`
4. If not found (comp filtered out by tribes): no-op — the tab switch still happens so the user sees the late game list

---

## Signal Flow

```
ComboCard.comp_link_clicked(name: str)
  → ComboList.comp_link_clicked(name: str)   [re-emitted]
    → BgOverlay._on_comp_link(name: str)
        → _tab_bar.set_active(1)
        → _stack.setCurrentIndex(1)
        → _comp_scroll.ensureWidgetVisible(_comp_cards[name])
```

---

## Combo Catalog (initial entries)

~25–30 curated combos covering all tribes represented in `comps.json`:

| Cards | Tribes | Leads To |
|-------|--------|----------|
| Lurking Leviathan + Sewer Lord | Beast | Beasts - Leviathan |
| Titus Rivendare + Goldrinn, The Great Wolf | Beast | Beasts - Summons |
| Rylak Metalhead + Hunting Tiger Shark | Beast | Beasts - RDU |
| Darkgaze Elder + Prickly Piper | Quillboar | Quilboar - Darkgaze |
| Gem Smuggler + Titus Rivendare | Quillboar | Quilboar - Smuggler |
| Bristlebach + Prickly Piper | Quillboar | Quilboar - Combat Scaling |
| Handless Forsaken + Drustfallen Butcher | Undead | Undead - Attack Scaling |
| Leeroy the Reckless + Bile Spitter | Undead | Undead - Overflow |
| Titus Rivendare + Cadaver Caretaker | Murloc | Murlocs - Reborn Loop |
| Magicfin Mycologist + Primitive Painter | Murloc | Murlocs - APM |
| Bile Spitter + Diremuck Forager | Murloc | Murlocs - Venom Scam |
| Groundbreaker + Darkcrest Strategist | Naga | Nagas - Groundbreaker |
| Ruthless Queensguard + Maelstrom Emergent | Naga | Nagas - Combat Scaling |
| Living Azerite + Leyline Surfacer | Elemental | Elementals - Shop Buff |
| Persistent Poet + Fire-forged Evoker | Dragon | Dragons - Spells |
| Ring Bearer + Persistent Poet | Dragon | Dragons - Shiny Ring |
| Nightbane, Ignited + Draconic Warden | Dragon | Dragons - Battlecries |
| Sky Admiral Rogers + Proud Privateer | Pirate | Pirates - Bounty APM |
| Malchezaar, Prince of Dance + Ashen Corruptor | Demon | Demons - Shop Buff |
| Ancestral Automaton + Kangor's Apprentice | Mech | Mechs - Automaton |
| Cataclysmic Harbinger + Drakkari Enchanter | Neutral | Back to Back |
| Cataclysmic Harbinger + Felfire Conjurer | Neutral | Back to Back |
| Gem Smuggler + Moon-bacon Jazzer | Quillboar | Quilboar - Smuggler |
| Brann Bronzebeard + Groundbreaker | Naga | Nagas - Groundbreaker |
| Brann Bronzebeard + Magicfin Mycologist | Murloc | Murlocs - APM |

---

## Out of Scope

- Trio or larger combos
- Combos that span tiers 5–6
- Auto-discovery of combos from the API
- Ranking or sorting combos by strength
- Combo-specific hotkey or scan integration

---

## Testing

- `tests/test_combo_recommender.py`: mirror of `test_recommender.py` — test load, filter by tribe subset, empty tribes returns empty list, unknown tribe returns empty list
- Manual: launch overlay, toggle tribes, verify combo list updates; click a card name, verify popup; click a comp link, verify tab switches and scrolls to correct `CompCard`
