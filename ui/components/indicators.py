"""Indicadores, tarjetas KPI y logo reactivos al tema."""

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPixmap
from PyQt6.QtWidgets import QHBoxLayout, QLabel, QVBoxLayout

from ui.components.base import GlassCard, connect_theme, rgba, style_label
from ui.components.controls import ProgressBarThin


class KpiCard(GlassCard):
    """Card KPI con icono circular, etiqueta y valor destacado."""

    def __init__(
        self,
        label: str,
        value: str | int | float,
        icon: str = "•",
        parent=None,
        *,
        shadow: bool = False,
        contrast: bool = False,
        compact: bool = False,
    ):
        super().__init__(
            parent,
            shadow=shadow,
            contrast=contrast,
            content_margins=10 if compact else None,
        )
        self._compact = compact
        if compact:
            self.setFixedHeight(72)
        row = QHBoxLayout()
        row.setSpacing(8 if compact else 12)
        self.icon_label = QLabel(icon)
        self.icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon_size = 30 if compact else 42
        self.icon_label.setFixedSize(icon_size, icon_size)

        text_column = QVBoxLayout()
        text_column.setSpacing(2 if compact else 3)
        self.caption_label = QLabel(label)
        self.value_label = QLabel(str(value))
        text_column.addWidget(self.caption_label)
        text_column.addWidget(self.value_label)
        row.addWidget(self.icon_label, 0, Qt.AlignmentFlag.AlignVCenter)
        row.addLayout(text_column, 1)
        self.add_layout(row)
        self._apply_theme(self._theme_manager.current())
        self._theme_manager.theme_changed.connect(self._apply_theme)

    def set_value(self, value: str | int | float) -> None:
        self.value_label.setText(str(value))

    def set_label(self, label: str) -> None:
        self.caption_label.setText(label)

    def _apply_theme(self, theme_name: str) -> None:
        tokens = self._theme_manager.tokens(theme_name)
        style_label(
            self.icon_label,
            tokens["text_primary"],
            tokens["font_size_lg"],
            weight=700,
        )
        self.icon_label.setStyleSheet(
            f"""
            QLabel {{
                color: {tokens["text_primary"]};
                background-color: {rgba(tokens["accent"], 35)};
                border: 1px solid {tokens["border"]};
                border-radius: 21px;
                font-size: {tokens["font_size_lg"]};
                font-weight: 700;
            }}
            """
        )
        style_label(self.caption_label, tokens["text_secondary"], tokens["font_size_sm"])
        style_label(
            self.value_label,
            tokens["text_primary"],
            tokens["font_size_title"] if self._compact else tokens["font_size_display"],
            weight=700,
        )
        if self._compact:
            style_label(
                self.caption_label,
                tokens["text_secondary"],
                tokens["font_size_xs"],
            )


class ContrastCard(GlassCard):
    """Card destacada para alertas o información relevante."""

    def __init__(self, parent=None, *, shadow: bool = False, content_margins: int | None = None):
        super().__init__(
            parent,
            shadow=shadow,
            contrast=True,
            content_margins=content_margins,
        )


class StatusBadge(QLabel):
    """Badge de estado con colores semánticos y fondo de contraste."""

    _STATUS_COLORS = {
        "ok": "success",
        "warning": "warning",
        "danger": "danger",
        "info": "accent",
    }

    def __init__(self, text: str, status: str = "info", parent=None):
        if status not in self._STATUS_COLORS:
            raise ValueError(
                f"Estado no válido: {status!r}. Opciones: {sorted(self._STATUS_COLORS)}"
            )
        super().__init__(text, parent)
        self.status = status
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        connect_theme(self, self._apply_theme)

    def _apply_theme(self, theme_name: str) -> None:
        tokens = self._theme_manager.tokens(theme_name)
        status_color = tokens[self._STATUS_COLORS[self.status]]
        background = rgba(status_color, 12)
        self.setStyleSheet(
            f"""
            QLabel {{
                color: {tokens["text_primary"]};
                background-color: {background};
                border: 1px solid {status_color};
                border-radius: {tokens["radius_lg"]};
                padding: {tokens["spacing_xs"]} {tokens["spacing_sm"]};
                font-size: {tokens["font_size_sm"]};
                font-weight: 600;
            }}
            """
        )

    def set_status(self, status: str) -> None:
        if status not in self._STATUS_COLORS:
            raise ValueError(
                f"Estado no válido: {status!r}. Opciones: {sorted(self._STATUS_COLORS)}"
            )
        self.status = status
        self._apply_theme(self._theme_manager.current())


class CountChip(StatusBadge):
    """Contador compacto en formato pill, con superficie discreta."""

    def __init__(self, count: int, parent=None):
        super().__init__(str(count), "info", parent)
        self.setMinimumWidth(32)

    def set_count(self, count: int) -> None:
        self.setText(str(count))


class ThemeLogo(QLabel):
    """Logo institucional que cambia de variante al cambiar el tema."""

    def __init__(self, size: int = 44, parent=None):
        super().__init__(parent)
        self._size = size
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        connect_theme(self, self._apply_theme)

    def _apply_theme(self, theme_name: str) -> None:
        logo = QPixmap(self._theme_manager.tokens(theme_name)["logo_path"])
        if logo.isNull():
            self.clear()
            self.setToolTip(f"No se pudo cargar el logo para el tema {theme_name}.")
            return
        self.setPixmap(
            logo.scaled(
                self._size,
                self._size,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
        )
        self.setToolTip(f"Logo del tema {theme_name}")


__all__ = ["ContrastCard", "KpiCard", "ProgressBarThin", "StatusBadge", "ThemeLogo"]
