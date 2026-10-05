from PyQt6.QtCore import QRectF, Qt
from PyQt6.QtGui import QColor, QPainter, QPainterPath
from PyQt6.QtWidgets import QCheckBox
from ui.theme.theme_manager import get_theme_manager


class ToggleSwitch(QCheckBox):
    """Switch compacto dibujado con QPainter, usable desde cualquier formulario."""

    def __init__(self, text: str = "", parent=None):
        super().__init__(text, parent)
        self._theme_manager = get_theme_manager()
        self.setFixedSize(50, 28)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setAccessibleName(text or "Interruptor")
        self._theme_manager.theme_changed.connect(lambda _name: self.update())

    def paintEvent(self, _event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        track = QRectF(1, 4, 48, 20)
        tokens = self._theme_manager.tokens()
        track_color = QColor(
            tokens["accent"] if self.isChecked() else tokens["surface_alt"]
        )
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(track_color)
        painter.drawRoundedRect(track, 10, 10)
        thumb = QRectF(28 if self.isChecked() else 4, 6, 16, 16)
        painter.setBrush(
            QColor(tokens["accent_text"] if self.isChecked() else tokens["text_primary"])
        )
        painter.drawEllipse(thumb)
        painter.end()

    def hitButton(self, position):
        return self.rect().contains(position)
