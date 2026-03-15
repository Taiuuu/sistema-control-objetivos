from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QComboBox, QDateEdit, QMessageBox
)
from PyQt6.QtCore import QDate
import sqlite3


def cargar_supervisores():
    conexion = sqlite3.connect('seguridad.db')
    cursor = conexion.cursor()
    cursor.execute('SELECT id, nombre FROM supervisores')
    resultado = cursor.fetchall()
    conexion.close()
    return resultado


def guardar_turno(fecha, turno, sup1_id, sup2_id):
    conexion = sqlite3.connect('seguridad.db')
    cursor = conexion.cursor()

    cursor.execute('''
        DELETE FROM equipos WHERE fecha = ? AND turno = ?
    ''', (fecha, turno))

    cursor.execute('''
        INSERT INTO equipos (fecha, turno, supervisor1_id, supervisor2_id)
        VALUES (?, ?, ?, ?)
    ''', (fecha, turno, sup1_id, sup2_id))

    conexion.commit()
    conexion.close()


class FormTurno(QWidget):

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Registrar turno")
        self.setGeometry(300, 300, 350, 250)

        layout = QVBoxLayout()

        # Fecha
        layout.addWidget(QLabel("Fecha:"))
        self.input_fecha = QDateEdit()
        self.input_fecha.setDate(QDate.currentDate())
        self.input_fecha.setCalendarPopup(True)
        layout.addWidget(self.input_fecha)

        # Turno
        layout.addWidget(QLabel("Turno:"))
        self.input_turno = QComboBox()
        self.input_turno.addItems(["dia", "noche"])
        layout.addWidget(self.input_turno)

        supervisores = cargar_supervisores()

        # Supervisor 1
        layout.addWidget(QLabel("Supervisor 1:"))
        self.input_sup1 = QComboBox()
        for s in supervisores:
            self.input_sup1.addItem(s[1], s[0])
        layout.addWidget(self.input_sup1)

        # Supervisor 2
        layout.addWidget(QLabel("Supervisor 2:"))
        self.input_sup2 = QComboBox()
        for s in supervisores:
            self.input_sup2.addItem(s[1], s[0])
        layout.addWidget(self.input_sup2)

        # Boton guardar
        boton_guardar = QPushButton("Guardar turno")
        boton_guardar.clicked.connect(self.guardar)
        layout.addWidget(boton_guardar)

        self.setLayout(layout)

    def guardar(self):
        fecha = self.input_fecha.date().toString("yyyy-MM-dd")
        turno = self.input_turno.currentText()
        sup1_id = self.input_sup1.currentData()
        sup2_id = self.input_sup2.currentData()

        if sup1_id == sup2_id:
            QMessageBox.warning(self, "Error", "Los dos supervisores deben ser distintos.")
            return

        guardar_turno(fecha, turno, sup1_id, sup2_id)
        QMessageBox.information(self, "Listo", "Turno registrado correctamente.")
        self.close()