# =============================================================================
# VESP Organizations - Widget de Sidebar
# Menú lateral con botones y controles inferiores
# =============================================================================

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QToolButton, QScrollArea, QFrame,
    QGraphicsDropShadowEffect
)
from PyQt6.QtCore import Qt, QSize, pyqtSignal
from PyQt6.QtGui import QPixmap, QIcon, QFont
from services.permisos import tiene_permiso
from services.assets import ruta_asset


# =============================================================================
# PALETAS DE COLOR
# =============================================================================

PALETA_OSCURA = {
    "bg_sidebar":        "#111318",
    "bg_sidebar_hover":  "#1e2128",
    "accent":            "#4ade80",
    "accent_dark":       "#22c55e",
    "accent_red":        "#f87171",
    "text_primary":      "#f1f5f9",
    "text_secondary":    "#94a3b8",
    "text_muted":        "#475569",
    "border":            "#2a2d36",
    "btn_menu_hover":    "#2a2d36",
    "btn_menu_text":     "#cbd5e1",
    "scrollbar":         "#2a2d36",
    "scrollbar_handle":  "#3f4556",
}

PALETA_CLARA = {
    "bg_sidebar":        "#f8fafc",
    "bg_sidebar_hover":  "#f1f5f9",
    "accent":            "#16a34a",
    "accent_dark":       "#15803d",
    "accent_red":        "#dc2626",
    "text_primary":      "#0f172a",
    "text_secondary":    "#475569",
    "text_muted":        "#94a3b8",
    "border":            "#e2e8f0",
    "btn_menu_hover":    "#e2e8f0",
    "btn_menu_text":     "#334155",
    "scrollbar":         "#e2e8f0",
    "scrollbar_handle":  "#94a3b8",
}


def p(key: str, oscuro: bool) -> str:
    """Acceso rápido a paleta."""
    return (PALETA_OSCURA if oscuro else PALETA_CLARA)[key]


# =============================================================================
# BOTÓN MENÚ LATERAL CON ANIMACIÓN
# =============================================================================

class BotonMenu(QPushButton):
    """Botón del menú lateral con soporte para colapsar/expandir."""
    
    clicked_with_action = pyqtSignal(object)  # Señal que emite la acción

    def __init__(self, icono: str, texto: str, oscuro: bool, parent=None):
        super().__init__(parent)
        self._icono = icono
        self._texto_completo = f"  {icono}   {texto}"
        self._expandido = True
        self._oscuro = oscuro
        self._activo = False
        self._accion = None  # Callback de acción

        self.setText(self._texto_completo)
        self.setProperty("icono", icono)
        self.setProperty("texto_completo", self._texto_completo)
        self.setToolTip(texto)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.setFixedHeight(38)
        self._aplicar_estilo()

    def set_accion(self, fn):
        """Establece la función a ejecutar cuando se hace clic."""
        self._accion = fn
        self.clicked.connect(lambda: self.clicked_with_action.emit(fn))

    def _aplicar_estilo(self):
        bg_activo   = p("accent", self._oscuro)
        text_activo = "#ffffff"
        bg_hover    = p("btn_menu_hover", self._oscuro)
        text_normal = p("btn_menu_text", self._oscuro)

        if self._activo:
            self.setStyleSheet(f"""
                QPushButton {{
                    background-color: {bg_activo};
                    color: {text_activo};
                    border: none;
                    border-radius: 8px;
                    padding: 0px 10px;
                    text-align: left;
                    font-size: 12px;
                    font-weight: 600;
                }}
            """)
        else:
            self.setStyleSheet(f"""
                QPushButton {{
                    background-color: transparent;
                    color: {text_normal};
                    border: none;
                    border-radius: 8px;
                    padding: 0px 10px;
                    text-align: left;
                    font-size: 12px;
                }}
                QPushButton:hover {{
                    background-color: {bg_hover};
                    color: {p("text_primary", self._oscuro)};
                }}
                QPushButton:pressed {{
                    background-color: {bg_activo};
                    color: white;
                }}
            """)

    def set_activo(self, activo: bool):
        self._activo = activo
        self._aplicar_estilo()

    def colapsar(self):
        self._expandido = False
        self.setText(f" {self._icono}")
        self.setFixedHeight(38)

    def expandir(self):
        self._expandido = True
        self.setText(self._texto_completo)


# =============================================================================
# SEPARADOR ELEGANTE
# =============================================================================

def crear_separador(oscuro: bool) -> QFrame:
    s = QFrame()
    s.setFrameShape(QFrame.Shape.HLine)
    color = p("border", oscuro)
    s.setStyleSheet(f"QFrame {{ color: {color}; background-color: {color}; border: none; max-height: 1px; margin: 4px 6px; }}")
    return s


# =============================================================================
# WIDGET SIDEBAR COMPLETO
# =============================================================================

class SidebarWidget(QWidget):
    """Widget completo del menú lateral."""
    
    # Señales
    boton_presionado = pyqtSignal(str)  # Nombre de la acción
    tema_clicado = pyqtSignal()
    logout_clicado = pyqtSignal()
    zoom_cambiado = pyqtSignal(int)  # Nuevo nivel de zoom
    
    EXPANDIDO = 230
    COLAPSADO = 56
    
    def __init__(self, oscuro: bool, usuario_id: int, parent=None):
        super().__init__(parent)
        self._oscuro = oscuro
        self._usuario_id = usuario_id
        self._sidebar_expandido = True
        self._botones = {}
        self._zoom_nivel = 13
        
        self.setFixedWidth(self.EXPANDIDO)
        self._construir_ui()

    def _construir_ui(self):
        oscuro = self._oscuro
        self.setStyleSheet(f"""
            QWidget {{
                background-color: {p('bg_sidebar', oscuro)};
                border-right: 1px solid {p('border', oscuro)};
            }}
        """)
        
        layout = QVBoxLayout(self)
        layout.setSpacing(0)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Cabecera
        layout.addWidget(self._construir_cabecera())
        layout.addWidget(crear_separador(oscuro))
        
        # Scroll con botones
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll.setStyleSheet(f"""
            QScrollArea {{ border: none; background: transparent; }}
            QScrollBar:vertical {{
                width: 4px;
                background: transparent;
                border-radius: 2px;
            }}
            QScrollBar::handle:vertical {{
                background: {p('scrollbar_handle', oscuro)};
                border-radius: 2px;
                min-height: 24px;
            }}
            QScrollBar::add-line:vertical,
            QScrollBar::sub-line:vertical {{ height: 0px; }}
        """)
        
        self._contenedor = QWidget()
        self._contenedor.setStyleSheet(f"background-color: {p('bg_sidebar', oscuro)};")
        self._layout_botones = QVBoxLayout(self._contenedor)
        self._layout_botones.setSpacing(2)
        self._layout_botones.setContentsMargins(8, 8, 8, 8)
        
        scroll.setWidget(self._contenedor)
        layout.addWidget(scroll, 1)
        
        # Zona inferior
        layout.addWidget(self._construir_zona_inferior())

    def _construir_cabecera(self) -> QWidget:
        oscuro = self._oscuro
        cabecera = QWidget()
        cabecera.setFixedHeight(100)
        cabecera.setStyleSheet(f"background-color: {p('bg_sidebar', oscuro)};")
        
        lay = QVBoxLayout(cabecera)
        lay.setContentsMargins(10, 10, 10, 6)
        lay.setSpacing(2)
        
        # Fila con logo y botón colapsar
        fila = QHBoxLayout()
        fila.setContentsMargins(0, 0, 0, 0)
        
        self._logo_label = QLabel()
        pixmap = QPixmap(ruta_asset("assets/vesp.png")).scaled(
            36, 36, Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation
        )
        self._logo_label.setPixmap(pixmap)
        
        self._btn_colapsar = QToolButton()
        self._btn_colapsar.setText("‹")
        self._btn_colapsar.setFixedSize(24, 24)
        self._btn_colapsar.setToolTip("Colapsar menú (Ctrl+\\)")
        self._btn_colapsar.setCursor(Qt.CursorShape.PointingHandCursor)
        self._btn_colapsar.setStyleSheet(f"""
            QToolButton {{
                background: {p('btn_menu_hover', oscuro)};
                color: {p('text_secondary', oscuro)};
                border: none;
                border-radius: 5px;
                font-size: 14px;
                font-weight: bold;
            }}
            QToolButton:hover {{
                background: {p('accent', oscuro)};
                color: white;
            }}
        """)
        self._btn_colapsar.clicked.connect(self._toggle_sidebar)
        
        fila.addWidget(self._logo_label)
        fila.addStretch()
        fila.addWidget(self._btn_colapsar)
        lay.addLayout(fila)
        
        # Títulos
        self._titulo = QLabel("V.E.S.P")
        self._titulo.setStyleSheet(f"""
            color: {p('accent', oscuro)};
            font-size: 16px;
            font-weight: 800;
            letter-spacing: 2px;
        """)
        lay.addWidget(self._titulo)
        
        self._subtitulo = QLabel("Organizations")
        self._subtitulo.setStyleSheet(f"""
            color: {p('text_muted', oscuro)};
            font-size: 10px;
            letter-spacing: 1px;
        """)
        lay.addWidget(self._subtitulo)
        
        return cabecera

    def _construir_zona_inferior(self) -> QWidget:
        oscuro = self._oscuro
        zona = QWidget()
        zona.setStyleSheet(f"background-color: {p('bg_sidebar', oscuro)};")
        lay = QVBoxLayout(zona)
        lay.setContentsMargins(8, 4, 8, 10)
        lay.setSpacing(4)
        
        lay.addWidget(crear_separador(oscuro))
        
        # Zoom
        fila_zoom = QHBoxLayout()
        fila_zoom.setSpacing(4)
        
        estilo_btn = f"""
            QPushButton {{
                background-color: {p('btn_menu_hover', oscuro)};
                color: {p('text_secondary', oscuro)};
                border: 1px solid {p('border', oscuro)};
                border-radius: 5px;
                font-size: 11px;
                min-width: 30px;
                max-width: 36px;
                min-height: 26px;
            }}
            QPushButton:hover {{
                background-color: {p('accent', oscuro)};
                color: white;
                border-color: {p('accent', oscuro)};
            }}
        """
        
        self._btn_zoom_menos = QPushButton("A−")
        self._btn_zoom_menos.setToolTip("Reducir zoom (Ctrl+−)")
        self._btn_zoom_menos.setStyleSheet(estilo_btn)
        self._btn_zoom_menos.setCursor(Qt.CursorShape.PointingHandCursor)
        self._btn_zoom_menos.clicked.connect(self._zoom_menos)
        
        self._btn_zoom_mas = QPushButton("A+")
        self._btn_zoom_mas.setToolTip("Aumentar zoom (Ctrl+=)")
        self._btn_zoom_mas.setStyleSheet(estilo_btn)
        self._btn_zoom_mas.setCursor(Qt.CursorShape.PointingHandCursor)
        self._btn_zoom_mas.clicked.connect(self._zoom_mas)
        
        self._lbl_zoom = QLabel(f"{self._zoom_nivel}px")
        self._lbl_zoom.setStyleSheet(f"color: {p('text_muted', oscuro)}; font-size: 10px;")
        self._lbl_zoom.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        fila_zoom.addWidget(self._btn_zoom_menos)
        fila_zoom.addWidget(self._lbl_zoom, 1)
        fila_zoom.addWidget(self._btn_zoom_mas)
        lay.addLayout(fila_zoom)
        
        # Botón tema
        texto_tema = "☀  Modo claro" if self._oscuro else "🌙  Modo oscuro"
        self._btn_tema = QPushButton(texto_tema)
        self._btn_tema.setCursor(Qt.CursorShape.PointingHandCursor)
        self._btn_tema.setFixedHeight(34)
        self._btn_tema.setStyleSheet(f"""
            QPushButton {{
                background-color: {p('btn_menu_hover', oscuro)};
                color: {p('text_secondary', oscuro)};
                border: 1px solid {p('border', oscuro)};
                border-radius: 7px;
                font-size: 11px;
                padding: 0 10px;
                text-align: left;
            }}
            QPushButton:hover {{
                background-color: {p('accent', oscuro)};
                color: white;
                border-color: {p('accent', oscuro)};
            }}
        """)
        self._btn_tema.clicked.connect(self.tema_clicado.emit)
        lay.addWidget(self._btn_tema)
        
        # Usuario
        from services.usuarios import get_username_by_id
        nombre = get_username_by_id(self._usuario_id) or "Usuario"
        self._usuario_label = QLabel(f"👤  {nombre}")
        self._usuario_label.setStyleSheet(f"""
            color: {p('text_muted', oscuro)};
            font-size: 10px;
            padding: 3px 4px;
            border-radius: 5px;
            background: {p('btn_menu_hover', oscuro)};
        """)
        self._usuario_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._usuario_label.setWordWrap(True)
        lay.addWidget(self._usuario_label)
        
        # Logout
        self._btn_logout = QPushButton("🚪 Cerrar sesión")
        self._btn_logout.setCursor(Qt.CursorShape.PointingHandCursor)
        self._btn_logout.setFixedHeight(34)
        self._btn_logout.setStyleSheet(f"""
            QPushButton {{
                background-color: {p('accent_red', oscuro)};
                color: white;
                border: 1px solid {p('accent_red', oscuro)};
                border-radius: 7px;
                font-size: 11px;
                padding: 0 10px;
                text-align: center;
            }}
            QPushButton:hover {{
                background-color: #ff5252;
                border-color: #ff5252;
            }}
        """)
        self._btn_logout.clicked.connect(self.logout_clicado.emit)
        lay.addWidget(self._btn_logout)
        
        return zona

    def agregar_boton(self, icono: str, texto: str, accion, tooltip: str = ""):
        """Agrega un botón al menú."""
        btn = BotonMenu(icono, texto, self._oscuro)
        if tooltip:
            btn.setToolTip(tooltip)
        btn.set_accion(accion)
        self._botones[texto] = btn
        self._layout_botones.addWidget(btn)
        return btn

    def agregar_separador(self):
        self._layout_botones.addWidget(crear_separador(self._oscuro))
        self._layout_botones.addSpacing(2)

    def _toggle_sidebar(self):
        if self._sidebar_expandido:
            self.setFixedWidth(self.COLAPSADO)
            self._sidebar_expandido = False
            self._btn_colapsar.setText("›")
            self._btn_colapsar.setToolTip("Expandir menú (Ctrl+\\)")
            self._titulo.hide()
            self._subtitulo.hide()
            self._usuario_label.hide()
            self._btn_tema.hide()
            self._lbl_zoom.hide()
            for btn in self._botones.values():
                btn.colapsar()
        else:
            self.setFixedWidth(self.EXPANDIDO)
            self._sidebar_expandido = True
            self._btn_colapsar.setText("‹")
            self._btn_colapsar.setToolTip("Colapsar menú (Ctrl+\\)")
            self._titulo.show()
            self._subtitulo.show()
            self._usuario_label.show()
            self._btn_tema.show()
            self._lbl_zoom.show()
            for btn in self._botones.values():
                btn.expandir()

    def _zoom_mas(self):
        if self._zoom_nivel < 20:
            self._zoom_nivel += 1
            self._lbl_zoom.setText(f"{self._zoom_nivel}px")
            self.zoom_cambiado.emit(self._zoom_nivel)

    def _zoom_menos(self):
        if self._zoom_nivel > 9:
            self._zoom_nivel -= 1
            self._lbl_zoom.setText(f"{self._zoom_nivel}px")
            self.zoom_cambiado.emit(self._zoom_nivel)

    def set_activo(self, texto: str):
        """Marca un botón como activo."""
        for nombre, btn in self._botones.items():
            btn.set_activo(nombre == texto)

    def actualizar_tema(self, oscuro: bool):
        """Actualiza los estilos cuando cambia el tema."""
        self._oscuro = oscuro
        # Por implementar: recrear estilos con nueva paleta