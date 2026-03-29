# =============================================================================
# VESP Organizations - Sistema de Control de Objetivos
# Ventana principal del sistema
# =============================================================================

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QTableWidget, QTableWidgetItem, QLabel,
    QPushButton, QDateEdit, QComboBox, QMessageBox,
    QFrame, QLineEdit, QSizePolicy
)
from PyQt6.QtCore import QDate, QTimer, QEvent, Qt, QPropertyAnimation, QEasingCurve, QRect
from PyQt6.QtGui import QColor, QPixmap, QIcon, QShortcut, QKeySequence, QFont
from services.reportes import obtener_objetivos_del_dia
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
from models.objetivos import dar_de_baja_objetivo
from services.backup import hacer_backup
from services.logger import registrar_accion
from services.assets import ruta_asset
from database.db import DB_PATH
from ui.animaciones import animar_tabla
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

    def __init__(self, usuario_id=None, rol=None, on_login_exitoso=None, app=None, alternar_tema_fn=None):
        self.usuario_id = usuario_id
        self.rol = rol
        self.on_login_exitoso = on_login_exitoso
        self.app = app
        self.alternar_tema_fn = alternar_tema_fn
        self.zoom_nivel = 13  # Tamaño de fuente base
        super().__init__()
        self.setWindowTitle("VESP Control de Objetivos")
        self.setGeometry(100, 100, 1300, 600)
        self.setWindowIcon(QIcon(ruta_asset("assets/vesp.png")))

        layout_principal = QHBoxLayout()
        layout_principal.setSpacing(0)
        layout_principal.setContentsMargins(0, 0, 0, 0)

        # PANEL LATERAL
        panel_lateral = QFrame()
        panel_lateral.setFixedWidth(190)
        panel_lateral.setStyleSheet("background-color: #1a1a1a; border-right: 1px solid #333;")
        layout_lateral = QVBoxLayout(panel_lateral)
        layout_lateral.setSpacing(4)
        layout_lateral.setContentsMargins(8, 12, 8, 12)

        logo_label = QLabel()
        pixmap = QPixmap(ruta_asset("assets/vesp.png")).scaled(
            60, 60, Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation
        )
        logo_label.setPixmap(pixmap)
        logo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout_lateral.addWidget(logo_label)

        titulo_lateral = QLabel("V.E.S.P")
        titulo_lateral.setAlignment(Qt.AlignmentFlag.AlignCenter)
        titulo_lateral.setStyleSheet("color: #4CAF50; font-size: 14px; font-weight: bold;")
        layout_lateral.addWidget(titulo_lateral)

        subtitulo_lateral = QLabel("Organizations")
        subtitulo_lateral.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitulo_lateral.setStyleSheet("color: #888; font-size: 10px;")
        layout_lateral.addWidget(subtitulo_lateral)

        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet("color: #333;")
        layout_lateral.addWidget(sep)
        layout_lateral.addSpacing(4)

        estilo_boton = """
            QPushButton {
                background-color: transparent;
                color: #cccccc;
                border: none;
                border-radius: 4px;
                padding: 8px 12px;
                text-align: left;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #2a2a2a;
                color: white;
            }
            QPushButton:pressed {
                background-color: #4CAF50;
                color: white;
            }
        """

        def boton_menu(texto, accion, shortcut=None):
            b = QPushButton(texto if not shortcut else f"{texto}  {shortcut}")
            b.setStyleSheet(estilo_boton)
            b.clicked.connect(accion)
            return b

        layout_lateral.addWidget(boton_menu("Control diario", self.cargar_tabla, "Ctrl+B"))
        layout_lateral.addWidget(boton_menu("Registrar pasada", self.abrir_form_pasada, "Ctrl+P"))
        layout_lateral.addWidget(boton_menu("Registrar turno", self.abrir_form_turno, "Ctrl+T"))

        sep2 = QFrame()
        sep2.setFrameShape(QFrame.Shape.HLine)
        sep2.setStyleSheet("color: #333;")
        layout_lateral.addWidget(sep2)

        layout_lateral.addWidget(boton_menu("Agregar objetivo", self.abrir_form_objetivo, "Ctrl+O"))
        layout_lateral.addWidget(boton_menu("Ver objetivos", self.abrir_lista_objetivos))
        layout_lateral.addWidget(boton_menu("Agregar supervisor", self.abrir_form_supervisor, "Ctrl+S"))
        layout_lateral.addWidget(boton_menu("Ver supervisores", self.abrir_lista_supervisores))

        sep3 = QFrame()
        sep3.setFrameShape(QFrame.Shape.HLine)
        sep3.setStyleSheet("color: #333;")
        layout_lateral.addWidget(sep3)

        layout_lateral.addWidget(boton_menu("Ver pasadas", self.abrir_lista_pasadas))
        layout_lateral.addWidget(boton_menu("Notas del día", self.abrir_notas, "Ctrl+N"))
        layout_lateral.addWidget(boton_menu("Reporte mensual", self.abrir_reporte_mensual, "Ctrl+R"))
        layout_lateral.addWidget(boton_menu("Transferir datos", self.abrir_transferir_datos))
        layout_lateral.addWidget(boton_menu("Importar Excel", self.abrir_importar_excel))
        layout_lateral.addWidget(boton_menu("Ayuda", self.abrir_ayuda, "Ctrl+H"))

        if self.rol == "admin":
            sep4 = QFrame()
            sep4.setFrameShape(QFrame.Shape.HLine)
            sep4.setStyleSheet("color: #333;")
            layout_lateral.addWidget(sep4)
            layout_lateral.addWidget(boton_menu("Gestionar usuarios", self.abrir_gestionar_usuarios))
            layout_lateral.addWidget(boton_menu("Historial", self.abrir_logs))

        layout_lateral.addStretch()

        # Botones de zoom y tema
        fila_zoom = QHBoxLayout()
        btn_zoom_menos = QPushButton("A-")
        btn_zoom_menos.setFixedSize(35, 28)
        btn_zoom_menos.setToolTip("Reducir zoom")
        btn_zoom_menos.clicked.connect(self._zoom_menos)

        btn_zoom_mas = QPushButton("A+")
        btn_zoom_mas.setFixedSize(35, 28)
        btn_zoom_mas.setToolTip("Aumentar zoom")
        btn_zoom_mas.clicked.connect(self._zoom_mas)

        fila_zoom.addWidget(btn_zoom_menos)
        fila_zoom.addWidget(btn_zoom_mas)
        layout_lateral.addLayout(fila_zoom)

        # Botón modo claro/oscuro
        self.btn_tema = QPushButton("☀ Modo claro")
        self.btn_tema.setStyleSheet(estilo_boton)
        self.btn_tema.clicked.connect(self._alternar_tema)
        layout_lateral.addWidget(self.btn_tema)

        nombre_usuario = obtener_nombre_usuario(usuario_id)
        usuario_label = QLabel(f"👤 {nombre_usuario}")
        usuario_label.setStyleSheet("color: #888; font-size: 11px; padding: 4px;")
        usuario_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout_lateral.addWidget(usuario_label)

        layout_principal.addWidget(panel_lateral)

        # PANEL DERECHO
        panel_derecho = QWidget()
        layout_derecho = QVBoxLayout(panel_derecho)
        layout_derecho.setContentsMargins(12, 12, 12, 12)
        layout_derecho.setSpacing(8)

        fila_superior = QHBoxLayout()

        self.selector_fecha = QDateEdit()
        self.selector_fecha.setDate(QDate.currentDate())
        self.selector_fecha.setCalendarPopup(True)

        boton_buscar = QPushButton("Buscar")
        boton_buscar.clicked.connect(self.cargar_tabla)

        self.filtro_turno = QComboBox()
        self.filtro_turno.addItems(["Todos los turnos", "diurno", "nocturno"])

        self.filtro_supervisor = QComboBox()
        self.filtro_supervisor.addItem("Todos los supervisores", None)
        for s in cargar_supervisores():
            self.filtro_supervisor.addItem(s[1], s[0])

        self.filtro_estado = QComboBox()
        self.filtro_estado.addItems([
            "Todos", "Pasaron los dos", "No pasó nadie",
            "No pasó día", "No pasó noche"
        ])

        boton_filtrar = QPushButton("Filtrar")
        boton_filtrar.clicked.connect(self.cargar_tabla)

        self.buscador = QLineEdit()
        self.buscador.setPlaceholderText("Buscar objetivo...")
        self.buscador.setFixedWidth(180)
        self.buscador.textChanged.connect(self.cargar_tabla)

        fila_superior.addWidget(QLabel("Fecha:"))
        fila_superior.addWidget(self.selector_fecha)
        fila_superior.addWidget(boton_buscar)
        fila_superior.addSpacing(20)
        fila_superior.addWidget(QLabel("Turno:"))
        fila_superior.addWidget(self.filtro_turno)
        fila_superior.addWidget(QLabel("Supervisor:"))
        fila_superior.addWidget(self.filtro_supervisor)
        fila_superior.addWidget(QLabel("Estado:"))
        fila_superior.addWidget(self.filtro_estado)
        fila_superior.addWidget(boton_filtrar)
        fila_superior.addSpacing(20)
        fila_superior.addWidget(QLabel("Buscar:"))
        fila_superior.addWidget(self.buscador)
        fila_superior.addStretch()

        layout_derecho.addLayout(fila_superior)

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
        layout_derecho.addWidget(self.tabla)

        layout_principal.addWidget(panel_derecho)
        self.setLayout(layout_principal)

        self.objetivos_actuales = []
        self.cargar_tabla()
        animar_tabla(self.tabla)

        # Shortcuts
        QShortcut(QKeySequence("Ctrl+P"), self).activated.connect(self.abrir_form_pasada)
        QShortcut(QKeySequence("Ctrl+O"), self).activated.connect(self.abrir_form_objetivo)
        QShortcut(QKeySequence("Ctrl+S"), self).activated.connect(self.abrir_form_supervisor)
        QShortcut(QKeySequence("Ctrl+T"), self).activated.connect(self.abrir_form_turno)
        QShortcut(QKeySequence("Ctrl+N"), self).activated.connect(self.abrir_notas)
        QShortcut(QKeySequence("Ctrl+R"), self).activated.connect(self.abrir_reporte_mensual)
        QShortcut(QKeySequence("Ctrl+B"), self).activated.connect(self.cargar_tabla)
        QShortcut(QKeySequence("Ctrl+H"), self).activated.connect(self.abrir_ayuda)
        QShortcut(QKeySequence("Ctrl+="), self).activated.connect(self._zoom_mas)
        QShortcut(QKeySequence("Ctrl+-"), self).activated.connect(self._zoom_menos)

        # Timer inactividad
        self.timer_inactividad = QTimer()
        self.timer_inactividad.setInterval(30 * 60 * 1000)
        self.timer_inactividad.timeout.connect(self.cerrar_por_inactividad)
        self.timer_inactividad.start()

    # =============================================================================
    # ZOOM
    # =============================================================================

    def _zoom_mas(self) -> None:
        """Aumenta el tamaño de fuente de toda la aplicación."""
        if self.zoom_nivel < 20:
            self.zoom_nivel += 1
            self._aplicar_zoom()

    def _zoom_menos(self) -> None:
        """Reduce el tamaño de fuente de toda la aplicación."""
        if self.zoom_nivel > 9:
            self.zoom_nivel -= 1
            self._aplicar_zoom()

    def _aplicar_zoom(self) -> None:
        """Aplica el nivel de zoom actual."""
        if self.app:
            stylesheet_actual = self.app.styleSheet()
            import re
            nuevo = re.sub(r'font-size: \d+px;', f'font-size: {self.zoom_nivel}px;', stylesheet_actual)
            self.app.setStyleSheet(nuevo)

    # =============================================================================
    # TEMA
    # =============================================================================

    def _alternar_tema(self) -> None:
        """Alterna entre modo claro y oscuro."""
        if self.alternar_tema_fn and self.app:
            self.alternar_tema_fn(self.app, self)

    # =============================================================================
    # EVENTOS
    # =============================================================================

    def event(self, evento):
        if evento.type() in (
            QEvent.Type.MouseMove,
            QEvent.Type.KeyPress,
            QEvent.Type.MouseButtonPress
        ):
            self.timer_inactividad.start()
        return super().event(evento)

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

    def cargar_tabla(self) -> None:
        """Carga los objetivos del día con pasadas diurnas y nocturnas separadas."""
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
        equipo_dia = obtener_equipo(fecha, "diurno")
        equipo_noche = obtener_equipo(fecha, "nocturno")

        filas = []
        for o in self.objetivos_actuales:
            if texto_busqueda and texto_busqueda not in o[1].lower():
                continue

            pasadas_dia = contar_pasadas(fecha, o[0], turno="diurno",
                supervisor_id=supervisor_id if turno == "diurno" else None)
            pasadas_noche = contar_pasadas(fecha, o[0], turno="nocturno",
                supervisor_id=supervisor_id if turno == "nocturno" else None)
            estado_detallado, color_hex = obtener_estado_detallado(fecha, o[0])

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
            self.form_pasada = FormPasada(fecha_inicial=self.selector_fecha.date().toString("yyyy-MM-dd"))
            self.form_pasada.destroyed.connect(self.cargar_tabla)
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

    def abrir_importar_excel(self):
        if not hasattr(self, 'importar_excel') or not self.importar_excel.isVisible():
            self.importar_excel = ImportarExcel()
            self.importar_excel.show()
        else:
            self.importar_excel.raise_()
            self.importar_excel.activateWindow()