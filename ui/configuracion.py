"""Diálogo de configuración de apariencia y preferencias visuales."""

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPixmap
from PyQt6.QtWidgets import (
    QDialog,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QFileDialog,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from ui.theme.theme_manager import get_theme_manager
from core.configuracion import (
    establecer_ruta_backup_externo,
    obtener_ruta_backup_externo,
)


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
    """Preferencias visuales, de funciones, datos y cuenta."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Configuración")
        ancho_disponible = max(420, parent.width() - 32) if parent else 620
        alto_disponible = max(340, parent.height() - 48) if parent else 500
        self.setMinimumSize(min(420, ancho_disponible), min(340, alto_disponible))
        self.resize(min(620, ancho_disponible), min(480, alto_disponible))
        self._manager = get_theme_manager()
        self._password_window = None
        self.tabs = QTabWidget(self)

        def crear_pagina():
            contenido = QWidget()
            layout = QVBoxLayout(contenido)
            layout.setContentsMargins(20, 18, 20, 18)
            layout.setSpacing(14)
            scroll = QScrollArea(self.tabs)
            scroll.setWidgetResizable(True)
            scroll.setFrameShape(QFrame.Shape.NoFrame)
            scroll.setWidget(contenido)
            return scroll, layout

        funciones_page, funciones = crear_pagina()
        navigation_description = QLabel(
            "Elegí qué accesos querés ver. Ocultarlos no cambia los permisos ni los datos."
        )
        navigation_description.setWordWrap(True)
        funciones.addWidget(navigation_description)
        self.customize_menu_button = QPushButton("Elegir funciones visibles")
        self.customize_menu_button.setAccessibleName("Elegir funciones visibles")
        if parent and hasattr(parent, "_configurar_menu"):
            self.customize_menu_button.clicked.connect(parent._configurar_menu)
        else:
            self.customize_menu_button.setEnabled(False)
            self.customize_menu_button.setToolTip(
                "La configuración de funciones requiere una sesión iniciada."
            )
        funciones.addWidget(self.customize_menu_button)
        self.keyboard_help_button = QPushButton("Atajos de teclado")
        self.keyboard_help_button.setToolTip("Abrir la ayuda de atajos (F1)")
        self.keyboard_help_button.setAccessibleName("Atajos de teclado")
        if parent and hasattr(parent, "abrir_ayuda"):
            self.keyboard_help_button.clicked.connect(parent.abrir_ayuda)
        else:
            self.keyboard_help_button.setEnabled(False)
        funciones.addWidget(self.keyboard_help_button)
        funciones.addStretch(1)

        datos_page, datos = crear_pagina()
        backup_title = QLabel("Copias de seguridad")
        backup_title.setStyleSheet(
            "font-size: 16px; font-weight: 700; background: transparent;"
        )
        datos.addWidget(backup_title)
        backup_description = QLabel(
            "Las copias verificadas permiten recuperar la base de datos. "
            "La copia externa es opcional."
        )
        backup_description.setWordWrap(True)
        datos.addWidget(backup_description)
        backup_buttons = QHBoxLayout()
        self.create_backup_button = QPushButton("Crear copia ahora")
        self.create_backup_button.clicked.connect(self._crear_backup)
        self.external_backup_button = QPushButton("Elegir ruta de copia externa")
        self.external_backup_button.clicked.connect(self._elegir_ruta_externa)
        backup_buttons.addWidget(self.create_backup_button)
        backup_buttons.addWidget(self.external_backup_button)
        datos.addLayout(backup_buttons)
        self.external_backup_path = QLabel()
        self.external_backup_path.setWordWrap(True)
        datos.addWidget(self.external_backup_path)
        self.backup_list = QListWidget()
        self.backup_list.setMinimumHeight(110)
        datos.addWidget(self.backup_list)
        self.restore_backup_button = QPushButton("Restaurar copia seleccionada")
        self.restore_backup_button.clicked.connect(self._restaurar_backup)
        datos.addWidget(self.restore_backup_button)
        self._actualizar_backups()

        temas_page, temas = crear_pagina()
        appearance_title = QLabel("Apariencia")
        appearance_title.setStyleSheet("font-size: 16px; font-weight: 700; background: transparent;")
        temas.addWidget(appearance_title)

        themes_grid = QGridLayout()
        themes_grid.setHorizontalSpacing(12)
        themes_grid.setVerticalSpacing(12)
        for index, theme_name in enumerate(self._manager.available_themes()):
            themes_grid.addWidget(ThemeSelectionCard(theme_name), index // 2, index % 2)
        temas.addLayout(themes_grid)

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
        temas.addWidget(font_section)
        temas.addStretch(1)

        cuenta_page, cuenta = crear_pagina()
        cuenta.addWidget(QLabel("Administrá el acceso de tu cuenta."))
        self.change_password_button = QPushButton("Cambiar contraseña")
        self.change_password_button.clicked.connect(self._cambiar_contrasena)
        tiene_sesion = isinstance(getattr(parent, "usuario_id", None), int)
        self.change_password_button.setEnabled(tiene_sesion)
        if not tiene_sesion:
            self.change_password_button.setToolTip(
                "Iniciá sesión para cambiar la contraseña."
            )
        cuenta.addWidget(self.change_password_button)
        cuenta.addStretch(1)

        acerca_page, acerca = crear_pagina()
        acerca.addWidget(QLabel("VESP Organizations"))
        acerca.addWidget(
            QLabel("Sistema de control de objetivos, supervisores y pasadas.")
        )
        acerca.addStretch(1)

        self.tabs.addTab(temas_page, "Temas")
        self.tabs.addTab(funciones_page, "Funciones visibles")
        self.tabs.addTab(datos_page, "Backups y datos")
        self.tabs.addTab(cuenta_page, "Cuenta")
        self.tabs.addTab(acerca_page, "Acerca de")
        layout_principal = QVBoxLayout(self)
        layout_principal.setContentsMargins(8, 8, 8, 8)
        layout_principal.addWidget(self.tabs)

        self.decrease_font_button.clicked.connect(lambda: self._change_font_size(-1))
        self.increase_font_button.clicked.connect(lambda: self._change_font_size(1))
        self._manager.font_size_changed.connect(self._show_font_size)
        self._manager.theme_changed.connect(self._apply_theme)
        self._apply_theme(self._manager.current())
        self._show_font_size(self._manager.font_size())
        self._actualizar_ruta_externa()

    def _cambiar_contrasena(self) -> None:
        usuario_id = getattr(self.parent(), "usuario_id", None)
        if not isinstance(usuario_id, int):
            self.change_password_button.setEnabled(False)
            self.change_password_button.setToolTip(
                "Iniciá sesión para cambiar la contraseña."
            )
            return

        from ui.cambiar_password import CambiarPassword

        self._password_window = CambiarPassword(usuario_id, lambda: None)
        self._password_window.show()

    def _actualizar_ruta_externa(self) -> None:
        ruta = obtener_ruta_backup_externo()
        self.external_backup_path.setText(
            f"Copia externa: {ruta if ruta else 'No configurada'}"
        )

    def _actualizar_backups(self) -> None:
        from services.backups.backup import listar_backups

        self.backup_list.clear()
        for copia in listar_backups():
            estado = "verificado" if copia["verificado"] else "NO verificado"
            fila = QListWidgetItem(
                f"{copia['fecha']:%d-%m-%Y %H:%M:%S} · {copia['motivo']} · "
                f"{copia['tamaño'] / (1024 * 1024):.2f} MB · {estado}"
            )
            fila.setData(Qt.ItemDataRole.UserRole, str(copia["path"]))
            fila.setData(Qt.ItemDataRole.UserRole + 1, copia["verificado"])
            self.backup_list.addItem(fila)

    def _crear_backup(self) -> None:
        from services.backups.backup import crear_backup

        try:
            ruta = crear_backup("manual")
        except Exception as error:
            QMessageBox.critical(self, "No se creó la copia", str(error))
            return
        self._actualizar_backups()
        QMessageBox.information(self, "Copia creada", f"Copia verificada:\n{ruta}")

    def _elegir_ruta_externa(self) -> None:
        ruta = QFileDialog.getExistingDirectory(
            self, "Elegir carpeta sincronizada para copias"
        )
        if not ruta:
            return
        try:
            establecer_ruta_backup_externo(ruta)
        except OSError as error:
            QMessageBox.critical(
                self, "No se guardó la ruta externa", str(error)
            )
            return
        self._actualizar_ruta_externa()

    def _restaurar_backup(self) -> None:
        fila = self.backup_list.currentItem()
        if fila is None or not fila.data(Qt.ItemDataRole.UserRole + 1):
            QMessageBox.warning(
                self, "Copia no disponible", "Seleccioná una copia verificada."
            )
            return
        ruta = fila.data(Qt.ItemDataRole.UserRole)
        respuesta = QMessageBox.question(
            self,
            "Confirmar restauración",
            "La base actual será reemplazada. ¿Querés continuar?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if respuesta != QMessageBox.StandardButton.Yes:
            return
        confirmacion, aceptada = QInputDialog.getText(
            self,
            "Segunda confirmación",
            "Escribí RESTAURAR para reemplazar la base:",
        )
        if not aceptada or confirmacion != "RESTAURAR":
            QMessageBox.information(self, "Restauración cancelada", "No se modificó la base.")
            return
        from services.backups.backup import restaurar_backup

        try:
            restaurar_backup(ruta)
        except Exception as error:
            QMessageBox.critical(self, "No se restauró la copia", str(error))
            return
        QMessageBox.information(
            self,
            "Restauración completada",
            "La copia fue restaurada. Cerrá y volvé a abrir VESP para refrescar todas las vistas.",
        )

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
