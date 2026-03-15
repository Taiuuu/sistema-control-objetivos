import sys
from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout,
    QTableWidget, QTableWidgetItem, QLabel, QPushButton, QDateEdit
)
from PyQt6.QtCore import QDate
from PyQt6.QtGui import QColor
from services.reportes import obtener_objetivos_del_dia
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


class TablaDiaria(QWidget):

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Control diario de objetivos")
        self.setGeometry(200, 200, 700, 400)

        layout = QVBoxLayout()

        # Selector de fecha
        fecha_layout = QHBoxLayout()
        self.selector_fecha = QDateEdit()
        self.selector_fecha.setDate(QDate.currentDate())
        self.selector_fecha.setCalendarPopup(True)
        boton_buscar = QPushButton("Buscar")
        boton_buscar.clicked.connect(self.cargar_tabla)
        fecha_layout.addWidget(QLabel("Fecha:"))
        fecha_layout.addWidget(self.selector_fecha)
        fecha_layout.addWidget(boton_buscar)
        layout.addLayout(fecha_layout)

        # Tabla
        self.tabla = QTableWidget()
        self.tabla.setColumnCount(3)
        self.tabla.setHorizontalHeaderLabels(["Objetivo", "Pasadas", "Estado"])
        self.tabla.setColumnWidth(0, 300)
        self.tabla.setColumnWidth(1, 100)
        self.tabla.setColumnWidth(2, 100)
        layout.addWidget(self.tabla)

        self.setLayout(layout)
        self.cargar_tabla()

    def cargar_tabla(self):
        fecha = self.selector_fecha.date().toString("yyyy-MM-dd")
        objetivos = obtener_objetivos_del_dia(fecha)

        self.tabla.setRowCount(len(objetivos))

        for i, o in enumerate(objetivos):
            pasadas = contar_pasadas(fecha, o[0])
            estado = "OK" if pasadas > 0 else "FALTA"

            self.tabla.setItem(i, 0, QTableWidgetItem(o[1]))
            self.tabla.setItem(i, 1, QTableWidgetItem(str(pasadas)))
            self.tabla.setItem(i, 2, QTableWidgetItem(estado))

            # Colorear la fila
            color = QColor("#90EE90") if pasadas > 0 else QColor("#FF6B6B")
            for col in range(3):
                self.tabla.item(i, col).setBackground(color)


def iniciar_interfaz():
    app = QApplication(sys.argv)
    ventana = TablaDiaria()
    ventana.show()
    sys.exit(app.exec())