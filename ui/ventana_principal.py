import sys
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QTableWidget, QTableWidgetItem, QLabel,
    QPushButton, QDateEdit
)
from PyQt6.QtCore import QDate
from PyQt6.QtGui import QColor
from services.reportes import obtener_objetivos_del_dia
from ui.form_objetivo import FormObjetivo
from ui.form_supervisor import FormSupervisor
from ui.form_pasada import FormPasada
from ui.lista_objetivos import ListaObjetivos
from ui.lista_supervisores import ListaSupervisores
from models.objetivos import dar_de_baja_objetivo
import sqlite3


def contar_pasadas(fecha, objetivo_id):
    conexion = sqlite3.connect('seguridad.db')
    cursor = conexion.cursor()
    cursor.execute('''
        SELECT COUNT(*) FROM pasadas
        WHERE fecha = ? AND objetivo_id = ?
    ''', (fecha, objetivo_id))
    resultado = cursor.fetchone()[0]
    conexion.close()
    return resultado


class VentanaPrincipal(QWidget):

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Sistema de control de objetivos")
        self.setGeometry(100, 100, 900, 500)

        layout = QVBoxLayout()

        # Fila superior
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

        fila_superior.addWidget(QLabel("Fecha:"))
        fila_superior.addWidget(self.selector_fecha)
        fila_superior.addWidget(boton_buscar)
        fila_superior.addStretch()
        fila_superior.addWidget(boton_objetivo)
        fila_superior.addWidget(boton_supervisor)
        fila_superior.addWidget(boton_pasada)
        fila_superior.addWidget(boton_lista_objetivos)
        fila_superior.addWidget(boton_lista_supervisores)

        layout.addLayout(fila_superior)

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
        self.objetivos_actuales = obtener_objetivos_del_dia(fecha)

        self.tabla.setRowCount(len(self.objetivos_actuales))

        for i, o in enumerate(self.objetivos_actuales):
            pasadas = contar_pasadas(fecha, o[0])
            estado = "OK" if pasadas > 0 else "FALTA"

            self.tabla.setItem(i, 0, QTableWidgetItem(o[1]))
            self.tabla.setItem(i, 1, QTableWidgetItem(str(pasadas)))
            self.tabla.setItem(i, 2, QTableWidgetItem(estado))

            color = QColor("#90EE90") if pasadas > 0 else QColor("#FF6B6B")
            for col in range(3):
                self.tabla.item(i, col).setBackground(color)

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