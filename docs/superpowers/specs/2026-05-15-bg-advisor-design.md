# Hearthstone Battlegrounds Advisor — Design Spec

**Date:** 2026-05-15  
**Project:** BG-Advisor  
**Location:** `C:\Users\egarb\Projects\BG-Advisor`

---

## Overview

A Windows overlay application that runs alongside Hearthstone Battlegrounds. When the player presses a hotkey while hovering over the tribe info panel, the app OCR-scans the screen to detect which tribes are available that game, then displays recommended endgame compositions and their key minions in a semi-transparent always-on-top overlay.

---

## Architecture

Five focused components with clear responsibilities:

### 1. Hotkey Listener
- `keyboard` library registers global hotkeys
- `F8` — triggers screenshot + OCR scan
- `F9` — toggles overlay visible/hidden
- `Shift+F8` — enters crop calibration mode (crosshair selector to draw the OCR region)

### 2. OCR Engine
- Captures full screenshot via `Pillow`
- Crops to a configurable region defined in `config.json`
- Passes cropped image to Windows built-in OCR via `winrt.windows.media.ocr` (no Tesseract required)
- Matches recognized text against the known tribe name list using fuzzy matching (`difflib`) to handle minor OCR errors (e.g. "Murioc" → "Murloc")
- Returns a list of detected tribe names

### 3. Tribe Panel (Override UI)
- Always renders all possible Battlegrounds tribes
- OCR result sets the initial active/inactive state of each tribe
- Tribes are displayed as toggleable chips:
  - **Highlighted** = active (available this game)
  - **Dim** = inactive (not available or not detected)
- User can click any chip to toggle it on or off, overriding OCR
- A "Rescan" button (↺) re-triggers the OCR pipeline
- Unrecognized OCR tokens are flagged in orange so the user knows to verify

### 4. Comp Recommender
- Pure logic layer — no UI dependencies
- Takes the set of currently active tribes
- Filters `comps.json` to return comps whose `tribes` list is a subset of active tribes
- Comps requiring two tribes (e.g. Mech + Pirate) only appear if both tribes are active
- Returns results sorted by tier (descending)

### 5. Overlay Window
- PyQt6 `QWidget` with `Qt.WindowStaysOnTopHint` and `WA_TranslucentBackground`
- Click-through enabled on non-interactive areas so the game remains playable underneath
- Narrow vertical panel anchored to the right side of the screen by default
- Draggable via a title bar at the top
- Semi-transparent background (opacity configurable in `config.json`)

---

## UI Layout

```
┌─────────────────────────────┐
│  TRIBES                [↺]  │  ← rescan button
│  [Murlocs] [Pirates] [Mechs] │  ← all tribes shown; active = highlighted
│  [Beasts]  [Demons]  [...]   │  ← dim = inactive; click to toggle
├─────────────────────────────┤
│  COMPS                       │
│  ★★★ Murloc Flood            │
│    Key: Warleader, Tidecaller │
│    + Old Murk-Eye             │
│                              │
│  ★★  Mech Divine Shield       │
│    Key: Deflecto, Kangor      │
│                              │
│  ★★  Pirate Aggro             │
│    Key: Peggy, Yohoho         │
└─────────────────────────────┘
```

- Comps sorted by tier (★★★ highest first)
- Each comp shows: name, tier, and 2–4 key minions
- Panel is semi-transparent and draggable

---

## Data

### `comps.json`
Each entry:
```json
{
  "name": "Murloc Flood",
  "tier": 3,
  "tribes": ["Murloc"],
  "key_minions": ["Murloc Warleader", "Tidecaller", "Old Murk-Eye"]
}
```

- `tribes` — all tribes that must be active for this comp to appear
- `tier` — 1–3 representing comp strength/consistency (3 = strongest)
- `key_minions` — 2–4 most important minions for the comp

### `config.json`
```json
{
  "hotkey_scan": "F8",
  "hotkey_toggle": "F9",
  "crop_region": [x, y, width, height],
  "opacity": 0.85
}
```

### Data Source
- The Blizzard Battle.net API (free with developer account) provides authoritative tribe and card data for reference
- `comps.json` is a locally maintained file — updated manually after balance patches
- No runtime dependency on any external API; the Blizzard API is used only as a reference during initial data population and patch updates

---

## OCR Pipeline (Step-by-Step)

1. User hovers over the tribe info button in Hearthstone to reveal the tribe panel
2. User presses `F8`
3. App captures a full screenshot via `Pillow`
4. Screenshot is cropped to the region defined in `config.json` (`crop_region`)
5. Cropped image is passed to `winrt.windows.media.ocr`
6. Recognized text is fuzzy-matched against the known tribe name list
7. Matched tribes are set as active in the Tribe Panel; unmatched tokens are flagged orange
8. Comp Recommender recalculates and updates the comp list

### Calibration Mode (`Shift+F8`)
- Overlay temporarily shows a fullscreen crosshair selector
- User draws a rectangle over the tribe panel area
- Selected region is saved to `config.json` as `crop_region`

---

## Error Handling

| Scenario | Behavior |
|---|---|
| OCR finds no tribes | Overlay shows "No tribes detected"; all tribes default to inactive; Rescan button highlighted |
| OCR partial match | Unrecognized tokens flagged orange in Tribe Panel; user verifies manually |
| `comps.json` missing or malformed | Error banner shown in overlay; comp list empty; app does not crash |
| `config.json` missing | App starts with sensible defaults; prompts user to run calibration |
| Hotkey conflict | Logged to `bg.log`; notification shown in overlay |

---

## File Structure

```
BG-Advisor/
├── main.py              # entry point, hotkey listener setup
├── ocr.py               # screenshot capture and OCR pipeline
├── recommender.py       # comp filtering logic
├── overlay.py           # PyQt6 overlay window
├── calibrate.py         # crop region selector
├── comps.json           # comp data (manually maintained)
├── config.json          # user configuration
├── bg.log               # error/event log
└── docs/
    └── superpowers/
        └── specs/
            └── 2026-05-15-bg-advisor-design.md
```

---

## Dependencies

| Package | Purpose |
|---|---|
| `PyQt6` | Overlay window and UI |
| `Pillow` | Screenshot capture and image cropping |
| `keyboard` | Global hotkey listener |
| `winrt` | Windows OCR engine access |
| `difflib` | Fuzzy tribe name matching (stdlib) |
