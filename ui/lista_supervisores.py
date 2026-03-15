from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QTableWidget,
    QTableWidgetItem, QPushButton, QMessageBox
)
import sqlite3


def cargar_supervisores():
    conexion = sqlite3.connect('seguridad.db')
    cursor = conexion.cursor()
    cursor.execute('SELECT id, nombre FROM supervisores')
    resultado = cursor.fetchall()
    conexion.close()
    return resultado


def eliminar_supervisor(supervisor_id):
    conexion = sqlite3.connect('seguridad.db')
    cursor = conexion.cursor()
    cursor.execute('DELETE FROM supervisores WHERE id = ?', (supervisor_id,))
    conexion.commit()
    conexion.close()


class ListaSupervisores(QWidget):

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Listado de supervisores")
        self.setGeometry(200, 200, 400, 300)

        layout = QVBoxLayout()

        self.tabla = QTableWidget()
        self.tabla.setColumnCount(2)
        self.tabla.setHorizontalHeaderLabels(["Nombre", "Acción"])
        self.tabla.setColumnWidth(0, 250)
        self.tabla.setColumnWidth(1, 120)
        layout.addWidget(self.tabla)

        self.setLayout(layout)
        self.cargar_tabla()

    def cargar_tabla(self):
        supervisores = cargar_supervisores()
        self.tabla.setRowCount(len(supervisores))

        for i, s in enumerate(supervisores):
            self.tabla.setItem(i, 0, QTableWidgetItem(s[1]))

            boton = QPushButton("Eliminar")
            boton.clicked.connect(lambda checked, sid=s[0]: self.eliminar(sid))
            self.tabla.setCellWidget(i, 1, boton)

    def eliminar(self, supervisor_id):
        confirmar = QMessageBox.question(
            self, "Confirmar",
            "¿Seguro que querés eliminar este supervisor?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if confirmar == QMessageBox.StandardButton.Yes:
            from services.logger import registrar_accion
            from services.sesion import get_usuario_id

            conexion = sqlite3.connect('seguridad.db')
            cursor = conexion.cursor()
            cursor.execute('SELECT nombre FROM supervisores WHERE id = ?', (supervisor_id,))
            info = cursor.fetchone()
            conexion.close()

            eliminar_supervisor(supervisor_id)

            if info:
                registrar_accion(get_usuario_id(), f"Eliminó supervisor: {info[0]}")

            self.cargar_tabla()