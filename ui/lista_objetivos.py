from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QTableWidget,
    QTableWidgetItem, QPushButton, QHBoxLayout, QMessageBox
)
from PyQt6.QtCore import QDate
from models.objetivos import dar_de_baja_objetivo
import sqlite3


def cargar_objetivos():
    conexion = sqlite3.connect('seguridad.db')
    cursor = conexion.cursor()
    cursor.execute('SELECT id, nombre, fecha_inicio, fecha_fin, dias_semana FROM objetivos')
    resultado = cursor.fetchall()
    conexion.close()
    return resultado


DIAS_MAP = {
    "1": "Lun", "2": "Mar", "3": "Mié",
    "4": "Jue", "5": "Vie", "6": "Sáb", "7": "Dom"
}


class ListaObjetivos(QWidget):

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Listado de objetivos")
        self.setGeometry(200, 200, 700, 400)

        layout = QVBoxLayout()

        self.tabla = QTableWidget()
        self.tabla.setColumnCount(5)
        self.tabla.setHorizontalHeaderLabels([
            "Nombre", "Inicio", "Fin", "Días", "Acción"
        ])
        self.tabla.setColumnWidth(0, 200)
        self.tabla.setColumnWidth(1, 100)
        self.tabla.setColumnWidth(2, 100)
        self.tabla.setColumnWidth(3, 150)
        self.tabla.setColumnWidth(4, 120)
        layout.addWidget(self.tabla)

        self.setLayout(layout)
        self.cargar_tabla()

    def cargar_tabla(self):
        objetivos = cargar_objetivos()
        self.tabla.setRowCount(len(objetivos))
        self.ids = []

        for i, o in enumerate(objetivos):
            self.ids.append(o[0])

            dias_texto = ", ".join([DIAS_MAP.get(d, d) for d in o[4].split(",")])
            fin_texto = o[3] if o[3] else "Activo"

            self.tabla.setItem(i, 0, QTableWidgetItem(o[1]))
            self.tabla.setItem(i, 1, QTableWidgetItem(o[2]))
            self.tabla.setItem(i, 2, QTableWidgetItem(fin_texto))
            self.tabla.setItem(i, 3, QTableWidgetItem(dias_texto))

            if not o[3]:
                boton = QPushButton("Dar de baja")
                boton.clicked.connect(lambda checked, obj_id=o[0]: self.dar_de_baja(obj_id))
                self.tabla.setCellWidget(i, 4, boton)

    def dar_de_baja(self, objetivo_id):
        fecha_hoy = QDate.currentDate().toString("yyyy-MM-dd")
        dar_de_baja_objetivo(objetivo_id, fecha_hoy)

        from services.logger import registrar_accion
        from services.sesion import get_usuario_id

        conexion = sqlite3.connect('seguridad.db')
        cursor = conexion.cursor()
        cursor.execute('SELECT nombre FROM objetivos WHERE id = ?', (objetivo_id,))
        info = cursor.fetchone()
        conexion.close()

        if info:
            registrar_accion(get_usuario_id(), f"Dio de baja objetivo: {info[0]} | Fecha: {fecha_hoy}")

        QMessageBox.information(self, "Listo", "Objetivo dado de baja correctamente.")
        self.cargar_tabla()