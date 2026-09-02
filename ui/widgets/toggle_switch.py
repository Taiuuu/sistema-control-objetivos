from PyQt6.QtCore import QRectF, Qt
from PyQt6.QtGui import QColor, QPainter, QPainterPath
from PyQt6.QtWidgets import QCheckBox


class ToggleSwitch(QCheckBox):
    """Switch compacto dibujado con QPainter, usable desde cualquier formulario."""

    def __init__(self, text: str = "", parent=None):
        super().__init__(text, parent)
        self.setFixedSize(50, 28)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setAccessibleName(text or "Interruptor")

    def paintEvent(self, _event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        track = QRectF(1, 4, 48, 20)
        track_color = QColor("#63E6BE" if self.isChecked() else "#3C4A70")
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(track_color)
        painter.drawRoundedRect(track, 10, 10)
        thumb = QRectF(28 if self.isChecked() else 4, 6, 16, 16)
        painter.setBrush(QColor("#FFFFFF"))
        painter.drawEllipse(thumb)
        painter.end()

    def hitButton(self, position):
        return self.rect().contains(position)
