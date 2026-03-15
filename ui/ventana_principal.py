from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QTableWidget, QTableWidgetItem, QLabel,
    QPushButton, QDateEdit, QComboBox
)
from PyQt6.QtCore import QDate
from PyQt6.QtGui import QColor
from services.reportes import obtener_objetivos_del_dia
from ui.form_objetivo import FormObjetivo
from ui.form_supervisor import FormSupervisor
from ui.form_pasada import FormPasada
from ui.lista_objetivos import ListaObjetivos
from ui.lista_supervisores import ListaSupervisores
from ui.reporte_mensual import ReporteMensual
from models.objetivos import dar_de_baja_objetivo
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

def cargar_supervisores():
    conexion = sqlite3.connect('seguridad.db')
    cursor = conexion.cursor()
    cursor.execute('SELECT id, nombre FROM supervisores')
    resultado = cursor.fetchall()
    conexion.close()
    return resultado


class VentanaPrincipal(QWidget):

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Sistema de control de objetivos")
        self.setGeometry(100, 100, 1000, 500)

        layout = QVBoxLayout()

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

        boton_lista_objetivos = QPushButton("Ver objetivos")
        boton_lista_objetivos.clicked.connect(self.abrir_lista_objetivos)

        boton_lista_supervisores = QPushButton("Ver supervisores")
        boton_lista_supervisores.clicked.connect(self.abrir_lista_supervisores)

        boton_reporte = QPushButton("Reporte mensual")
        boton_reporte.clicked.connect(self.abrir_reporte_mensual)

        fila_superior.addWidget(QLabel("Fecha:"))
        fila_superior.addWidget(self.selector_fecha)
        fila_superior.addWidget(boton_buscar)
        fila_superior.addStretch()
        fila_superior.addWidget(boton_objetivo)
        fila_superior.addWidget(boton_supervisor)
        fila_superior.addWidget(boton_pasada)
        fila_superior.addWidget(boton_lista_objetivos)
        fila_superior.addWidget(boton_lista_supervisores)
        fila_superior.addWidget(boton_reporte)

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
        self.tabla.setColumnCount(4)
        self.tabla.setHorizontalHeaderLabels(["Objetivo", "Pasadas", "Estado", "Dar de baja"])
        self.tabla.setColumnWidth(0, 300)
        self.tabla.setColumnWidth(1, 100)
        self.tabla.setColumnWidth(2, 100)
        self.tabla.setColumnWidth(3, 150)
        layout.addWidget(self.tabla)

        self.setLayout(layout)
        self.objetivos_actuales = []
        self.cargar_tabla()

    def cargar_tabla(self):
        fecha = self.selector_fecha.date().toString("yyyy-MM-dd")
        turno = self.filtro_turno.currentText()
        turno = None if turno == "Todos los turnos" else turno
        supervisor_id = self.filtro_supervisor.currentData()
        filtro_estado = self.filtro_estado.currentText()

        self.objetivos_actuales = obtener_objetivos_del_dia(fecha)

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
            self.tabla.setItem(i, 1, QTableWidgetItem(str(pasadas)))
            self.tabla.setItem(i, 2, QTableWidgetItem(estado_detallado))

            color = QColor(color_hex)
            for col in range(3):
                self.tabla.item(i, col).setBackground(color)
                self.tabla.item(i, col).setForeground(QColor("#000000"))

            boton_baja = QPushButton("Dar de baja")
            boton_baja.clicked.connect(lambda checked, obj_id=o[0]: self.dar_de_baja(obj_id))
            self.tabla.setCellWidget(i, 3, boton_baja)

    def dar_de_baja(self, objetivo_id):
        fecha = self.selector_fecha.date().toString("yyyy-MM-dd")
        dar_de_baja_objetivo(objetivo_id, fecha)
        self.cargar_tabla()

    def abrir_form_objetivo(self):
        self.form_objetivo = FormObjetivo()
        self.form_objetivo.destroyed.connect(self.cargar_tabla)
        self.form_objetivo.show()

    def abrir_form_supervisor(self):
        self.form_supervisor = FormSupervisor()
        self.form_supervisor.show()

    def abrir_form_pasada(self):
        self.form_pasada = FormPasada()
        self.form_pasada.destroyed.connect(self.cargar_tabla)
        self.form_pasada.show()

    def abrir_lista_objetivos(self):
        self.lista_objetivos = ListaObjetivos()
        self.lista_objetivos.show()

    def abrir_lista_supervisores(self):
        self.lista_supervisores = ListaSupervisores()
        self.lista_supervisores.show()

    def abrir_reporte_mensual(self):
        self.reporte_mensual = ReporteMensual()
        self.reporte_mensual.show()