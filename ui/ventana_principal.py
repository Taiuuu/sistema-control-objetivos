# =============================================================================
# VESP Organizations - Sistema de Control de Objetivos
# Ventana principal del sistema — UI/UX mejorada
# =============================================================================

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QTableWidget, QTableWidgetItem, QLabel,
    QPushButton, QDateEdit, QComboBox, QMessageBox,
    QFrame, QLineEdit, QHeaderView, QScrollArea,
    QToolButton, QSizePolicy, QSpacerItem, QGraphicsDropShadowEffect
)
from PyQt6.QtCore import (
    QDate, QTimer, QEvent, Qt, QSize,
    QPropertyAnimation, QEasingCurve, QPoint, pyqtSignal, QParallelAnimationGroup
)
from PyQt6.QtGui import QColor, QPixmap, QIcon, QShortcut, QKeySequence, QFont, QPalette
from services.reportes import obtener_objetivos_del_dia
from ui.animaciones import animar_entrada
from ui.form_objetivo import FormObjetivo
from ui.form_supervisor import FormSupervisor
from ui.form_pasada import FormPasada
from ui.form_de_turno import FormTurno
from ui.lista_objetivos import ListaObjetivos
from ui.lista_supervisores import ListaSupervisores
from ui.reporte_mensual import ReporteMensual
from ui.reporte_objetivo import ReporteObjetivo
from ui.lista_pasadas import ListaPasadas
from ui.notas_diarias import NotasDiarias
from ui.vista_logs import VistaLogs
from ui.gestionar_usuarios import GestionarUsuarios
from ui.ayuda import Ayuda
from ui.transferir_datos import TransferirDatos
from ui.importar_excel import ImportarExcel
from ui.dashboard import Dashboard
from ui.vista_auditoria import VistaAuditoria
from ui.vista_validaciones import VistaValidaciones
from ui.vista_cache import VistaCache
from ui.vista_indexacion import VistaIndexacion
from ui.vista_sincronizacion import VistaSincronizacion
from models.objetivos import dar_de_baja_objetivo
from services.tema import obtener_tema_actual
from services.permisos import tiene_permiso
from services.backup import hacer_backup
from services.logger import registrar_accion
from services.assets import ruta_asset
from services.sincronizacion import obtener_sincronizador
from database.db import DB_PATH
import sqlite3


# =============================================================================
# FUNCIONES DE CONSULTA
# =============================================================================

def contar_pasadas(fecha: str, objetivo_id: int, turno: str = None, supervisor_id: int = None) -> int:
    conexion = sqlite3.connect(DB_PATH)
    cursor = conexion.cursor()
    query = 'SELECT COUNT(*) FROM pasadas WHERE fecha = ? AND objetivo_id = ?'
    params = [fecha, objetivo_id]
    if turno:
        query += ' AND turno = ?'
        params.append(turno)
    if supervisor_id:
        query += ' AND supervisor_id = ?'
        params.append(supervisor_id)
    cursor.execute(query, params)
    resultado = cursor.fetchone()[0]
    conexion.close()
    return resultado


def obtener_estado_detallado(fecha: str, objetivo_id: int) -> tuple:
    pasadas_dia   = contar_pasadas(fecha, objetivo_id, turno="diurno")
    pasadas_noche = contar_pasadas(fecha, objetivo_id, turno="nocturno")
    if pasadas_dia > 0 and pasadas_noche > 0:
        return "Pasaron los dos", "#90EE90"
    elif pasadas_dia > 0 and pasadas_noche == 0:
        return "No pasó noche", "#FFD700"
    elif pasadas_dia == 0 and pasadas_noche > 0:
        return "No pasó día", "#FFD700"
    else:
        return "No pasó nadie", "#FF6B6B"


def obtener_equipo(fecha: str, turno: str) -> str:
    conexion = sqlite3.connect(DB_PATH)
    cursor = conexion.cursor()
    cursor.execute("""
        SELECT s1.nombre, s2.nombre,
               CASE WHEN e.supervisor3_id IS NOT NULL THEN s3.nombre ELSE NULL END
        FROM equipos e
        JOIN supervisores s1 ON e.supervisor1_id = s1.id
        JOIN supervisores s2 ON e.supervisor2_id = s2.id
        LEFT JOIN supervisores s3 ON e.supervisor3_id = s3.id
        WHERE e.fecha = ? AND e.turno = ?
    """, (fecha, turno))
    resultado = cursor.fetchone()
    conexion.close()
    if not resultado:
        return "—"
    nombres = [n for n in resultado if n is not None]
    if len(nombres) == 1:
        return nombres[0]
    return ", ".join(nombres[:-1]) + " y " + nombres[-1]

def cargar_supervisores() -> list:
    conexion = sqlite3.connect(DB_PATH)
    cursor = conexion.cursor()
    cursor.execute('SELECT id, nombre FROM supervisores')
    resultado = cursor.fetchall()
    conexion.close()
    return resultado


def obtener_nombre_usuario(usuario_id: int) -> str:
    conexion = sqlite3.connect(DB_PATH)
    cursor = conexion.cursor()
    cursor.execute('SELECT username FROM usuarios WHERE id = ?', (usuario_id,))
    resultado = cursor.fetchone()
    conexion.close()
    return resultado[0] if resultado else "Usuario"


# =============================================================================
# PALETAS DE COLOR
# =============================================================================

PALETA_OSCURA = {
    "bg_sidebar":        "#111318",
    "bg_sidebar_hover":  "#1e2128",
    "bg_main":           "#16181e",
    "bg_header":         "#1a1d24",
    "bg_tabla":          "#1e2128",
    "bg_tabla_alt":      "#1a1d24",
    "accent":            "#4ade80",
    "accent_dark":       "#22c55e",
    "accent_red":        "#f87171",
    "accent_yellow":     "#fbbf24",
    "text_primary":      "#f1f5f9",
    "text_secondary":    "#94a3b8",
    "text_muted":        "#475569",
    "border":            "#2a2d36",
    "border_light":      "#1e2128",
    "btn_menu_text":     "#cbd5e1",
    "btn_menu_hover":    "#2a2d36",
    "scrollbar":         "#2a2d36",
    "scrollbar_handle":  "#3f4556",
    "badge_bg":          "#1e2128",
    "estado_verde_bg":   "#14532d",
    "estado_verde_fg":   "#4ade80",
    "estado_rojo_bg":    "#7f1d1d",
    "estado_rojo_fg":    "#fca5a5",
    "estado_amarillo_bg": "#78350f",
    "estado_amarillo_fg": "#fcd34d",
}

PALETA_CLARA = {
    "bg_sidebar":        "#f8fafc",
    "bg_sidebar_hover":  "#f1f5f9",
    "bg_main":           "#ffffff",
    "bg_header":         "#f8fafc",
    "bg_tabla":          "#ffffff",
    "bg_tabla_alt":      "#f8fafc",
    "accent":            "#16a34a",
    "accent_dark":       "#15803d",
    "accent_red":        "#dc2626",
    "accent_yellow":     "#d97706",
    "text_primary":      "#0f172a",
    "text_secondary":    "#475569",
    "text_muted":        "#94a3b8",
    "border":            "#e2e8f0",
    "border_light":      "#f1f5f9",
    "btn_menu_text":     "#334155",
    "btn_menu_hover":    "#e2e8f0",
    "scrollbar":         "#e2e8f0",
    "scrollbar_handle":  "#94a3b8",
    "badge_bg":          "#f1f5f9",
    "estado_verde_bg":   "#dcfce7",
    "estado_verde_fg":   "#15803d",
    "estado_rojo_bg":    "#fee2e2",
    "estado_rojo_fg":    "#dc2626",
    "estado_amarillo_bg": "#fef9c3",
    "estado_amarillo_fg": "#b45309",
}


def p(key: str, oscuro: bool) -> str:
    """Acceso rápido a paleta."""
    return (PALETA_OSCURA if oscuro else PALETA_CLARA)[key]


# =============================================================================
# WIDGET BADGE ESTADO (pill coloreado)
# =============================================================================

class BadgeEstado(QLabel):
    """Label con forma de pill para mostrar el estado de cobertura."""

    _MAPA = {
        "Pasaron los dos": ("estado_verde_bg",    "estado_verde_fg",    "✔  Pasaron los dos"),
        "No pasó noche":   ("estado_amarillo_bg",  "estado_amarillo_fg", "🌙  No pasó noche"),
        "No pasó día":     ("estado_amarillo_bg",  "estado_amarillo_fg", "☀  No pasó día"),
        "No pasó nadie":   ("estado_rojo_bg",      "estado_rojo_fg",     "✖  No pasó nadie"),
    }

    def __init__(self, estado: str, oscuro: bool, parent=None):
        super().__init__(parent)
        bg_key, fg_key, texto = self._MAPA.get(
            estado,
            ("badge_bg", "text_secondary", estado)
        )
        bg = p(bg_key, oscuro)
        fg = p(fg_key, oscuro)
        self.setText(texto)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setStyleSheet(f"""
            QLabel {{
                background-color: {bg};
                color: {fg};
                border-radius: 10px;
                padding: 3px 10px;
                font-size: 11px;
                font-weight: 600;
                letter-spacing: 0.3px;
            }}
        """)


# =============================================================================
# WIDGET BADGE NUMÉRICO (conteo de pasadas)
# =============================================================================

class BadgeNumero(QLabel):
    def __init__(self, numero: int, oscuro: bool, parent=None):
        super().__init__(parent)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        if numero == 0:
            bg = p("estado_rojo_bg", oscuro)
            fg = p("estado_rojo_fg", oscuro)
        elif numero == 1:
            bg = p("estado_amarillo_bg", oscuro)
            fg = p("estado_amarillo_fg", oscuro)
        else:
            bg = p("estado_verde_bg", oscuro)
            fg = p("estado_verde_fg", oscuro)
        self.setText(str(numero))
        self.setStyleSheet(f"""
            QLabel {{
                background-color: {bg};
                color: {fg};
                border-radius: 12px;
                padding: 2px 10px;
                font-size: 12px;
                font-weight: 700;
            }}
        """)


# =============================================================================
# BOTÓN MENÚ LATERAL CON ANIMACIÓN
# =============================================================================

class BotonMenu(QPushButton):
    def __init__(self, icono: str, texto: str, oscuro: bool, parent=None):
        super().__init__(parent)
        self._icono = icono
        self._texto_completo = f"  {icono}   {texto}"
        self._expandido = True
        self._oscuro = oscuro
        self._activo = False

        self.setText(self._texto_completo)
        self.setProperty("icono", icono)
        self.setProperty("texto_completo", self._texto_completo)
        self.setToolTip(texto)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.setFixedHeight(38)
        self._aplicar_estilo()

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
# VENTANA PRINCIPAL
# =============================================================================

class VentanaPrincipal(QWidget):

    SIDEBAR_EXPANDIDO = 230
    SIDEBAR_COLAPSADO = 56

    def __init__(self, usuario_id=None, rol=None, on_login_exitoso=None, app=None, alternar_tema_fn=None):
        self.usuario_id       = usuario_id
        self.rol              = rol
        self.on_login_exitoso = on_login_exitoso
        self.app              = app
        self.alternar_tema_fn = alternar_tema_fn
        self.zoom_nivel       = 13
        self._sidebar_expandido = True
        self._boton_activo      = None

        super().__init__()
        self.setWindowTitle("VESP · Control de Objetivos")
        self.setWindowFlags(Qt.WindowType.Window)
        self.move(80, 60)
        self.resize(1340, 660)
        self.setMinimumSize(720, 440)
        self.setWindowIcon(QIcon(ruta_asset("assets/vesp.png")))

        self._oscuro = obtener_tema_actual() == "oscuro"

        self._construir_ui()
        self.cargar_tabla()
        animar_entrada(self)
        self._configurar_shortcuts()
        self._configurar_timers()
        self._configurar_sincronizacion()

    # =========================================================================
    # CONSTRUCCIÓN UI
    # =========================================================================

    def _construir_ui(self):
        layout_raiz = QHBoxLayout(self)
        layout_raiz.setSpacing(0)
        layout_raiz.setContentsMargins(0, 0, 0, 0)

        self._construir_sidebar(layout_raiz)
        self._construir_panel_derecho(layout_raiz)

        self.setStyleSheet(f"QWidget#VentanaPrincipal {{ background-color: {p('bg_main', self._oscuro)}; }}")
        self.setObjectName("VentanaPrincipal")

    # -------------------------------------------------------------------------
    # SIDEBAR
    # -------------------------------------------------------------------------

    def _construir_sidebar(self, layout_raiz):
        oscuro = self._oscuro

        self.panel_lateral = QFrame()
        self.panel_lateral.setObjectName("PanelLateral")
        self.panel_lateral.setFixedWidth(self.SIDEBAR_EXPANDIDO)
        self.panel_lateral.setStyleSheet(f"""
            QFrame#PanelLateral {{
                background-color: {p('bg_sidebar', oscuro)};
                border-right: 1px solid {p('border', oscuro)};
            }}
        """)

        layout_lateral = QVBoxLayout(self.panel_lateral)
        layout_lateral.setSpacing(0)
        layout_lateral.setContentsMargins(0, 0, 0, 0)

        cabecera = self._construir_cabecera_sidebar()
        layout_lateral.addWidget(cabecera)
        layout_lateral.addWidget(crear_separador(oscuro))

        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll_area.setStyleSheet(f"""
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

        self._contenedor_scroll = QWidget()
        self._contenedor_scroll.setStyleSheet(f"background-color: {p('bg_sidebar', oscuro)};")
        self.layout_scroll = QVBoxLayout(self._contenedor_scroll)
        self.layout_scroll.setSpacing(2)
        self.layout_scroll.setContentsMargins(8, 8, 8, 8)

        self._botones_menu = []
        self._construir_botones_menu()

        self.layout_scroll.addStretch()
        scroll_area.setWidget(self._contenedor_scroll)
        layout_lateral.addWidget(scroll_area, 1)

        self._zona_inferior = self._construir_zona_inferior()
        layout_lateral.addWidget(self._zona_inferior)

        layout_raiz.addWidget(self.panel_lateral)

    def _construir_cabecera_sidebar(self) -> QWidget:
        oscuro = self._oscuro
        self._cabecera_sidebar = QWidget()
        self._cabecera_sidebar.setFixedHeight(100)
        self._cabecera_sidebar.setStyleSheet(f"background-color: {p('bg_sidebar', oscuro)};")

        lay = QVBoxLayout(self._cabecera_sidebar)
        lay.setContentsMargins(10, 10, 10, 6)
        lay.setSpacing(2)

        self.btn_colapsar = QToolButton()
        self.btn_colapsar.setText("‹")
        self.btn_colapsar.setFixedSize(24, 24)
        self.btn_colapsar.setToolTip("Colapsar menú (Ctrl+\\)")
        self.btn_colapsar.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_colapsar.setStyleSheet(f"""
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
        self.btn_colapsar.clicked.connect(self._toggle_sidebar)

        self.logo_label = QLabel()
        pixmap = QPixmap(ruta_asset("assets/vesp.png")).scaled(
            36, 36, Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation
        )
        self.logo_label.setPixmap(pixmap)

        fila_logo = QHBoxLayout()
        fila_logo.setContentsMargins(0, 0, 0, 0)
        fila_logo.addWidget(self.logo_label)
        fila_logo.addStretch()
        fila_logo.addWidget(self.btn_colapsar)
        lay.addLayout(fila_logo)

        self.titulo_lateral = QLabel("V.E.S.P")
        self.titulo_lateral.setStyleSheet(f"""
            color: {p('accent', oscuro)};
            font-size: 16px;
            font-weight: 800;
            letter-spacing: 2px;
        """)
        lay.addWidget(self.titulo_lateral)

        self.subtitulo_lateral = QLabel("Organizations")
        self.subtitulo_lateral.setStyleSheet(f"""
            color: {p('text_muted', oscuro)};
            font-size: 10px;
            letter-spacing: 1px;
        """)
        lay.addWidget(self.subtitulo_lateral)

        return self._cabecera_sidebar

    def _construir_botones_menu(self):
        oscuro = self._oscuro

        def add_btn(icono, texto, accion, tooltip_extra=""):
            b = BotonMenu(icono, texto, oscuro)
            if tooltip_extra:
                b.setToolTip(f"{texto}  {tooltip_extra}")
            b.clicked.connect(lambda: self._activar_boton(b, accion))
            self._botones_menu.append(b)
            self.layout_scroll.addWidget(b)
            return b

        def add_sep():
            self.layout_scroll.addWidget(crear_separador(oscuro))
            self.layout_scroll.addSpacing(2)

        self._btn_control   = add_btn("📋", "Control diario",     self.cargar_tabla,         "(Ctrl+B)")
        self._btn_dashboard = add_btn("📊", "Dashboard",          self.abrir_dashboard,      "(Ctrl+D)")
        self._btn_pasada    = add_btn("✅", "Registrar pasada",   self.abrir_form_pasada,    "(Ctrl+P)")
        self._btn_turno     = add_btn("🕐", "Registrar turno",    self.abrir_form_turno,     "(Ctrl+T)")

        add_sep()

        self._btn_add_obj = add_btn("➕", "Agregar objetivo",    self.abrir_form_objetivo,  "(Ctrl+O)")
        add_btn("📍", "Ver objetivos",       self.abrir_lista_objetivos)
        self._btn_add_sup = add_btn("👤", "Agregar supervisor",  self.abrir_form_supervisor, "(Ctrl+S)")
        add_btn("👥", "Ver supervisores",    self.abrir_lista_supervisores)

        add_sep()

        add_btn("🔍", "Ver pasadas",         self.abrir_lista_pasadas)
        add_btn("📝", "Notas del día",       self.abrir_notas,              "(Ctrl+N)")
        add_btn("📅", "Reporte mensual",     self.abrir_reporte_mensual,    "(Ctrl+R)")
        add_btn("📅", "Reporte objetivo",    self.abrir_reporte_mensual_objetivo, "(Ctrl+Ñ)")
        add_btn("💾", "Transferir datos",    self.abrir_transferir_datos)
        add_btn("📥", "Importar Excel",      self.abrir_importar_excel)
        add_btn("❓", "Ayuda",               self.abrir_ayuda,              "(Ctrl+H)")

        if tiene_permiso('usuarios.ver'):
            add_sep()
            self._lbl_admin = QLabel("  ADMINISTRACIÓN")
            self._lbl_admin.setStyleSheet(f"""
                color: {p('text_muted', oscuro)};
                font-size: 9px;
                letter-spacing: 1.2px;
                font-weight: 600;
                padding: 4px 0 2px 4px;
            """)
            self.layout_scroll.addWidget(self._lbl_admin)
            add_btn("⚙️",  "Gestionar usuarios", self.abrir_gestionar_usuarios)
            add_btn("📜",  "Historial",           self.abrir_logs)
            add_btn("🗄️",  "Monitor de Caché",    self.abrir_cache)
            add_btn("🔧",  "Optimización de BD",  self.abrir_indexacion)
            add_btn("🛡️",  "Validaciones BD",     self.abrir_validaciones)
            add_btn("🔎",  "Auditoría detallada", self.abrir_auditoria)
            add_btn("🔄",  "Sincronización",      self.abrir_sincronizacion)

    def _activar_boton(self, btn: BotonMenu, accion):
        if self._boton_activo and self._boton_activo is not btn:
            self._boton_activo.set_activo(False)
        btn.set_activo(True)
        self._boton_activo = btn
        accion()

    def _construir_zona_inferior(self) -> QWidget:
        oscuro = self._oscuro
        zona = QWidget()
        zona.setStyleSheet(f"background-color: {p('bg_sidebar', oscuro)};")
        lay = QVBoxLayout(zona)
        lay.setContentsMargins(8, 4, 8, 10)
        lay.setSpacing(4)

        lay.addWidget(crear_separador(oscuro))

        fila_zoom = QHBoxLayout()
        fila_zoom.setSpacing(4)

        estilo_mini_btn = f"""
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
        self._btn_zoom_menos.setStyleSheet(estilo_mini_btn)
        self._btn_zoom_menos.setCursor(Qt.CursorShape.PointingHandCursor)
        self._btn_zoom_menos.clicked.connect(self._zoom_menos)

        self._btn_zoom_mas = QPushButton("A+")
        self._btn_zoom_mas.setToolTip("Aumentar zoom (Ctrl+=)")
        self._btn_zoom_mas.setStyleSheet(estilo_mini_btn)
        self._btn_zoom_mas.setCursor(Qt.CursorShape.PointingHandCursor)
        self._btn_zoom_mas.clicked.connect(self._zoom_mas)

        self.lbl_zoom = QLabel(f"{self.zoom_nivel}px")
        self.lbl_zoom.setStyleSheet(f"color: {p('text_muted', oscuro)}; font-size: 10px;")
        self.lbl_zoom.setAlignment(Qt.AlignmentFlag.AlignCenter)

        fila_zoom.addWidget(self._btn_zoom_menos)
        fila_zoom.addWidget(self.lbl_zoom, 1)
        fila_zoom.addWidget(self._btn_zoom_mas)
        lay.addLayout(fila_zoom)

        texto_tema = "☀  Modo claro" if oscuro else "🌙  Modo oscuro"
        self.btn_tema = QPushButton(texto_tema)
        self.btn_tema.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_tema.setFixedHeight(34)
        self.btn_tema.setStyleSheet(self._estilo_btn_tema(oscuro))
        self.btn_tema.clicked.connect(self._alternar_tema)
        lay.addWidget(self.btn_tema)

        nombre_usuario = obtener_nombre_usuario(self.usuario_id)
        self.usuario_label = QLabel(f"👤  {nombre_usuario}")
        self.usuario_label.setStyleSheet(f"""
            color: {p('text_muted', oscuro)};
            font-size: 10px;
            padding: 3px 4px;
            border-radius: 5px;
            background: {p('btn_menu_hover', oscuro)};
        """)
        self.usuario_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.usuario_label.setWordWrap(True)
        lay.addWidget(self.usuario_label)

        # Botón de cerrar sesión
        self.btn_logout = QPushButton("🚪 Cerrar sesión")
        self.btn_logout.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_logout.setFixedHeight(34)
        self.btn_logout.setStyleSheet(self._estilo_btn_logout(oscuro))
        self.btn_logout.clicked.connect(self._cerrar_sesion)
        lay.addWidget(self.btn_logout)

        return zona

    def _estilo_btn_tema(self, oscuro: bool) -> str:
        return f"""
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
        """

    def _estilo_btn_logout(self, oscuro: bool) -> str:
        return f"""
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
        """

    # -------------------------------------------------------------------------
    # PANEL DERECHO
    # -------------------------------------------------------------------------

    def _construir_panel_derecho(self, layout_raiz):
        oscuro = self._oscuro

        self._panel_derecho = QWidget()
        self._panel_derecho.setStyleSheet(f"background-color: {p('bg_main', oscuro)};")
        layout_derecho = QVBoxLayout(self._panel_derecho)
        layout_derecho.setContentsMargins(0, 0, 0, 0)
        layout_derecho.setSpacing(0)

        self._header = self._construir_header()
        layout_derecho.addWidget(self._header)

        self._barra_filtros_widget = self._construir_barra_filtros()
        layout_derecho.addWidget(self._barra_filtros_widget)

        self._sep_header = QFrame()
        self._sep_header.setFrameShape(QFrame.Shape.HLine)
        self._sep_header.setStyleSheet(f"QFrame {{ background: {p('border', oscuro)}; max-height: 1px; border: none; margin: 0; }}")
        layout_derecho.addWidget(self._sep_header)

        self._construir_tabla(layout_derecho)

        layout_raiz.addWidget(self._panel_derecho, 1)

    def _construir_header(self) -> QWidget:
        oscuro = self._oscuro
        header = QFrame()
        header.setFixedHeight(56)
        header.setStyleSheet(f"""
            QFrame {{
                background-color: {p('bg_header', oscuro)};
                border-bottom: 1px solid {p('border', oscuro)};
            }}
        """)
        lay = QHBoxLayout(header)
        lay.setContentsMargins(20, 0, 20, 0)
        lay.setSpacing(12)

        self._lbl_titulo_header = QLabel("Control de Objetivos")
        self._lbl_titulo_header.setStyleSheet(f"""
            color: {p('text_primary', oscuro)};
            font-size: 17px;
            font-weight: 700;
            letter-spacing: 0.3px;
        """)
        lay.addWidget(self._lbl_titulo_header)

        self._lbl_subtitulo_header = QLabel("·  VESP Organizations")
        self._lbl_subtitulo_header.setStyleSheet(f"""
            color: {p('text_muted', oscuro)};
            font-size: 12px;
        """)
        lay.addWidget(self._lbl_subtitulo_header)
        lay.addStretch()

        self.lbl_estado_sync = QLabel("● En vivo")
        self.lbl_estado_sync.setStyleSheet(f"""
            color: {p('accent', oscuro)};
            font-size: 10px;
            font-weight: 600;
        """)
        lay.addWidget(self.lbl_estado_sync)

        return header

    def _construir_barra_filtros(self) -> QWidget:
        oscuro = self._oscuro

        scroll_filtros = QScrollArea()
        scroll_filtros.setWidgetResizable(True)
        scroll_filtros.setFixedHeight(54)
        scroll_filtros.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll_filtros.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll_filtros.setStyleSheet(f"""
            QScrollArea {{
                border: none;
                background: {p('bg_header', oscuro)};
            }}
            QScrollBar:horizontal {{
                height: 3px;
                background: transparent;
            }}
            QScrollBar::handle:horizontal {{
                background: {p('scrollbar_handle', oscuro)};
                border-radius: 1px;
            }}
        """)

        estilo_input = self._estilo_input(oscuro)
        estilo_lbl   = f"color: {p('text_secondary', oscuro)}; font-size: 11px; font-weight: 500;"

        estilo_btn_nav = f"""
            QPushButton {{
                background-color: {p('bg_tabla', oscuro)};
                color: {p('text_secondary', oscuro)};
                border: 1px solid {p('border', oscuro)};
                border-radius: 7px;
                font-size: 13px;
                min-width: 28px;
                max-width: 28px;
                min-height: 28px;
            }}
            QPushButton:hover {{
                background-color: {p('accent', oscuro)};
                color: white;
                border-color: {p('accent', oscuro)};
            }}
        """

        estilo_btn_accion = f"""
            QPushButton {{
                background-color: {p('accent', oscuro)};
                color: white;
                border: none;
                border-radius: 7px;
                padding: 4px 14px;
                font-size: 12px;
                font-weight: 600;
                min-height: 28px;
            }}
            QPushButton:hover {{
                background-color: {p('accent_dark', oscuro)};
            }}
        """

        self._widget_filtros = QWidget()
        self._widget_filtros.setStyleSheet(f"background-color: {p('bg_header', oscuro)};")
        fila = QHBoxLayout(self._widget_filtros)
        fila.setContentsMargins(16, 0, 16, 0)
        fila.setSpacing(8)

        self.selector_fecha = QDateEdit()
        self.selector_fecha.setDate(QDate.currentDate())
        self.selector_fecha.setCalendarPopup(True)
        self.selector_fecha.setFixedWidth(115)
        self.selector_fecha.setStyleSheet(estilo_input)

        self._boton_ant = QPushButton("‹")
        self._boton_ant.setToolTip("Día anterior (Ctrl+←)")
        self._boton_ant.setStyleSheet(estilo_btn_nav)
        self._boton_ant.setCursor(Qt.CursorShape.PointingHandCursor)
        self._boton_ant.clicked.connect(self._fecha_anterior)

        self._boton_sig = QPushButton("›")
        self._boton_sig.setToolTip("Día siguiente (Ctrl+→)")
        self._boton_sig.setStyleSheet(estilo_btn_nav)
        self._boton_sig.setCursor(Qt.CursorShape.PointingHandCursor)
        self._boton_sig.clicked.connect(self._fecha_siguiente)

        self.filtro_turno = QComboBox()
        self.filtro_turno.addItems(["Todos los turnos", "diurno", "nocturno"])
        self.filtro_turno.setFixedWidth(140)
        self.filtro_turno.setStyleSheet(estilo_input)

        self.filtro_supervisor = QComboBox()
        self.filtro_supervisor.addItem("Todos los supervisores", None)
        self.filtro_supervisor.setFixedWidth(170)
        self.filtro_supervisor.setStyleSheet(estilo_input)
        for s in cargar_supervisores():
            self.filtro_supervisor.addItem(s[1], s[0])

        self.filtro_estado = QComboBox()
        self.filtro_estado.addItems([
            "Todos", "Pasaron los dos", "No pasó nadie",
            "No pasó día", "No pasó noche"
        ])
        self.filtro_estado.setFixedWidth(155)
        self.filtro_estado.setStyleSheet(estilo_input)

        self.buscador = QLineEdit()
        self.buscador.setPlaceholderText("🔍  Buscar objetivo...")
        self.buscador.setFixedWidth(170)
        self.buscador.setStyleSheet(estilo_input)
        self.buscador.textChanged.connect(self.cargar_tabla)

        self._btn_filtrar = QPushButton("Aplicar")
        self._btn_filtrar.setFixedWidth(75)
        self._btn_filtrar.setStyleSheet(estilo_btn_accion)
        self._btn_filtrar.setCursor(Qt.CursorShape.PointingHandCursor)
        self._btn_filtrar.clicked.connect(self.cargar_tabla)

        lbl_fecha  = QLabel("Fecha");     lbl_fecha.setStyleSheet(estilo_lbl)
        lbl_turno  = QLabel("Turno");     lbl_turno.setStyleSheet(estilo_lbl)
        lbl_sup    = QLabel("Supervisor"); lbl_sup.setStyleSheet(estilo_lbl)
        lbl_estado = QLabel("Estado");    lbl_estado.setStyleSheet(estilo_lbl)

        fila.addWidget(lbl_fecha)
        fila.addWidget(self._boton_ant)
        fila.addWidget(self.selector_fecha)
        fila.addWidget(self._boton_sig)
        fila.addSpacing(4)
        fila.addWidget(lbl_turno)
        fila.addWidget(self.filtro_turno)
        fila.addWidget(lbl_sup)
        fila.addWidget(self.filtro_supervisor)
        fila.addWidget(lbl_estado)
        fila.addWidget(self.filtro_estado)
        fila.addSpacing(4)
        fila.addWidget(self.buscador)
        fila.addWidget(self._btn_filtrar)
        fila.addStretch()

        scroll_filtros.setWidget(self._widget_filtros)
        return scroll_filtros

    def _estilo_input(self, oscuro: bool) -> str:
        return f"""
            QComboBox, QLineEdit, QDateEdit {{
                background-color: {p('bg_tabla', oscuro)};
                color: {p('text_primary', oscuro)};
                border: 1px solid {p('border', oscuro)};
                border-radius: 7px;
                padding: 4px 8px;
                font-size: 12px;
                min-height: 28px;
                selection-background-color: {p('accent', oscuro)};
            }}
            QComboBox:hover, QLineEdit:hover, QDateEdit:hover {{
                border-color: {p('accent', oscuro)};
            }}
            QComboBox:focus, QLineEdit:focus, QDateEdit:focus {{
                border-color: {p('accent', oscuro)};
                outline: none;
            }}
            QComboBox::drop-down {{
                border: none;
                width: 20px;
            }}
            QComboBox QAbstractItemView {{
                background-color: {p('bg_tabla', oscuro)};
                color: {p('text_primary', oscuro)};
                border: 1px solid {p('border', oscuro)};
                selection-background-color: {p('accent', oscuro)};
                selection-color: white;
                outline: none;
            }}
        """

    def _construir_tabla(self, layout_derecho):
        oscuro = self._oscuro

        self.tabla = QTableWidget()
        self.tabla.setColumnCount(7)
        self.tabla.setHorizontalHeaderLabels([
            "Objetivo",
            "Equipo diurno", "Pasadas día",
            "Equipo nocturno", "Pasadas noche",
            "Estado", "Acción"
        ])

        self.tabla.setColumnWidth(0, 210)
        self.tabla.setColumnWidth(1, 155)
        self.tabla.setColumnWidth(2, 95)
        self.tabla.setColumnWidth(3, 155)
        self.tabla.setColumnWidth(4, 95)
        self.tabla.setColumnWidth(5, 145)
        self.tabla.setColumnWidth(6, 110)

        self.tabla.setAlternatingRowColors(False)
        self.tabla.setSortingEnabled(True)
        self.tabla.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.tabla.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.tabla.setShowGrid(False)
        self.tabla.verticalHeader().setVisible(False)
        self.tabla.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        self.tabla.horizontalHeader().setStretchLastSection(True)
        self.tabla.verticalHeader().setDefaultSectionSize(44)

        self.tabla.setStyleSheet(self._estilo_tabla(oscuro))
        layout_derecho.addWidget(self.tabla)

    def _estilo_tabla(self, oscuro: bool) -> str:
        return f"""
            QTableWidget {{
                background-color: {p('bg_tabla', oscuro)};
                gridline-color: transparent;
                border: none;
                outline: none;
                font-size: 12px;
                color: {p('text_primary', oscuro)};
                selection-background-color: transparent;
            }}
            QTableWidget::item {{
                padding: 6px 10px;
                border-bottom: 1px solid {p('border_light', oscuro)};
                color: {p('text_primary', oscuro)};
            }}
            QTableWidget::item:selected {{
                background-color: {p('btn_menu_hover', oscuro)};
                color: {p('text_primary', oscuro)};
            }}
            QHeaderView::section {{
                background-color: {p('bg_header', oscuro)};
                color: {p('text_secondary', oscuro)};
                border: none;
                border-bottom: 2px solid {p('accent', oscuro)};
                padding: 8px 10px;
                font-size: 11px;
                font-weight: 600;
                letter-spacing: 0.5px;
            }}
            QScrollBar:vertical {{
                width: 6px;
                background: transparent;
            }}
            QScrollBar::handle:vertical {{
                background: {p('scrollbar_handle', oscuro)};
                border-radius: 3px;
                min-height: 24px;
            }}
            QScrollBar::add-line:vertical,
            QScrollBar::sub-line:vertical {{ height: 0px; }}
            QScrollBar:horizontal {{
                height: 6px;
                background: transparent;
            }}
            QScrollBar::handle:horizontal {{
                background: {p('scrollbar_handle', oscuro)};
                border-radius: 3px;
            }}
        """

    # =========================================================================
    # TEMA — ALTERNAR Y REFRESCAR
    # =========================================================================

    def _alternar_tema(self):
        if self.alternar_tema_fn and self.app:
            self.alternar_tema_fn(self.app, self)
            self._oscuro = obtener_tema_actual() == "oscuro"
            self._refrescar_tema()

    def _cerrar_sesion(self):
        """Cierra la sesión actual y regresa a la ventana de login."""
        from services.sesion import cerrar_sesion
        from services.auditoria import registrar_evento

        # Registrar el logout en auditoría
        registrar_evento(self.usuario_id, "LOGOUT", "Usuario cerró sesión manualmente")

        # Cerrar sesión
        cerrar_sesion()

        # Cerrar esta ventana
        self.close()

        # Mostrar ventana de login nuevamente
        if self.on_login_exitoso:
            from ui.login import LoginWindow
            self.login = LoginWindow(self.on_login_exitoso)
            self.login.show()

    def _refrescar_tema(self):
        """Reaplica todos los estilos con la paleta actual sin reconstruir widgets."""
        oscuro = self._oscuro

        # Ventana raíz
        self.setStyleSheet(f"QWidget#VentanaPrincipal {{ background-color: {p('bg_main', oscuro)}; }}")

        # Sidebar
        self.panel_lateral.setStyleSheet(f"""
            QFrame#PanelLateral {{
                background-color: {p('bg_sidebar', oscuro)};
                border-right: 1px solid {p('border', oscuro)};
            }}
        """)
        self._cabecera_sidebar.setStyleSheet(f"background-color: {p('bg_sidebar', oscuro)};")
        self._contenedor_scroll.setStyleSheet(f"background-color: {p('bg_sidebar', oscuro)};")
        self._zona_inferior.setStyleSheet(f"background-color: {p('bg_sidebar', oscuro)};")

        # Títulos sidebar
        self.titulo_lateral.setStyleSheet(f"""
            color: {p('accent', oscuro)};
            font-size: 16px;
            font-weight: 800;
            letter-spacing: 2px;
        """)
        self.subtitulo_lateral.setStyleSheet(f"""
            color: {p('text_muted', oscuro)};
            font-size: 10px;
            letter-spacing: 1px;
        """)

        # Botón colapsar
        self.btn_colapsar.setStyleSheet(f"""
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

        # Botones del menú
        for b in self._botones_menu:
            b._oscuro = oscuro
            b._aplicar_estilo()

        # Label admin (solo existe si rol == admin)
        if hasattr(self, '_lbl_admin'):
            self._lbl_admin.setStyleSheet(f"""
                color: {p('text_muted', oscuro)};
                font-size: 9px;
                letter-spacing: 1.2px;
                font-weight: 600;
                padding: 4px 0 2px 4px;
            """)

        # Zoom
        estilo_mini_btn = f"""
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
        self._btn_zoom_menos.setStyleSheet(estilo_mini_btn)
        self._btn_zoom_mas.setStyleSheet(estilo_mini_btn)
        self.lbl_zoom.setStyleSheet(f"color: {p('text_muted', oscuro)}; font-size: 10px;")

        # Botón tema
        texto_tema = "☀  Modo claro" if oscuro else "🌙  Modo oscuro"
        self.btn_tema.setText(texto_tema)
        self.btn_tema.setStyleSheet(self._estilo_btn_tema(oscuro))

        # Botón logout
        self.btn_logout.setStyleSheet(self._estilo_btn_logout(oscuro))

        # Usuario label
        self.usuario_label.setStyleSheet(f"""
            color: {p('text_muted', oscuro)};
            font-size: 10px;
            padding: 3px 4px;
            border-radius: 5px;
            background: {p('btn_menu_hover', oscuro)};
        """)

        # Panel derecho
        self._panel_derecho.setStyleSheet(f"background-color: {p('bg_main', oscuro)};")

        # Header
        self._header.setStyleSheet(f"""
            QFrame {{
                background-color: {p('bg_header', oscuro)};
                border-bottom: 1px solid {p('border', oscuro)};
            }}
        """)
        self._lbl_titulo_header.setStyleSheet(f"""
            color: {p('text_primary', oscuro)};
            font-size: 17px;
            font-weight: 700;
            letter-spacing: 0.3px;
        """)
        self._lbl_subtitulo_header.setStyleSheet(f"color: {p('text_muted', oscuro)}; font-size: 12px;")
        self.lbl_estado_sync.setStyleSheet(f"color: {p('accent', oscuro)}; font-size: 10px; font-weight: 600;")

        # Barra de filtros
        self._barra_filtros_widget.setStyleSheet(f"""
            QScrollArea {{
                border: none;
                background: {p('bg_header', oscuro)};
            }}
            QScrollBar:horizontal {{
                height: 3px;
                background: transparent;
            }}
            QScrollBar::handle:horizontal {{
                background: {p('scrollbar_handle', oscuro)};
                border-radius: 1px;
            }}
        """)
        self._widget_filtros.setStyleSheet(f"background-color: {p('bg_header', oscuro)};")
        estilo_input = self._estilo_input(oscuro)
        self.selector_fecha.setStyleSheet(estilo_input)
        self.filtro_turno.setStyleSheet(estilo_input)
        self.filtro_supervisor.setStyleSheet(estilo_input)
        self.filtro_estado.setStyleSheet(estilo_input)
        self.buscador.setStyleSheet(estilo_input)

        estilo_btn_nav = f"""
            QPushButton {{
                background-color: {p('bg_tabla', oscuro)};
                color: {p('text_secondary', oscuro)};
                border: 1px solid {p('border', oscuro)};
                border-radius: 7px;
                font-size: 13px;
                min-width: 28px;
                max-width: 28px;
                min-height: 28px;
            }}
            QPushButton:hover {{
                background-color: {p('accent', oscuro)};
                color: white;
                border-color: {p('accent', oscuro)};
            }}
        """
        self._boton_ant.setStyleSheet(estilo_btn_nav)
        self._boton_sig.setStyleSheet(estilo_btn_nav)

        self._btn_filtrar.setStyleSheet(f"""
            QPushButton {{
                background-color: {p('accent', oscuro)};
                color: white;
                border: none;
                border-radius: 7px;
                padding: 4px 14px;
                font-size: 12px;
                font-weight: 600;
                min-height: 28px;
            }}
            QPushButton:hover {{
                background-color: {p('accent_dark', oscuro)};
            }}
        """)

        # Separador header
        self._sep_header.setStyleSheet(
            f"QFrame {{ background: {p('border', oscuro)}; max-height: 1px; border: none; margin: 0; }}"
        )

        # Tabla (el stylesheet + recargar regenera badges con la paleta nueva)
        self.tabla.setStyleSheet(self._estilo_tabla(oscuro))
        self.cargar_tabla()

    # =========================================================================
    # SIDEBAR COLAPSAR / EXPANDIR
    # =========================================================================

    def _toggle_sidebar(self):
        if self._sidebar_expandido:
            self._animar_sidebar(self.SIDEBAR_COLAPSADO)
            self._sidebar_expandido = False
            self.btn_colapsar.setText("›")
            self.btn_colapsar.setToolTip("Expandir menú (Ctrl+\\)")
            self.titulo_lateral.hide()
            self.subtitulo_lateral.hide()
            self.usuario_label.hide()
            self.btn_tema.hide()
            self.lbl_zoom.hide()
            for b in self._botones_menu:
                b.colapsar()
        else:
            self._animar_sidebar(self.SIDEBAR_EXPANDIDO)
            self._sidebar_expandido = True
            self.btn_colapsar.setText("‹")
            self.btn_colapsar.setToolTip("Colapsar menú (Ctrl+\\)")
            self.titulo_lateral.show()
            self.subtitulo_lateral.show()
            self.usuario_label.show()
            self.btn_tema.show()
            self.lbl_zoom.show()
            for b in self._botones_menu:
                b.expandir()

    def _animar_sidebar(self, ancho_destino: int):
        anim = QPropertyAnimation(self.panel_lateral, b"minimumWidth")
        anim.setDuration(220)
        anim.setStartValue(self.panel_lateral.width())
        anim.setEndValue(ancho_destino)
        anim.setEasingCurve(QEasingCurve.Type.OutCubic)

        anim2 = QPropertyAnimation(self.panel_lateral, b"maximumWidth")
        anim2.setDuration(220)
        anim2.setStartValue(self.panel_lateral.width())
        anim2.setEndValue(ancho_destino)
        anim2.setEasingCurve(QEasingCurve.Type.OutCubic)

        grupo = QParallelAnimationGroup(self)
        grupo.addAnimation(anim)
        grupo.addAnimation(anim2)
        grupo.start()
        self._anim_sidebar = grupo

    # =========================================================================
    # ZOOM
    # =========================================================================

    def _zoom_mas(self):
        if self.zoom_nivel < 20:
            self.zoom_nivel += 1
            self._aplicar_zoom()

    def _zoom_menos(self):
        if self.zoom_nivel > 9:
            self.zoom_nivel -= 1
            self._aplicar_zoom()

    def _aplicar_zoom(self):
        self.lbl_zoom.setText(f"{self.zoom_nivel}px")
        if self.app:
            import re
            stylesheet_actual = self.app.styleSheet()
            nuevo = re.sub(r'font-size: \d+px;', f'font-size: {self.zoom_nivel}px;', stylesheet_actual)
            self.app.setStyleSheet(nuevo)

    # =========================================================================
    # SINCRONIZACIÓN
    # =========================================================================

    def _configurar_sincronizacion(self):
        self.sincronizador = obtener_sincronizador()
        self.sincronizador.datos_cambiados.connect(self._on_datos_cambiados)
        self.sincronizador.tabla_actualizar.connect(self._on_tabla_actualizar)
        self.sincronizador.cache_invalidado.connect(self._on_cache_invalidado)

    def _on_datos_cambiados(self, tabla, operacion, datos):
        if tabla in ['objetivos', 'supervisores', 'pasadas', 'equipos']:
            self.cargar_tabla()

    def _on_tabla_actualizar(self, nombre_tabla):
        if nombre_tabla == 'principal':
            self.cargar_tabla()

    def _on_cache_invalidado(self, patron):
        pass

    # =========================================================================
    # FECHA
    # =========================================================================

    def _fecha_anterior(self):
        self.selector_fecha.setDate(self.selector_fecha.date().addDays(-1))
        self.cargar_tabla()

    def _fecha_siguiente(self):
        self.selector_fecha.setDate(self.selector_fecha.date().addDays(1))
        self.cargar_tabla()

    # =========================================================================
    # CONFIGURAR SHORTCUTS Y TIMERS
    # =========================================================================

    def _configurar_shortcuts(self):
        mapa = [
            ("Ctrl+P",     self.abrir_form_pasada),
            ("Ctrl+O",     self.abrir_form_objetivo),
            ("Ctrl+S",     self.abrir_form_supervisor),
            ("Ctrl+T",     self.abrir_form_turno),
            ("Ctrl+N",     self.abrir_notas),
            ("Ctrl+R",     self.abrir_reporte_mensual),
            ("Ctrl+B",     self.cargar_tabla),
            ("Ctrl+D",     self.abrir_dashboard),
            ("Ctrl+H",     self.abrir_ayuda),
            ("Ctrl+=",     self._zoom_mas),
            ("Ctrl+-",     self._zoom_menos),
            ("Ctrl+Left",  self._fecha_anterior),
            ("Ctrl+Right", self._fecha_siguiente),
            ("Ctrl+\\",    self._toggle_sidebar),
        ]
        for seq, fn in mapa:
            QShortcut(QKeySequence(seq), self).activated.connect(fn)

    def _configurar_timers(self):
        self.timer_inactividad = QTimer()
        self.timer_inactividad.setInterval(30 * 60 * 1000)
        self.timer_inactividad.timeout.connect(self.cerrar_por_inactividad)
        self.timer_inactividad.start()

        self.timer_refresco = QTimer()
        self.timer_refresco.setInterval(30 * 1000)
        self.timer_refresco.timeout.connect(self.cargar_tabla)
        self.timer_refresco.start()

    # =========================================================================
    # EVENTOS
    # =========================================================================

    def event(self, evento):
        try:
            if evento.type() in (
                QEvent.Type.MouseMove,
                QEvent.Type.KeyPress,
                QEvent.Type.MouseButtonPress
            ):
                self.timer_inactividad.start()
            return super().event(evento)
        except Exception as e:
            print(f"Error en event: {e}")
            return super().event(evento)

    def moveEvent(self, evento):
        try:
            self.timer_inactividad.start()
        except Exception:
            pass
        super().moveEvent(evento)

    def resizeEvent(self, evento):
        try:
            self.timer_inactividad.start()
        except Exception:
            pass
        super().resizeEvent(evento)

    def cerrar_por_inactividad(self):
        hacer_backup()
        QMessageBox.information(
            self, "Sesión cerrada",
            "La sesión se cerró por inactividad.\nSe realizó un backup automático."
        )
        registrar_accion(self.usuario_id, "Sesión cerrada por inactividad")
        self.close()
        from ui.login import LoginWindow
        self.login = LoginWindow(self.on_login_exitoso)
        self.login.show()

    def closeEvent(self, evento):
        confirmar = QMessageBox.question(
            self, "Confirmar salida",
            "¿Seguro que querés cerrar el sistema?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if confirmar == QMessageBox.StandardButton.Yes:
            registrar_accion(self.usuario_id, "Cerró el sistema")
            evento.accept()
        else:
            evento.ignore()

    # =========================================================================
    # TABLA PRINCIPAL
    # =========================================================================

    def _limpiar_tabla(self):
        for row in range(self.tabla.rowCount()):
            for col in (2, 4, 5, 6):
                w = self.tabla.cellWidget(row, col)
                if w is not None:
                    self.tabla.removeCellWidget(row, col)
                    w.deleteLater()
        self.tabla.clearContents()
        self.tabla.setRowCount(0)

    def _obtener_todas_pasadas_por_turno(self, fecha: str, supervisor_id: int = None) -> tuple:
        conexion = sqlite3.connect(DB_PATH)
        cursor = conexion.cursor()
        query = """
            SELECT objetivo_id, turno, COUNT(*)
            FROM pasadas WHERE fecha = ?
        """
        params = [fecha]
        if supervisor_id:
            query += " AND supervisor_id = ?"
            params.append(supervisor_id)
        query += " GROUP BY objetivo_id, turno"
        cursor.execute(query, params)
        resultados = cursor.fetchall()
        conexion.close()
        pasadas_dia   = {}
        pasadas_noche = {}
        for obj_id, turno, count in resultados:
            if turno == "diurno":
                pasadas_dia[obj_id] = count
            elif turno == "nocturno":
                pasadas_noche[obj_id] = count
        return pasadas_dia, pasadas_noche

    def _obtener_estado_detallado(self, pasadas_dia: int, pasadas_noche: int) -> tuple:
        if pasadas_dia > 0 and pasadas_noche > 0:
            return "Pasaron los dos", "#90EE90"
        if pasadas_dia > 0 and pasadas_noche == 0:
            return "No pasó noche", "#FFD700"
        if pasadas_dia == 0 and pasadas_noche > 0:
            return "No pasó día", "#FFD700"
        return "No pasó nadie", "#FF6B6B"

    def _crear_item(self, texto: str) -> QTableWidgetItem:
        item = QTableWidgetItem(texto)
        item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
        return item

    def _crear_widget_celda(self, widget: QWidget) -> QWidget:
        contenedor = QWidget()
        lay = QHBoxLayout(contenedor)
        lay.setContentsMargins(8, 4, 8, 4)
        lay.setSpacing(0)
        lay.addStretch()
        lay.addWidget(widget)
        lay.addStretch()
        return contenedor

    def cargar_tabla(self):
        fecha          = self.selector_fecha.date().toString("yyyy-MM-dd")
        turno          = self.filtro_turno.currentText()
        turno          = None if turno == "Todos los turnos" else turno
        supervisor_id  = self.filtro_supervisor.currentData()
        filtro_estado  = self.filtro_estado.currentText()
        texto_busqueda = self.buscador.text().strip().lower()

        self.objetivos_actuales = sorted(
            obtener_objetivos_del_dia(fecha),
            key=lambda o: o[1].lower()
        )
        equipo_dia   = obtener_equipo(fecha, "diurno")
        equipo_noche = obtener_equipo(fecha, "nocturno")

        sorting_enabled = self.tabla.isSortingEnabled()
        self.tabla.setSortingEnabled(False)
        self.tabla.setUpdatesEnabled(False)
        self._limpiar_tabla()

        pasadas_dia_totales, pasadas_noche_totales = self._obtener_todas_pasadas_por_turno(fecha)

        if turno == "diurno":
            pasadas_dia_filtradas = (
                self._obtener_todas_pasadas_por_turno(fecha, supervisor_id)[0]
                if supervisor_id else pasadas_dia_totales
            )
            pasadas_noche_filtradas = pasadas_noche_totales
        elif turno == "nocturno":
            pasadas_noche_filtradas = (
                self._obtener_todas_pasadas_por_turno(fecha, supervisor_id)[1]
                if supervisor_id else pasadas_noche_totales
            )
            pasadas_dia_filtradas = pasadas_dia_totales
        else:
            pasadas_dia_filtradas   = pasadas_dia_totales
            pasadas_noche_filtradas = pasadas_noche_totales

        filas = []
        for o in self.objetivos_actuales:
            if texto_busqueda and texto_busqueda not in o[1].lower():
                continue
            pd = pasadas_dia_filtradas.get(o[0], 0)
            pn = pasadas_noche_filtradas.get(o[0], 0)
            estado, _ = self._obtener_estado_detallado(
                pasadas_dia_totales.get(o[0], 0),
                pasadas_noche_totales.get(o[0], 0)
            )
            if filtro_estado != "Todos" and estado != filtro_estado:
                continue
            filas.append((o, pd, pn, estado))

        self.tabla.setRowCount(len(filas))
        oscuro  = self._oscuro
        bg_fila = p("bg_tabla",     oscuro)
        bg_alt  = p("bg_tabla_alt", oscuro)

        for i, (o, pd, pn, estado) in enumerate(filas):
            bg = bg_fila if i % 2 == 0 else bg_alt

            item_obj = self._crear_item(o[1])
            item_obj.setForeground(QColor(p("text_primary", oscuro)))
            item_obj.setBackground(QColor(bg))
            self.tabla.setItem(i, 0, item_obj)

            item_ed = self._crear_item(equipo_dia)
            item_ed.setForeground(QColor(p("text_secondary", oscuro)))
            item_ed.setBackground(QColor(bg))
            self.tabla.setItem(i, 1, item_ed)

            badge_pd = BadgeNumero(pd, oscuro)
            cont_pd = self._crear_widget_celda(badge_pd)
            cont_pd.setStyleSheet(f"background-color: {bg};")
            self.tabla.setCellWidget(i, 2, cont_pd)

            item_en = self._crear_item(equipo_noche)
            item_en.setForeground(QColor(p("text_secondary", oscuro)))
            item_en.setBackground(QColor(bg))
            self.tabla.setItem(i, 3, item_en)

            badge_pn = BadgeNumero(pn, oscuro)
            cont_pn = self._crear_widget_celda(badge_pn)
            cont_pn.setStyleSheet(f"background-color: {bg};")
            self.tabla.setCellWidget(i, 4, cont_pn)

            badge_estado = BadgeEstado(estado, oscuro)
            cont_est = self._crear_widget_celda(badge_estado)
            cont_est.setStyleSheet(f"background-color: {bg};")
            self.tabla.setCellWidget(i, 5, cont_est)

            boton_baja = QPushButton("Dar de baja")
            boton_baja.setCursor(Qt.CursorShape.PointingHandCursor)
            boton_baja.setStyleSheet(f"""
                QPushButton {{
                    background-color: transparent;
                    color: {p('accent_red', oscuro)};
                    border: 1px solid {p('accent_red', oscuro)};
                    border-radius: 6px;
                    padding: 4px 10px;
                    font-size: 11px;
                    font-weight: 600;
                }}
                QPushButton:hover {{
                    background-color: {p('accent_red', oscuro)};
                    color: white;
                }}
            """)
            boton_baja.clicked.connect(lambda checked, obj_id=o[0]: self.dar_de_baja(obj_id))
            cont_baja = self._crear_widget_celda(boton_baja)
            cont_baja.setStyleSheet(f"background-color: {bg};")
            self.tabla.setCellWidget(i, 6, cont_baja)

        self.tabla.setUpdatesEnabled(True)
        self.tabla.setSortingEnabled(sorting_enabled)
        self.tabla.update()

    def dar_de_baja(self, objetivo_id: int):
        confirmar = QMessageBox.question(
            self, "Confirmar",
            "¿Seguro que querés dar de baja este objetivo?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if confirmar == QMessageBox.StandardButton.Yes:
            fecha = self.selector_fecha.date().toString("yyyy-MM-dd")
            dar_de_baja_objetivo(objetivo_id, fecha)
            registrar_accion(self.usuario_id, f"Dio de baja objetivo id={objetivo_id}")
            self.cargar_tabla()

    # =========================================================================
    # ABRIR VENTANAS
    # =========================================================================

    def _abrir_ventana(self, attr: str, cls, *args, **kwargs):
        ventana = getattr(self, attr, None)
        if ventana is None or not ventana.isVisible():
            ventana = cls(*args, **kwargs)
            setattr(self, attr, ventana)
            ventana.show()
        else:
            ventana.raise_()
            ventana.activateWindow()

    def abrir_form_objetivo(self):
        v = getattr(self, 'form_objetivo', None)
        if v is None or not v.isVisible():
            self.form_objetivo = FormObjetivo()
            self.form_objetivo.destroyed.connect(self.cargar_tabla)
            self.form_objetivo.show()
        else:
            v.raise_(); v.activateWindow()

    def abrir_form_supervisor(self):
        self._abrir_ventana('form_supervisor', FormSupervisor)

    def abrir_form_pasada(self):
        v = getattr(self, 'form_pasada', None)
        if v is None or not v.isVisible():
            self.form_pasada = FormPasada(
                fecha_inicial=self.selector_fecha.date().toString("yyyy-MM-dd")
            )
            self.form_pasada.pasada_registrada.connect(self.cargar_tabla)
            self.form_pasada.show()
        else:
            v.raise_(); v.activateWindow()

    def abrir_form_turno(self):
        v = getattr(self, 'form_turno', None)
        if v is None or not v.isVisible():
            self.form_turno = FormTurno()
            self.form_turno.destroyed.connect(self.cargar_tabla)
            self.form_turno.show()
        else:
            v.raise_(); v.activateWindow()

    def abrir_lista_objetivos(self):
        self._abrir_ventana('lista_objetivos', ListaObjetivos)

    def abrir_lista_supervisores(self):
        self._abrir_ventana('lista_supervisores', ListaSupervisores)

    def abrir_lista_pasadas(self):
        v = getattr(self, 'lista_pasadas', None)
        if v is None or not v.isVisible():
            self.lista_pasadas = ListaPasadas()
            self.lista_pasadas.destroyed.connect(self.cargar_tabla)
            self.lista_pasadas.show()
        else:
            v.raise_(); v.activateWindow()

    def abrir_notas(self):
        self._abrir_ventana('notas', NotasDiarias)

    def abrir_dashboard(self):
        self._abrir_ventana('dashboard', Dashboard)

    def abrir_reporte_mensual(self):
        self._abrir_ventana('reporte_mensual', ReporteMensual)

    def abrir_reporte_mensual_objetivo(self):
        self._abrir_ventana('reporte_mensual_objetivo', ReporteObjetivo)

    def abrir_gestionar_usuarios(self):
        self._abrir_ventana('gestionar_usuarios', GestionarUsuarios)

    def abrir_logs(self):
        self._abrir_ventana('logs', VistaLogs)

    def abrir_cache(self):
        v = getattr(self, 'cache_monitor', None)
        if v is None or not v.isVisible():
            self.cache_monitor = VistaCache(self.usuario_id)
            self.cache_monitor.setWindowTitle("Monitor de Caché Inteligente")
            self.cache_monitor.setGeometry(100, 100, 1000, 600)
            self.cache_monitor.show()
        else:
            v.raise_(); v.activateWindow()

    def abrir_indexacion(self):
        v = getattr(self, 'indexacion', None)
        if v is None or not v.isVisible():
            self.indexacion = VistaIndexacion(self.usuario_id)
            self.indexacion.setWindowTitle("Optimización de Índices y Rendimiento")
            self.indexacion.setGeometry(100, 100, 1200, 700)
            self.indexacion.show()
        else:
            v.raise_(); v.activateWindow()

    def abrir_validaciones(self):
        v = getattr(self, 'validaciones', None)
        if v is None or not v.isVisible():
            self.validaciones = VistaValidaciones(self.usuario_id)
            self.validaciones.setWindowTitle("Validaciones e Integridad de BD")
            self.validaciones.setGeometry(100, 100, 1000, 600)
            self.validaciones.show()
        else:
            v.raise_(); v.activateWindow()

    def abrir_ayuda(self):
        self._abrir_ventana('ayuda', Ayuda)

    def abrir_transferir_datos(self):
        self._abrir_ventana('transferir_datos', TransferirDatos)

    def abrir_sincronizacion(self):
        v = getattr(self, 'sincronizacion', None)
        if v is None or not v.isVisible():
            self.sincronizacion = VistaSincronizacion(self.usuario_id)
            self.sincronizacion.setWindowTitle("Monitoreo de Sincronización de Datos")
            self.sincronizacion.setGeometry(100, 100, 1200, 700)
            self.sincronizacion.show()
        else:
            v.raise_(); v.activateWindow()

    def abrir_importar_excel(self):
        self._abrir_ventana('importar_excel', ImportarExcel)

    def abrir_auditoria(self):
        self._abrir_ventana('auditoria', VistaAuditoria)