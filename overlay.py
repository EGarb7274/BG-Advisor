import sys
import logging
from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QPushButton, QFrame, QScrollArea,
)
from PyQt6.QtCore import Qt, QPoint, pyqtSignal

logger = logging.getLogger(__name__)

ALL_TRIBES = [
    "Murloc", "Beast", "Mech", "Demon", "Dragon",
    "Elemental", "Pirate", "Naga", "Undead", "Quillboar",
]


# ── Tribe Panel ────────────────────────────────────────────────────────────────

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
    rescan_requested = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._chips: dict[str, TribeChip] = {}
        self._build()

    def _build(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)

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


# ── Comp List ──────────────────────────────────────────────────────────────────

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

        detail = QLabel(f"Key: {', '.join(comp.get('key_minions', []))}")
        detail.setStyleSheet("color: #999; font-size: 11px;")
        detail.setWordWrap(True)
        layout.addWidget(detail)


class CompList(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(4)
        self._show_empty("No tribes active")

    def _show_empty(self, message: str):
        lbl = QLabel(message)
        lbl.setStyleSheet("color: #555; font-size: 11px;")
        self._layout.addWidget(lbl)

    def update_comps(self, comps: list[dict]):
        while self._layout.count():
            item = self._layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        if not comps:
            self._show_empty("No matching comps")
            return

        title = QLabel("COMPS")
        title.setStyleSheet("color: #bbb; font-size: 11px; font-weight: bold; letter-spacing: 1px;")
        self._layout.addWidget(title)
        for comp in comps:
            self._layout.addWidget(CompCard(comp))
        self._layout.addStretch()


# ── Error Banner ───────────────────────────────────────────────────────────────

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


# ── Main Overlay Window ────────────────────────────────────────────────────────

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
        self.resize(280, 560)
        screen = QApplication.primaryScreen().geometry()
        self.move(screen.width() - 300, 100)

    def _build_ui(self):
        container = QFrame(self)
        container.setStyleSheet(
            "QFrame { background: rgba(20, 20, 20, 210); border-radius: 8px; }"
        )
        main_layout = QVBoxLayout(container)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(8)

        self._error_banner = ErrorBanner()
        main_layout.addWidget(self._error_banner)

        self._tribe_panel = TribePanel()
        self._tribe_panel.tribes_changed.connect(self._on_tribes_changed)
        self._tribe_panel.rescan_requested.connect(self._on_rescan)
        main_layout.addWidget(self._tribe_panel)

        divider = QFrame()
        divider.setFrameShape(QFrame.Shape.HLine)
        divider.setStyleSheet("QFrame { color: #444; }")
        main_layout.addWidget(divider)

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
        main_layout.addWidget(scroll, stretch=1)

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
            self._drag_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.MouseButton.LeftButton and self._drag_pos:
            self.move(event.globalPosition().toPoint() - self._drag_pos)

    def toggle_visibility(self):
        self.setVisible(not self.isVisible())

    def show_error(self, message: str):
        self._error_banner.show_error(message)

    def clear_error(self):
        self._error_banner.clear_error()
