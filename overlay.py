import logging
from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QFrame, QScrollArea,
)
from PyQt6.QtCore import Qt, QPoint, pyqtSignal

logger = logging.getLogger(__name__)

ALL_TRIBES = [
    "Murloc", "Beast", "Mech", "Demon", "Dragon",
    "Elemental", "Pirate", "Naga", "Undead", "Quillboar",
    "Neutral",
]

# ── Palette ────────────────────────────────────────────────────────────────────
BG_APP       = "#13161d"
BG_TOPBAR    = "#0d1016"
BG_SECTION   = "#1a1f2c"
BG_ROW_A     = "#141820"
BG_ROW_B     = "#161b26"
BG_UNAVAIL   = "#111318"
COLOR_TEXT   = "#dde2f0"
COLOR_DIM    = "#6b7898"
COLOR_MUTED  = "#353d58"
COLOR_UNAVAIL = "#394060"

TRIBE_ACCENT = {
    "Murloc":    "#1a8060",
    "Beast":     "#7a3c10",
    "Mech":      "#1868a0",
    "Demon":     "#7a1535",
    "Dragon":    "#5030a0",
    "Elemental": "#b05010",
    "Pirate":    "#a82020",
    "Naga":      "#1848b0",
    "Undead":    "#287828",
    "Quillboar": "#982870",
    "Neutral":   "#484e68",
}


# ── Top-bar tribe icon chip ────────────────────────────────────────────────────

class TribeIconChip(QPushButton):
    def __init__(self, tribe: str, parent=None):
        super().__init__(tribe[:2].upper(), parent)
        self._tribe = tribe
        self.setCheckable(True)
        self.setFixedSize(26, 26)
        self.setToolTip(tribe)
        self.toggled.connect(self._apply_style)
        self._apply_style(False)

    def _apply_style(self, active: bool):
        accent = TRIBE_ACCENT.get(self._tribe, "#4a5268")
        if active:
            self.setStyleSheet(
                f"QPushButton {{ background: {accent}; color: #fff;"
                f"  border-radius: 4px; font-size: 8px; font-weight: bold;"
                f"  border: 1px solid {accent}; }}"
                f"QPushButton:hover {{ background: {accent}; }}"
            )
        else:
            self.setStyleSheet(
                "QPushButton { background: #1a1f2e; color: #3a4260;"
                "  border-radius: 4px; font-size: 8px; font-weight: bold;"
                "  border: 1px solid #252d42; }"
                "QPushButton:hover { color: #6b7898; border-color: #353d58; }"
            )


# ── Tribe section header ───────────────────────────────────────────────────────

class TribeSectionHeader(QFrame):
    def __init__(self, tribe: str, parent=None):
        super().__init__(parent)
        accent = TRIBE_ACCENT.get(tribe, "#4a5268")
        self.setStyleSheet(
            f"QFrame {{ background: {BG_SECTION}; border-left: 3px solid {accent}; }}"
        )
        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 5, 10, 5)
        lbl = QLabel(tribe.upper())
        lbl.setStyleSheet(
            f"color: {COLOR_DIM}; font-family: 'Segoe UI', sans-serif;"
            f"font-size: 10px; font-weight: bold; letter-spacing: 1px;"
            f"background: transparent;"
        )
        layout.addWidget(lbl)
        layout.addStretch()


# ── Minion row ─────────────────────────────────────────────────────────────────

class MinionRow(QFrame):
    def __init__(self, name: str, tribe: str, alt: bool = False, parent=None):
        super().__init__(parent)
        accent = TRIBE_ACCENT.get(tribe, "#4a5268")
        bg = BG_ROW_B if alt else BG_ROW_A
        self.setStyleSheet(
            f"QFrame {{ background: {bg}; border-right: 3px solid {accent}; }}"
            f"QFrame:hover {{ background: #1c2235; }}"
        )
        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 5, 10, 5)
        lbl = QLabel(name)
        lbl.setStyleSheet(
            f"color: {COLOR_TEXT}; font-family: 'Segoe UI', sans-serif;"
            f"font-size: 11px; background: transparent;"
        )
        layout.addWidget(lbl)
        layout.addStretch()


# ── Unavailable footer ─────────────────────────────────────────────────────────

class UnavailableSection(QFrame):
    def __init__(self, tribes: list[str], parent=None):
        super().__init__(parent)
        self.setStyleSheet(
            f"QFrame {{ background: {BG_UNAVAIL}; border-top: 1px solid #1a1f2c; }}"
        )
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 8, 10, 10)
        layout.setSpacing(3)
        header = QLabel("Unavailable")
        header.setStyleSheet(
            f"color: {COLOR_DIM}; font-family: 'Segoe UI', sans-serif;"
            f"font-size: 10px; font-weight: bold; letter-spacing: 1px;"
            f"background: transparent;"
        )
        layout.addWidget(header)
        names = QLabel(",  ".join(tribes))
        names.setStyleSheet(
            f"color: {COLOR_UNAVAIL}; font-family: 'Segoe UI', sans-serif;"
            f"font-size: 10px; background: transparent;"
        )
        names.setWordWrap(True)
        layout.addWidget(names)


# ── Error banner ───────────────────────────────────────────────────────────────

class ErrorBanner(QLabel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWordWrap(True)
        self.setStyleSheet(
            "QLabel { background: rgba(120, 20, 20, 200); color: #ffb8b8;"
            " padding: 6px 10px; font-size: 10px;"
            " font-family: 'Segoe UI', sans-serif;"
            " border-bottom: 1px solid #6a1a1a; }"
        )
        self.hide()

    def show_error(self, msg: str):
        self.setText(msg)
        self.show()

    def clear_error(self):
        self.hide()
        self.setText("")


# ── Main overlay window ────────────────────────────────────────────────────────

class BgOverlay(QWidget):
    rescan_requested = pyqtSignal()

    def __init__(self, config: dict):
        super().__init__()
        self._config = config
        self._drag_pos = QPoint()
        self._active_tribes: set[str] = set()
        self._chips: dict[str, TribeIconChip] = {}
        self._setup_window()
        self._build_ui()

    def _setup_window(self):
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setWindowOpacity(self._config.get("opacity", 0.93))
        self.setMinimumWidth(240)
        self.resize(240, 620)
        screen = QApplication.primaryScreen().geometry()
        self.move(screen.width() - 260, 80)

    def _build_ui(self):
        container = QFrame(self)
        container.setObjectName("container")
        container.setStyleSheet(
            f"QFrame#container {{ background: {BG_APP}; border-radius: 6px;"
            f"  border: 1px solid #1e2535; }}"
        )
        root = QVBoxLayout(container)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # ── Top bar ──
        top_bar = QFrame()
        top_bar.setObjectName("top_bar")
        top_bar.setStyleSheet(
            f"QFrame#top_bar {{ background: {BG_TOPBAR}; border-radius: 6px 6px 0 0;"
            f"  border-bottom: 1px solid #1a2030; }}"
        )
        top_layout = QHBoxLayout(top_bar)
        top_layout.setContentsMargins(6, 6, 6, 6)
        top_layout.setSpacing(3)

        for tribe in ALL_TRIBES:
            chip = TribeIconChip(tribe)
            chip.toggled.connect(lambda checked, t=tribe: self._on_chip_toggle(t, checked))
            self._chips[tribe] = chip
            top_layout.addWidget(chip)

        top_layout.addStretch()

        rescan_btn = QPushButton("↺")
        rescan_btn.setFixedSize(22, 22)
        rescan_btn.setToolTip("Rescan (F8)")
        rescan_btn.setStyleSheet(
            f"QPushButton {{ background: #1e2535; color: {COLOR_DIM};"
            f"  border-radius: 4px; font-size: 13px; border: 1px solid #252d42; }}"
            f"QPushButton:hover {{ color: {COLOR_TEXT}; border-color: #353d58; }}"
        )
        rescan_btn.clicked.connect(self.rescan_requested.emit)
        top_layout.addWidget(rescan_btn)

        exit_btn = QPushButton("×")
        exit_btn.setFixedSize(22, 22)
        exit_btn.setStyleSheet(
            f"QPushButton {{ background: transparent; color: {COLOR_DIM};"
            f"  border-radius: 4px; font-size: 16px; font-weight: bold; border: none; }}"
            f"QPushButton:hover {{ background: rgba(160, 30, 30, 180); color: #ffaaaa; }}"
        )
        exit_btn.clicked.connect(QApplication.instance().quit)
        top_layout.addWidget(exit_btn)

        root.addWidget(top_bar)

        # ── Error banner ──
        self._error_banner = ErrorBanner()
        root.addWidget(self._error_banner)

        # ── Scroll area ──
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet(
            f"QScrollArea {{ border: none; background: {BG_APP}; }}"
            f"QScrollBar:vertical {{ background: {BG_APP}; width: 4px; border-radius: 2px; }}"
            f"QScrollBar::handle:vertical {{ background: #2a3050; border-radius: 2px; }}"
            f"QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0px; }}"
        )
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        self._scroll_content = QFrame()
        self._scroll_content.setStyleSheet(f"QFrame {{ background: {BG_APP}; }}")
        self._scroll_layout = QVBoxLayout(self._scroll_content)
        self._scroll_layout.setContentsMargins(0, 0, 0, 0)
        self._scroll_layout.setSpacing(0)
        self._show_placeholder("No tribes selected\nPress F8 to scan or toggle tribes above")
        self._scroll_layout.addStretch()

        scroll.setWidget(self._scroll_content)
        root.addWidget(scroll, stretch=1)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(container)

    # ── Scroll content helpers ─────────────────────────────────────────────────

    def _show_placeholder(self, msg: str):
        lbl = QLabel(msg)
        lbl.setStyleSheet(
            f"color: {COLOR_MUTED}; font-size: 11px; padding: 20px 14px;"
            f"font-family: 'Segoe UI', sans-serif; background: transparent;"
        )
        lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl.setWordWrap(True)
        self._scroll_layout.addWidget(lbl)

    def _clear_scroll(self):
        while self._scroll_layout.count():
            item = self._scroll_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

    def _rebuild_list(self, comps: list[dict]):
        self._clear_scroll()

        if not self._active_tribes:
            self._show_placeholder("No tribes selected\nPress F8 to scan or toggle tribes above")
            self._scroll_layout.addStretch()
            return

        # Collect key minions per active tribe
        tribe_minions: dict[str, list[str]] = {t: [] for t in ALL_TRIBES if t in self._active_tribes}
        for comp in comps:
            for tribe in comp.get("tribes", []):
                if tribe in tribe_minions:
                    for minion in comp.get("key_minions", []):
                        if minion not in tribe_minions[tribe]:
                            tribe_minions[tribe].append(minion)

        # Render one section per active tribe
        for tribe in ALL_TRIBES:
            if tribe not in self._active_tribes:
                continue
            self._scroll_layout.addWidget(TribeSectionHeader(tribe))
            minions = tribe_minions.get(tribe, [])
            if minions:
                for i, minion in enumerate(minions):
                    self._scroll_layout.addWidget(MinionRow(minion, tribe, alt=bool(i % 2)))
            else:
                lbl = QLabel("  No comps available")
                lbl.setStyleSheet(
                    f"color: {COLOR_MUTED}; font-size: 10px; padding: 5px 16px;"
                    f"font-family: 'Segoe UI', sans-serif; background: {BG_ROW_A};"
                )
                self._scroll_layout.addWidget(lbl)

        # Unavailable footer
        unavailable = [t for t in ALL_TRIBES if t not in self._active_tribes]
        if unavailable:
            self._scroll_layout.addWidget(UnavailableSection(unavailable))

        self._scroll_layout.addStretch()

    def _refresh_comps(self):
        from recommender import load_comps, filter_comps
        comps = filter_comps(load_comps(), self._active_tribes)
        self._rebuild_list(comps)

    # ── Chip toggle ────────────────────────────────────────────────────────────

    def _on_chip_toggle(self, tribe: str, checked: bool):
        if checked:
            self._active_tribes.add(tribe)
        else:
            self._active_tribes.discard(tribe)
        self._refresh_comps()

    # ── Public API (called by main.py) ─────────────────────────────────────────

    @property
    def _tribe_panel(self):
        """Compatibility shim — main.py accesses overlay._tribe_panel.*"""
        return self

    def set_active_tribes(self, tribes: list[str], flagged_tokens: list[str] | None = None):
        self._active_tribes = set(tribes)
        for name, chip in self._chips.items():
            chip.blockSignals(True)
            chip.setChecked(name in self._active_tribes)
            chip.blockSignals(False)
            chip._apply_style(name in self._active_tribes)
        if flagged_tokens:
            self.show_error(f"⚠ Unrecognized: {', '.join(flagged_tokens)}")
        self._refresh_comps()

    def toggle_visibility(self):
        self.setVisible(not self.isVisible())

    def show_error(self, msg: str):
        self._error_banner.show_error(msg)

    def clear_error(self):
        self._error_banner.clear_error()

    # ── Drag to move ───────────────────────────────────────────────────────────

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.MouseButton.LeftButton and self._drag_pos:
            self.move(event.globalPosition().toPoint() - self._drag_pos)
