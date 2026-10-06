"""Tarjeta de acceso a un módulo de la aplicación."""

from PyQt6.QtCore import QEvent, QPoint, Qt, QPropertyAnimation, QEasingCurve, pyqtSignal
from PyQt6.QtWidgets import QHBoxLayout, QLabel, QPushButton, QSizePolicy, QVBoxLayout, QWidget

from ui.components.base import connect_theme, rgba, style_label


class ModuleCard(QWidget):
    """Tarjeta de módulo con icono, descripción y elevación animada al pasar el cursor."""

    clicked = pyqtSignal()

    def __init__(
        self,
        key: str,
        icon: str,
        title: str,
        description: str,
        parent=None,
    ):
        super().__init__(parent)
        self.setProperty("menu_key", key)
        self.setMinimumHeight(116)
        self.setMinimumWidth(240)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

        self._button = QPushButton(self)
        self._button.setObjectName("ModuleCardSurface")
        self._button.setCursor(Qt.CursorShape.PointingHandCursor)
        self._button.setAccessibleName(f"{title}. {description}")
        self._button.installEventFilter(self)

        layout = QHBoxLayout(self._button)
        layout.setContentsMargins(16, 14, 16, 14)
        layout.setSpacing(12)

        self._icon = QLabel(icon)
        self._icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._icon.setFixedSize(42, 42)
        self._icon.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        layout.addWidget(self._icon, 0, Qt.AlignmentFlag.AlignVCenter)

        text_layout = QVBoxLayout()
        text_layout.setSpacing(4)
        self._title = QLabel(title)
        self._description = QLabel(description)
        self._description.setWordWrap(False)
        self._description.setSizePolicy(
            QSizePolicy.Policy.Ignored,
            QSizePolicy.Policy.Preferred,
        )
        for label in (self._title, self._description):
            label.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        text_layout.addWidget(self._title)
        text_layout.addWidget(self._description)
        layout.addLayout(text_layout, 1)

        self._arrow = QLabel("›")
        self._arrow.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._arrow.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        layout.addWidget(self._arrow, 0, Qt.AlignmentFlag.AlignVCenter)

        self._button.clicked.connect(self.clicked.emit)
        connect_theme(self, self._apply_theme)

        self._animation = QPropertyAnimation(self._button, b"pos", self)
        self._animation.setDuration(140)
        self._animation.setEasingCurve(QEasingCurve.Type.OutCubic)
        self._button.move(0, 2)

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        self._button.resize(self.width(), max(0, self.height() - 2))

    def eventFilter(self, watched, event) -> bool:
        if watched is self._button:
            if event.type() == QEvent.Type.Enter:
                self._animate_lift(0)
            elif event.type() == QEvent.Type.Leave:
                self._animate_lift(2)
        return super().eventFilter(watched, event)

    def _animate_lift(self, y: int) -> None:
        self._animation.stop()
        self._animation.setStartValue(self._button.pos())
        self._animation.setEndValue(QPoint(0, y))
        self._animation.start()

    def _apply_theme(self, theme_name: str) -> None:
        tokens = self._theme_manager.tokens(theme_name)
        self._button.setStyleSheet(
            f"""
            QPushButton#ModuleCardSurface {{
                color: {tokens["text_primary"]};
                background-color: {tokens["surface"]};
                border: 1px solid {tokens["border"]};
                border-radius: {tokens["radius_card"]};
                text-align: left;
            }}
            QPushButton#ModuleCardSurface:hover {{
                background-color: {rgba(tokens["accent"], 10)};
                border-color: {rgba(tokens["accent"], 150)};
            }}
            QPushButton#ModuleCardSurface:pressed {{
                background-color: {rgba(tokens["accent"], 18)};
            }}
            """
        )
        self._icon.setStyleSheet(
            f"""
            QLabel {{
                color: {tokens["text_primary"]};
                background-color: {rgba(tokens["accent"], 24)};
                border: 1px solid {tokens["border"]};
                border-radius: 21px;
                font-size: {tokens["font_size_lg"]};
            }}
            """
        )
        style_label(self._title, tokens["text_primary"], tokens["font_size_md"], weight=600)
        style_label(self._description, tokens["text_secondary"], tokens["font_size_sm"])
        style_label(self._arrow, tokens["text_secondary"], tokens["font_size_title"], weight=400)


__all__ = ["ModuleCard"]
