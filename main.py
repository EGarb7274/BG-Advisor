import sys
import logging
import keyboard
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QObject, pyqtSignal

from config import load_config, save_config
from ocr import scan_tribes
from overlay import BgOverlay


class _HotkeyBridge(QObject):
    scan_triggered = pyqtSignal()
    toggle_triggered = pyqtSignal()
    calibrate_triggered = pyqtSignal()

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
        overlay.clear_error()
        try:
            matched, flagged = scan_tribes(cfg.get("crop_region"))
            if not matched and not flagged:
                overlay.show_error(
                    "No tribes detected — hover over the tribe panel in Hearthstone, then press F8"
                )
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

    bridge = _HotkeyBridge()
    bridge.scan_triggered.connect(on_scan)
    bridge.toggle_triggered.connect(on_toggle)
    bridge.calibrate_triggered.connect(on_calibrate)

    # Wire rescan button to same handler as F8
    overlay._tribe_panel.rescan_requested.connect(on_scan)

    try:
        keyboard.add_hotkey(cfg["hotkey_scan"],      lambda: bridge.scan_triggered.emit())
        keyboard.add_hotkey(cfg["hotkey_toggle"],    lambda: bridge.toggle_triggered.emit())
        keyboard.add_hotkey(cfg["hotkey_calibrate"], lambda: bridge.calibrate_triggered.emit())
        logger.info("BG-Advisor started")
    except Exception as e:
        overlay.show_error(f"Hotkey registration failed: {e}")
        logger.error(f"Hotkey registration failed: {e}")

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
