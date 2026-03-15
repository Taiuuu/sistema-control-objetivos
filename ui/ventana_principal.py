from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QTableWidget, QTableWidgetItem, QLabel,
    QPushButton, QDateEdit, QComboBox, QMessageBox
)
from PyQt6.QtCore import QDate, QTimer, QEvent
from PyQt6.QtGui import QColor, QPixmap, QIcon
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
from models.objetivos import dar_de_baja_objetivo
from services.backup import hacer_backup
from services.logger import registrar_accion
import sqlite3


def contar_pasadas(fecha, objetivo_id, turno=None, supervisor_id=None):
    conexion = sqlite3.connect('seguridad.db')
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


def obtener_estado_detallado(fecha, objetivo_id):
    pasadas_dia = contar_pasadas(fecha, objetivo_id, turno="dia")
    pasadas_noche = contar_pasadas(fecha, objetivo_id, turno="noche")

    if pasadas_dia > 0 and pasadas_noche > 0:
        return "Pasaron los dos", "#90EE90"
    elif pasadas_dia > 0 and pasadas_noche == 0:
        return "No pasó noche", "#FFD700"
    elif pasadas_dia == 0 and pasadas_noche > 0:
        return "No pasó día", "#FFD700"
    else:
        return "No pasó nadie", "#FF6B6B"


def obtener_equipo(fecha, turno):
    conexion = sqlite3.connect('seguridad.db')
    cursor = conexion.cursor()

    cursor.execute('''
        SELECT s1.nombre, s2.nombre
        FROM equipos e
        JOIN supervisores s1 ON e.supervisor1_id = s1.id
        JOIN supervisores s2 ON e.supervisor2_id = s2.id
        WHERE e.fecha = ? AND e.turno = ?
    ''', (fecha, turno))

    resultado = cursor.fetchone()
    conexion.close()

    if resultado:
        return f"{resultado[0]} y {resultado[1]}"
    return "-"


def cargar_supervisores():
    conexion = sqlite3.connect('seguridad.db')
    cursor = conexion.cursor()
    cursor.execute('SELECT id, nombre FROM supervisores')
    resultado = cursor.fetchall()
    conexion.close()
    return resultado


def obtener_nombre_usuario(usuario_id):
    conexion = sqlite3.connect('seguridad.db')
    cursor = conexion.cursor()
    cursor.execute('SELECT username FROM usuarios WHERE id = ?', (usuario_id,))
    resultado = cursor.fetchone()
    conexion.close()
    return resultado[0] if resultado else "Usuario"


class VentanaPrincipal(QWidget):

    def __init__(self, usuario_id=None, rol=None, on_login_exitoso=None):
        self.usuario_id = usuario_id
        self.rol = rol
        self.on_login_exitoso = on_login_exitoso
        super().__init__()
        self.setWindowTitle("VESP Control de Objetivos")
        self.setGeometry(100, 100, 1100, 550)
        self.setWindowIcon(QIcon("assets/vesp.png"))

        layout = QVBoxLayout()

        # Barra superior con logo y bienvenida
        barra_top = QHBoxLayout()

        logo = QLabel()
        pixmap = QPixmap("assets/vesp.png").scaled(45, 45, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation) if hasattr(self, '_qt_imported') else QPixmap("assets/vesp.png")
        from PyQt6.QtCore import Qt
        pixmap = QPixmap("assets/vesp.png").scaled(45, 45, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
        logo.setPixmap(pixmap)

        titulo = QLabel("V.E.S.P Organizations")
        titulo.setStyleSheet("font-size: 16px; font-weight: bold; color: #4CAF50;")

        nombre_usuario = obtener_nombre_usuario(usuario_id)
        bienvenida = QLabel(f"Bienvenido, {nombre_usuario}")
        bienvenida.setStyleSheet("font-size: 12px; color: #888;")

        barra_top.addWidget(logo)
        barra_top.addWidget(titulo)
        barra_top.addStretch()
        barra_top.addWidget(bienvenida)

        layout.addLayout(barra_top)

        # Fila superior con fecha y botones
        fila_superior = QHBoxLayout()

        self.selector_fecha = QDateEdit()
        self.selector_fecha.setDate(QDate.currentDate())
        self.selector_fecha.setCalendarPopup(True)

        boton_buscar = QPushButton("Buscar")
        boton_buscar.clicked.connect(self.cargar_tabla)

        boton_objetivo = QPushButton("Agregar objetivo")
        boton_objetivo.clicked.connect(self.abrir_form_objetivo)

        boton_supervisor = QPushButton("Agregar supervisor")
        boton_supervisor.clicked.connect(self.abrir_form_supervisor)

        boton_pasada = QPushButton("Registrar pasada")
        boton_pasada.clicked.connect(self.abrir_form_pasada)

        boton_turno = QPushButton("Registrar turno")
        boton_turno.clicked.connect(self.abrir_form_turno)

        boton_lista_objetivos = QPushButton("Ver objetivos")
        boton_lista_objetivos.clicked.connect(self.abrir_lista_objetivos)

        boton_lista_supervisores = QPushButton("Ver supervisores")
        boton_lista_supervisores.clicked.connect(self.abrir_lista_supervisores)

        boton_lista_pasadas = QPushButton("Ver pasadas")
        boton_lista_pasadas.clicked.connect(self.abrir_lista_pasadas)

        boton_notas = QPushButton("Notas del día")
        boton_notas.clicked.connect(self.abrir_notas)

        boton_reporte = QPushButton("Reporte mensual")
        boton_reporte.clicked.connect(self.abrir_reporte_mensual)

        fila_superior.addWidget(QLabel("Fecha:"))
        fila_superior.addWidget(self.selector_fecha)
        fila_superior.addWidget(boton_buscar)
        fila_superior.addStretch()
        fila_superior.addWidget(boton_objetivo)
        fila_superior.addWidget(boton_supervisor)
        fila_superior.addWidget(boton_pasada)
        fila_superior.addWidget(boton_turno)
        fila_superior.addWidget(boton_lista_objetivos)
        fila_superior.addWidget(boton_lista_supervisores)
        fila_superior.addWidget(boton_lista_pasadas)
        fila_superior.addWidget(boton_notas)
        fila_superior.addWidget(boton_reporte)

        if self.rol == "admin":
            boton_usuarios = QPushButton("Gestionar usuarios")
            boton_usuarios.clicked.connect(self.abrir_gestionar_usuarios)
            fila_superior.addWidget(boton_usuarios)

            boton_logs = QPushButton("Historial")
            boton_logs.clicked.connect(self.abrir_logs)
            fila_superior.addWidget(boton_logs)

        layout.addLayout(fila_superior)

        # Fila de filtros
        fila_filtros = QHBoxLayout()

        self.filtro_turno = QComboBox()
        self.filtro_turno.addItems(["Todos los turnos", "dia", "noche"])

        self.filtro_supervisor = QComboBox()
        self.filtro_supervisor.addItem("Todos los supervisores", None)
        for s in cargar_supervisores():
            self.filtro_supervisor.addItem(s[1], s[0])

        self.filtro_estado = QComboBox()
        self.filtro_estado.addItems(["Todos", "OK", "FALTA"])

        boton_filtrar = QPushButton("Filtrar")
        boton_filtrar.clicked.connect(self.cargar_tabla)

        fila_filtros.addWidget(QLabel("Turno:"))
        fila_filtros.addWidget(self.filtro_turno)
        fila_filtros.addWidget(QLabel("Supervisor:"))
        fila_filtros.addWidget(self.filtro_supervisor)
        fila_filtros.addWidget(QLabel("Estado:"))
        fila_filtros.addWidget(self.filtro_estado)
        fila_filtros.addWidget(boton_filtrar)
        fila_filtros.addStretch()

        layout.addLayout(fila_filtros)

        # Tabla
        self.tabla = QTableWidget()
        self.tabla.setColumnCount(6)
        self.tabla.setHorizontalHeaderLabels([
            "Objetivo", "Turno día", "Turno noche", "Pasadas", "Estado", "Dar de baja"
        ])
        self.tabla.setColumnWidth(0, 200)
        self.tabla.setColumnWidth(1, 150)
        self.tabla.setColumnWidth(2, 150)
        self.tabla.setColumnWidth(3, 80)
        self.tabla.setColumnWidth(4, 130)
        self.tabla.setColumnWidth(5, 120)
        layout.addWidget(self.tabla)

        self.setLayout(layout)
        self.objetivos_actuales = []
        self.cargar_tabla()

        # Timer inactividad 15 minutos
        self.timer_inactividad = QTimer()
        self.timer_inactividad.setInterval(15 * 60 * 1000)
        self.timer_inactividad.timeout.connect(self.cerrar_por_inactividad)
        self.timer_inactividad.start()

    def event(self, evento):
        if evento.type() in (
            QEvent.Type.MouseMove,
            QEvent.Type.KeyPress,
            QEvent.Type.MouseButtonPress
        ):
            self.timer_inactividad.start()
        return super().event(evento)

    def cerrar_por_inactividad(self):
        hacer_backup()
        QMessageBox.information(
            self,
            "Sesión cerrada",
            "La sesión se cerró por inactividad. Se realizó un backup automático."
        )
        registrar_accion(self.usuario_id, "Sesión cerrada por inactividad")
        self.close()
        from ui.login import LoginWindow
        self.login = LoginWindow(self.on_login_exitoso)
        self.login.show()

    def closeEvent(self, evento):
        confirmar = QMessageBox.question(
            self,
            "Confirmar salida",
            "¿Seguro que querés cerrar el sistema?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if confirmar == QMessageBox.StandardButton.Yes:
            registrar_accion(self.usuario_id, "Cerró el sistema")
            evento.accept()
        else:
            evento.ignore()

    def cargar_tabla(self):
        fecha = self.selector_fecha.date().toString("yyyy-MM-dd")
        turno = self.filtro_turno.currentText()
        turno = None if turno == "Todos los turnos" else turno
        supervisor_id = self.filtro_supervisor.currentData()
        filtro_estado = self.filtro_estado.currentText()

        self.objetivos_actuales = obtener_objetivos_del_dia(fecha)

        equipo_dia = obtener_equipo(fecha, "dia")
        equipo_noche = obtener_equipo(fecha, "noche")

        filas = []
        for o in self.objetivos_actuales:
            pasadas = contar_pasadas(fecha, o[0], turno, supervisor_id)
            estado_detallado, color_hex = obtener_estado_detallado(fecha, o[0])

            if filtro_estado == "OK" and estado_detallado != "Pasaron los dos":
                continue
            if filtro_estado == "FALTA" and estado_detallado == "Pasaron los dos":
                continue

            filas.append((o, pasadas, estado_detallado, color_hex))

        self.tabla.setRowCount(len(filas))

        for i, (o, pasadas, estado_detallado, color_hex) in enumerate(filas):
            self.tabla.setItem(i, 0, QTableWidgetItem(o[1]))
            self.tabla.setItem(i, 1, QTableWidgetItem(equipo_dia))
            self.tabla.setItem(i, 2, QTableWidgetItem(equipo_noche))
            self.tabla.setItem(i, 3, QTableWidgetItem(str(pasadas)))
            self.tabla.setItem(i, 4, QTableWidgetItem(estado_detallado))

            color = QColor(color_hex)
            for col in range(5):
                self.tabla.item(i, col).setBackground(color)
                self.tabla.item(i, col).setForeground(QColor("#000000"))

            boton_baja = QPushButton("Dar de baja")
            boton_baja.clicked.connect(lambda checked, obj_id=o[0]: self.dar_de_baja(obj_id))
            self.tabla.setCellWidget(i, 5, boton_baja)

    def dar_de_baja(self, objetivo_id):
        fecha = self.selector_fecha.date().toString("yyyy-MM-dd")
        dar_de_baja_objetivo(objetivo_id, fecha)
        registrar_accion(self.usuario_id, f"Dio de baja objetivo id={objetivo_id}")
        self.cargar_tabla()

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
            self.form_pasada = FormPasada()
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