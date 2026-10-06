"""Botones, búsqueda y barra de progreso reutilizables."""

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QIcon, QPainter, QPen, QPixmap
from PyQt6.QtWidgets import QLineEdit, QProgressBar, QPushButton

from ui.components.base import connect_theme


class PillButton(QPushButton):
    """Botón pill con variantes primary, secondary, ghost y danger."""

    _VARIANTS = {"primary", "secondary", "ghost", "danger"}

    def __init__(self, text: str, variant: str = "primary", parent=None):
        if variant not in self._VARIANTS:
            raise ValueError(f"Variante no válida: {variant!r}. Opciones: {sorted(self._VARIANTS)}")
        super().__init__(text, parent)
        self.variant = variant
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        connect_theme(self, self._apply_theme)

    def _apply_theme(self, theme_name: str) -> None:
        tokens = self._theme_manager.tokens(theme_name)
        colors = {
            "primary": ("#0A6506", "#FFFFFF", "#075704", "#FFFFFF"),
            "secondary": (tokens["surface_alt"], tokens["text_primary"], tokens["surface"], tokens["text_primary"]),
            "ghost": ("transparent", tokens["text_primary"], tokens["surface_alt"], tokens["text_primary"]),
            "danger": (
                tokens["danger_button_bg"],
                tokens["danger_button_text"],
                tokens["danger_button_hover"],
                tokens["danger_button_text"],
            ),
        }
        background, foreground, hover_bg, hover_fg = colors[self.variant]
        pressed_bg = (
            "#064A03"
            if self.variant == "primary"
            else tokens["danger_button_bg"]
            if self.variant == "danger"
            else tokens["surface_alt"]
        )
        self.setStyleSheet(
            f"""
            QPushButton {{
                min-height: {tokens["control_height"]};
                padding: 0 {tokens["spacing_lg"]};
                color: {foreground};
                background-color: {background};
                border: 1px solid {tokens["border"] if self.variant in {"secondary", "ghost"} else background};
                border-radius: {tokens["radius_lg"]};
                font-weight: 600;
            }}
            QPushButton:hover {{
                color: {hover_fg};
                background-color: {hover_bg};
                border-color: {tokens["accent"]};
            }}
            QPushButton:pressed {{
                background-color: {pressed_bg};
                border-color: {pressed_bg};
            }}
            QPushButton:disabled {{
                color: {tokens["text_disabled"]};
                background-color: {tokens["surface_alt"]};
                border-color: {tokens["border"]};
            }}
            """
        )


class SearchInput(QLineEdit):
    """Campo de búsqueda con icono de lupa integrado al inicio."""

    def __init__(self, placeholder: str = "Buscar...", parent=None):
        super().__init__(parent)
        self.setPlaceholderText(placeholder)
        self._search_action = self.addAction(
            QIcon(),
            QLineEdit.ActionPosition.LeadingPosition,
        )
        connect_theme(self, self._apply_theme)

    def _apply_theme(self, theme_name: str) -> None:
        tokens = self._theme_manager.tokens(theme_name)
        self._search_action.setIcon(_search_icon(tokens["text_secondary"]))
        self.setStyleSheet(
            f"""
            QLineEdit {{
                min-height: {tokens["control_height"]};
                padding: 0 {tokens["spacing_sm"]};
                color: {tokens["text_primary"]};
                background-color: {tokens["surface_alt"]};
                border: 1px solid {tokens["border"]};
                border-radius: {tokens["radius_lg"]};
                selection-background-color: {tokens["accent"]};
                selection-color: {tokens["accent_text"]};
            }}
            QLineEdit:focus {{ border-color: {tokens["accent"]}; }}
            QLineEdit::placeholder {{ color: {tokens["text_secondary"]}; }}
            """
        )


def _search_icon(color: str) -> QIcon:
    pixmap = QPixmap(18, 18)
    pixmap.fill(Qt.GlobalColor.transparent)
    painter = QPainter(pixmap)
    pen = QPen(QColor(color), 1.8)
    pen.setCapStyle(Qt.PenCapStyle.RoundCap)
    painter.setPen(pen)
    painter.drawEllipse(2, 2, 9, 9)
    painter.drawLine(10, 10, 16, 16)
    painter.end()
    return QIcon(pixmap)


class ProgressBarThin(QProgressBar):
    """Barra de progreso delgada, sin texto y adaptable al tema."""

    def __init__(self, value: int = 0, parent=None):
        super().__init__(parent)
        self.setRange(0, 100)
        self.setValue(value)
        self.setTextVisible(False)
        connect_theme(self, self._apply_theme)

    def _apply_theme(self, theme_name: str) -> None:
        tokens = self._theme_manager.tokens(theme_name)
        self.setFixedHeight(6)
        self.setStyleSheet(
            f"""
            QProgressBar {{
                min-height: 6px;
                max-height: 6px;
                border: none;
                border-radius: 3px;
                background-color: {tokens["surface_alt"]};
            }}
            QProgressBar::chunk {{
                border-radius: 3px;
                background-color: {tokens["accent"]};
            }}
            """
        )
