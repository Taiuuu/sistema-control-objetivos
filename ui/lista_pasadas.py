from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QTableWidget, QTableWidgetItem, QPushButton,
    QDateEdit, QMessageBox
)
from PyQt6.QtCore import QDate
import sqlite3


def cargar_pasadas(fecha):
    conexion = sqlite3.connect('seguridad.db')
    cursor = conexion.cursor()

    cursor.execute('''
        SELECT p.id, p.hora, p.turno, o.nombre, s.nombre
        FROM pasadas p
        JOIN objetivos o ON p.objetivo_id = o.id
        JOIN supervisores s ON p.supervisor_id = s.id
        WHERE p.fecha = ?
        ORDER BY p.hora
    ''', (fecha,))

    resultado = cursor.fetchall()
    conexion.close()
    return resultado


def eliminar_pasada(pasada_id):
    conexion = sqlite3.connect('seguridad.db')
    cursor = conexion.cursor()
    cursor.execute('DELETE FROM pasadas WHERE id = ?', (pasada_id,))
    conexion.commit()
    conexion.close()


class ListaPasadas(QWidget):

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Pasadas del día")
        self.setGeometry(200, 200, 700, 400)

        layout = QVBoxLayout()

        # Selector de fecha
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

        # Tabla
        self.tabla = QTableWidget()
        self.tabla.setColumnCount(5)
        self.tabla.setHorizontalHeaderLabels([
            "Hora", "Turno", "Objetivo", "Supervisor", "Acción"
        ])
        self.tabla.setColumnWidth(0, 80)
        self.tabla.setColumnWidth(1, 80)
        self.tabla.setColumnWidth(2, 200)
        self.tabla.setColumnWidth(3, 150)
        self.tabla.setColumnWidth(4, 120)
        layout.addWidget(self.tabla)

        self.setLayout(layout)
        self.cargar_tabla()

    def cargar_tabla(self):
        fecha = self.selector_fecha.date().toString("yyyy-MM-dd")
        pasadas = cargar_pasadas(fecha)

        self.tabla.setRowCount(len(pasadas))
        self.ids = []

        for i, p in enumerate(pasadas):
            self.ids.append(p[0])
            self.tabla.setItem(i, 0, QTableWidgetItem(p[1]))
            self.tabla.setItem(i, 1, QTableWidgetItem(p[2]))
            self.tabla.setItem(i, 2, QTableWidgetItem(p[3]))
            self.tabla.setItem(i, 3, QTableWidgetItem(p[4]))

            boton = QPushButton("Eliminar")
            boton.clicked.connect(lambda checked, pid=p[0]: self.eliminar(pid))
            self.tabla.setCellWidget(i, 4, boton)

    def eliminar(self, pasada_id):
        confirmar = QMessageBox.question(
            self, "Confirmar",
            "¿Seguro que querés eliminar esta pasada?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if confirmar == QMessageBox.StandardButton.Yes:
            eliminar_pasada(pasada_id)
            self.cargar_tabla()