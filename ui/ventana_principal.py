# =============================================================================
# VESP Organizations - Sistema de Control de Objetivos
# Ventana principal del sistema — UI/UX mejorada
# =============================================================================
import sqlite3

from typing import Optional, Callable

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QTableWidget, QTableWidgetItem, QLabel,
    QPushButton, QDateEdit, QComboBox, QMessageBox,
    QFrame, QLineEdit, QHeaderView, QScrollArea,
    QToolButton, QSizePolicy
    , QDialog, QDialogButtonBox, QCheckBox, QGridLayout
)
from PyQt6.QtCore import (
    QDate, QTimer, QEvent, Qt, QPropertyAnimation, QEasingCurve, QParallelAnimationGroup
)
from PyQt6.QtGui import QColor, QPixmap, QIcon, QShortcut, QKeySequence
from services.reportes import obtener_objetivos_del_dia
from services.queries_tabla import (
    obtener_equipo, obtener_supervisores_de_pasadas, cargar_supervisores
)
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
from ui.feriados import VistaFeriados
from ui.vista_auditoria import VistaAuditoria
from ui.vista_validaciones import VistaValidaciones
from ui.vista_indexacion import VistaIndexacion
from ui.vista_sincronizacion import VistaSincronizacion
from ui.configuracion import ConfiguracionDialog
from ui.animaciones import animar_aparecer
from ui.theme.theme_manager import get_theme_manager
from ui.theme.tokens import THEMES
from services.permisos import tiene_permiso
from services.backup import hacer_backup
from services.logger import registrar_accion
from services.assets import ruta_asset
from services.sincronizacion import obtener_sincronizador
from services.usuarios import get_username_by_id
from services.menu_config import obtener_menu_usuario, guardar_menu_usuario
from services.sesion import actualizar_actividad_sesion, cerrar_sesion, TIEMPO_INACTIVIDAD_MAXIMA
from database.db import DB_PATH


# Componentes visuales y estilos centralizados
from ui.components import (
    CountChip,
    GlassCard,
    KpiCard,
    PillButton,
    SearchInput,
    StatusBadge,
)
from ui.widgets.estilos import (
    obtener_color, estilo_separador
)

# =============================================================================
# UTILIDADES
# =============================================================================

def obtener_nombre_usuario(usuario_id: int) -> str:
    """Obtiene el nombre de usuario por ID."""
    return get_username_by_id(usuario_id) or "Usuario"


def crear_separador(oscuro: bool) -> QFrame:
    """Crea un separador visual horizontal."""
    sep = QFrame()
    sep.setFrameShape(QFrame.Shape.HLine)
    sep.setStyleSheet(estilo_separador(oscuro))
    return sep


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
        self._theme_manager = get_theme_manager()

        self.setText(self._texto_completo)
        self.setProperty("icono", icono)
        self.setProperty("texto_completo", self._texto_completo)
        self.setToolTip(texto)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.setFixedHeight(38)
        self._aplicar_estilo()

    def _aplicar_estilo(self):
        bg_activo   = obtener_color("accent", self._oscuro)
        text_activo = self._theme_manager.tokens()["accent_text"]
        bg_hover    = obtener_color("btn_menu_hover", self._oscuro)
        text_normal = obtener_color("btn_menu_text", self._oscuro)

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
                    color: {obtener_color("text_primary", self._oscuro)};
                }}
                QPushButton:pressed {{
                    background-color: {bg_activo};
                    color: {obtener_color('accent_text', self._oscuro)};
                }}
            """)

    def set_activo(self, activo: bool):
        self._activo = activo
        self._aplicar_estilo()

    def actualizar_tema(self, oscuro: bool):
        """Actualiza la paleta del botón conservando su estado activo."""
        self._oscuro = oscuro
        self._aplicar_estilo()

    def colapsar(self):
        self._expandido = False
        self.setText(f" {self._icono}")
        self.setFixedHeight(38)

    def expandir(self):
        self._expandido = True
        self.setText(self._texto_completo)



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
        self._menu_visible = obtener_menu_usuario(usuario_id)

        super().__init__()
        self.setWindowTitle("VESP · Control de Objetivos")
        self.setWindowFlags(Qt.WindowType.Window)
        self.move(80, 60)
        self.resize(1340, 660)
        self.setMinimumSize(720, 440)
        self._theme_manager = get_theme_manager()
        self.zoom_nivel = self._theme_manager.font_size()
        self.setWindowIcon(QIcon(THEMES[self._theme_manager.current()]["logo_path"]))

        self._oscuro = self._theme_manager.current() != "Claro"

        self._construir_ui()
        self._theme_manager.theme_changed.connect(self._al_cambiar_tema)
        self._theme_manager.font_size_changed.connect(self._sincronizar_tamano_fuente)
        self.cargar_tabla()
        self._mostrar_landing_inicial()
        self._configurar_shortcuts()
        self._configurar_timers()
        self._configurar_event_filter()
        self._configurar_sincronizacion()

    def _actualizar_logo_tema(self, nombre_tema: str) -> None:
        ruta_logo = THEMES[nombre_tema]["logo_path"]
        self.setWindowIcon(QIcon(ruta_logo))
        if hasattr(self, "logo_label"):
            self.logo_label.setPixmap(
                QPixmap(ruta_logo).scaled(
                    36,
                    36,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation,
                )
            )

    def _al_cambiar_tema(self, nombre_tema: str) -> None:
        self._oscuro = nombre_tema != "Claro"
        self.btn_tema.setText(
            "🌙  Grafito" if nombre_tema == "Claro" else "☀  Claro"
        )
        self._actualizar_logo_tema(nombre_tema)
        self._refrescar_tema()

    # =========================================================================
    # CONSTRUCCIÓN UI
    # =========================================================================

    def _construir_ui(self):
        layout_raiz = QHBoxLayout(self)
        layout_raiz.setSpacing(0)
        layout_raiz.setContentsMargins(0, 0, 0, 0)

        self._construir_sidebar(layout_raiz)
        self._construir_panel_derecho(layout_raiz)

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
                background-color: {obtener_color('bg_sidebar', oscuro)};
                border-right: 1px solid {obtener_color('border', oscuro)};
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
                background: {obtener_color('scrollbar_handle', oscuro)};
                border-radius: 2px;
                min-height: 24px;
            }}
            QScrollBar::add-line:vertical,
            QScrollBar::sub-line:vertical {{ height: 0px; }}
        """)

        self._contenedor_scroll = QWidget()
        self._contenedor_scroll.setStyleSheet(f"background-color: {obtener_color('bg_sidebar', oscuro)};")
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
        self._cabecera_sidebar.setStyleSheet(f"background-color: {obtener_color('bg_sidebar', oscuro)};")

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
                background: {obtener_color('btn_menu_hover', oscuro)};
                color: {obtener_color('text_secondary', oscuro)};
                border: none;
                border-radius: 5px;
                font-size: 14px;
                font-weight: bold;
            }}
            QToolButton:hover {{
                background: {obtener_color('accent', oscuro)};
                color: {obtener_color('accent_text', oscuro)};
            }}
        """)
        self.btn_colapsar.clicked.connect(self._toggle_sidebar)

        self.logo_label = QLabel()
        self._actualizar_logo_tema(self._theme_manager.current())

        fila_logo = QHBoxLayout()
        fila_logo.setContentsMargins(0, 0, 0, 0)
        fila_logo.addWidget(self.logo_label)
        fila_logo.addStretch()
        fila_logo.addWidget(self.btn_colapsar)
        lay.addLayout(fila_logo)

        self.titulo_lateral = QLabel("V.E.S.P")
        self.titulo_lateral.setStyleSheet(f"""
            color: {obtener_color('accent', oscuro)};
            font-size: 16px;
            font-weight: 800;
            letter-spacing: 2px;
        """)
        lay.addWidget(self.titulo_lateral)

        self.subtitulo_lateral = QLabel("Organizations")
        self.subtitulo_lateral.setStyleSheet(f"""
            color: {obtener_color('text_muted', oscuro)};
            font-size: 10px;
            letter-spacing: 1px;
        """)
        lay.addWidget(self.subtitulo_lateral)

        return self._cabecera_sidebar

    def _construir_botones_menu(self):
        oscuro = self._oscuro

        def add_btn(icono, texto, accion, tooltip_extra="", clave=None):
            b = BotonMenu(icono, texto, oscuro)
            b.setProperty("menu_key", clave or "")
            if tooltip_extra:
                b.setToolTip(f"{texto}  {tooltip_extra}")
            b.clicked.connect(lambda: self._activar_boton(b, accion))
            self._botones_menu.append(b)
            self.layout_scroll.addWidget(b)
            if clave and not self._menu_visible.get(clave, True):
                b.hide()
            return b

        def add_sep():
            self.layout_scroll.addWidget(crear_separador(oscuro))
            self.layout_scroll.addSpacing(2)

        self._btn_control   = add_btn("📋", "Control diario",     self._mostrar_dashboard,   "(Ctrl+B)", "control_diario")
        self._btn_pasada    = add_btn("✅", "Registrar pasada",   self.abrir_form_pasada,    "(Ctrl+P)", "registrar_pasada")
        self._btn_turno     = add_btn("🕐", "Registrar turno",    self.abrir_form_turno,     "(Ctrl+T)", "registrar_turno")

        add_sep()

        self._btn_add_obj = add_btn("➕", "Agregar objetivo",    self.abrir_form_objetivo,  "(Ctrl+O)", "agregar_objetivo")
        add_btn("📍", "Ver objetivos",       self.abrir_lista_objetivos, clave="ver_objetivos")
        self._btn_add_sup = add_btn("👤", "Agregar supervisor",  self.abrir_form_supervisor, "(Ctrl+S)", "agregar_supervisor")
        add_btn("👥", "Ver supervisores",    self.abrir_lista_supervisores, clave="ver_supervisores")

        add_sep()

        add_btn("🔍", "Ver pasadas",         self.abrir_lista_pasadas, clave="ver_pasadas")
        add_btn("📝", "Notas del día",       self.abrir_notas,              "(Ctrl+N)", "notas")
        add_btn("🏖️", "Feriados",            self.abrir_feriados, clave="feriados")
        add_btn("📅", "Reporte mensual",     self.abrir_reporte_mensual,    "(Ctrl+R)", "reporte_mensual")
        add_btn("📅", "Reporte objetivo",    self.abrir_reporte_mensual_objetivo, "(Ctrl+Ñ)", "reporte_objetivo")
        add_btn("💾", "Transferir datos",    self.abrir_transferir_datos, clave="transferir_datos")
        add_btn("📥", "Importar Excel",      self.abrir_importar_excel, clave="importar_excel")
        add_btn("❓", "Ayuda",               self.abrir_ayuda,              "(Ctrl+H)", "ayuda")

        if tiene_permiso('usuarios.ver'):
            add_sep()
            self._lbl_admin = QLabel("  ADMINISTRACIÓN")
            self._lbl_admin.setStyleSheet(f"""
                color: {obtener_color('text_muted', oscuro)};
                font-size: 9px;
                letter-spacing: 1.2px;
                font-weight: 600;
                padding: 4px 0 2px 4px;
            """)
            self.layout_scroll.addWidget(self._lbl_admin)
            add_btn("⚙️",  "Gestionar usuarios", self.abrir_gestionar_usuarios, clave="gestionar_usuarios")
            add_btn("📜",  "Historial",           self.abrir_logs, clave="logs")
            add_btn("🔧",  "Optimización de BD",  self.abrir_indexacion, clave="optimizacion")
            add_btn("🛡️",  "Validaciones BD",     self.abrir_validaciones, clave="validaciones")
            add_btn("🔎",  "Auditoría detallada", self.abrir_auditoria, clave="auditoria")
            add_btn("🔄",  "Sincronización",      self.abrir_sincronizacion, clave="sincronizacion")

    def _activar_boton(self, btn: BotonMenu, accion):
        if self._boton_activo and self._boton_activo is not btn:
            self._boton_activo.set_activo(False)
        btn.set_activo(True)
        self._boton_activo = btn
        accion()

    def _construir_zona_inferior(self) -> QWidget:
        oscuro = self._oscuro
        zona = QWidget()
        zona.setStyleSheet(f"background-color: {obtener_color('bg_sidebar', oscuro)};")
        lay = QVBoxLayout(zona)
        lay.setContentsMargins(8, 4, 8, 10)
        lay.setSpacing(4)

        lay.addWidget(crear_separador(oscuro))

        fila_zoom = QHBoxLayout()
        fila_zoom.setSpacing(4)

        estilo_mini_btn = f"""
            QPushButton {{
                background-color: {obtener_color('btn_menu_hover', oscuro)};
                color: {obtener_color('text_secondary', oscuro)};
                border: 1px solid {obtener_color('border', oscuro)};
                border-radius: 5px;
                font-size: 11px;
                min-width: 30px;
                max-width: 36px;
                min-height: 26px;
            }}
            QPushButton:hover {{
                background-color: {obtener_color('accent', oscuro)};
                color: {obtener_color('accent_text', oscuro)};
                border-color: {obtener_color('accent', oscuro)};
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
        self.lbl_zoom.setStyleSheet(f"color: {obtener_color('text_muted', oscuro)}; font-size: 10px;")
        self.lbl_zoom.setAlignment(Qt.AlignmentFlag.AlignCenter)

        fila_zoom.addWidget(self._btn_zoom_menos)
        fila_zoom.addWidget(self.lbl_zoom, 1)
        fila_zoom.addWidget(self._btn_zoom_mas)
        lay.addLayout(fila_zoom)

        texto_tema = "☀  Claro" if oscuro else "🌙  Grafito"
        self.btn_tema = QPushButton(texto_tema)
        self.btn_tema.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_tema.setFixedHeight(34)
        self.btn_tema.setStyleSheet(self._estilo_btn_tema(oscuro))
        self.btn_tema.clicked.connect(self._alternar_tema)
        lay.addWidget(self.btn_tema)

        nombre_usuario = obtener_nombre_usuario(self.usuario_id)
        self.usuario_label = QLabel(f"👤  {nombre_usuario}")
        self.usuario_label.setStyleSheet(f"""
            color: {obtener_color('text_muted', oscuro)};
            font-size: 10px;
            padding: 3px 4px;
            border-radius: 5px;
            background: {obtener_color('btn_menu_hover', oscuro)};
        """)
        self.usuario_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.usuario_label.setWordWrap(True)
        lay.addWidget(self.usuario_label)

        self.btn_configuracion = QPushButton("⚙ Configuración")
        self.btn_configuracion.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_configuracion.setFixedHeight(30)
        self.btn_configuracion.setStyleSheet(self._estilo_btn_tema(oscuro))
        self.btn_configuracion.clicked.connect(self._abrir_configuracion)
        lay.addWidget(self.btn_configuracion)

        self.btn_configurar_menu = QPushButton("⚙ Configurar menú")
        self.btn_configurar_menu.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_configurar_menu.setFixedHeight(30)
        self.btn_configurar_menu.setStyleSheet(self._estilo_btn_tema(oscuro))
        self.btn_configurar_menu.clicked.connect(self._configurar_menu)
        lay.addWidget(self.btn_configurar_menu)

        # Botón de cerrar sesión
        self.btn_logout = QPushButton("🚪 Cerrar sesión")
        self.btn_logout.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_logout.setFixedHeight(34)
        self.btn_logout.setStyleSheet(self._estilo_btn_logout(oscuro))
        self.btn_logout.clicked.connect(self._cerrar_sesion)
        lay.addWidget(self.btn_logout)

        return zona

    def _abrir_configuracion(self) -> None:
        dialog = ConfiguracionDialog(self)
        dialog.exec()

    def _configurar_menu(self) -> None:
        dialogo = QDialog(self)
        dialogo.setWindowTitle("Configurar menú")
        layout = QVBoxLayout(dialogo)
        checks = {}
        etiquetas = {
            "auditoria": "Auditoría detallada",
            "validaciones": "Validaciones BD",
            "sincronizacion": "Sincronización",
            "optimizacion": "Optimización de BD",
            "ver_pasadas": "Ver pasadas",
            "reporte_mensual": "Reporte mensual",
            "reporte_objetivo": "Reporte objetivo",
            "notas": "Notas del día",
        }
        for clave, etiqueta in etiquetas.items():
            check = QCheckBox(etiqueta)
            check.setChecked(self._menu_visible.get(clave, True))
            checks[clave] = check
            layout.addWidget(check)

        botones = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel
        )
        botones.accepted.connect(dialogo.accept)
        botones.rejected.connect(dialogo.reject)
        layout.addWidget(botones)

        if dialogo.exec() != QDialog.DialogCode.Accepted:
            return
        self._menu_visible.update({clave: check.isChecked() for clave, check in checks.items()})
        guardar_menu_usuario(self.usuario_id, self._menu_visible)
        for boton in self._botones_menu:
            clave = boton.property("menu_key")
            if clave:
                boton.setVisible(self._menu_visible.get(clave, True))
        for tarjeta in self._landing.findChildren(QPushButton, "LandingCard"):
            clave = tarjeta.property("menu_key")
            tarjeta.setVisible(self._menu_visible.get(clave, True))

    def _estilo_btn_tema(self, oscuro: bool) -> str:
        return f"""
            QPushButton {{
                background-color: {obtener_color('btn_menu_hover', oscuro)};
                color: {obtener_color('text_secondary', oscuro)};
                border: 1px solid {obtener_color('border', oscuro)};
                border-radius: 7px;
                font-size: 11px;
                padding: 0 10px;
                text-align: left;
            }}
            QPushButton:hover {{
                background-color: {obtener_color('accent', oscuro)};
                color: {obtener_color('accent_text', oscuro)};
                border-color: {obtener_color('accent', oscuro)};
            }}
        """

    def _estilo_btn_logout(self, oscuro: bool) -> str:
        tokens = self._theme_manager.tokens()
        return f"""
            QPushButton {{
                background-color: {tokens['danger_button_bg']};
                color: {tokens['danger_button_text']};
                border: 1px solid {tokens['danger_button_bg']};
                border-radius: 7px;
                font-size: 11px;
                padding: 0 10px;
                text-align: center;
            }}
            QPushButton:hover {{
                background-color: {tokens['danger_button_hover']};
                border-color: {tokens['danger_button_hover']};
            }}
        """

    # -------------------------------------------------------------------------
    # PANEL DERECHO
    # -------------------------------------------------------------------------

    def _construir_panel_derecho(self, layout_raiz):
        oscuro = self._oscuro

        self._panel_derecho = QWidget()
        self._panel_derecho.setObjectName("panelControlObjetivos")
        tokens = self._theme_manager.tokens()
        self._panel_derecho.setStyleSheet(f"""
            QWidget#panelControlObjetivos {{
                background: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 1,
                    stop: 0 {tokens['bg_gradient_start']},
                    stop: 1 {tokens['bg_gradient_end']});
            }}
        """)
        layout_derecho = QVBoxLayout(self._panel_derecho)
        layout_derecho.setContentsMargins(20, 12, 20, 14)
        layout_derecho.setSpacing(10)

        self._header = self._construir_header()
        layout_derecho.addWidget(self._header)

        self._metricas = self._construir_metricas()
        layout_derecho.addWidget(self._metricas)

        self._barra_filtros_widget = self._construir_barra_filtros()
        layout_derecho.addWidget(self._barra_filtros_widget)

        self._sep_header = QFrame()
        self._sep_header.setFrameShape(QFrame.Shape.HLine)
        tokens = self._theme_manager.tokens()
        self._sep_header.setStyleSheet(
            f"QFrame {{ background: {tokens['border']}; max-height: 1px; border: none; margin: 0; }}"
        )
        layout_derecho.addWidget(self._sep_header)

        self._construir_tabla(layout_derecho)

        self._landing = self._construir_landing()
        layout_derecho.insertWidget(1, self._landing, 1)

        layout_raiz.addWidget(self._panel_derecho, 1)

    def _construir_landing(self) -> QWidget:
        landing = QWidget()
        layout = QVBoxLayout(landing)
        layout.setContentsMargins(28, 28, 28, 28)
        layout.setSpacing(18)

        titulo = QLabel("¿A dónde querés ir?")
        titulo.setObjectName("LandingTitle")
        subtitulo = QLabel("Elegí un módulo para comenzar")
        subtitulo.setObjectName("LandingSubtitle")
        layout.addWidget(titulo)
        layout.addWidget(subtitulo)

        acciones = [
            ("control_diario", "📋", "Control diario", self._mostrar_dashboard),
            ("registrar_pasada", "✅", "Registrar pasada", self.abrir_form_pasada),
            ("ver_pasadas", "🔍", "Ver pasadas", self.abrir_lista_pasadas),
            ("reporte_mensual", "📅", "Reporte mensual", self.abrir_reporte_mensual),
            ("reporte_objetivo", "🎯", "Reporte objetivo", self.abrir_reporte_mensual_objetivo),
            ("notas", "📝", "Notas del día", self.abrir_notas),
            ("agregar_objetivo", "➕", "Agregar objetivo", self.abrir_form_objetivo),
            ("feriados", "🏖", "Feriados", self.abrir_feriados),
        ]
        grilla = QGridLayout()
        grilla.setHorizontalSpacing(14)
        grilla.setVerticalSpacing(14)
        for indice, (clave, icono, texto, accion) in enumerate(acciones):
            if not self._menu_visible.get(clave, True):
                continue
            tarjeta = QPushButton(f"{icono}\n{texto}")
            tarjeta.setObjectName("LandingCard")
            tarjeta.setProperty("menu_key", clave)
            tarjeta.setMinimumHeight(92)
            tarjeta.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
            tarjeta.clicked.connect(accion)
            grilla.addWidget(tarjeta, indice // 3, indice % 3)
        layout.addLayout(grilla)
        layout.addStretch()
        return landing

    def _mostrar_dashboard(self) -> None:
        self._landing.hide()
        self._metricas.show()
        self._barra_filtros_widget.show()
        self._sep_header.show()
        self.tabla.show()
        self.cargar_tabla()
        self._panel_derecho.update()
        self.tabla.viewport().update()

    def _mostrar_landing_inicial(self) -> None:
        self._metricas.hide()
        self._barra_filtros_widget.hide()
        self._sep_header.hide()
        self.tabla.hide()
        self._landing.show()
        self._landing.update()

    def _construir_metricas(self) -> QWidget:
        contenedor = GlassCard(shadow=True, content_margins=12)
        layout = QHBoxLayout()
        layout.setSpacing(12)
        self._metricas_valores = {}

        for clave, titulo, valor, icono in (
            ("objetivos", "Objetivos activos", "0", "◎"),
            ("pasadas", "Pasadas del día", "0", "✓"),
            ("alertas", "Alertas pendientes", "0", "!"),
        ):
            card_type = KpiCard
            kwargs = {"contrast": True} if clave == "alertas" else {}
            metric = card_type(
                titulo,
                valor,
                icono,
                shadow=False,
                **kwargs,
            )
            metric.setMinimumWidth(0)
            layout.addWidget(metric, 1)
            self._metricas_valores[clave] = metric
        contenedor.add_layout(layout)
        return contenedor

    def _actualizar_metricas(self, objetivos, pasadas_dia, pasadas_noche) -> None:
        total_pasadas = sum(pasadas_dia.values()) + sum(pasadas_noche.values())
        objetivos_con_pasada = set(pasadas_dia) | set(pasadas_noche)
        alertas = sum(1 for objetivo in objetivos if objetivo[0] not in objetivos_con_pasada)
        self._metricas_valores["objetivos"].set_value(len(objetivos))
        self._metricas_valores["pasadas"].set_value(total_pasadas)
        self._metricas_valores["alertas"].set_value(alertas)

    def _construir_header(self) -> QWidget:
        header = QFrame()
        header.setObjectName("ControlObjectivesHeader")
        header.setMinimumHeight(86)
        header.setStyleSheet(
            f"QFrame#ControlObjectivesHeader {{ border-bottom: 1px solid {self._theme_manager.tokens()['border']}; }}"
        )
        lay = QHBoxLayout(header)
        lay.setContentsMargins(24, 12, 24, 12)
        lay.setSpacing(12)

        title_group = QVBoxLayout()
        title_group.setSpacing(2)
        self._lbl_titulo_header = QLabel("Control de Objetivos")
        self._lbl_subtitulo_header = QLabel("Seguimiento diario de objetivos y cobertura")
        title_group.addWidget(self._lbl_titulo_header)
        title_group.addWidget(self._lbl_subtitulo_header)
        lay.addLayout(title_group)
        lay.addStretch()

        self.lbl_estado_sync = StatusBadge("● En vivo", "ok")
        lay.addWidget(self.lbl_estado_sync)
        self._header = header
        self._theme_manager.theme_changed.connect(self._estilizar_header)
        self._estilizar_header(self._theme_manager.current())

        return header

    def _estilizar_header(self, theme_name: str) -> None:
        tokens = self._theme_manager.tokens(theme_name)
        self._header.setStyleSheet(
            f"QFrame#ControlObjectivesHeader {{ "
            f"background: transparent; border-bottom: 1px solid {tokens['border']}; }}"
        )
        self._lbl_titulo_header.setStyleSheet(
            f"color: {tokens['text_primary']}; font-size: {tokens['font_size_title']}; "
            "font-weight: 700; background: transparent;"
        )
        self._lbl_subtitulo_header.setStyleSheet(
            f"color: {tokens['text_secondary']}; font-size: {tokens['font_size_sm']}; "
            "background: transparent;"
        )

    def _construir_barra_filtros(self) -> QWidget:
        oscuro = self._oscuro

        scroll_filtros = QScrollArea()
        scroll_filtros.setWidgetResizable(True)
        scroll_filtros.setFixedHeight(78)
        scroll_filtros.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll_filtros.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll_filtros.setStyleSheet(f"""
            QScrollArea {{
                border: none;
                background: transparent;
            }}
            QScrollBar:horizontal {{
                height: 3px;
                background: transparent;
            }}
            QScrollBar::handle:horizontal {{
                background: {obtener_color('scrollbar_handle', oscuro)};
                border-radius: 1px;
            }}
        """)

        estilo_input = self._estilo_input(oscuro)
        fila = QHBoxLayout()
        fila.setContentsMargins(0, 0, 0, 0)
        fila.setSpacing(7)

        self.selector_fecha = QDateEdit()
        self.selector_fecha.setDate(QDate.currentDate())
        self.selector_fecha.setCalendarPopup(True)
        self.selector_fecha.setFixedWidth(132)
        self.selector_fecha.setStyleSheet(estilo_input)

        self._boton_ant = PillButton("‹", "secondary")
        self._boton_ant.setToolTip("Día anterior (Ctrl+←)")
        self._boton_ant.setFixedSize(34, 34)
        self._boton_ant.setCursor(Qt.CursorShape.PointingHandCursor)
        self._boton_ant.clicked.connect(self._fecha_anterior)

        self._boton_sig = PillButton("›", "secondary")
        self._boton_sig.setToolTip("Día siguiente (Ctrl+→)")
        self._boton_sig.setFixedSize(34, 34)
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

        self.buscador = SearchInput("Buscar objetivo...")
        self.buscador.setMinimumWidth(140)
        self.buscador.setMaximumWidth(240)
        self.buscador.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.buscador.textChanged.connect(self.cargar_tabla)

        self._btn_filtros = PillButton("Filtros", "secondary")
        self._btn_filtros.setCheckable(True)
        self._btn_filtros.setFixedWidth(100)
        self._btn_filtros.toggled.connect(self._alternar_panel_filtros)

        self._btn_filtrar = PillButton("Aplicar", "primary")
        self._btn_filtrar.setFixedWidth(92)
        self._btn_filtrar.setCursor(Qt.CursorShape.PointingHandCursor)
        self._btn_filtrar.clicked.connect(self.cargar_tabla)

        lbl_fecha = QLabel("Fecha")
        lbl_turno = QLabel("Turno")
        lbl_sup = QLabel("Supervisor")
        lbl_estado = QLabel("Estado")

        self._panel_filtros = QWidget()
        self._panel_filtros.setStyleSheet("background: transparent;")
        panel_filtros_layout = QHBoxLayout(self._panel_filtros)
        panel_filtros_layout.setContentsMargins(0, 4, 0, 0)
        panel_filtros_layout.setSpacing(8)
        panel_filtros_layout.addWidget(lbl_turno)
        panel_filtros_layout.addWidget(self.filtro_turno)
        panel_filtros_layout.addWidget(lbl_sup)
        panel_filtros_layout.addWidget(self.filtro_supervisor)
        panel_filtros_layout.addWidget(lbl_estado)
        panel_filtros_layout.addWidget(self.filtro_estado)
        panel_filtros_layout.addStretch()
        self._panel_filtros.setVisible(False)

        contenido = GlassCard(content_margins=10)
        contenido_layout = contenido.content_layout
        contenido_layout.setSpacing(8)
        contenido_layout.addLayout(fila)
        contenido_layout.addWidget(self._panel_filtros)
        scroll_filtros.setWidget(contenido)
        self._contenido_filtros = contenido

        fila.addWidget(lbl_fecha)
        fila.addWidget(self._boton_ant)
        fila.addWidget(self.selector_fecha)
        fila.addWidget(self._boton_sig)
        fila.addSpacing(4)
        fila.addWidget(self.buscador)
        fila.addWidget(self._btn_filtros)
        fila.addWidget(self._btn_filtrar)
        tokens = self._theme_manager.tokens()
        labels = (lbl_fecha, lbl_turno, lbl_sup, lbl_estado)
        self._estilizar_etiquetas_filtros(self._theme_manager.current(), labels)
        self._theme_manager.theme_changed.connect(
            lambda theme_name: self._estilizar_etiquetas_filtros(theme_name, labels)
        )
        return scroll_filtros

    def _estilizar_etiquetas_filtros(self, theme_name: str, labels: tuple[QLabel, ...]) -> None:
        tokens = self._theme_manager.tokens(theme_name)
        for label in labels:
            label.setStyleSheet(
                f"color: {tokens['text_secondary']}; font-size: {tokens['font_size_sm']}; "
                "font-weight: 500; background: transparent;"
            )

    def _alternar_panel_filtros(self, visible: bool) -> None:
        self._panel_filtros.setVisible(visible)
        self._btn_filtros.setText("Ocultar filtros" if visible else "Filtros")
        self._barra_filtros_widget.setFixedHeight(132 if visible else 78)
        self._contenido_filtros.adjustSize()
        self._barra_filtros_widget.updateGeometry()

    def _estilo_input(self, oscuro: bool) -> str:
        tokens = self._theme_manager.tokens()
        return f"""
            QComboBox, QLineEdit, QDateEdit {{
                background-color: {tokens['surface_alt']};
                color: {tokens['text_primary']};
                border: 1px solid {tokens['border']};
                border-radius: {tokens['radius_md']};
                padding: 4px 8px;
                font-size: {tokens['font_size_sm']};
                min-height: 28px;
                selection-background-color: {tokens['accent']};
                selection-color: {tokens['accent_text']};
            }}
            QComboBox:hover, QLineEdit:hover, QDateEdit:hover {{
                border-color: {tokens['accent']};
            }}
            QComboBox:focus, QLineEdit:focus, QDateEdit:focus {{
                border-color: {tokens['accent']};
                outline: none;
            }}
            QComboBox::drop-down {{
                border: none;
                width: 20px;
            }}
            QComboBox QAbstractItemView {{
                background-color: {tokens['surface']};
                color: {tokens['text_primary']};
                border: 1px solid {tokens['border']};
                selection-background-color: {tokens['accent']};
                selection-color: {tokens['accent_text']};
                outline: none;
            }}
        """

    def _construir_tabla(self, layout_derecho):
        oscuro = self._oscuro

        self.tabla = QTableWidget()
        self.tabla.setColumnCount(6)
        self.tabla.setHorizontalHeaderLabels([
            "Objetivo",
            "Equipo diurno", "Pasadas día",
            "Equipo nocturno", "Pasadas noche", "Estado"
        ])

        self.tabla.setColumnWidth(0, 210)
        self.tabla.setColumnWidth(1, 155)
        self.tabla.setColumnWidth(2, 95)
        self.tabla.setColumnWidth(3, 155)
        self.tabla.setColumnWidth(4, 95)
        self.tabla.setColumnWidth(5, 145)

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
        tokens = self._theme_manager.tokens()
        return f"""
            QTableWidget {{
                background-color: {tokens['surface']};
                gridline-color: transparent;
                border: none;
                outline: none;
                font-size: {tokens['font_size_sm']};
                color: {tokens['text_primary']};
                selection-background-color: transparent;
            }}
            QTableWidget::item {{
                padding: 6px 10px;
                border-bottom: 1px solid {tokens['border']};
                color: {tokens['text_primary']};
            }}
            QTableWidget::item:selected {{
                background-color: {tokens['surface_alt']};
                color: {tokens['text_primary']};
            }}
            QHeaderView::section {{
                background-color: {tokens['surface_alt']};
                color: {tokens['text_secondary']};
                border: none;
                border-bottom: 1px solid {tokens['border']};
                padding: 8px 10px;
                font-size: {tokens['font_size_sm']};
                font-weight: 600;
                letter-spacing: 0.5px;
            }}
            QScrollBar:vertical {{
                width: 6px;
                background: transparent;
            }}
            QScrollBar::handle:vertical {{
                background: {tokens['accent']};
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
                background: {tokens['accent']};
                border-radius: 3px;
            }}
        """

    # =========================================================================
    # TEMA — ALTERNAR Y REFRESCAR
    # =========================================================================

    def _alternar_tema(self) -> None:
        """
        Alterna entre tema claro y oscuro globalmente.
        
        Actualiza:
        - Tema general de la aplicación
        - Todos los componentes de la ventana
        - Estilos de botones, tabla, y paneles
        - Persistencia del tema elegido
        
        Raises:
            Loguea errores pero no los propaga para evitar crashes
        """
        try:
            # ✅ Validar que hay callback de tema
            if not self.alternar_tema_fn or not self.app:
                from PyQt6.QtWidgets import QMessageBox
                QMessageBox.warning(self, "Error", "Error al cambiar tema. Intenta nuevamente.")
                print("⚠️ Error: No hay callback de alternar_tema o app no disponible")
                return
            
            # ✅ Llamar al callback global de tema
            self.alternar_tema_fn(self.app, self)
            
            tema_actual = get_theme_manager().current()
            
            # ✅ Loguear cambio
            try:
                from services.logger import registrar_accion
                registrar_accion(
                    self.usuario_id,
                    f"Cambió tema a {tema_actual}"
                )
            except Exception:
                pass  # No interrumpir si logging falla
            
            print(f"✅ Tema cambiado a: {tema_actual}")
            
        except Exception as e:
            print(f"❌ Error al alternar tema: {e}")
            import traceback
            traceback.print_exc()
            # No lanzar excepción para que la app siga funcionando

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

    def _refrescar_tema(self) -> None:
        """Refresca todos los estilos de tema en la ventana."""
        try:
            oscuro = self._oscuro
            self._refrescar_tema_sidebar(oscuro)
            self._refrescar_tema_panel_derecho(oscuro)
            self.tabla.setStyleSheet(self._estilo_tabla(oscuro))
            self.cargar_tabla()
        except Exception as e:
            print(f"⚠️ Error refrescando tema: {e}")
            # No lanzar para que la app siga funcionando

    def _refrescar_tema_sidebar(self, oscuro: bool) -> None:
        """Reaplica estilos del sidebar y sus subcomponentes.
        
        Args:
            oscuro: Si usar tema oscuro.
        """
        self.setStyleSheet(f"QWidget#VentanaPrincipal {{ background-color: {obtener_color('bg_main', oscuro)}; }}")
        self.panel_lateral.setStyleSheet(f"""
            QFrame#PanelLateral {{
                background-color: {obtener_color('bg_sidebar', oscuro)};
                border-right: 1px solid {obtener_color('border', oscuro)};
            }}
        """)
        self._cabecera_sidebar.setStyleSheet(f"background-color: {obtener_color('bg_sidebar', oscuro)};")
        self._contenedor_scroll.setStyleSheet(f"background-color: {obtener_color('bg_sidebar', oscuro)};")
        self._zona_inferior.setStyleSheet(f"background-color: {obtener_color('bg_sidebar', oscuro)};")
        self.titulo_lateral.setStyleSheet(f"""
            color: {obtener_color('accent', oscuro)};
            font-size: 16px; font-weight: 800; letter-spacing: 2px;
        """)
        self.subtitulo_lateral.setStyleSheet(f"""
            color: {obtener_color('text_muted', oscuro)};
            font-size: 10px; letter-spacing: 1px;
        """)
        self.btn_colapsar.setStyleSheet(f"""
            QToolButton {{
                background: {obtener_color('btn_menu_hover', oscuro)};
                color: {obtener_color('text_secondary', oscuro)};
                border: none; border-radius: 5px;
                font-size: 14px; font-weight: bold;
            }}
            QToolButton:hover {{
                background: {obtener_color('accent', oscuro)};
                color: {obtener_color('accent_text', oscuro)};
            }}
        """)
        for b in self._botones_menu:
            b.actualizar_tema(oscuro)
        if hasattr(self, '_lbl_admin'):
            self._lbl_admin.setStyleSheet(f"""
                color: {obtener_color('text_muted', oscuro)};
                font-size: 9px; letter-spacing: 1.2px;
                font-weight: 600; padding: 4px 0 2px 4px;
            """)
        estilo_mini_btn = f"""
            QPushButton {{
                background-color: {obtener_color('btn_menu_hover', oscuro)};
                color: {obtener_color('text_secondary', oscuro)};
                border: 1px solid {obtener_color('border', oscuro)};
                border-radius: 5px; font-size: 11px;
                min-width: 30px; max-width: 36px; min-height: 26px;
            }}
            QPushButton:hover {{
                background-color: {obtener_color('accent', oscuro)};
                color: {obtener_color('accent_text', oscuro)};
                border-color: {obtener_color('accent', oscuro)};
            }}
        """
        self._btn_zoom_menos.setStyleSheet(estilo_mini_btn)
        self._btn_zoom_mas.setStyleSheet(estilo_mini_btn)
        self.lbl_zoom.setStyleSheet(f"color: {obtener_color('text_muted', oscuro)}; font-size: 10px;")
        texto_tema = "☀  Modo claro" if oscuro else "🌙  Modo oscuro"
        self.btn_tema.setText(texto_tema)
        self.btn_tema.setStyleSheet(self._estilo_btn_tema(oscuro))
        self.btn_configuracion.setStyleSheet(self._estilo_btn_tema(oscuro))
        self.btn_configurar_menu.setStyleSheet(self._estilo_btn_tema(oscuro))
        self.btn_logout.setStyleSheet(self._estilo_btn_logout(oscuro))
        self.usuario_label.setStyleSheet(f"""
            color: {obtener_color('text_muted', oscuro)};
            font-size: 10px; padding: 3px 4px; border-radius: 5px;
            background: {obtener_color('btn_menu_hover', oscuro)};
        """)

    def _refrescar_tema_panel_derecho(self, oscuro: bool) -> None:
        """Reaplica estilos del panel derecho (header, filtros, tabla).
        
        Args:
            oscuro: Si usar tema oscuro.
        """
        tokens = self._theme_manager.tokens()
        self._panel_derecho.setStyleSheet(f"""
            QWidget#panelControlObjetivos {{
                background: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 1,
                    stop: 0 {tokens['bg_gradient_start']},
                    stop: 1 {tokens['bg_gradient_end']});
            }}
        """)
        self._lbl_titulo_header.setStyleSheet(f"""
            color: {tokens['text_primary']};
            font-size: {tokens['font_size_title']}; font-weight: 700; letter-spacing: 0.3px;
        """)
        self._lbl_subtitulo_header.setStyleSheet(
            f"color: {tokens['text_secondary']}; font-size: {tokens['font_size_sm']};"
        )
        self._barra_filtros_widget.setStyleSheet(f"""
            QScrollArea {{ border: none; background: transparent; }}
            QScrollBar:horizontal {{ height: 3px; background: transparent; }}
            QScrollBar::handle:horizontal {{
                background: {tokens['accent']}; border-radius: 1px;
            }}
        """)
        estilo_input = self._estilo_input(oscuro)
        for w in (self.selector_fecha, self.filtro_turno,
                self.filtro_supervisor, self.filtro_estado):
            w.setStyleSheet(estilo_input)
        estilo_btn_nav = f"""
            QPushButton {{
                background-color: {tokens['surface_alt']};
                color: {tokens['text_secondary']};
                border: 1px solid {tokens['border']};
                border-radius: {tokens['radius_md']}; font-size: {tokens['font_size_md']};
                min-width: 28px; max-width: 28px; min-height: 28px;
            }}
            QPushButton:hover {{
                background-color: {tokens['accent']};
                color: {tokens['accent_text']}; border-color: {tokens['accent']};
            }}
        """
        self._boton_ant.setStyleSheet(estilo_btn_nav)
        self._boton_sig.setStyleSheet(estilo_btn_nav)
        self._sep_header.setStyleSheet(f"""
            QFrame {{ background: {tokens['border']}; max-height: 1px; border: none; margin: 0; }}
        """)

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
        if self.zoom_nivel < self._theme_manager.MAX_FONT_SIZE:
            self._theme_manager.set_font_size(self.zoom_nivel + 1)

    def _zoom_menos(self):
        if self.zoom_nivel > self._theme_manager.MIN_FONT_SIZE:
            self._theme_manager.set_font_size(self.zoom_nivel - 1)

    def _aplicar_zoom(self):
        self._theme_manager.set_font_size(self.zoom_nivel)

    def _sincronizar_tamano_fuente(self, size: int) -> None:
        self.zoom_nivel = size
        if hasattr(self, "lbl_zoom"):
            self.lbl_zoom.setText(f"{size}px")

    # =========================================================================
    # SINCRONIZACIÓN
    # =========================================================================

    def _configurar_sincronizacion(self):
        self.sincronizador = obtener_sincronizador()
        self.sincronizador.datos_cambiados.connect(self._on_datos_cambiados)
        self.sincronizador.tabla_actualizar.connect(self._on_tabla_actualizar)

    def _on_datos_cambiados(self, tabla, operacion, datos):
        if tabla in ['objetivos', 'supervisores', 'pasadas', 'equipos']:
            self.cargar_tabla()

    def _on_tabla_actualizar(self, nombre_tabla):
        if nombre_tabla == 'principal':
            self.cargar_tabla()

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
            ("Ctrl+F",     self._enfocar_buscador_activo),
            ("Ctrl+H",     self.abrir_ayuda),
            ("Ctrl+=",     self._zoom_mas),
            ("Ctrl+-",     self._zoom_menos),
            ("Ctrl+Left",  self._fecha_anterior),
            ("Ctrl+Right", self._fecha_siguiente),
            ("Ctrl+\\",    self._toggle_sidebar),
        ]
        for seq, fn in mapa:
            QShortcut(QKeySequence(seq), self).activated.connect(fn)

    def _enfocar_buscador_activo(self) -> None:
        ventana_activa = self.app.activeWindow() if self.app else self
        buscador = ventana_activa.findChild(QLineEdit) if ventana_activa else None
        (buscador or self.buscador).setFocus()

    def _configurar_timers(self):
        self.timer_inactividad = QTimer()
        self.timer_inactividad.setInterval(int(TIEMPO_INACTIVIDAD_MAXIMA * 1000))
        self.timer_inactividad.timeout.connect(self.cerrar_por_inactividad)
        self.timer_inactividad.start()

        self.timer_refresco = QTimer()
        self.timer_refresco.setInterval(30 * 1000)
        self.timer_refresco.timeout.connect(self.cargar_tabla)
        self.timer_refresco.start()

    def _configurar_event_filter(self):
        if self.app:
            self.app.installEventFilter(self)

    def _registrar_actividad(self):
        try:
            if hasattr(self, "timer_inactividad"):
                self.timer_inactividad.start()
            actualizar_actividad_sesion()
        except Exception:
            pass

    def eventFilter(self, objeto, evento):
        if evento.type() in (
            QEvent.Type.MouseMove,
            QEvent.Type.KeyPress,
            QEvent.Type.MouseButtonPress,
            QEvent.Type.Wheel
        ):
            self._registrar_actividad()
        return super().eventFilter(objeto, evento)

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
                self._registrar_actividad()
            return super().event(evento)
        except Exception as e:
            print(f"Error en event: {e}")
            return super().event(evento)

    def moveEvent(self, evento):
        try:
            self._registrar_actividad()
        except Exception:
            pass
        super().moveEvent(evento)

    def resizeEvent(self, evento):
        try:
            self._registrar_actividad()
        except Exception:
            pass
        super().resizeEvent(evento)

    def cerrar_por_inactividad(self):
        hacer_backup()
        cerrar_sesion()
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
            for col in (2, 4, 5):
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
            FROM pasadas WHERE (fecha_operativa = ? OR fecha = ?)
        """
        params = [fecha, fecha]
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
            if turno in ("D", "diurno"):
                pasadas_dia[obj_id] = pasadas_dia.get(obj_id, 0) + count
            elif turno in ("N", "nocturno"):
                pasadas_noche[obj_id] = pasadas_noche.get(obj_id, 0) + count
        return pasadas_dia, pasadas_noche

    def _obtener_estado_detallado(self, pasadas_dia: int, pasadas_noche: int) -> tuple:
        tokens = self._theme_manager.tokens()
        if pasadas_dia > 0 and pasadas_noche > 0:
            return "Pasaron los dos", tokens["success"]
        if pasadas_dia > 0 and pasadas_noche == 0:
            return "No pasó noche", tokens["warning"]
        if pasadas_dia == 0 and pasadas_noche > 0:
            return "No pasó día", tokens["warning"]
        return "No pasó nadie", tokens["danger"]

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

    def cargar_tabla(self) -> None:
        fecha         = self.selector_fecha.date().toString("yyyy-MM-dd")
        turno         = self.filtro_turno.currentText()
        turno         = None if turno == "Todos los turnos" else turno
        supervisor_id = self.filtro_supervisor.currentData()
        filtro_estado = self.filtro_estado.currentText()
        texto_busq    = self.buscador.text().strip().lower()

        objetivos = sorted(obtener_objetivos_del_dia(fecha), key=lambda o: o[1].lower())
        equipo_dia_importado = obtener_supervisores_de_pasadas(fecha, "diurno")
        equipo_noche_importado = obtener_supervisores_de_pasadas(fecha, "nocturno")
        equipo_dia_manual = obtener_equipo(fecha, "diurno")
        equipo_noche_manual = obtener_equipo(fecha, "nocturno")
        equipo_dia = equipo_dia_manual if equipo_dia_manual != "—" else equipo_dia_importado
        equipo_noche = equipo_noche_manual if equipo_noche_manual != "—" else equipo_noche_importado

        pasadas_dia_tot, pasadas_noche_tot = self._obtener_todas_pasadas_por_turno(fecha)
        self._actualizar_metricas(objetivos, pasadas_dia_tot, pasadas_noche_tot)
        pasadas_dia_fil, pasadas_noche_fil = self._aplicar_filtro_pasadas(
            fecha, turno, supervisor_id, pasadas_dia_tot, pasadas_noche_tot
        )

        filas = self._filtrar_filas(
            objetivos, texto_busq, filtro_estado,
            pasadas_dia_fil, pasadas_noche_fil,
            pasadas_dia_tot, pasadas_noche_tot
        )

        sorting_enabled = self.tabla.isSortingEnabled()
        self.tabla.setSortingEnabled(False)
        self.tabla.setUpdatesEnabled(False)
        self._limpiar_tabla()
        self.tabla.setRowCount(len(filas))
        
        for i, fila in enumerate(filas):
            self._poblar_fila(i, fila, equipo_dia, equipo_noche)

        self.tabla.setUpdatesEnabled(True)
        self.tabla.setSortingEnabled(sorting_enabled)
        self.tabla.update()
        
    def _aplicar_filtro_pasadas(
        self,
        fecha: str,
        turno: Optional[str],
        supervisor_id: Optional[int],
        pasadas_dia_tot: dict,
        pasadas_noche_tot: dict
    ) -> tuple:
        """Calcula pasadas filtradas por turno y supervisor.
        
        Args:
            fecha: Fecha en formato yyyy-MM-dd.
            turno: 'diurno', 'nocturno' o None para todos.
            supervisor_id: ID del supervisor o None para todos.
            pasadas_dia_tot: Totales de pasadas diurnas sin filtrar.
            pasadas_noche_tot: Totales de pasadas nocturnas sin filtrar.
        
        Returns:
            Tupla (pasadas_dia_filtradas, pasadas_noche_filtradas).
        """
        if turno == "diurno":
            dia = (
                self._obtener_todas_pasadas_por_turno(fecha, supervisor_id)[0]
                if supervisor_id else pasadas_dia_tot
            )
            return dia, pasadas_noche_tot
        if turno == "nocturno":
            noche = (
                self._obtener_todas_pasadas_por_turno(fecha, supervisor_id)[1]
                if supervisor_id else pasadas_noche_tot
            )
            return pasadas_dia_tot, noche
        return pasadas_dia_tot, pasadas_noche_tot

    def _filtrar_filas(
        self,
        objetivos: list,
        texto_busq: str,
        filtro_estado: str,
        pasadas_dia_fil: dict,
        pasadas_noche_fil: dict,
        pasadas_dia_tot: dict,
        pasadas_noche_tot: dict
    ) -> list:
        """Aplica filtros de texto y estado a la lista de objetivos.
        
        Args:
            objetivos: Lista de tuplas (id, nombre, ...) de objetivos.
            texto_busq: Texto de búsqueda en minúsculas.
            filtro_estado: Estado a filtrar o 'Todos'.
            pasadas_dia_fil: Pasadas diurnas filtradas por supervisor.
            pasadas_noche_fil: Pasadas nocturnas filtradas por supervisor.
            pasadas_dia_tot: Totales diurnos (para calcular estado real).
            pasadas_noche_tot: Totales nocturnos (para calcular estado real).
        
        Returns:
            Lista de tuplas (objetivo, pd, pn, estado) listas para renderizar.
        """
        filas = []
        for o in objetivos:
            if texto_busq and texto_busq not in o[1].lower():
                continue
            pd = pasadas_dia_fil.get(o[0], 0)
            pn = pasadas_noche_fil.get(o[0], 0)
            estado, _ = self._obtener_estado_detallado(
                pasadas_dia_tot.get(o[0], 0),
                pasadas_noche_tot.get(o[0], 0)
            )
            if filtro_estado != "Todos" and estado != filtro_estado:
                continue
            filas.append((o, pd, pn, estado))
        return filas

    def _poblar_fila(
        self,
        i: int,
        fila: tuple,
        equipo_dia: str,
        equipo_noche: str
    ) -> None:
        """Rellena una fila de la tabla con datos de un objetivo.
        
        Args:
            i: Índice de la fila (0-based).
            fila: Tupla (objetivo, pasadas_dia, pasadas_noche, estado).
            equipo_dia: Nombre del equipo diurno.
            equipo_noche: Nombre del equipo nocturno.
        """
        o, pd, pn, estado = fila
        tokens = self._theme_manager.tokens()
        bg = tokens["surface"] if i % 2 == 0 else tokens["surface_alt"]

        def item(txt: str, color_key: str = "text_primary") -> QTableWidgetItem:
            it = self._crear_item(txt)
            it.setForeground(QColor(tokens[color_key]))
            it.setBackground(QColor(bg))
            return it

        def celda(widget: QWidget) -> QWidget:
            c = self._crear_widget_celda(widget)
            c.setStyleSheet(f"background-color: {bg};")
            return c

        self.tabla.setItem(i, 0, item(o[1]))
        self.tabla.setItem(i, 1, item(equipo_dia, "text_secondary"))
        self.tabla.setCellWidget(i, 2, celda(CountChip(pd)))
        self.tabla.setItem(i, 3, item(equipo_noche, "text_secondary"))
        self.tabla.setCellWidget(i, 4, celda(CountChip(pn)))
        estado_status = {
            "Pasaron los dos": "ok",
            "No pasó día": "warning",
            "No pasó noche": "warning",
            "No pasó nadie": "danger",
        }.get(estado, "info")
        self.tabla.setCellWidget(
            i, 5, celda(StatusBadge(estado, estado_status))
        )

    # =========================================================================
    # ABRIR VENTANAS
    # =========================================================================

    def _abrir_ventana(
        self,
        attr: str,
        cls,
        *args,
        on_close: Optional[Callable] = None,
        **kwargs
    ) -> QWidget:
        """
        Abre o trae al frente una ventana secundaria.

        Si la ventana ya existe y está visible, la trae al frente.
        Si no existe o fue cerrada, la crea nuevamente.

        Args:
            attr: Nombre del atributo donde se guarda la instancia.
            cls: Clase de la ventana a abrir.
            *args: Argumentos posicionales del constructor.
            on_close: Función opcional al cerrar.
            **kwargs: Argumentos nombrados del constructor.

        Returns:
            Instancia de la ventana abierta.
        """
        ventana = getattr(self, attr, None)

        if ventana is None or not ventana.isVisible():
            ventana = cls(*args, **kwargs)
            setattr(self, attr, ventana)

            QShortcut(QKeySequence("Esc"), ventana).activated.connect(ventana.close)

            if on_close:
                ventana.destroyed.connect(on_close)

            ventana.show()
            if ventana.graphicsEffect() is None:
                animar_aparecer(ventana, 180)
        else:
            ventana.raise_()
            ventana.activateWindow()

        return ventana


    def abrir_form_objetivo(self) -> None:
        self._abrir_ventana(
            'form_objetivo',
            FormObjetivo,
            on_close=self.cargar_tabla
        )


    def abrir_form_supervisor(self) -> None:
        self._abrir_ventana('form_supervisor', FormSupervisor)


    def abrir_form_pasada(self) -> None:
        self._abrir_ventana(
            'form_pasada',
            FormPasada,
            fecha_inicial=self.selector_fecha.date().toString("yyyy-MM-dd"),
            on_close=self.cargar_tabla
        )


    def abrir_form_turno(self) -> None:
        self._abrir_ventana(
            'form_turno',
            FormTurno,
            on_close=self.cargar_tabla
        )


    def abrir_lista_objetivos(self) -> None:
        self._abrir_ventana('lista_objetivos', ListaObjetivos)


    def abrir_lista_supervisores(self) -> None:
        self._abrir_ventana('lista_supervisores', ListaSupervisores)


    def abrir_lista_pasadas(self) -> None:
        self._abrir_ventana(
            'lista_pasadas',
            ListaPasadas,
            on_close=self.cargar_tabla
        )


    def abrir_notas(self) -> None:
        self._abrir_ventana('notas', NotasDiarias)


    def abrir_feriados(self) -> None:
        self._abrir_ventana('feriados', VistaFeriados)


    def abrir_reporte_mensual(self) -> None:
        self._abrir_ventana('reporte_mensual', ReporteMensual)


    def abrir_reporte_mensual_objetivo(self) -> None:
        self._abrir_ventana(
            'reporte_mensual_objetivo',
            ReporteObjetivo
        )


    def abrir_gestionar_usuarios(self) -> None:
        self._abrir_ventana(
            'gestionar_usuarios',
            GestionarUsuarios
        )

    def abrir_logs(self) -> None:
        self._abrir_ventana('logs', VistaLogs)

    def abrir_indexacion(self) -> None:
        ventana = self._abrir_ventana(
            'indexacion',
            VistaIndexacion,
            self.usuario_id
        )
        ventana.setWindowTitle("Optimización de Índices y Rendimiento")
        ventana.setGeometry(100, 100, 1200, 700)


    def abrir_validaciones(self) -> None:
        ventana = self._abrir_ventana(
            'validaciones',
            VistaValidaciones,
            self.usuario_id
        )
        ventana.setWindowTitle("Validaciones e Integridad de BD")
        ventana.setGeometry(100, 100, 1000, 600)


    def abrir_ayuda(self) -> None:
        self._abrir_ventana('ayuda', Ayuda)


    def abrir_transferir_datos(self) -> None:
        self._abrir_ventana(
            'transferir_datos',
            TransferirDatos
        )


    def abrir_sincronizacion(self) -> None:
        ventana = self._abrir_ventana(
            'sincronizacion',
            VistaSincronizacion,
            self.usuario_id
        )
        ventana.setWindowTitle("Monitoreo de Sincronización de Datos")
        ventana.setGeometry(100, 100, 1200, 700)


    def abrir_importar_excel(self) -> None:
        self._abrir_ventana(
            'importar_excel',
            ImportarExcel,
            on_close=self.cargar_tabla,
        )

    def abrir_auditoria(self) -> None:
        self._abrir_ventana('auditoria', VistaAuditoria)