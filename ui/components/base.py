"""Bases y estilos compartidos para componentes que responden al tema."""

from PyQt6.QtWidgets import QFrame, QGraphicsDropShadowEffect, QVBoxLayout

from ui.theme.colors import parse_color
from ui.theme.theme_manager import get_theme_manager


def px(tokens: dict[str, str], key: str) -> int:
    return int(tokens[key].removesuffix("px"))


def rgba(color: str, alpha: int) -> str:
    red, green, blue, _ = parse_color(color).getRgb()
    return f"rgba({red}, {green}, {blue}, {alpha})"


class GlassCard(QFrame):
    """Tarjeta con superficie opaca del tema y sombra opcional."""

    def __init__(
        self,
        parent=None,
        *,
        shadow: bool = False,
        contrast: bool = False,
        content_margins: int | None = None,
    ):
        super().__init__(parent)
        self._theme_manager = get_theme_manager()
        self._shadow_enabled = shadow
        self._contrast = contrast
        self.setObjectName("ContrastCard" if contrast else "GlassCard")
        self.setFrameShape(QFrame.Shape.NoFrame)
        self.content_layout = QVBoxLayout(self)
        margins = 18 if content_margins is None else content_margins
        self.content_layout.setContentsMargins(margins, margins, margins, margins)
        self.content_layout.setSpacing(12)

        self._shadow_effect = None
        if shadow:
            effect = QGraphicsDropShadowEffect(self)
            effect.setBlurRadius(22)
            effect.setOffset(0, 7)
            self.setGraphicsEffect(effect)
            self._shadow_effect = effect

        GlassCard._apply_theme(self, self._theme_manager.current())
        self._theme_manager.theme_changed.connect(self._apply_theme)

    def _apply_theme(self, theme_name: str) -> None:
        tokens = self._theme_manager.tokens(theme_name)
        background = tokens["card_contrast"] if self._contrast else tokens["surface"]
        self.setStyleSheet(
            f"""
            QFrame#{self.objectName()} {{
                background-color: {background};
                border: 1px solid {tokens["border"]};
                border-radius: {tokens["radius_card"]};
            }}
            """
        )
        if self._shadow_effect is not None:
            color = parse_color(tokens["shadow"])
            self._shadow_effect.setColor(color)

    def add_widget(self, widget, stretch: int = 0) -> None:
        self.content_layout.addWidget(widget, stretch)

    def add_layout(self, layout, stretch: int = 0) -> None:
        self.content_layout.addLayout(layout, stretch)


def style_label(label, color: str, font_size: str, *, weight: int = 400) -> None:
    label.setStyleSheet(
        f"color: {color}; font-size: {font_size}; font-weight: {weight};"
        " background-color: transparent;"
    )


def connect_theme(widget, callback) -> None:
    widget._theme_manager = get_theme_manager()
    widget._theme_manager.theme_changed.connect(callback)
    callback(widget._theme_manager.current())
