from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QTableWidget, QTableWidgetItem, QDateEdit, QPushButton
)
from PyQt6.QtCore import QDate
import sqlite3


def cargar_logs(fecha):
    conexion = sqlite3.connect('seguridad.db')
    cursor = conexion.cursor()

    cursor.execute('''
        SELECT l.fecha, l.hora, u.username, l.accion
        FROM logs l
        JOIN usuarios u ON l.usuario_id = u.id
        WHERE l.fecha = ?
        ORDER BY l.hora DESC
    ''', (fecha,))

    resultado = cursor.fetchall()
    conexion.close()
    return resultado


class VistaLogs(QWidget):

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Historial de acciones")
        self.setGeometry(200, 200, 650, 400)

        layout = QVBoxLayout()

        fila = QHBoxLayout()
        self.selector_fecha = QDateEdit()
        self.selector_fecha.setDate(QDate.currentDate())
        self.selector_fecha.setCalendarPopup(True)
        boton_buscar = QPushButton("Buscar")
        boton_buscar.clicked.connect(self.cargar_tabla)
        fila.addWidget(QLabel("Fecha:"))
        fila.addWidget(self.selector_fecha)
        fila.addWidget(boton_buscar)
        fila.addStretch()
        layout.addLayout(fila)

        self.tabla = QTableWidget()
        self.tabla.setColumnCount(4)
        self.tabla.setHorizontalHeaderLabels(["Fecha", "Hora", "Usuario", "Acción"])
        self.tabla.setColumnWidth(0, 100)
        self.tabla.setColumnWidth(1, 80)
        self.tabla.setColumnWidth(2, 120)
        self.tabla.setColumnWidth(3, 300)
        layout.addWidget(self.tabla)

        self.setLayout(layout)
        self.cargar_tabla()

    def cargar_tabla(self):
        fecha = self.selector_fecha.date().toString("yyyy-MM-dd")
        logs = cargar_logs(fecha)

        self.tabla.setRowCount(len(logs))
        for i, l in enumerate(logs):
            for j, valor in enumerate(l):
                self.tabla.setItem(i, j, QTableWidgetItem(str(valor)))