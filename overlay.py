import sys
import logging
from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QPushButton, QFrame, QScrollArea,
)
from PyQt6.QtCore import Qt, QPoint, QRect, QThread, pyqtSignal
from PyQt6.QtGui import QFont, QColor, QPixmap, QCursor

logger = logging.getLogger(__name__)

ALL_TRIBES = [
    "Murloc", "Beast", "Mech", "Demon", "Dragon",
    "Elemental", "Pirate", "Naga", "Undead", "Quillboar",
    "Neutral",
]

# ── Palette ────────────────────────────────────────────────────────────────────
BG_CONTAINER   = "rgba(14, 11, 9, 230)"
BG_HEADER      = "rgba(22, 16, 9, 245)"
BG_CHIP_ACTIVE = "#b8821e"
BG_CHIP_IDLE   = "rgba(38, 30, 20, 220)"
BG_CARD        = "rgba(28, 22, 14, 190)"
COLOR_GOLD     = "#c8922a"
COLOR_DIM      = "#6b5a45"
COLOR_BODY     = "#b8a898"
COLOR_MUTED    = "#4a3c2c"
COLOR_DIVIDER  = "#2e2216"
COLOR_WARN     = "#e07830"


# ── Tribe Chip ─────────────────────────────────────────────────────────────────

class TribeChip(QPushButton):
    def __init__(self, name: str, parent=None):
        super().__init__(name, parent)
        self.setCheckable(True)
        self.setStyleSheet(
            f"QPushButton {{"
            f"  background: {BG_CHIP_IDLE}; color: {COLOR_DIM};"
            f"  border-radius: 4px; padding: 5px 8px;"
            f"  font-family: 'Segoe UI', sans-serif;"
            f"  font-size: 11px; border: 1px solid #2a1e10;"
            f"}}"
            f"QPushButton:hover {{"
            f"  background: rgba(55, 42, 26, 220); color: {COLOR_BODY};"
            f"}}"
            f"QPushButton:checked {{"
            f"  background: {BG_CHIP_ACTIVE}; color: #fff;"
            f"  font-family: 'Segoe UI Semibold', 'Segoe UI', sans-serif;"
            f"  font-weight: 600; border: 1px solid #d4a030;"
            f"}}"
            f"QPushButton:checked:hover {{ background: #c8922a; }}"
        )


# ── Tribe Panel ────────────────────────────────────────────────────────────────

class TribePanel(QFrame):
    tribes_changed = pyqtSignal(set)
    rescan_requested = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._chips: dict[str, TribeChip] = {}
        self._build()

    def _build(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)

        header = QHBoxLayout()
        title = QLabel("TRIBES")
        title.setStyleSheet(
            f"color: {COLOR_GOLD}; font-family: 'Palatino Linotype', Georgia, serif;"
            f"font-size: 10px; font-weight: bold; letter-spacing: 2px;"
        )
        header.addWidget(title)
        header.addStretch()
        rescan = QPushButton("↺")
        rescan.setFixedSize(22, 22)
        rescan.setStyleSheet(
            f"QPushButton {{ background: {COLOR_MUTED}; color: {COLOR_BODY};"
            f"  border-radius: 4px; font-size: 13px; border: 1px solid #3a2c1a; }}"
            f"QPushButton:hover {{ background: #3d2e1a; color: {COLOR_GOLD}; }}"
        )
        rescan.clicked.connect(self.rescan_requested.emit)
        header.addWidget(rescan)
        layout.addLayout(header)

        grid = QGridLayout()
        grid.setSpacing(4)
        for i, tribe in enumerate(ALL_TRIBES):
            chip = TribeChip(tribe)
            chip.toggled.connect(self._emit_change)
            self._chips[tribe] = chip
            grid.addWidget(chip, i // 3, i % 3)
        layout.addLayout(grid)

        self._warning_label = QLabel("")
        self._warning_label.setStyleSheet(
            f"QLabel {{ color: {COLOR_WARN}; font-size: 10px; padding: 2px;"
            f"  font-family: 'Segoe UI', sans-serif; }}"
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


# ── Comp Card ──────────────────────────────────────────────────────────────────

TIER_COLORS = {1: "#7a7a7a", 2: "#4a9aff", 3: COLOR_GOLD}


# ── Card popup ─────────────────────────────────────────────────────────────────

_active_popup: 'CardPopup | None' = None


def _show_card_popup(card_name: str, global_pos: QPoint) -> None:
    global _active_popup
    if _active_popup is not None:
        try:
            _active_popup.close()
        except RuntimeError:
            pass
    _active_popup = CardPopup(card_name)
    _active_popup.position_near(global_pos)
    _active_popup.show()


class _CardFetcher(QThread):
    card_ready = pyqtSignal(dict)
    not_found = pyqtSignal()

    def __init__(self, name: str):
        super().__init__()
        self._name = name

    def run(self):
        from api import fetch_card
        card = fetch_card(self._name)
        if card:
            self.card_ready.emit(card)
        else:
            self.not_found.emit()


class _ImageFetcher(QThread):
    image_ready = pyqtSignal(bytes)

    def __init__(self, path: str):
        super().__init__()
        self._path = path

    def run(self):
        from api import fetch_image_bytes
        data = fetch_image_bytes(self._path)
        if data:
            self.image_ready.emit(data)


class CardPopup(QWidget):
    def __init__(self, card_name: str, parent=None):
        super().__init__(parent)
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setFixedWidth(230)
        self._fetcher: _CardFetcher | None = None
        self._img_fetcher: _ImageFetcher | None = None
        self._build_shell(card_name)
        self._start_fetch(card_name)

    def _build_shell(self, name: str):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)

        self._container = QFrame()
        self._container.setStyleSheet(
            f"QFrame {{ background: {BG_HEADER}; border-radius: 8px;"
            f"  border: 1px solid #3a2c1a; }}"
        )
        root = QVBoxLayout(self._container)
        root.setContentsMargins(0, 0, 0, 8)
        root.setSpacing(0)

        # Header row
        hdr = QFrame()
        hdr.setStyleSheet(
            f"QFrame {{ background: rgba(28, 20, 10, 250); border-radius: 8px 8px 0 0;"
            f"  border-bottom: 1px solid {COLOR_DIVIDER}; }}"
        )
        hdr_layout = QHBoxLayout(hdr)
        hdr_layout.setContentsMargins(10, 6, 6, 6)
        self._name_lbl = QLabel(name)
        self._name_lbl.setStyleSheet(
            f"color: #e8d8c0; font-family: 'Palatino Linotype', Georgia, serif;"
            f"font-size: 12px; font-weight: bold; background: transparent;"
        )
        close_btn = QPushButton("×")
        close_btn.setFixedSize(20, 20)
        close_btn.setStyleSheet(
            f"QPushButton {{ background: transparent; color: {COLOR_DIM};"
            f"  font-size: 15px; font-weight: bold; border: none; }}"
            f"QPushButton:hover {{ color: #ffaaaa; }}"
        )
        close_btn.clicked.connect(self.close)
        hdr_layout.addWidget(self._name_lbl)
        hdr_layout.addStretch()
        hdr_layout.addWidget(close_btn)
        root.addWidget(hdr)

        # Image area
        self._img_lbl = QLabel("Loading…")
        self._img_lbl.setFixedHeight(60)
        self._img_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._img_lbl.setStyleSheet(
            f"color: {COLOR_MUTED}; font-size: 10px;"
            f"background: rgba(10, 7, 4, 140); border: none;"
        )
        root.addWidget(self._img_lbl)

        # Stats + text body
        self._body = QFrame()
        self._body.setStyleSheet("QFrame { background: transparent; }")
        self._body_layout = QVBoxLayout(self._body)
        self._body_layout.setContentsMargins(10, 6, 10, 0)
        self._body_layout.setSpacing(4)
        root.addWidget(self._body)

        outer.addWidget(self._container)

    def _start_fetch(self, name: str):
        self._fetcher = _CardFetcher(name)
        self._fetcher.card_ready.connect(self._populate)
        self._fetcher.not_found.connect(self._show_not_found)
        self._fetcher.start()

    def _clear_body(self):
        while self._body_layout.count():
            item = self._body_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
            elif item.layout():
                # clear sub-layout
                while item.layout().count():
                    sub = item.layout().takeAt(0)
                    if sub.widget():
                        sub.widget().deleteLater()

    def _populate(self, card: dict):
        self._name_lbl.setText(card.get("name", self._name_lbl.text()))
        self._clear_body()

        tier = card.get("tier", 0)
        stars = ("★" * tier + "☆" * max(0, 3 - tier)) if tier else ""
        star_color = {1: "#7a7a7a", 2: "#4a9aff", 3: COLOR_GOLD}.get(tier, COLOR_DIM)
        tribe = ", ".join(card.get("minionTypes", [])) or "Neutral"
        atk = card.get("attack", "?")
        hp = card.get("health", "?")

        meta = QHBoxLayout()
        star_lbl = QLabel(stars)
        star_lbl.setStyleSheet(f"color: {star_color}; font-size: 10px; background: transparent;")
        tribe_lbl = QLabel(tribe)
        tribe_lbl.setStyleSheet(f"color: {COLOR_DIM}; font-size: 10px; background: transparent;")
        stats_lbl = QLabel(f"{atk} / {hp}")
        stats_lbl.setStyleSheet(
            f"color: {COLOR_BODY}; font-size: 11px; font-weight: bold; background: transparent;"
        )
        meta.addWidget(star_lbl)
        meta.addSpacing(4)
        meta.addWidget(tribe_lbl)
        meta.addStretch()
        meta.addWidget(stats_lbl)
        self._body_layout.addLayout(meta)

        div = QFrame()
        div.setFrameShape(QFrame.Shape.HLine)
        div.setStyleSheet(f"color: {COLOR_DIVIDER};")
        self._body_layout.addWidget(div)

        text = card.get("text", "").strip()
        if text:
            txt_lbl = QLabel(text)
            txt_lbl.setWordWrap(True)
            txt_lbl.setStyleSheet(
                f"color: {COLOR_BODY}; font-family: 'Segoe UI', sans-serif;"
                f"font-size: 10px; font-style: italic; background: transparent;"
            )
            self._body_layout.addWidget(txt_lbl)

        self.adjustSize()

        img_path = card.get("image")
        if img_path:
            self._img_fetcher = _ImageFetcher(img_path)
            self._img_fetcher.image_ready.connect(self._set_image)
            self._img_fetcher.start()

    def _set_image(self, data: bytes):
        px = QPixmap()
        if px.loadFromData(data):
            px = px.scaledToWidth(228, Qt.TransformationMode.SmoothTransformation)
            self._img_lbl.setFixedHeight(px.height())
            self._img_lbl.setPixmap(px)
            self._img_lbl.setText("")
        self.adjustSize()

    def _show_not_found(self):
        self._clear_body()
        lbl = QLabel("Card not found in API")
        lbl.setStyleSheet(f"color: {COLOR_MUTED}; font-size: 10px; background: transparent;")
        self._body_layout.addWidget(lbl)
        self._img_lbl.setText("—")
        self.adjustSize()

    def position_near(self, global_pos: QPoint):
        screen = QApplication.primaryScreen().geometry()
        x = global_pos.x() + 14
        y = global_pos.y() - 20
        if x + self.width() > screen.right():
            x = global_pos.x() - self.width() - 14
        y = max(screen.top(), min(y, screen.bottom() - self.height()))
        self.move(x, y)


# ── Card name chip (clickable) ──────────────────────────────────────────────────

class CardChip(QPushButton):
    def __init__(self, name: str, parent=None):
        super().__init__(name, parent)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setStyleSheet(
            f"QPushButton {{ background: transparent; color: {COLOR_BODY};"
            f"  font-family: 'Segoe UI', sans-serif; font-size: 10px;"
            f"  border: none; padding: 1px 0; text-align: left; }}"
            f"QPushButton:hover {{ color: {COLOR_GOLD}; text-decoration: underline; }}"
        )
        self.clicked.connect(self._on_click)

    def _on_click(self):
        pos = self.mapToGlobal(self.rect().bottomLeft())
        _show_card_popup(self.text(), pos)


# ── Detail section ─────────────────────────────────────────────────────────────

def _detail_section(label: str, items: list[str] | str, clickable: bool = False) -> QFrame:
    """A labelled section row used inside the expanded comp detail."""
    frame = QFrame()
    frame.setStyleSheet("QFrame { background: transparent; }")
    layout = QVBoxLayout(frame)
    layout.setContentsMargins(0, 4, 0, 0)
    layout.setSpacing(2)

    lbl = QLabel(label.upper())
    lbl.setStyleSheet(
        f"color: {COLOR_GOLD}; font-family: 'Segoe UI', sans-serif;"
        f"font-size: 9px; font-weight: bold; letter-spacing: 1px; background: transparent;"
    )
    layout.addWidget(lbl)

    if clickable and isinstance(items, list):
        for name in items:
            chip = CardChip(name)
            layout.addWidget(chip)
    else:
        text = ", ".join(items) if isinstance(items, list) else items
        body = QLabel(text)
        body.setStyleSheet(
            f"color: {COLOR_BODY}; font-family: 'Segoe UI', sans-serif;"
            f"font-size: 10px; background: transparent;"
        )
        body.setWordWrap(True)
        layout.addWidget(body)

    return frame


class CompCard(QFrame):
    def __init__(self, comp: dict, parent=None):
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

        # ── Header row (always visible) ──
        tier = comp.get("tier", 1)
        star_color = TIER_COLORS.get(tier, COLOR_GOLD)
        stars = "★" * tier + "☆" * (3 - tier)

        header_row = QHBoxLayout()
        header_row.setSpacing(6)

        star_lbl = QLabel(stars)
        star_lbl.setStyleSheet(
            f"color: {star_color}; font-size: 11px; letter-spacing: 1px; background: transparent;"
        )
        name_lbl = QLabel(comp["name"])
        name_lbl.setStyleSheet(
            f"color: #e8d8c0; font-family: 'Palatino Linotype', Georgia, serif;"
            f"font-size: 13px; font-weight: bold; background: transparent;"
        )
        self._arrow = QLabel("▶")
        self._arrow.setStyleSheet(
            f"color: {COLOR_MUTED}; font-size: 9px; background: transparent;"
        )

        header_row.addWidget(star_lbl)
        header_row.addWidget(name_lbl)
        header_row.addStretch()
        header_row.addWidget(self._arrow)
        root.addLayout(header_row)

        # ── Collapsed summary ──
        summary_text = ", ".join(comp.get("key_minions", [])[:3])
        if len(comp.get("key_minions", [])) > 3:
            summary_text += "…"
        self._summary = QLabel(summary_text)
        self._summary.setStyleSheet(
            f"color: {COLOR_DIM}; font-size: 10px;"
            f"font-family: 'Segoe UI', sans-serif; background: transparent;"
        )
        self._summary.setWordWrap(True)
        root.addWidget(self._summary)

        # ── Expanded detail panel (hidden by default) ──
        self._detail = QFrame()
        self._detail.setStyleSheet(
            f"QFrame {{ background: transparent; border-top: 1px solid #3a2c1a; }}"
        )
        detail_layout = QVBoxLayout(self._detail)
        detail_layout.setContentsMargins(0, 6, 0, 2)
        detail_layout.setSpacing(0)

        if comp.get("key_minions"):
            detail_layout.addWidget(_detail_section("Key Minions", comp["key_minions"], clickable=True))
        if comp.get("enablers"):
            detail_layout.addWidget(_detail_section("Enablers", comp["enablers"]))
        if comp.get("addon_cards"):
            detail_layout.addWidget(_detail_section("Addon Cards", comp["addon_cards"], clickable=True))
        if comp.get("when_to_commit"):
            detail_layout.addWidget(_detail_section("When to Commit", comp["when_to_commit"]))
        if comp.get("how_to_play"):
            detail_layout.addWidget(_detail_section("How to Play", comp["how_to_play"]))

        self._detail.hide()
        root.addWidget(self._detail)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._expanded = not self._expanded
            self._detail.setVisible(self._expanded)
            self._summary.setVisible(not self._expanded)
            self._arrow.setText("▼" if self._expanded else "▶")


# ── Comp List ──────────────────────────────────────────────────────────────────

class CompList(QFrame):
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

    def update_comps(self, comps: list[dict]):
        while self._layout.count():
            item = self._layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

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
            self._layout.addWidget(CompCard(comp))
        self._layout.addStretch()


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


# ── Error Banner ───────────────────────────────────────────────────────────────

class ErrorBanner(QLabel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWordWrap(True)
        self.setStyleSheet(
            "QLabel { background: rgba(100, 20, 20, 200); color: #ffb8b8;"
            " padding: 6px 8px; border-radius: 4px; font-size: 10px;"
            " font-family: 'Segoe UI', sans-serif;"
            " border: 1px solid #6a1a1a; }"
        )
        self.hide()

    def show_error(self, message: str):
        self.setText(message)
        self.show()

    def clear_error(self):
        self.hide()
        self.setText("")


# ── Main Overlay Window ────────────────────────────────────────────────────────

_RESIZE_MARGIN = 8

_EDGE_CURSORS = {
    'tl': Qt.CursorShape.SizeFDiagCursor,
    'br': Qt.CursorShape.SizeFDiagCursor,
    'tr': Qt.CursorShape.SizeBDiagCursor,
    'bl': Qt.CursorShape.SizeBDiagCursor,
    'l':  Qt.CursorShape.SizeHorCursor,
    'r':  Qt.CursorShape.SizeHorCursor,
    't':  Qt.CursorShape.SizeVerCursor,
    'b':  Qt.CursorShape.SizeVerCursor,
}


class BgOverlay(QWidget):
    def __init__(self, config: dict):
        super().__init__()
        self._config = config
        self._dragging = False
        self._drag_pos = QPoint()
        self._resizing = False
        self._resize_edge: str | None = None
        self._resize_start_global = QPoint()
        self._resize_start_geom: QRect | None = None
        self._setup_window()
        self._build_ui()

    def _setup_window(self):
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setWindowOpacity(self._config.get("opacity", 0.88))
        self.setMinimumSize(240, 300)
        self.resize(285, 580)
        screen = QApplication.primaryScreen().geometry()
        self.move(screen.width() - 305, 100)

    def _get_edge(self, pos: QPoint) -> str | None:
        x, y, w, h, m = pos.x(), pos.y(), self.width(), self.height(), _RESIZE_MARGIN
        left, right, top, bottom = x < m, x > w - m, y < m, y > h - m
        if top and left:    return 'tl'
        if top and right:   return 'tr'
        if bottom and left: return 'bl'
        if bottom and right: return 'br'
        if left:   return 'l'
        if right:  return 'r'
        if top:    return 't'
        if bottom: return 'b'
        return None

    def _do_resize(self, gpos: QPoint):
        delta = gpos - self._resize_start_global
        g = self._resize_start_geom
        new_geom = QRect(g)
        e = self._resize_edge
        if 'r' in e: new_geom.setRight(g.right() + delta.x())
        if 'l' in e: new_geom.setLeft(g.left() + delta.x())
        if 'b' in e: new_geom.setBottom(g.bottom() + delta.y())
        if 't' in e: new_geom.setTop(g.top() + delta.y())
        self.setGeometry(new_geom)  # Qt enforces minimumSize automatically

    def _build_ui(self):
        container = QFrame(self)
        container.setStyleSheet(
            f"QFrame {{ background: {BG_CONTAINER}; border-radius: 8px;"
            f"  border: 1px solid #2a1e10; }}"
        )

        main_layout = QVBoxLayout(container)
        main_layout.setContentsMargins(0, 0, 0, 10)
        main_layout.setSpacing(0)

        # ── Header bar ──
        header_bar = QFrame()
        header_bar.setStyleSheet(
            f"QFrame {{ background: {BG_HEADER}; border-radius: 8px 8px 0 0;"
            f"  border-bottom: 1px solid {COLOR_DIVIDER}; }}"
        )
        header_layout = QHBoxLayout(header_bar)
        header_layout.setContentsMargins(12, 8, 8, 8)

        title = QLabel("BG ADVISOR")
        title.setStyleSheet(
            f"color: {COLOR_GOLD}; font-family: 'Palatino Linotype', Georgia, serif;"
            f"font-size: 13px; font-weight: bold; letter-spacing: 2px;"
            f"border: none; background: transparent;"
        )
        header_layout.addWidget(title)
        header_layout.addStretch()

        exit_btn = QPushButton("×")
        exit_btn.setFixedSize(22, 22)
        exit_btn.setStyleSheet(
            f"QPushButton {{ background: transparent; color: {COLOR_DIM};"
            f"  border-radius: 4px; font-size: 16px; font-weight: bold; border: none; }}"
            f"QPushButton:hover {{ background: rgba(160, 30, 30, 180); color: #ffaaaa; }}"
        )
        exit_btn.clicked.connect(QApplication.instance().quit)
        header_layout.addWidget(exit_btn)
        main_layout.addWidget(header_bar)

        # ── Body ──
        body = QVBoxLayout()
        body.setContentsMargins(10, 10, 10, 0)
        body.setSpacing(8)

        self._error_banner = ErrorBanner()
        body.addWidget(self._error_banner)

        self._tribe_panel = TribePanel()
        self._tribe_panel.tribes_changed.connect(self._on_tribes_changed)
        self._tribe_panel.rescan_requested.connect(self._on_rescan)
        body.addWidget(self._tribe_panel)

        divider = QFrame()
        divider.setFrameShape(QFrame.Shape.HLine)
        divider.setStyleSheet(f"QFrame {{ color: {COLOR_DIVIDER}; }}")
        body.addWidget(divider)

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

        main_layout.addLayout(body)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(container)

    def _on_rescan(self):
        pass  # replaced by main.py

    def _on_tribes_changed(self, active: set):
        from recommender import load_comps, filter_comps
        comps = load_comps()
        self._comp_list.update_comps(filter_comps(comps, active))

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            pos = event.position().toPoint()
            edge = self._get_edge(pos)
            if edge:
                self._resizing = True
                self._resize_edge = edge
                self._resize_start_global = event.globalPosition().toPoint()
                self._resize_start_geom = self.geometry()
            else:
                self._dragging = True
                self._drag_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()

    def mouseMoveEvent(self, event):
        gpos = event.globalPosition().toPoint()
        if self._resizing and event.buttons() == Qt.MouseButton.LeftButton:
            self._do_resize(gpos)
        elif self._dragging and event.buttons() == Qt.MouseButton.LeftButton:
            self.move(gpos - self._drag_pos)
        else:
            edge = self._get_edge(event.position().toPoint())
            self.setCursor(_EDGE_CURSORS.get(edge, Qt.CursorShape.ArrowCursor))

    def mouseReleaseEvent(self, event):
        self._resizing = False
        self._dragging = False
        self._resize_edge = None
        self._drag_pos = QPoint()
        self.setCursor(Qt.CursorShape.ArrowCursor)

    def toggle_visibility(self):
        self.setVisible(not self.isVisible())

    def show_error(self, message: str):
        self._error_banner.show_error(message)

    def clear_error(self):
        self._error_banner.clear_error()
