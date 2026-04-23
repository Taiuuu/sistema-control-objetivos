# =============================================================================
# VESP Organizations - Widget de Tabla de Cobertura
# Tabla principal que muestra el estado de objetivos por día
# =============================================================================

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QLabel, QPushButton, QDateEdit, QComboBox, QLineEdit, QScrollArea,
    QFrame, QHeaderView
)
from PyQt6.QtCore import Qt, QDate, pyqtSignal
from PyQt6.QtGui import QColor, QFont
import sqlite3
from database.db import DB_PATH
from services.reportes import obtener_objetivos_del_dia
from ui.widgets.badges import BadgeEstado, BadgeNumero


# =============================================================================
# PALETAS DE COLOR
# =============================================================================

PALETA_OSCURA = {
    "bg_main":           "#16181e",
    "bg_header":         "#1a1d24",
    "bg_tabla":          "#1e2128",
    "bg_tabla_alt":      "#1a1d24",
    "accent":            "#4ade80",
    "accent_dark":       "#22c55e",
    "accent_red":        "#f87171",
    "text_primary":      "#f1f5f9",
    "text_secondary":    "#94a3b8",
    "text_muted":        "#475569",
    "border":            "#2a2d36",
    "border_light":      "#1e2128",
    "btn_menu_hover":    "#2a2d36",
    "scrollbar_handle":  "#3f4556",
}

PALETA_CLARA = {
    "bg_main":           "#ffffff",
    "bg_header":         "#f8fafc",
    "bg_tabla":          "#ffffff",
    "bg_tabla_alt":      "#f8fafc",
    "accent":            "#16a34a",
    "accent_dark":       "#15803d",
    "accent_red":        "#dc2626",
    "text_primary":      "#0f172a",
    "text_secondary":    "#475569",
    "text_muted":        "#94a3b8",
    "border":            "#e2e8f0",
    "border_light":      "#f1f5f9",
    "btn_menu_hover":    "#e2e8f0",
    "scrollbar_handle":  "#94a3b8",
}


def p(key: str, oscuro: bool) -> str:
    """Acceso rápido a paleta."""
    return (PALETA_OSCURA if oscuro else PALETA_CLARA)[key]


# =============================================================================
# WIDGET DE TABLA DE COBERTURA
# =============================================================================

class TablaCoberturaWidget(QWidget):
    """Widget de tabla que muestra el control diario de objetivos."""
    
    # Señales
    objetivo_seleccionado = pyqtSignal(int)  # objetivo_id
    objetivo_dar_de_baja = pyqtSignal(int)   # objetivo_id
    fecha_cambiada = pyqtSignal(str)         # fecha en formato yyyy-MM-dd
    filtros_cambiados = pyqtSignal()         # cuando cambian filtros
    
    def __init__(self, oscuro: bool, parent=None):
        super().__init__(parent)
        self._oscuro = oscuro
        self._objetivos = []
        
        self._construir_ui()

    def _construir_ui(self):
        oscuro = self._oscuro
        layout = QVBoxLayout(self)
        layout.setSpacing(0)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Barra de filtros
        layout.addWidget(self._construir_filtros())
        
        # Separador
        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet(f"QFrame {{ background: {p('border', oscuro)}; max-height: 1px; border: none; margin: 0; }}")
        layout.addWidget(sep)
        
        # Tabla
        self._tabla = QTableWidget()
        self._tabla.setColumnCount(7)
        self._tabla.setHorizontalHeaderLabels([
            "Objetivo",
            "Equipo diurno", "Pasadas día",
            "Equipo nocturno", "Pasadas noche",
            "Estado", "Acción"
        ])
        
        # Anchos de columna
        self._tabla.setColumnWidth(0, 210)
        self._tabla.setColumnWidth(1, 155)
        self._tabla.setColumnWidth(2, 95)
        self._tabla.setColumnWidth(3, 155)
        self._tabla.setColumnWidth(4, 95)
        self._tabla.setColumnWidth(5, 145)
        self._tabla.setColumnWidth(6, 110)
        
        self._tabla.setAlternatingRowColors(False)
        self._tabla.setSortingEnabled(True)
        self._tabla.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self._tabla.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self._tabla.setShowGrid(False)
        self._tabla.verticalHeader().setVisible(False)
        self._tabla.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        self._tabla.horizontalHeader().setStretchLastSection(True)
        self._tabla.verticalHeader().setDefaultSectionSize(44)
        
        self._aplicar_estilo_tabla()
        layout.addWidget(self._tabla)

    def _construir_filtros(self) -> QWidget:
        oscuro = self._oscuro
        
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFixedHeight(54)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll.setStyleSheet(f"""
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
        
        widget = QWidget()
        widget.setStyleSheet(f"background-color: {p('bg_header', oscuro)};")
        fila = QHBoxLayout(widget)
        fila.setContentsMargins(16, 0, 16, 0)
        fila.setSpacing(8)
        
        # Fecha
        self._selector_fecha = QDateEdit()
        self._selector_fecha.setDate(QDate.currentDate())
        self._selector_fecha.setCalendarPopup(True)
        self._selector_fecha.setFixedWidth(115)
        self._selector_fecha.setStyleSheet(self._estilo_input(oscuro))
        self._selector_fecha.dateChanged.connect(self._on_fecha_cambiada)
        
        # Botones navegación fecha
        btn_ant = QPushButton("‹")
        btn_ant.setToolTip("Día anterior (Ctrl+←)")
        btn_ant.setStyleSheet(self._estilo_btn_nav(oscuro))
        btn_ant.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_ant.clicked.connect(lambda: self._cambiar_fecha(-1))
        
        btn_sig = QPushButton("›")
        btn_sig.setToolTip("Día siguiente (Ctrl+→)")
        btn_sig.setStyleSheet(self._estilo_btn_nav(oscuro))
        btn_sig.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_sig.clicked.connect(lambda: self._cambiar_fecha(1))
        
        # Filtros
        self._filtro_turno = QComboBox()
        self._filtro_turno.addItems(["Todos los turnos", "diurno", "nocturno"])
        self._filtro_turno.setFixedWidth(140)
        self._filtro_turno.setStyleSheet(self._estilo_input(oscuro))
        self._filtro_turno.currentTextChanged.connect(self.filtros_cambiados.emit)
        
        self._filtro_supervisor = QComboBox()
        self._filtro_supervisor.addItem("Todos los supervisores", None)
        self._filtro_supervisor.setFixedWidth(170)
        self._filtro_supervisor.setStyleSheet(self._estilo_input(oscuro))
        self._cargar_supervisores()
        self._filtro_supervisor.currentTextChanged.connect(self.filtros_cambiados.emit)
        
        self._filtro_estado = QComboBox()
        self._filtro_estado.addItems([
            "Todos", "Pasaron los dos", "No pasó nadie",
            "No pasó día", "No pasó noche"
        ])
        self._filtro_estado.setFixedWidth(155)
        self._filtro_estado.setStyleSheet(self._estilo_input(oscuro))
        self._filtro_estado.currentTextChanged.connect(self.filtros_cambiados.emit)
        
        # Buscador
        self._buscador = QLineEdit()
        self._buscador.setPlaceholderText("🔍  Buscar objetivo...")
        self._buscador.setFixedWidth(170)
        self._buscador.setStyleSheet(self._estilo_input(oscuro))
        self._buscador.textChanged.connect(self.filtros_cambiados.emit)
        
        # Botón aplicar
        btn_aplicar = QPushButton("Aplicar")
        btn_aplicar.setFixedWidth(75)
        btn_aplicar.setStyleSheet(self._estilo_btn_accion(oscuro))
        btn_aplicar.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_aplicar.clicked.connect(self.cargar_datos)
        
        # Labels
        estilo_lbl = f"color: {p('text_secondary', oscuro)}; font-size: 11px; font-weight: 500;"
        
        fila.addWidget(QLabel("Fecha")); fila.setSpacing(4)
        fila.addWidget(btn_ant)
        fila.addWidget(self._selector_fecha)
        fila.addWidget(btn_sig)
        fila.addSpacing(4)
        fila.addWidget(QLabel("Turno")); fila.addWidget(self._filtro_turno)
        fila.addWidget(QLabel("Supervisor")); fila.addWidget(self._filtro_supervisor)
        fila.addWidget(QLabel("Estado")); fila.addWidget(self._filtro_estado)
        fila.addSpacing(4)
        fila.addWidget(self._buscador)
        fila.addWidget(btn_aplicar)
        fila.addStretch()
        
        scroll.setWidget(widget)
        return scroll

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

    def _estilo_btn_nav(self, oscuro: bool) -> str:
        return f"""
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

    def _estilo_btn_accion(self, oscuro: bool) -> str:
        return f"""
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

    def _aplicar_estilo_tabla(self):
        oscuro = self._oscuro
        self._tabla.setStyleSheet(f"""
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
        """)

    def _cargar_supervisores(self):
        """Carga la lista de supervisores en el filtro."""
        conexion = sqlite3.connect(DB_PATH)
        cursor = conexion.cursor()
        cursor.execute('SELECT id, nombre FROM supervisores WHERE activo = 1')
        for sid, nombre in cursor.fetchall():
            self._filtro_supervisor.addItem(nombre, sid)
        conexion.close()

    def _on_fecha_cambiada(self):
        self.fecha_cambiada.emit(self.get_fecha())

    def _cambiar_fecha(self, dias: int):
        self._selector_fecha.setDate(self._selector_fecha.date().addDays(dias))

    # =========================================================================
    # MÉTODOS PÚBLICOS
    # =========================================================================
    
    def get_fecha(self) -> str:
        return self._selector_fecha.date().toString("yyyy-MM-dd")
    
    def get_turno(self) -> str:
        turno = self._filtro_turno.currentText()
        return None if turno == "Todos los turnos" else turno
    
    def get_supervisor_id(self):
        return self._filtro_supervisor.currentData()
    
    def get_filtro_estado(self) -> str:
        return self._filtro_estado.currentText()
    
    def get_texto_busqueda(self) -> str:
        return self._buscador.text().strip().lower()
    
    def set_fecha(self, fecha: str):
        """Establece la fecha desde un string yyyy-MM-dd."""
        from PyQt6.QtCore import QDate
        partes = fecha.split('-')
        if len(partes) == 3:
            self._selector_fecha.setDate(QDate(int(partes[0]), int(partes[1]), int(partes[2])))

    def cargar_datos(self):
        """Carga los datos en la tabla."""
        fecha = self.get_fecha()
        turno = self.get_turno()
        supervisor_id = self.get_supervisor_id()
        filtro_estado = self.get_filtro_estado()
        texto_busqueda = self.get_texto_busqueda()
        
        # Obtener objetivos del día
        self._objetivos = sorted(
            obtener_objetivos_del_dia(fecha),
            key=lambda o: o[1].lower()
        )
        
        # Obtener pasadas por turno
        pasadas_dia, pasadas_noche = self._obtener_pasadas_por_turno(fecha, supervisor_id)
        
        # Aplicar filtros
        if turno == "diurno":
            pasadas_dia_filtradas = self._obtener_pasadas_por_turno(fecha, supervisor_id)[0] if supervisor_id else pasadas_dia
            pasadas_noche_filtradas = pasadas_noche
        elif turno == "nocturno":
            pasadas_noche_filtradas = self._obtener_pasadas_por_turno(fecha, supervisor_id)[1] if supervisor_id else pasadas_noche
            pasadas_dia_filtradas = pasadas_dia
        else:
            pasadas_dia_filtradas = pasadas_dia
            pasadas_noche_filtradas = pasadas_noche
        
        # Obtener equipos
        equipo_dia = self._obtener_equipo(fecha, "diurno")
        equipo_noche = self._obtener_equipo(fecha, "nocturno")
        
        # Filtrar y crear filas
        filas = []
        for o in self._objetivos:
            if texto_busqueda and texto_busqueda not in o[1].lower():
                continue
            
            pd = pasadas_dia_filtradas.get(o[0], 0)
            pn = pasadas_noche_filtradas.get(o[0], 0)
            estado = self._calcular_estado(
                pasadas_dia.get(o[0], 0),
                pasadas_noche.get(o[0], 0)
            )
            
            if filtro_estado != "Todos" and estado != filtro_estado:
                continue
            
            filas.append((o, pd, pn, estado))
        
        self._render_filas(filas, equipo_dia, equipo_noche)

    def _obtener_pasadas_por_turno(self, fecha: str, supervisor_id: int = None) -> tuple:
        """Retorna diccionarios de pasadas por objetivo y turno."""
        conexion = sqlite3.connect(DB_PATH)
        cursor = conexion.cursor()
        
        query = "SELECT objetivo_id, turno, COUNT(*) FROM pasadas WHERE fecha = ?"
        params = [fecha]
        
        if supervisor_id:
            query += " AND supervisor_id = ?"
            params.append(supervisor_id)
        
        query += " GROUP BY objetivo_id, turno"
        cursor.execute(query, params)
        
        pasadas_dia = {}
        pasadas_noche = {}
        
        for obj_id, turno, count in cursor.fetchall():
            if turno == "diurno":
                pasadas_dia[obj_id] = count
            elif turno == "nocturno":
                pasadas_noche[obj_id] = count
        
        conexion.close()
        return pasadas_dia, pasadas_noche

    def _obtener_equipo(self, fecha: str, turno: str) -> str:
        """Obtiene el equipo asignado para una fecha y turno."""
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

    def _calcular_estado(self, pasadas_dia: int, pasadas_noche: int) -> str:
        if pasadas_dia > 0 and pasadas_noche > 0:
            return "Pasaron los dos"
        if pasadas_dia > 0 and pasadas_noche == 0:
            return "No pasó noche"
        if pasadas_dia == 0 and pasadas_noche > 0:
            return "No pasó día"
        return "No pasó nadie"

    def _render_filas(self, filas, equipo_dia: str, equipo_noche: str):
        """Renderiza las filas de la tabla."""
        self._tabla.setUpdatesEnabled(False)
        sorting_enabled = self._tabla.isSortingEnabled()
        self._tabla.setSortingEnabled(False)
        
        # Limpiar
        self._tabla.clearContents()
        self._tabla.setRowCount(0)
        self._tabla.setRowCount(len(filas))
        
        oscuro = self._oscuro
        bg_fila = p("bg_tabla", oscuro)
        bg_alt = p("bg_tabla_alt", oscuro)
        
        for i, (o, pd, pn, estado) in enumerate(filas):
            bg = bg_fila if i % 2 == 0 else bg_alt
            
            # Objetivo
            item = QTableWidgetItem(o[1])
            item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            item.setForeground(QColor(p("text_primary", oscuro)))
            item.setBackground(QColor(bg))
            self._tabla.setItem(i, 0, item)
            
            # Equipo día
            item = QTableWidgetItem(equipo_dia)
            item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            item.setForeground(QColor(p("text_secondary", oscuro)))
            item.setBackground(QColor(bg))
            self._tabla.setItem(i, 1, item)
            
            # Pasadas día (badge)
            badge = BadgeNumero(pd, oscuro)
            self._tabla.setCellWidget(i, 2, self._envolver_widget(badge, bg))
            
            # Equipo noche
            item = QTableWidgetItem(equipo_noche)
            item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            item.setForeground(QColor(p("text_secondary", oscuro)))
            item.setBackground(QColor(bg))
            self._tabla.setItem(i, 3, item)
            
            # Pasadas noche (badge)
            badge = BadgeNumero(pn, oscuro)
            self._tabla.setCellWidget(i, 4, self._envolver_widget(badge, bg))
            
            # Estado
            badge = BadgeEstado(estado, oscuro)
            self._tabla.setCellWidget(i, 5, self._envolver_widget(badge, bg))
            
            # Botón dar de baja
            btn = QPushButton("Dar de baja")
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setStyleSheet(f"""
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
            btn.clicked.connect(lambda checked, oid=o[0]: self.objetivo_dar_de_baja.emit(oid))
            self._tabla.setCellWidget(i, 6, self._envolver_widget(btn, bg))
        
        self._tabla.setSortingEnabled(sorting_enabled)
        self._tabla.setUpdatesEnabled(True)
        self._tabla.update()

    def _envolver_widget(self, widget, bg_color: str) -> QWidget:
        """Envuelve un widget en un contenedor centrado."""
        contenedor = QWidget()
        lay = QHBoxLayout(contenedor)
        lay.setContentsMargins(8, 4, 8, 4)
        lay.setSpacing(0)
        lay.addStretch()
        lay.addWidget(widget)
        lay.addStretch()
        contenedor.setStyleSheet(f"background-color: {bg_color};")
        return contenedor

    def actualizar_tema(self, oscuro: bool):
        """Actualiza los estilos cuando cambia el tema."""
        self._oscuro = oscuro
        self._aplicar_estilo_tabla()
        self.cargar_datos()