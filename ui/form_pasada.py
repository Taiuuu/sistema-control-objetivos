from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel,
    QPushButton, QComboBox, QDateEdit, QTimeEdit, QMessageBox
)
from PyQt6.QtCore import QDate, QTime
from models.turnos import registrar_turno
import sqlite3


def cargar_objetivos():
    conexion = sqlite3.connect('seguridad.db')
    cursor = conexion.cursor()
    cursor.execute('SELECT id, nombre FROM objetivos')
    resultado = cursor.fetchall()
    conexion.close()
    return resultado


def cargar_supervisores():
    conexion = sqlite3.connect('seguridad.db')
    cursor = conexion.cursor()
    cursor.execute('SELECT id, nombre FROM supervisores')
    resultado = cursor.fetchall()
    conexion.close()
    return resultado


class FormPasada(QWidget):

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Registrar pasada")
        self.setGeometry(300, 300, 350, 350)

        layout = QVBoxLayout()

        # Fecha
        layout.addWidget(QLabel("Fecha:"))
        self.input_fecha = QDateEdit()
        self.input_fecha.setDate(QDate.currentDate())
        self.input_fecha.setCalendarPopup(True)
        layout.addWidget(self.input_fecha)

        # Hora
        layout.addWidget(QLabel("Hora:"))
        self.input_hora = QTimeEdit()
        self.input_hora.setTime(QTime.currentTime())
        layout.addWidget(self.input_hora)

        # Turno
        layout.addWidget(QLabel("Turno:"))
        self.input_turno = QComboBox()
        self.input_turno.addItems(["dia", "noche"])
        layout.addWidget(self.input_turno)

        # Objetivo
        layout.addWidget(QLabel("Objetivo:"))
        self.input_objetivo = QComboBox()
        self.objetivos = cargar_objetivos()
        for o in self.objetivos:
            self.input_objetivo.addItem(o[1], o[0])
        layout.addWidget(self.input_objetivo)

        # Supervisor
        layout.addWidget(QLabel("Supervisor:"))
        self.input_supervisor = QComboBox()
        self.supervisores = cargar_supervisores()
        for s in self.supervisores:
            self.input_supervisor.addItem(s[1], s[0])
        layout.addWidget(self.input_supervisor)

        # Boton guardar
        boton_guardar = QPushButton("Registrar pasada")
        boton_guardar.clicked.connect(self.guardar)
        layout.addWidget(boton_guardar)

        self.setLayout(layout)

    def guardar(self):
        fecha = self.input_fecha.date().toString("yyyy-MM-dd")
        hora = self.input_hora.time().toString("HH:mm")
        turno = self.input_turno.currentText()
        objetivo_id = self.input_objetivo.currentData()
        supervisor_id = self.input_supervisor.currentData()
        objetivo_nombre = self.input_objetivo.currentText()
        supervisor_nombre = self.input_supervisor.currentText()

        registrar_turno(fecha, hora, turno, objetivo_id, supervisor_id)

        from services.logger import registrar_accion
        from services.sesion import get_usuario_id
        registrar_accion(get_usuario_id(), f"Registró pasada - Objetivo: {objetivo_nombre} | Supervisor: {supervisor_nombre} | Turno: {turno} | Fecha: {fecha} | Hora: {hora}")

        QMessageBox.information(self, "Listo", "Pasada registrada correctamente.")