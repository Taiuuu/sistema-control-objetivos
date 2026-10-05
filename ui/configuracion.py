"""Diálogo de configuración de apariencia y preferencias visuales."""

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPixmap
from PyQt6.QtWidgets import (
    QDialog,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
)

from ui.theme.theme_manager import get_theme_manager


class ThemeSelectionCard(QFrame):
    """Tarjeta seleccionable con previsualización del fondo, acento y logo."""

    def __init__(self, theme_name: str, parent=None):
        super().__init__(parent)
        self.theme_name = theme_name
        self._manager = get_theme_manager()
        self.setObjectName("ThemeSelectionCard")
        self.setCursor(Qt.CursorShape.PointingHandCursor)

        self.preview = QPushButton(self)
        self.preview.setCheckable(True)
        self.preview.setObjectName("ThemePreviewButton")
        self.preview.setCursor(Qt.CursorShape.PointingHandCursor)
        self.preview.setAccessibleName(f"Tema {theme_name}")
        self.preview.setAccessibleDescription(f"Aplicar el tema {theme_name}")
        self.preview.clicked.connect(lambda: self._manager.set_theme(self.theme_name))

        inner = QVBoxLayout(self.preview)
        inner.setContentsMargins(12, 12, 12, 10)
        inner.setSpacing(9)

        top_row = QHBoxLayout()
        self.logo = QLabel()
        self.logo.setFixedSize(42, 42)
        self.logo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.check = QLabel("✓")
        self.check.setFixedSize(22, 22)
        self.check.setAlignment(Qt.AlignmentFlag.AlignCenter)
        top_row.addWidget(self.logo)
        top_row.addStretch()
        top_row.addWidget(self.check)
        inner.addLayout(top_row)

        self.preview_surface = QFrame()
        self.preview_surface.setObjectName("ThemePreviewSurface")
        self.preview_surface.setFixedHeight(34)
        surface_layout = QVBoxLayout(self.preview_surface)
        surface_layout.setContentsMargins(8, 8, 8, 8)
        self.accent_bar = QFrame()
        self.accent_bar.setObjectName("ThemePreviewAccent")
        self.accent_bar.setFixedHeight(8)
        surface_layout.addWidget(self.accent_bar)
        inner.addWidget(self.preview_surface)

        self.name = QLabel(theme_name)
        self.name.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        inner.addWidget(self.name)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(self.preview)

        for child in (
            self.logo,
            self.check,
            self.preview_surface,
            self.accent_bar,
            self.name,
        ):
            child.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)

        self._manager.theme_changed.connect(self._apply_theme)
        self._apply_theme(self._manager.current())

    def _apply_theme(self, active_name: str) -> None:
        tokens = self._manager.tokens(self.theme_name)
        active_tokens = self._manager.tokens(active_name)
        self.preview.setChecked(active_name == self.theme_name)
        self.check.setVisible(active_name == self.theme_name)
        self.logo.setPixmap(
            QPixmap(tokens["logo_path"]).scaled(
                38,
                38,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
        )
        self.logo.setStyleSheet("background: transparent;")
        self.preview_surface.setStyleSheet(
            f"""
            QFrame#ThemePreviewSurface {{
                background-color: {tokens["bg_gradient_start"]};
                border: 1px solid {tokens["border"]};
                border-radius: {tokens["radius_sm"]};
            }}
            """
        )
        self.accent_bar.setStyleSheet(
            f"""
            QFrame#ThemePreviewAccent {{
                background-color: {tokens["accent"]};
                border: none;
                border-radius: 4px;
            }}
            """
        )
        self.check.setStyleSheet(
            f"""
            QLabel {{
                color: {active_tokens["accent_text"]};
                background-color: {active_tokens["accent"]};
                border: none;
                border-radius: 11px;
                font-weight: 700;
            }}
            """
        )
        self.name.setStyleSheet(
            f"color: {tokens['text_primary']}; background: transparent; font-weight: 600;"
        )
        self.preview.setStyleSheet(
            f"""
            QPushButton#ThemePreviewButton {{
                text-align: left;
                background-color: {tokens["surface"]};
                border: 1px solid {tokens["border"]};
                border-radius: {tokens["radius_card"]};
                padding: 0;
            }}
            QPushButton#ThemePreviewButton:hover {{
                border: 2px solid {tokens["accent"]};
            }}
            QPushButton#ThemePreviewButton:checked {{
                border: 2px solid {tokens["accent"]};
            }}
            """
        )

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._manager.set_theme(self.theme_name)
            event.accept()
            return
        super().mousePressEvent(event)


class ConfiguracionDialog(QDialog):
    """Preferencias de apariencia con selector de temas y tamaño de letra."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Configuración")
        self.setMinimumWidth(620)
        self._manager = get_theme_manager()

        root = QVBoxLayout(self)
        root.setContentsMargins(24, 22, 24, 24)
        root.setSpacing(16)

        title = QLabel("Configuración")
        title.setStyleSheet("font-size: 22px; font-weight: 700; background: transparent;")
        root.addWidget(title)

        appearance_title = QLabel("Apariencia")
        appearance_title.setStyleSheet("font-size: 16px; font-weight: 700; background: transparent;")
        root.addWidget(appearance_title)

        themes_grid = QGridLayout()
        themes_grid.setHorizontalSpacing(12)
        themes_grid.setVerticalSpacing(12)
        for index, theme_name in enumerate(self._manager.available_themes()):
            themes_grid.addWidget(ThemeSelectionCard(theme_name), index // 2, index % 2)
        root.addLayout(themes_grid)

        font_section = QFrame()
        font_section.setObjectName("FontSizeSection")
        font_row = QHBoxLayout(font_section)
        font_row.setContentsMargins(14, 10, 14, 10)
        font_row.setSpacing(10)

        font_title = QLabel("Tamaño de letra")
        font_row.addWidget(font_title)
        font_row.addStretch()
        self.font_size_label = QLabel(f'{self._manager.font_size()} px')
        self.font_size_label.setMinimumWidth(48)
        self.font_size_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        font_row.addWidget(self.font_size_label)

        self.decrease_font_button = QPushButton("A−")
        self.decrease_font_button.setAccessibleName("Reducir tamaño de letra")
        self.decrease_font_button.setToolTip("Reducir tamaño de letra")
        self.increase_font_button = QPushButton("A+")
        self.increase_font_button.setAccessibleName("Aumentar tamaño de letra")
        self.increase_font_button.setToolTip("Aumentar tamaño de letra")
        font_row.addWidget(self.decrease_font_button)
        font_row.addWidget(self.increase_font_button)
        root.addWidget(font_section)

        close_button = QPushButton("Cerrar")
        close_button.clicked.connect(self.accept)
        root.addWidget(close_button, 0, Qt.AlignmentFlag.AlignRight)

        self.decrease_font_button.clicked.connect(lambda: self._change_font_size(-1))
        self.increase_font_button.clicked.connect(lambda: self._change_font_size(1))
        self._manager.font_size_changed.connect(self._show_font_size)
        self._manager.theme_changed.connect(self._apply_theme)
        self._apply_theme(self._manager.current())
        self._show_font_size(self._manager.font_size())

    def _change_font_size(self, delta: int) -> None:
        next_size = self._manager.font_size() + delta
        bounded_size = min(
            self._manager.MAX_FONT_SIZE,
            max(self._manager.MIN_FONT_SIZE, next_size),
        )
        self._manager.set_font_size(bounded_size)

    def _show_font_size(self, size: int) -> None:
        self.font_size_label.setText(f"{size} px")
        self.decrease_font_button.setEnabled(size > self._manager.MIN_FONT_SIZE)
        self.increase_font_button.setEnabled(size < self._manager.MAX_FONT_SIZE)

    def _apply_theme(self, theme_name: str) -> None:
        tokens = self._manager.tokens(theme_name)
        self.setStyleSheet(
            f"""
            QDialog {{
                color: {tokens["text_primary"]};
                background-color: {tokens["surface"]};
                border: 1px solid {tokens["border"]};
                border-radius: {tokens["radius_card"]};
            }}
            QFrame#FontSizeSection {{
                background-color: {tokens["surface_alt"]};
                border: 1px solid {tokens["border"]};
                border-radius: {tokens["radius_md"]};
            }}
            """
        )


__all__ = ["ConfiguracionDialog", "ThemeSelectionCard"]
