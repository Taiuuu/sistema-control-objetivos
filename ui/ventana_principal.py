# =============================================================================
# VESP Organizations - Sistema de Control de Objetivos
# Ventana principal del sistema
# =============================================================================

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QTableWidget, QTableWidgetItem, QLabel,
    QPushButton, QDateEdit, QComboBox, QMessageBox,
    QFrame, QLineEdit, QHeaderView, QScrollArea,
    QToolButton, QSizePolicy, QSpacerItem
)
from PyQt6.QtCore import QDate, QTimer, QEvent, Qt, QSize, QPropertyAnimation, QEasingCurve
from PyQt6.QtGui import QColor, QPixmap, QIcon, QShortcut, QKeySequence
from services.reportes import obtener_objetivos_del_dia
from ui.animaciones import animar_entrada
from ui.form_objetivo import FormObjetivo
from ui.form_supervisor import FormSupervisor
from ui.form_pasada import FormPasada
from ui.form_de_turno import FormTurno
from ui.lista_objetivos import ListaObjetivos
from ui.lista_supervisores import ListaSupervisores
from ui.reporte_mensual import ReporteMensual
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
    pasadas_dia = contar_pasadas(fecha, objetivo_id, turno="diurno")
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
        SELECT s1.nombre, s2.nombre
        FROM equipos e
        JOIN supervisores s1 ON e.supervisor1_id = s1.id
        JOIN supervisores s2 ON e.supervisor2_id = s2.id
        WHERE e.fecha = ? AND e.turno = ?
    """, (fecha, turno))
    resultado = cursor.fetchone()
    conexion.close()
    if resultado:
        return f"{resultado[0]} y {resultado[1]}"
    return "-"


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
# VENTANA PRINCIPAL
# =============================================================================

class VentanaPrincipal(QWidget):

    # Ancho expandido y colapsado del sidebar
    SIDEBAR_EXPANDIDO = 220
    SIDEBAR_COLAPSADO = 52

    def __init__(self, usuario_id=None, rol=None, on_login_exitoso=None, app=None, alternar_tema_fn=None):
        self.usuario_id = usuario_id
        self.rol = rol
        self.on_login_exitoso = on_login_exitoso
        self.app = app
        self.alternar_tema_fn = alternar_tema_fn
        self.zoom_nivel = 13
        self._sidebar_expandido = True

        super().__init__()
        self.setWindowTitle("VESP Control de Objetivos")
        self.setWindowFlags(Qt.WindowType.Window)
        self.move(100, 100)
        self.resize(1300, 600)
        # Mínimo más bajo para que funcione en ventanas chicas
        self.setMinimumSize(700, 420)
        self.setWindowIcon(QIcon(ruta_asset("assets/vesp.png")))

        layout_principal = QHBoxLayout()
        layout_principal.setSpacing(0)
        layout_principal.setContentsMargins(0, 0, 0, 0)

        # =====================================================================
        # PANEL LATERAL
        # =====================================================================
        self.panel_lateral = QFrame()
        self.panel_lateral.setFixedWidth(self.SIDEBAR_EXPANDIDO)

        oscuro = obtener_tema_actual() == "oscuro"
        panel_bg    = "#1a1a1a" if oscuro else "#e8e8e8"
        panel_border = "#333"   if oscuro else "#ccc"
        sep_color    = "#333"   if oscuro else "#ccc"
        titulo_color = "#4CAF50" if oscuro else "#2E7D32"
        subtitulo_color = "#888" if oscuro else "#666"
        usuario_color   = "#888" if oscuro else "#666"

        self.panel_lateral.setStyleSheet(
            f"background-color: {panel_bg}; border-right: 1px solid {panel_border};"
        )

        layout_lateral = QVBoxLayout(self.panel_lateral)
        layout_lateral.setSpacing(0)
        layout_lateral.setContentsMargins(0, 0, 0, 0)

        # ----- Cabecera con logo + botón colapsar -----
        cabecera = QWidget()
        cabecera.setFixedHeight(110)
        cabecera.setStyleSheet(f"background-color: {panel_bg};")
        lay_cabecera = QVBoxLayout(cabecera)
        lay_cabecera.setContentsMargins(8, 10, 8, 4)
        lay_cabecera.setSpacing(2)

        # Botón colapsar (esquina superior derecha de la cabecera)
        self.btn_colapsar = QToolButton()
        self.btn_colapsar.setText("◀")
        self.btn_colapsar.setFixedSize(22, 22)
        self.btn_colapsar.setToolTip("Colapsar menú")
        self.btn_colapsar.setStyleSheet("""
            QToolButton {
                background: transparent;
                color: #888;
                border: none;
                font-size: 11px;
            }
            QToolButton:hover { color: white; }
        """)
        self.btn_colapsar.clicked.connect(self._toggle_sidebar)

        fila_logo = QHBoxLayout()
        fila_logo.setContentsMargins(0, 0, 0, 0)

        self.logo_label = QLabel()
        pixmap = QPixmap(ruta_asset("assets/vesp.png")).scaled(
            40, 40, Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation
        )
        self.logo_label.setPixmap(pixmap)
        self.logo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        fila_logo.addWidget(self.logo_label)
        fila_logo.addStretch()
        fila_logo.addWidget(self.btn_colapsar)
        lay_cabecera.addLayout(fila_logo)

        self.titulo_lateral = QLabel("V.E.S.P")
        self.titulo_lateral.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.titulo_lateral.setStyleSheet(
            f"color: {titulo_color}; font-size: 15px; font-weight: bold;"
        )
        lay_cabecera.addWidget(self.titulo_lateral)

        self.subtitulo_lateral = QLabel("Organizations")
        self.subtitulo_lateral.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.subtitulo_lateral.setStyleSheet(
            f"color: {subtitulo_color}; font-size: 10px;"
        )
        lay_cabecera.addWidget(self.subtitulo_lateral)

        layout_lateral.addWidget(cabecera)

        sep_top = QFrame()
        sep_top.setFrameShape(QFrame.Shape.HLine)
        sep_top.setStyleSheet(f"color: {sep_color}; margin: 0px;")
        layout_lateral.addWidget(sep_top)

        # ----- Zona scrollable con los botones -----
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll_area.setStyleSheet("""
            QScrollArea { border: none; background: transparent; }
            QScrollBar:vertical {
                width: 4px;
                background: transparent;
            }
            QScrollBar::handle:vertical {
                background: #555;
                border-radius: 2px;
                min-height: 20px;
            }
            QScrollBar::add-line:vertical,
            QScrollBar::sub-line:vertical { height: 0px; }
        """)

        contenedor_scroll = QWidget()
        contenedor_scroll.setStyleSheet(f"background-color: {panel_bg};")
        self.layout_scroll = QVBoxLayout(contenedor_scroll)
        self.layout_scroll.setSpacing(2)
        self.layout_scroll.setContentsMargins(6, 6, 6, 6)

        estilo_boton = f"""
            QPushButton {{
                background-color: transparent;
                color: {'#cccccc' if oscuro else '#333333'};
                border: none;
                border-radius: 6px;
                padding: 8px 10px;
                text-align: left;
                font-size: 12px;
                min-height: 34px;
            }}
            QPushButton:hover {{
                background-color: {'#2a2a2a' if oscuro else '#d0d0d0'};
                color: {'white' if oscuro else '#111'};
            }}
            QPushButton:pressed {{
                background-color: #4CAF50;
                color: white;
            }}
        """

        # Guardamos referencia a todos los botones para colapsar/expandir
        self._botones_menu = []

        def boton_menu(icono, texto, accion, shortcut=None):
            b = QPushButton(f"{icono}  {texto}")
            b.setProperty("icono", icono)
            b.setProperty("texto_completo", f"{icono}  {texto}")
            if shortcut:
                b.setToolTip(f"{texto} ({shortcut})")
            else:
                b.setToolTip(texto)
            b.setStyleSheet(estilo_boton)
            b.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
            b.clicked.connect(accion)
            self._botones_menu.append(b)
            return b

        def separador():
            s = QFrame()
            s.setFrameShape(QFrame.Shape.HLine)
            s.setStyleSheet(f"color: {sep_color}; margin: 3px 0px;")
            return s

        # Grupo principal
        self.layout_scroll.addWidget(boton_menu("📋", "Control diario",     self.cargar_tabla,          "Ctrl+B"))
        self.layout_scroll.addWidget(boton_menu("📊", "Dashboard",          self.abrir_dashboard,       "Ctrl+D"))
        self.layout_scroll.addWidget(boton_menu("✅", "Registrar pasada",   self.abrir_form_pasada,     "Ctrl+P"))
        self.layout_scroll.addWidget(boton_menu("🕐", "Registrar turno",    self.abrir_form_turno,      "Ctrl+T"))

        self.layout_scroll.addWidget(separador())

        self.layout_scroll.addWidget(boton_menu("➕", "Agregar objetivo",   self.abrir_form_objetivo,   "Ctrl+O"))
        self.layout_scroll.addWidget(boton_menu("📍", "Ver objetivos",      self.abrir_lista_objetivos))
        self.layout_scroll.addWidget(boton_menu("👤", "Agregar supervisor", self.abrir_form_supervisor, "Ctrl+S"))
        self.layout_scroll.addWidget(boton_menu("👥", "Ver supervisores",   self.abrir_lista_supervisores))

        self.layout_scroll.addWidget(separador())

        self.layout_scroll.addWidget(boton_menu("🔍", "Ver pasadas",        self.abrir_lista_pasadas))
        self.layout_scroll.addWidget(boton_menu("📝", "Notas del día",      self.abrir_notas,           "Ctrl+N"))
        self.layout_scroll.addWidget(boton_menu("📅", "Reporte mensual",    self.abrir_reporte_mensual, "Ctrl+R"))
        self.layout_scroll.addWidget(boton_menu("💾", "Transferir datos",   self.abrir_transferir_datos))
        self.layout_scroll.addWidget(boton_menu("📥", "Importar Excel",     self.abrir_importar_excel))
        self.layout_scroll.addWidget(boton_menu("❓", "Ayuda",              self.abrir_ayuda,           "Ctrl+H"))

        if self.rol == "admin":
            self.layout_scroll.addWidget(separador())
            self.layout_scroll.addWidget(boton_menu("⚙️",  "Gestionar usuarios",   self.abrir_gestionar_usuarios))
            self.layout_scroll.addWidget(boton_menu("📜",  "Historial",            self.abrir_logs))
            self.layout_scroll.addWidget(boton_menu("🗄️",  "Monitor de Caché",     self.abrir_cache))
            self.layout_scroll.addWidget(boton_menu("🔧",  "Optimización de BD",   self.abrir_indexacion))
            self.layout_scroll.addWidget(boton_menu("🛡️",  "Validaciones BD",      self.abrir_validaciones))
            self.layout_scroll.addWidget(boton_menu("🔎",  "Auditoría detallada",  self.abrir_auditoria))
            self.layout_scroll.addWidget(boton_menu("🔄",  "Sincronización",       self.abrir_sincronizacion))

        self.layout_scroll.addStretch()

        scroll_area.setWidget(contenedor_scroll)
        layout_lateral.addWidget(scroll_area, 1)

        # ----- Zona inferior fija (zoom, tema, usuario) -----
        zona_inferior = QWidget()
        zona_inferior.setStyleSheet(f"background-color: {panel_bg};")
        lay_inf = QVBoxLayout(zona_inferior)
        lay_inf.setContentsMargins(6, 4, 6, 8)
        lay_inf.setSpacing(4)

        sep_inf = QFrame()
        sep_inf.setFrameShape(QFrame.Shape.HLine)
        sep_inf.setStyleSheet(f"color: {sep_color};")
        lay_inf.addWidget(sep_inf)

        # Fila zoom
        fila_zoom = QHBoxLayout()
        fila_zoom.setSpacing(4)

        estilo_btn_pequeño = """
            QPushButton {
                background-color: transparent;
                color: #888;
                border: 1px solid #555;
                border-radius: 4px;
                font-size: 11px;
                min-width: 30px;
                min-height: 26px;
            }
            QPushButton:hover { color: white; border-color: #888; }
        """

        btn_zoom_menos = QPushButton("A−")
        btn_zoom_menos.setToolTip("Reducir zoom (Ctrl+−)")
        btn_zoom_menos.setStyleSheet(estilo_btn_pequeño)
        btn_zoom_menos.clicked.connect(self._zoom_menos)

        btn_zoom_mas = QPushButton("A+")
        btn_zoom_mas.setToolTip("Aumentar zoom (Ctrl+=)")
        btn_zoom_mas.setStyleSheet(estilo_btn_pequeño)
        btn_zoom_mas.clicked.connect(self._zoom_mas)

        self.lbl_zoom = QLabel(f"{self.zoom_nivel}px")
        self.lbl_zoom.setStyleSheet(f"color: {subtitulo_color}; font-size: 10px;")
        self.lbl_zoom.setAlignment(Qt.AlignmentFlag.AlignCenter)

        fila_zoom.addWidget(btn_zoom_menos)
        fila_zoom.addWidget(self.lbl_zoom)
        fila_zoom.addWidget(btn_zoom_mas)
        lay_inf.addLayout(fila_zoom)

        # Botón tema
        self.btn_tema = QPushButton("☀  Modo claro" if oscuro else "🌙  Modo oscuro")
        self.btn_tema.setStyleSheet(estilo_boton)
        self.btn_tema.clicked.connect(self._alternar_tema)
        lay_inf.addWidget(self.btn_tema)

        # Etiqueta usuario
        nombre_usuario = obtener_nombre_usuario(usuario_id)
        self.usuario_label = QLabel(f"👤 {nombre_usuario}")
        self.usuario_label.setStyleSheet(
            f"color: {usuario_color}; font-size: 10px; padding: 2px;"
        )
        self.usuario_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.usuario_label.setWordWrap(True)
        lay_inf.addWidget(self.usuario_label)

        layout_lateral.addWidget(zona_inferior)

        layout_principal.addWidget(self.panel_lateral)

        # =====================================================================
        # PANEL DERECHO
        # =====================================================================
        panel_derecho = QWidget()
        layout_derecho = QVBoxLayout(panel_derecho)
        layout_derecho.setContentsMargins(10, 10, 10, 10)
        layout_derecho.setSpacing(8)

        # Fila superior: scroll horizontal para no cortar nada en ventanas chicas
        scroll_filtros = QScrollArea()
        scroll_filtros.setWidgetResizable(True)
        scroll_filtros.setFixedHeight(46)
        scroll_filtros.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll_filtros.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll_filtros.setStyleSheet("QScrollArea { border: none; background: transparent; }")

        widget_filtros = QWidget()
        fila_superior = QHBoxLayout(widget_filtros)
        fila_superior.setContentsMargins(0, 0, 0, 0)
        fila_superior.setSpacing(6)

        self.selector_fecha = QDateEdit()
        self.selector_fecha.setDate(QDate.currentDate())
        self.selector_fecha.setCalendarPopup(True)
        self.selector_fecha.setFixedWidth(110)

        boton_fecha_anterior = QPushButton("◀")
        boton_fecha_anterior.setFixedWidth(28)
        boton_fecha_anterior.setToolTip("Día anterior (Ctrl+←)")
        boton_fecha_anterior.clicked.connect(self._fecha_anterior)

        boton_fecha_siguiente = QPushButton("▶")
        boton_fecha_siguiente.setFixedWidth(28)
        boton_fecha_siguiente.setToolTip("Día siguiente (Ctrl+→)")
        boton_fecha_siguiente.clicked.connect(self._fecha_siguiente)

        boton_buscar = QPushButton("Buscar")
        boton_buscar.setFixedWidth(70)
        boton_buscar.clicked.connect(self.cargar_tabla)

        self.filtro_turno = QComboBox()
        self.filtro_turno.addItems(["Todos los turnos", "diurno", "nocturno"])
        self.filtro_turno.setFixedWidth(130)

        self.filtro_supervisor = QComboBox()
        self.filtro_supervisor.addItem("Todos los supervisores", None)
        self.filtro_supervisor.setFixedWidth(160)
        for s in cargar_supervisores():
            self.filtro_supervisor.addItem(s[1], s[0])

        self.filtro_estado = QComboBox()
        self.filtro_estado.addItems([
            "Todos", "Pasaron los dos", "No pasó nadie",
            "No pasó día", "No pasó noche"
        ])
        self.filtro_estado.setFixedWidth(150)

        boton_filtrar = QPushButton("Filtrar")
        boton_filtrar.setFixedWidth(65)
        boton_filtrar.clicked.connect(self.cargar_tabla)

        self.buscador = QLineEdit()
        self.buscador.setPlaceholderText("Buscar objetivo...")
        self.buscador.setFixedWidth(160)
        self.buscador.textChanged.connect(self.cargar_tabla)

        fila_superior.addWidget(QLabel("Fecha:"))
        fila_superior.addWidget(boton_fecha_anterior)
        fila_superior.addWidget(self.selector_fecha)
        fila_superior.addWidget(boton_fecha_siguiente)
        fila_superior.addWidget(boton_buscar)
        fila_superior.addSpacing(10)
        fila_superior.addWidget(QLabel("Turno:"))
        fila_superior.addWidget(self.filtro_turno)
        fila_superior.addWidget(QLabel("Supervisor:"))
        fila_superior.addWidget(self.filtro_supervisor)
        fila_superior.addWidget(QLabel("Estado:"))
        fila_superior.addWidget(self.filtro_estado)
        fila_superior.addWidget(boton_filtrar)
        fila_superior.addSpacing(10)
        fila_superior.addWidget(self.buscador)
        fila_superior.addStretch()

        scroll_filtros.setWidget(widget_filtros)
        layout_derecho.addWidget(scroll_filtros)

        # Tabla principal
        self.tabla = QTableWidget()
        self.tabla.setColumnCount(7)
        self.tabla.setHorizontalHeaderLabels([
            "Objetivo",
            "Equipo diurno", "Pasadas día",
            "Equipo nocturno", "Pasadas noche",
            "Estado", "Acción"
        ])
        self.tabla.setColumnWidth(0, 200)
        self.tabla.setColumnWidth(1, 150)
        self.tabla.setColumnWidth(2, 90)
        self.tabla.setColumnWidth(3, 150)
        self.tabla.setColumnWidth(4, 90)
        self.tabla.setColumnWidth(5, 130)
        self.tabla.setColumnWidth(6, 100)
        self.tabla.setAlternatingRowColors(True)
        self.tabla.setSortingEnabled(True)
        self.tabla.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        self.tabla.horizontalHeader().setStretchLastSection(True)
        layout_derecho.addWidget(self.tabla)

        layout_principal.addWidget(panel_derecho, 1)
        self.setLayout(layout_principal)

        self.objetivos_actuales = []
        self.cargar_tabla()
        animar_entrada(self)

        # Shortcuts
        QShortcut(QKeySequence("Ctrl+P"), self).activated.connect(self.abrir_form_pasada)
        QShortcut(QKeySequence("Ctrl+O"), self).activated.connect(self.abrir_form_objetivo)
        QShortcut(QKeySequence("Ctrl+S"), self).activated.connect(self.abrir_form_supervisor)
        QShortcut(QKeySequence("Ctrl+T"), self).activated.connect(self.abrir_form_turno)
        QShortcut(QKeySequence("Ctrl+N"), self).activated.connect(self.abrir_notas)
        QShortcut(QKeySequence("Ctrl+R"), self).activated.connect(self.abrir_reporte_mensual)
        QShortcut(QKeySequence("Ctrl+B"), self).activated.connect(self.cargar_tabla)
        QShortcut(QKeySequence("Ctrl+D"), self).activated.connect(self.abrir_dashboard)
        QShortcut(QKeySequence("Ctrl+H"), self).activated.connect(self.abrir_ayuda)
        QShortcut(QKeySequence("Ctrl+="), self).activated.connect(self._zoom_mas)
        QShortcut(QKeySequence("Ctrl+-"), self).activated.connect(self._zoom_menos)
        QShortcut(QKeySequence("Ctrl+Left"),  self).activated.connect(self._fecha_anterior)
        QShortcut(QKeySequence("Ctrl+Right"), self).activated.connect(self._fecha_siguiente)

        # Shortcut para colapsar/expandir sidebar
        QShortcut(QKeySequence("Ctrl+\\"), self).activated.connect(self._toggle_sidebar)

        # Timer inactividad
        self.timer_inactividad = QTimer()
        self.timer_inactividad.setInterval(30 * 60 * 1000)
        self.timer_inactividad.timeout.connect(self.cerrar_por_inactividad)
        self.timer_inactividad.start()

        # Timer refresco automático cada 30 segundos
        self.timer_refresco = QTimer()
        self.timer_refresco.setInterval(30 * 1000)
        self.timer_refresco.timeout.connect(self.cargar_tabla)
        self.timer_refresco.start()

        # Sincronizador
        self.sincronizador = obtener_sincronizador()
        self.sincronizador.datos_cambiados.connect(self._on_datos_cambiados)
        self.sincronizador.tabla_actualizar.connect(self._on_tabla_actualizar)
        self.sincronizador.cache_invalidado.connect(self._on_cache_invalidado)

    # =============================================================================
    # SIDEBAR COLAPSABLE
    # =============================================================================

    def _toggle_sidebar(self) -> None:
        """Alterna el sidebar entre expandido y colapsado."""
        if self._sidebar_expandido:
            self._colapsar_sidebar()
        else:
            self._expandir_sidebar()

    def _colapsar_sidebar(self) -> None:
        self._sidebar_expandido = False
        self.panel_lateral.setFixedWidth(self.SIDEBAR_COLAPSADO)
        self.btn_colapsar.setText("▶")
        self.btn_colapsar.setToolTip("Expandir menú (Ctrl+\\)")
        self.titulo_lateral.hide()
        self.subtitulo_lateral.hide()
        self.usuario_label.hide()
        self.btn_tema.hide()
        self.lbl_zoom.hide()
        # Mostrar solo icono en botones
        for b in self._botones_menu:
            icono = b.property("icono")
            b.setText(icono or "•")
            b.setToolTip(b.toolTip())  # tooltip ya fue seteado

    def _expandir_sidebar(self) -> None:
        self._sidebar_expandido = True
        self.panel_lateral.setFixedWidth(self.SIDEBAR_EXPANDIDO)
        self.btn_colapsar.setText("◀")
        self.btn_colapsar.setToolTip("Colapsar menú (Ctrl+\\)")
        self.titulo_lateral.show()
        self.subtitulo_lateral.show()
        self.usuario_label.show()
        self.btn_tema.show()
        self.lbl_zoom.show()
        for b in self._botones_menu:
            texto = b.property("texto_completo")
            b.setText(texto or b.text())

    # =============================================================================
    # ZOOM
    # =============================================================================

    def _zoom_mas(self) -> None:
        if self.zoom_nivel < 20:
            self.zoom_nivel += 1
            self._aplicar_zoom()

    def _zoom_menos(self) -> None:
        if self.zoom_nivel > 9:
            self.zoom_nivel -= 1
            self._aplicar_zoom()

    def _aplicar_zoom(self) -> None:
        self.lbl_zoom.setText(f"{self.zoom_nivel}px")
        if self.app:
            import re
            stylesheet_actual = self.app.styleSheet()
            nuevo = re.sub(r'font-size: \d+px;', f'font-size: {self.zoom_nivel}px;', stylesheet_actual)
            self.app.setStyleSheet(nuevo)

    # =============================================================================
    # TEMA
    # =============================================================================

    def _alternar_tema(self) -> None:
        if self.alternar_tema_fn and self.app:
            self.alternar_tema_fn(self.app, self)

    # =============================================================================
    # SINCRONIZACIÓN
    # =============================================================================

    def _on_datos_cambiados(self, tabla, operacion, datos):
        if tabla in ['objetivos', 'supervisores', 'pasadas', 'equipos']:
            self.cargar_tabla()

    def _on_tabla_actualizar(self, nombre_tabla):
        if nombre_tabla == 'principal':
            self.cargar_tabla()

    def _on_cache_invalidado(self, patron):
        pass

    # =============================================================================
    # FECHA
    # =============================================================================

    def _fecha_anterior(self) -> None:
        fecha = self.selector_fecha.date().addDays(-1)
        self.selector_fecha.setDate(fecha)
        self.cargar_tabla()

    def _fecha_siguiente(self) -> None:
        fecha = self.selector_fecha.date().addDays(1)
        self.selector_fecha.setDate(fecha)
        self.cargar_tabla()

    # =============================================================================
    # EVENTOS
    # =============================================================================

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
            print(f"Error en event handling: {e}")
            return super().event(evento)

    def moveEvent(self, evento):
        try:
            self.timer_inactividad.start()
            super().moveEvent(evento)
        except Exception as e:
            print(f"Error en moveEvent: {e}")
            super().moveEvent(evento)

    def resizeEvent(self, evento):
        try:
            self.timer_inactividad.start()
            super().resizeEvent(evento)
        except Exception as e:
            print(f"Error en resizeEvent: {e}")
            super().resizeEvent(evento)

    def cerrar_por_inactividad(self) -> None:
        hacer_backup()
        QMessageBox.information(
            self, "Sesión cerrada",
            "La sesión se cerró por inactividad. Se realizó un backup automático."
        )
        registrar_accion(self.usuario_id, "Sesión cerrada por inactividad")
        self.close()
        from ui.login import LoginWindow
        self.login = LoginWindow(self.on_login_exitoso)
        self.login.show()

    def closeEvent(self, evento) -> None:
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

    # =============================================================================
    # TABLA PRINCIPAL
    # =============================================================================

    def _limpiar_tabla(self) -> None:
        row_count = self.tabla.rowCount()
        for row in range(row_count):
            widget = self.tabla.cellWidget(row, 6)
            if widget is not None:
                self.tabla.removeCellWidget(row, 6)
                widget.deleteLater()
        self.tabla.clearContents()
        self.tabla.setRowCount(0)

    def _obtener_pasadas_agrupadas(self, fecha: str, turno: str = None, supervisor_id: int = None) -> dict:
        conexion = sqlite3.connect(DB_PATH)
        cursor = conexion.cursor()
        query = "SELECT objetivo_id, COUNT(*) FROM pasadas WHERE fecha = ?"
        params = [fecha]
        if turno:
            query += " AND turno = ?"
            params.append(turno)
        if supervisor_id:
            query += " AND supervisor_id = ?"
            params.append(supervisor_id)
        query += " GROUP BY objetivo_id"
        cursor.execute(query, params)
        resultados = dict(cursor.fetchall())
        conexion.close()
        return resultados

    def _obtener_todas_pasadas_por_turno(self, fecha: str, supervisor_id: int = None) -> tuple:
        conexion = sqlite3.connect(DB_PATH)
        cursor = conexion.cursor()
        query = """
            SELECT objetivo_id, turno, COUNT(*)
            FROM pasadas
            WHERE fecha = ?
        """
        params = [fecha]
        if supervisor_id:
            query += " AND supervisor_id = ?"
            params.append(supervisor_id)
        query += " GROUP BY objetivo_id, turno"
        cursor.execute(query, params)
        resultados = cursor.fetchall()
        conexion.close()
        pasadas_dia = {}
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

    def cargar_tabla(self) -> None:
        fecha = self.selector_fecha.date().toString("yyyy-MM-dd")
        turno = self.filtro_turno.currentText()
        turno = None if turno == "Todos los turnos" else turno
        supervisor_id = self.filtro_supervisor.currentData()
        filtro_estado = self.filtro_estado.currentText()
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
            if supervisor_id:
                pasadas_dia_filtradas, _ = self._obtener_todas_pasadas_por_turno(fecha, supervisor_id)
                pasadas_noche_filtradas = pasadas_noche_totales
            else:
                pasadas_dia_filtradas   = pasadas_dia_totales
                pasadas_noche_filtradas = pasadas_noche_totales
        elif turno == "nocturno":
            if supervisor_id:
                _, pasadas_noche_filtradas = self._obtener_todas_pasadas_por_turno(fecha, supervisor_id)
                pasadas_dia_filtradas = pasadas_dia_totales
            else:
                pasadas_dia_filtradas   = pasadas_dia_totales
                pasadas_noche_filtradas = pasadas_noche_totales
        else:
            pasadas_dia_filtradas   = pasadas_dia_totales
            pasadas_noche_filtradas = pasadas_noche_totales

        filas = []
        for o in self.objetivos_actuales:
            if texto_busqueda and texto_busqueda not in o[1].lower():
                continue
            pasadas_dia   = pasadas_dia_filtradas.get(o[0], 0)
            pasadas_noche = pasadas_noche_filtradas.get(o[0], 0)
            estado_detallado, color_hex = self._obtener_estado_detallado(
                pasadas_dia_totales.get(o[0], 0),
                pasadas_noche_totales.get(o[0], 0)
            )
            if filtro_estado != "Todos" and estado_detallado != filtro_estado:
                continue
            filas.append((o, pasadas_dia, pasadas_noche, estado_detallado, color_hex))

        self.tabla.setRowCount(len(filas))

        for i, (o, pasadas_dia, pasadas_noche, estado_detallado, color_hex) in enumerate(filas):
            self.tabla.setItem(i, 0, QTableWidgetItem(o[1]))
            self.tabla.setItem(i, 1, QTableWidgetItem(equipo_dia))
            self.tabla.setItem(i, 2, QTableWidgetItem(str(pasadas_dia)))
            self.tabla.setItem(i, 3, QTableWidgetItem(equipo_noche))
            self.tabla.setItem(i, 4, QTableWidgetItem(str(pasadas_noche)))
            self.tabla.setItem(i, 5, QTableWidgetItem(estado_detallado))

            color = QColor(color_hex)
            for col in range(6):
                self.tabla.item(i, col).setBackground(color)
                self.tabla.item(i, col).setForeground(QColor("#000000"))

            boton_baja = QPushButton("Dar de baja")
            boton_baja.clicked.connect(lambda checked, obj_id=o[0]: self.dar_de_baja(obj_id))
            self.tabla.setCellWidget(i, 6, boton_baja)

        self.tabla.setUpdatesEnabled(True)
        self.tabla.setSortingEnabled(sorting_enabled)
        self.tabla.update()

    def dar_de_baja(self, objetivo_id: int) -> None:
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

    # =============================================================================
    # ABRIR VENTANAS
    # =============================================================================

    def abrir_form_objetivo(self):
        if not hasattr(self, 'form_objetivo') or not self.form_objetivo.isVisible():
            self.form_objetivo = FormObjetivo()
            self.form_objetivo.destroyed.connect(self.cargar_tabla)
            self.form_objetivo.show()
        else:
            self.form_objetivo.raise_()
            self.form_objetivo.activateWindow()

    def abrir_form_supervisor(self):
        if not hasattr(self, 'form_supervisor') or not self.form_supervisor.isVisible():
            self.form_supervisor = FormSupervisor()
            self.form_supervisor.show()
        else:
            self.form_supervisor.raise_()
            self.form_supervisor.activateWindow()

    def abrir_form_pasada(self):
        if not hasattr(self, 'form_pasada') or not self.form_pasada.isVisible():
            self.form_pasada = FormPasada(
                fecha_inicial=self.selector_fecha.date().toString("yyyy-MM-dd")
            )
            self.form_pasada.pasada_registrada.connect(self.cargar_tabla)
            self.form_pasada.show()
        else:
            self.form_pasada.raise_()
            self.form_pasada.activateWindow()

    def abrir_form_turno(self):
        if not hasattr(self, 'form_turno') or not self.form_turno.isVisible():
            self.form_turno = FormTurno()
            self.form_turno.destroyed.connect(self.cargar_tabla)
            self.form_turno.show()
        else:
            self.form_turno.raise_()
            self.form_turno.activateWindow()

    def abrir_lista_objetivos(self):
        if not hasattr(self, 'lista_objetivos') or not self.lista_objetivos.isVisible():
            self.lista_objetivos = ListaObjetivos()
            self.lista_objetivos.show()
        else:
            self.lista_objetivos.raise_()
            self.lista_objetivos.activateWindow()

    def abrir_lista_supervisores(self):
        if not hasattr(self, 'lista_supervisores') or not self.lista_supervisores.isVisible():
            self.lista_supervisores = ListaSupervisores()
            self.lista_supervisores.show()
        else:
            self.lista_supervisores.raise_()
            self.lista_supervisores.activateWindow()

    def abrir_lista_pasadas(self):
        if not hasattr(self, 'lista_pasadas') or not self.lista_pasadas.isVisible():
            self.lista_pasadas = ListaPasadas()
            self.lista_pasadas.destroyed.connect(self.cargar_tabla)
            self.lista_pasadas.show()
        else:
            self.lista_pasadas.raise_()
            self.lista_pasadas.activateWindow()

    def abrir_notas(self):
        if not hasattr(self, 'notas') or not self.notas.isVisible():
            self.notas = NotasDiarias()
            self.notas.show()
        else:
            self.notas.raise_()
            self.notas.activateWindow()

    def abrir_dashboard(self):
        if not hasattr(self, 'dashboard') or not self.dashboard.isVisible():
            self.dashboard = Dashboard()
            self.dashboard.show()
        else:
            self.dashboard.raise_()
            self.dashboard.activateWindow()

    def abrir_reporte_mensual(self):
        if not hasattr(self, 'reporte_mensual') or not self.reporte_mensual.isVisible():
            self.reporte_mensual = ReporteMensual()
            self.reporte_mensual.show()
        else:
            self.reporte_mensual.raise_()
            self.reporte_mensual.activateWindow()

    def abrir_gestionar_usuarios(self):
        if not hasattr(self, 'gestionar_usuarios') or not self.gestionar_usuarios.isVisible():
            self.gestionar_usuarios = GestionarUsuarios()
            self.gestionar_usuarios.show()
        else:
            self.gestionar_usuarios.raise_()
            self.gestionar_usuarios.activateWindow()

    def abrir_logs(self):
        if not hasattr(self, 'logs') or not self.logs.isVisible():
            self.logs = VistaLogs()
            self.logs.show()
        else:
            self.logs.raise_()
            self.logs.activateWindow()

    def abrir_cache(self):
        if not hasattr(self, 'cache_monitor') or not self.cache_monitor.isVisible():
            self.cache_monitor = VistaCache(self.usuario_actual)
            self.cache_monitor.setWindowTitle("Monitor de Caché Inteligente")
            self.cache_monitor.setGeometry(100, 100, 1000, 600)
            self.cache_monitor.show()
        else:
            self.cache_monitor.raise_()
            self.cache_monitor.activateWindow()

    def abrir_indexacion(self):
        if not hasattr(self, 'indexacion') or not self.indexacion.isVisible():
            self.indexacion = VistaIndexacion(self.usuario_actual)
            self.indexacion.setWindowTitle("Optimización de Índices y Rendimiento")
            self.indexacion.setGeometry(100, 100, 1200, 700)
            self.indexacion.show()
        else:
            self.indexacion.raise_()
            self.indexacion.activateWindow()

    def abrir_validaciones(self):
        if not hasattr(self, 'validaciones') or not self.validaciones.isVisible():
            self.validaciones = VistaValidaciones(self.usuario_actual)
            self.validaciones.setWindowTitle("Validaciones e Integridad de BD")
            self.validaciones.setGeometry(100, 100, 1000, 600)
            self.validaciones.show()
        else:
            self.validaciones.raise_()
            self.validaciones.activateWindow()

    def abrir_ayuda(self):
        if not hasattr(self, 'ayuda') or not self.ayuda.isVisible():
            self.ayuda = Ayuda()
            self.ayuda.show()
        else:
            self.ayuda.raise_()
            self.ayuda.activateWindow()

    def abrir_transferir_datos(self):
        if not hasattr(self, 'transferir_datos') or not self.transferir_datos.isVisible():
            self.transferir_datos = TransferirDatos()
            self.transferir_datos.show()
        else:
            self.transferir_datos.raise_()
            self.transferir_datos.activateWindow()

    def abrir_sincronizacion(self):
        if not hasattr(self, 'sincronizacion') or not self.sincronizacion.isVisible():
            self.sincronizacion = VistaSincronizacion(self.usuario_actual)
            self.sincronizacion.setWindowTitle("Monitoreo de Sincronización de Datos")
            self.sincronizacion.setGeometry(100, 100, 1200, 700)
            self.sincronizacion.show()
        else:
            self.sincronizacion.raise_()
            self.sincronizacion.activateWindow()

    def abrir_importar_excel(self):
        if not hasattr(self, 'importar_excel') or not self.importar_excel.isVisible():
            self.importar_excel = ImportarExcel()
            self.importar_excel.show()
        else:
            self.importar_excel.raise_()
            self.importar_excel.activateWindow()

    def abrir_auditoria(self):
        if not hasattr(self, 'auditoria') or not self.auditoria.isVisible():
            self.auditoria = VistaAuditoria()
            self.auditoria.show()
        else:
            self.auditoria.raise_()
            self.auditoria.activateWindow()