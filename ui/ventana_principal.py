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
    , QDialog, QDialogButtonBox, QCheckBox, QGridLayout, QMenu
)
from PyQt6.QtCore import QDate, QTimer, QEvent, Qt, pyqtSignal
from PyQt6.QtGui import QColor, QIcon, QShortcut, QKeySequence
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
from ui.animaciones import animar_aparecer, tiene_animacion_activa
from ui.theme.theme_manager import get_theme_manager
from ui.theme.stylesheet import generate_date_edit_dropdown_stylesheet
from ui.theme.tokens import THEMES
from ui.theme.colors import parse_color
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
    ModuleCard,
    PillButton,
    SearchInput,
    StatusBadge,
    ThemeLogo,
)
from ui.components.base import rgba
from ui.components.calendar import configure_calendar_theme
from ui.widgets.estilos import obtener_color

# =============================================================================
# UTILIDADES
# =============================================================================

def obtener_nombre_usuario(usuario_id: int) -> str:
    """Obtiene el nombre de usuario por ID."""
    return get_username_by_id(usuario_id) or "Usuario"


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
        tokens = self._theme_manager.tokens()
        bg_activo = tokens["surface_alt"]
        text_activo = tokens["text_primary"]
        border_activo = rgba(tokens["accent"], 112)
        bg_hover    = obtener_color("btn_menu_hover", self._oscuro)
        text_normal = obtener_color("btn_menu_text", self._oscuro)
        alignment = "left" if self._expandido else "center"
        padding = "0px 10px" if self._expandido else "0px"

        if self._activo:
            self.setStyleSheet(f"""
                QPushButton {{
                    background-color: {bg_activo};
                    color: {text_activo};
                    border: 1px solid {border_activo};
                    border-radius: {tokens['radius_lg']};
                    padding: {padding};
                    text-align: {alignment};
                    font-size: 12px;
                    font-weight: 600;
                }}
            """)
        else:
            self.setStyleSheet(f"""
                QPushButton {{
                    background-color: transparent;
                    color: {text_normal};
                    border: 1px solid transparent;
                    border-radius: {tokens['radius_lg']};
                    padding: {padding};
                    text-align: {alignment};
                    font-size: 12px;
                }}
                QPushButton:hover {{
                    background-color: {bg_hover};
                    color: {tokens['text_primary']};
                    border-color: {tokens['border']};
                }}
                QPushButton:pressed {{
                    background-color: {tokens['surface_alt']};
                    color: {tokens['text_primary']};
                    border-color: {border_activo};
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
        self._aplicar_estilo()

    def expandir(self):
        self._expandido = True
        self.setText(self._texto_completo)
        self._aplicar_estilo()


class LandingScrollArea(QScrollArea):
    resized = pyqtSignal()

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        self.resized.emit()


# =============================================================================
# VENTANA PRINCIPAL
# =============================================================================

class VentanaPrincipal(QWidget):

    SIDEBAR_EXPANDIDO = 248
    SIDEBAR_COLAPSADO = 68

    def __init__(self, usuario_id=None, rol=None, on_login_exitoso=None, app=None):
        self.usuario_id       = usuario_id
        self.rol              = rol
        self.on_login_exitoso = on_login_exitoso
        self.app              = app
        self.zoom_nivel       = 13
        self._sidebar_expandido = True
        self._metricas_colapsadas = False
        self._boton_activo      = None
        self._menu_visible = obtener_menu_usuario(usuario_id)

        super().__init__()
        self.setWindowTitle("VESP Organizations")
        self.setWindowFlags(Qt.WindowType.Window)
        self.move(80, 60)
        self.resize(1340, 660)
        self.setMinimumSize(720, 440)
        self._theme_manager = get_theme_manager()
        self.zoom_nivel = self._theme_manager.font_size()
        self.setWindowIcon(QIcon(THEMES[self._theme_manager.current()]["logo_path"]))
        self.setObjectName("VentanaPrincipal")

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

    def _al_cambiar_tema(self, nombre_tema: str) -> None:
        self._oscuro = nombre_tema != "Claro"
        self._actualizar_logo_tema(nombre_tema)
        self._refrescar_tema()

    # =========================================================================
    # CONSTRUCCIÓN UI
    # =========================================================================

    def _construir_ui(self):
        layout_raiz = QHBoxLayout(self)
        layout_raiz.setSpacing(12)
        layout_raiz.setContentsMargins(14, 14, 14, 14)

        self._construir_sidebar(layout_raiz)
        self._construir_panel_derecho(layout_raiz)

        self._aplicar_fondo_ventana()
        self._refrescar_tema_sidebar(self._oscuro)

    def _aplicar_fondo_ventana(self) -> None:
        tokens = self._theme_manager.tokens()
        self.setStyleSheet(f"""
            QWidget#VentanaPrincipal {{
                background: qlineargradient(
                    x1: 0, y1: 0, x2: 1, y2: 1,
                    stop: 0 {tokens['bg_gradient_start']},
                    stop: 1 {tokens['bg_gradient_end']}
                );
            }}
        """)

    # -------------------------------------------------------------------------
    # SIDEBAR
    # -------------------------------------------------------------------------

    def _construir_sidebar(self, layout_raiz):
        oscuro = self._oscuro

        self.panel_lateral = GlassCard(
            shadow=True,
            content_margins=0,
            background_alpha=220,
        )
        self.panel_lateral.setFixedWidth(self.SIDEBAR_EXPANDIDO)

        layout_lateral = self.panel_lateral.content_layout
        layout_lateral.setSpacing(0)

        cabecera = self._construir_cabecera_sidebar()
        layout_lateral.addWidget(cabecera)

        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll_area.setStyleSheet(f"""
            QScrollArea, QScrollArea QWidget#qt_scrollarea_viewport {{
                border: none;
                background: transparent;
            }}
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
        self._contenedor_scroll.setStyleSheet("background: transparent;")
        self.layout_scroll = QVBoxLayout(self._contenedor_scroll)
        self.layout_scroll.setSpacing(2)
        self.layout_scroll.setContentsMargins(12, 6, 12, 10)

        self._botones_menu = []
        self._secciones_sidebar = []
        self._construir_botones_menu()

        self.layout_scroll.addStretch(1)
        scroll_area.setWidget(self._contenedor_scroll)
        layout_lateral.addWidget(scroll_area, 1)

        self._zona_inferior = self._construir_zona_inferior()
        layout_lateral.addWidget(self._zona_inferior)

        layout_raiz.addWidget(self.panel_lateral)

    def _construir_cabecera_sidebar(self) -> QWidget:
        oscuro = self._oscuro
        self._cabecera_sidebar = QWidget()
        self._cabecera_sidebar.setFixedHeight(72)
        self._cabecera_sidebar.setStyleSheet("background: transparent;")

        lay = QHBoxLayout(self._cabecera_sidebar)
        lay.setContentsMargins(6, 12, 6, 8)
        lay.setSpacing(0)

        self.btn_colapsar = QToolButton()
        self.btn_colapsar.setText("‹")
        self.btn_colapsar.setFixedSize(28, 28)
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

        self.logo_label = ThemeLogo(size=44)
        lay.addWidget(self.logo_label)
        lay.addStretch(1)
        lay.addWidget(self.btn_colapsar)

        return self._cabecera_sidebar

    def _construir_botones_menu(self):
        oscuro = self._oscuro

        def add_section(title):
            label = QLabel(title)
            label.setObjectName("SidebarSectionTitle")
            label.setStyleSheet(
                f"color: {obtener_color('text_muted', oscuro)};"
                " font-size: 9px; font-weight: 700; letter-spacing: 1px;"
                " padding: 10px 8px 4px; background: transparent;"
            )
            self._secciones_sidebar.append(label)
            self.layout_scroll.addWidget(label)

        def add_btn(icono, texto, accion, tooltip_extra="", clave=None):
            b = BotonMenu(icono, texto, oscuro)
            b.setProperty("menu_key", clave or "")
            b.setToolTip(f"{texto}  {tooltip_extra}".strip())
            b.clicked.connect(lambda: self._activar_boton(b, accion))
            self._botones_menu.append(b)
            self.layout_scroll.addWidget(b)
            if clave and not self._menu_visible.get(clave, True):
                b.hide()
            return b

        add_section("OPERACIÓN")
        self._btn_control   = add_btn("📋", "Control diario",     self._mostrar_dashboard,   "(Ctrl+B)", "control_diario")
        self._btn_pasada    = add_btn("✅", "Registrar pasada",   self.abrir_form_pasada,    "(Ctrl+P)", "registrar_pasada")
        self._btn_turno     = add_btn("🕐", "Registrar turno",    self.abrir_form_turno,     "(Ctrl+T)", "registrar_turno")

        add_section("GESTIÓN")
        self._btn_add_obj = add_btn("➕", "Agregar objetivo",    self.abrir_form_objetivo,  "(Ctrl+O)", "agregar_objetivo")
        add_btn("📍", "Ver objetivos",       self.abrir_lista_objetivos, clave="ver_objetivos")
        self._btn_add_sup = add_btn("👤", "Agregar supervisor",  self.abrir_form_supervisor, "(Ctrl+S)", "agregar_supervisor")
        add_btn("👥", "Ver supervisores",    self.abrir_lista_supervisores, clave="ver_supervisores")

        add_section("CONSULTAS")
        add_btn("🔍", "Ver pasadas",         self.abrir_lista_pasadas, clave="ver_pasadas")
        add_btn("🏖️", "Feriados",            self.abrir_feriados, clave="feriados")
        add_btn("📝", "Notas del día",       self.abrir_notas,              "(Ctrl+N)", "notas")
        add_btn("📅", "Reporte mensual",     self.abrir_reporte_mensual,    "(Ctrl+R)", "reporte_mensual")
        add_btn("📅", "Reporte objetivo",    self.abrir_reporte_mensual_objetivo, "(Ctrl+Ñ)", "reporte_objetivo")
        add_btn("💾", "Transferir datos",    self.abrir_transferir_datos, clave="transferir_datos")
        add_btn("📥", "Importar Excel",      self.abrir_importar_excel, clave="importar_excel")
        add_btn("❓", "Ayuda",               self.abrir_ayuda,              "(Ctrl+H)", "ayuda")

        if tiene_permiso('usuarios.ver'):
            add_section("ADMINISTRACIÓN")
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
        zona.setObjectName("SidebarFooter")
        zona.setStyleSheet("background: transparent;")
        lay = QVBoxLayout(zona)
        lay.setContentsMargins(12, 8, 12, 12)
        lay.setSpacing(6)

        nombre_usuario = obtener_nombre_usuario(self.usuario_id)
        nombre_rol = {
            "admin": "Administrador",
            "supervisor": "Supervisor",
            "auditor": "Auditor",
            "gerente": "Gerente",
            "operador": "Operador",
        }.get(str(self.rol or "").casefold(), "Usuario")
        partes_nombre = nombre_usuario.split()
        iniciales = (
            "".join(parte[0] for parte in partes_nombre[:2]).upper()
            if len(partes_nombre) > 1
            else nombre_usuario[:2].upper()
        )
        self.usuario_chip = QFrame()
        self.usuario_chip.setObjectName("SidebarUserChip")
        fila_usuario = QHBoxLayout(self.usuario_chip)
        fila_usuario.setContentsMargins(8, 8, 8, 8)
        fila_usuario.setSpacing(8)

        self.usuario_avatar = QLabel(iniciales)
        self.usuario_avatar.setObjectName("SidebarUserAvatar")
        self.usuario_avatar.setFixedSize(34, 34)
        self.usuario_avatar.setAlignment(Qt.AlignmentFlag.AlignCenter)
        fila_usuario.addWidget(self.usuario_avatar)

        datos_usuario = QVBoxLayout()
        datos_usuario.setSpacing(1)
        self.usuario_nombre = QLabel(nombre_usuario)
        self.usuario_nombre.setObjectName("SidebarUserName")
        self.usuario_nombre.setToolTip(nombre_usuario)
        self.usuario_rol = QLabel(nombre_rol)
        self.usuario_rol.setObjectName("SidebarUserRole")
        datos_usuario.addWidget(self.usuario_nombre)
        datos_usuario.addWidget(self.usuario_rol)
        fila_usuario.addLayout(datos_usuario, 1)
        lay.addWidget(self.usuario_chip)

        self.btn_configuracion = QPushButton("⚙  Configuración")
        self.btn_configuracion.setObjectName("SidebarUtility")
        self.btn_configuracion.setToolTip("Configuración")
        self.btn_configuracion.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_configuracion.setFixedHeight(38)
        self.btn_configuracion.clicked.connect(self._abrir_configuracion)
        lay.addWidget(self.btn_configuracion)

        self.btn_logout = QPushButton("🚪  Cerrar sesión")
        self.btn_logout.setObjectName("SidebarLogout")
        self.btn_logout.setToolTip("Cerrar sesión")
        self.btn_logout.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_logout.setFixedHeight(38)
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
        self._refrescar_tarjetas_landing()

    # -------------------------------------------------------------------------
    # PANEL DERECHO
    # -------------------------------------------------------------------------

    def _construir_panel_derecho(self, layout_raiz):
        oscuro = self._oscuro

        self._panel_derecho = QWidget()
        self._panel_derecho.setObjectName("panelControlObjetivos")
        self._panel_derecho.setStyleSheet(f"""
            QWidget#panelControlObjetivos {{
                background: transparent;
            }}
        """)
        layout_derecho = QVBoxLayout(self._panel_derecho)
        layout_derecho.setContentsMargins(20, 12, 20, 14)
        layout_derecho.setSpacing(10)

        self._header = self._construir_header()
        layout_derecho.addWidget(self._header)

        self._metricas = self._construir_metricas()
        layout_derecho.addWidget(self._metricas)

        self._landing = self._construir_landing()
        layout_derecho.insertWidget(2, self._landing, 1)
        self._refrescar_tarjetas_landing()
        self._landing.resized.connect(self._refrescar_tarjetas_landing)

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

        layout_raiz.addWidget(self._panel_derecho, 1)

    def _construir_landing(self) -> LandingScrollArea:
        landing = LandingScrollArea()
        landing.setObjectName("LandingScrollArea")
        landing.setWidgetResizable(True)
        landing.setFrameShape(QFrame.Shape.NoFrame)
        landing.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        landing.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)

        contenido = QWidget()
        contenido.setStyleSheet("background: transparent;")
        layout = QVBoxLayout(contenido)
        layout.setContentsMargins(28, 28, 28, 28)
        layout.setSpacing(18)

        titulo = QLabel("Módulos")
        titulo.setObjectName("LandingTitle")
        subtitulo = QLabel("Accesos rápidos a las herramientas de trabajo")
        subtitulo.setObjectName("LandingSubtitle")
        layout.addWidget(titulo)
        layout.addWidget(subtitulo)

        acciones = [
            (
                "control_diario", "📋", "Control diario",
                "Revisá la cobertura del día", self._mostrar_dashboard,
            ),
            (
                "registrar_pasada", "✅", "Registrar pasada",
                "Cargá una nueva pasada", self.abrir_form_pasada,
            ),
            (
                "ver_pasadas", "🔍", "Ver pasadas",
                "Consultá el historial de pasadas", self.abrir_lista_pasadas,
            ),
            (
                "reporte_mensual", "📅", "Reporte mensual",
                "Resumen mensual de actividad", self.abrir_reporte_mensual,
            ),
            (
                "reporte_objetivo", "🎯", "Reporte objetivo",
                "Seguimiento por objetivo", self.abrir_reporte_mensual_objetivo,
            ),
            ("notas", "📝", "Notas del día", "Novedades y observaciones", self.abrir_notas),
            (
                "agregar_objetivo", "➕", "Agregar objetivo",
                "Creá un nuevo objetivo", self.abrir_form_objetivo,
            ),
            (
                "feriados", "🏖", "Feriados",
                "Administrá días no laborables", self.abrir_feriados,
            ),
        ]
        self._landing_grid = QGridLayout()
        self._landing_grid.setHorizontalSpacing(14)
        self._landing_grid.setVerticalSpacing(14)
        self._landing_cards = []
        for clave, icono, texto, descripcion, accion in acciones:
            tarjeta = ModuleCard(clave, icono, texto, descripcion, parent=contenido)
            tarjeta.clicked.connect(accion)
            self._landing_cards.append(tarjeta)
        layout.addLayout(self._landing_grid)
        layout.addStretch()
        landing.setWidget(contenido)
        return landing

    def _refrescar_tarjetas_landing(self) -> None:
        columnas = max(1, min(3, self._landing.viewport().width() // 300))
        for columna in range(3):
            self._landing_grid.setColumnStretch(columna, 1 if columna < columnas else 0)
        for tarjeta in self._landing_cards:
            self._landing_grid.removeWidget(tarjeta)
        indice = 0
        for tarjeta in self._landing_cards:
            visible = self._menu_visible.get(tarjeta.property("menu_key"), True)
            tarjeta.setVisible(visible)
            if visible:
                self._landing_grid.addWidget(
                    tarjeta, indice // columnas, indice % columnas
                )
                indice += 1

    def _mostrar_dashboard(self) -> None:
        self._landing.hide()
        self._metricas.setVisible(not self._metricas_colapsadas)
        self._btn_toggle_metricas.show()
        self._barra_filtros_widget.show()
        self._sep_header.show()
        self._tabla_card.show()
        self.tabla.show()
        self.cargar_tabla()
        self._panel_derecho.update()
        self.tabla.viewport().update()

    def _mostrar_landing_inicial(self) -> None:
        self._metricas.hide()
        self._btn_toggle_metricas.hide()
        self._barra_filtros_widget.hide()
        self._sep_header.hide()
        self._tabla_card.hide()
        self.tabla.hide()
        self._landing.show()
        self._landing.update()

    def _construir_metricas(self) -> QWidget:
        contenedor = GlassCard(shadow=False, content_margins=8)
        layout = QHBoxLayout()
        layout.setSpacing(8)
        self._metricas_valores = {}

        for clave, titulo, valor, icono in (
            ("objetivos", "Objetivos activos", "0", "◎"),
            ("pasadas", "Pasadas del día", "0", "✓"),
            ("alertas", "Alertas pendientes", "0", "!"),
        ):
            card_type = KpiCard
            metric = card_type(
                titulo,
                valor,
                icono,
                shadow=False,
                contrast=False,
                compact=True,
            )
            metric.setMinimumWidth(0)
            layout.addWidget(metric, 1)
            self._metricas_valores[clave] = metric
        contenedor.add_layout(layout)
        return contenedor

    def _alternar_metricas(self) -> None:
        self._metricas_colapsadas = not self._metricas_colapsadas
        visible = not self._metricas_colapsadas
        self._metricas.setVisible(visible)
        self._btn_toggle_metricas.setText("⌃" if visible else "⌄")
        accion = "Ocultar" if visible else "Mostrar"
        self._btn_toggle_metricas.setToolTip(
            f"{accion} métricas para {'dar más espacio' if visible else 'ver el resumen'}"
        )

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

        self._btn_toggle_metricas = QToolButton()
        self._btn_toggle_metricas.setObjectName("ToggleMetrics")
        self._btn_toggle_metricas.setText("⌃")
        self._btn_toggle_metricas.setToolTip("Ocultar métricas para dar más espacio")
        self._btn_toggle_metricas.setAccessibleName("Plegar o desplegar métricas")
        self._btn_toggle_metricas.setFixedSize(28, 28)
        self._btn_toggle_metricas.setCursor(Qt.CursorShape.PointingHandCursor)
        self._btn_toggle_metricas.clicked.connect(self._alternar_metricas)
        lay.addWidget(self._btn_toggle_metricas)
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
            f"color: {tokens['text_primary']}; "
            f"font-size: {int(tokens['font_size_title'].removesuffix('px')) + 6}px; "
            "font-weight: 400; background: transparent;"
        )
        self._lbl_subtitulo_header.setStyleSheet(
            f"color: {tokens['text_secondary']}; font-size: {tokens['font_size_sm']}; "
            "background: transparent;"
        )
        self._btn_toggle_metricas.setStyleSheet(
            f"""
            QToolButton#ToggleMetrics {{
                color: {tokens["text_secondary"]};
                background: {tokens["surface"]};
                border: 1px solid {tokens["border"]};
                border-radius: {tokens["radius_sm"]};
                font-size: {tokens["font_size_md"]};
                font-weight: 700;
            }}
            QToolButton#ToggleMetrics:hover {{
                color: {tokens["accent_text"]};
                background: {tokens["accent"]};
                border-color: {tokens["accent"]};
            }}
            """
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
        configure_calendar_theme(self.selector_fecha)
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
        """ + generate_date_edit_dropdown_stylesheet(tokens)

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
        self._tabla_card = GlassCard(content_margins=8)
        self._tabla_card.add_widget(self.tabla, 1)
        layout_derecho.addWidget(self._tabla_card, 1)

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
                border-bottom: 1px solid {rgba(tokens['border'], 45)};
                color: {tokens['text_primary']};
            }}
            QTableWidget::item:hover {{
                background-color: {rgba(tokens['accent'], 10)};
                color: {tokens['text_primary']};
            }}
            QTableWidget::item:selected {{
                background-color: {rgba(tokens['accent'], 14)};
                color: {tokens['text_primary']};
            }}
            QHeaderView::section {{
                background-color: {rgba(tokens['surface_alt'], 220)};
                color: {tokens['text_secondary']};
                border: none;
                border-bottom: 1px solid {rgba(tokens['border'], 70)};
                padding: 8px 10px;
                font-size: {tokens['font_size_xs']};
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
            self._actualizar_colores_tabla()
        except Exception as e:
            print(f"⚠️ Error refrescando tema: {e}")
            # No lanzar para que la app siga funcionando

    def _refrescar_tema_sidebar(self, oscuro: bool) -> None:
        """Reaplica estilos del sidebar y sus subcomponentes.
        
        Args:
            oscuro: Si usar tema oscuro.
        """
        tokens = self._theme_manager.tokens()
        self._aplicar_fondo_ventana()
        self._cabecera_sidebar.setStyleSheet("background: transparent;")
        self._contenedor_scroll.setStyleSheet("background: transparent;")
        self._zona_inferior.setStyleSheet("background: transparent;")
        self.btn_colapsar.setStyleSheet(f"""
            QToolButton {{
                background: transparent;
                color: {tokens['text_secondary']};
                border: 1px solid transparent;
                border-radius: {tokens['radius_sm']};
                font-size: 14px; font-weight: bold;
            }}
            QToolButton:hover {{
                background: {tokens['surface_alt']};
                color: {tokens['text_primary']};
                border-color: {tokens['border']};
            }}
        """)
        for b in self._botones_menu:
            b.actualizar_tema(oscuro)
        for label in self._secciones_sidebar:
            label.setStyleSheet(
                f"color: {tokens['text_disabled']}; font-size: 9px;"
                " font-weight: 700; letter-spacing: 1px;"
                " padding: 10px 8px 4px; background: transparent;"
            )
        self.btn_configuracion.setStyleSheet(f"""
            QPushButton#SidebarUtility {{
                background: transparent;
                color: {tokens['text_secondary']};
                border: 1px solid transparent;
                border-radius: {tokens['radius_lg']};
                padding: 0 10px;
                text-align: left;
            }}
            QPushButton#SidebarUtility:hover {{
                background: {tokens['surface_alt']};
                color: {tokens['text_primary']};
                border-color: {tokens['border']};
            }}
        """)
        self.btn_logout.setStyleSheet(f"""
            QPushButton#SidebarLogout {{
                background: transparent;
                color: {tokens['text_secondary']};
                border: 1px solid transparent;
                border-radius: {tokens['radius_lg']};
                padding: 0 10px;
                text-align: left;
            }}
            QPushButton#SidebarLogout:hover {{
                background: {tokens['danger_button_bg']};
                color: {tokens['danger_button_text']};
                border-color: {tokens['danger_button_bg']};
            }}
        """)
        self.usuario_chip.setStyleSheet(f"""
            QFrame#SidebarUserChip {{
                background: {tokens['surface_alt']};
                border: 1px solid {tokens['border']};
                border-radius: {tokens['radius_lg']};
            }}
            QLabel#SidebarUserAvatar {{
                background: {tokens['accent']};
                color: {tokens['accent_text']};
                border-radius: 17px;
                font-size: 11px;
                font-weight: 700;
            }}
            QLabel#SidebarUserName {{
                color: {tokens['text_primary']};
                background: transparent;
                font-size: 11px;
                font-weight: 600;
            }}
            QLabel#SidebarUserRole {{
                color: {tokens['text_secondary']};
                background: transparent;
                font-size: 9px;
            }}
        """)

    def _refrescar_tema_panel_derecho(self, oscuro: bool) -> None:
        """Reaplica estilos del panel derecho (header, filtros, tabla).
        
        Args:
            oscuro: Si usar tema oscuro.
        """
        tokens = self._theme_manager.tokens()
        self._panel_derecho.setStyleSheet(f"""
            QWidget#panelControlObjetivos {{
                background: transparent;
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

        # El tema actualiza los badges; las celdas se recolorean sin consultar datos.
        self.tabla.setStyleSheet(self._estilo_tabla(oscuro))

    def _actualizar_colores_tabla(self) -> None:
        """Aplica los colores actuales sin volver a consultar ni recrear filas."""
        tokens = self._theme_manager.tokens()
        self.tabla.setUpdatesEnabled(False)
        try:
            for row in range(self.tabla.rowCount()):
                background = parse_color(
                    tokens["surface"] if row % 2 == 0 else tokens["surface_alt"]
                )
                for column in range(self.tabla.columnCount()):
                    item = self.tabla.item(row, column)
                    if item is not None:
                        color_key = (
                            "text_secondary" if column in (1, 3) else "text_primary"
                        )
                        item.setForeground(parse_color(tokens[color_key]))
                        item.setBackground(background)

                    cell_widget = self.tabla.cellWidget(row, column)
                    if cell_widget is not None:
                        cell_widget.setStyleSheet(
                            f"background-color: {background.name(QColor.NameFormat.HexArgb)};"
                        )
        finally:
            self.tabla.setUpdatesEnabled(True)
        self.tabla.viewport().update()

    # =========================================================================
    # SIDEBAR COLAPSAR / EXPANDIR
    # =========================================================================

    def _toggle_sidebar(self):
        if self._sidebar_expandido:
            self._ajustar_sidebar(self.SIDEBAR_COLAPSADO)
            self._sidebar_expandido = False
            self.btn_colapsar.setText("›")
            self.btn_colapsar.setToolTip("Expandir menú (Ctrl+\\)")
            self.logo_label.set_size(28)
            self.usuario_chip.hide()
            self.btn_configuracion.setText("⚙")
            self.btn_logout.setText("🚪")
            for b in self._botones_menu:
                b.colapsar()
            for label in self._secciones_sidebar:
                label.hide()
        else:
            self._ajustar_sidebar(self.SIDEBAR_EXPANDIDO)
            self._sidebar_expandido = True
            self.btn_colapsar.setText("‹")
            self.btn_colapsar.setToolTip("Colapsar menú (Ctrl+\\)")
            self.logo_label.set_size(44)
            self.usuario_chip.show()
            self.btn_configuracion.setText("⚙  Configuración")
            self.btn_logout.setText("🚪  Cerrar sesión")
            for b in self._botones_menu:
                b.expandir()
            for label in self._secciones_sidebar:
                label.show()
        self.btn_configuracion.setToolTip("Configuración")
        self.btn_logout.setToolTip("Cerrar sesión")

    def _ajustar_sidebar(self, ancho_destino: int) -> None:
        self.panel_lateral.setFixedWidth(ancho_destino)

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
            it.setForeground(parse_color(tokens[color_key]))
            it.setBackground(parse_color(bg))
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
            if not tiene_animacion_activa(ventana):
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