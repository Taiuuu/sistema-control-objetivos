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
        background_alpha: int | None = None,
    ):
        super().__init__(parent)
        if background_alpha is not None and not 0 <= background_alpha <= 255:
            raise ValueError("La opacidad de fondo debe estar entre 0 y 255.")
        self._theme_manager = get_theme_manager()
        self._shadow_enabled = shadow
        self._contrast = contrast
        self._background_alpha = background_alpha
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
        if self._background_alpha is not None:
            background = rgba(background, self._background_alpha)
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


def wrap_content_in_glass_card(widget, *, content_margins: int = 18) -> GlassCard:
    """Wrap an existing root layout in a theme-aware card without changing its contents."""
    root_layout = widget.layout()
    if root_layout is None:
        raise ValueError("El widget debe tener un layout raíz para envolver su contenido.")
    if getattr(widget, "_glass_card_wrapper", None) is not None:
        return widget._glass_card_wrapper

    card = GlassCard(widget, content_margins=content_margins)
    while root_layout.count():
        item = root_layout.takeAt(0)
        child_widget = item.widget()
        child_layout = item.layout()
        if child_widget is not None:
            card.add_widget(child_widget)
        elif child_layout is not None:
            card.add_layout(child_layout)
        else:
            card.content_layout.addItem(item)
    root_layout.addWidget(card)
    widget._glass_card_wrapper = card
    return card
