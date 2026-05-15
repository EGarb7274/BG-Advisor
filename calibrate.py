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
        painter.setPen(QPen(QColor(255, 255, 255, 220)))
        painter.setFont(QFont("Arial", 14))
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
