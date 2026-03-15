# =============================================================================
# VESP Organizations - Sistema de Control de Objetivos
# Pantalla de listado y gestión de supervisores
# =============================================================================

import sqlite3
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QTableWidget,
    QTableWidgetItem, QPushButton, QMessageBox
)
from database.db import DB_PATH

# =============================================================================
# CONSULTAS A BASE DE DATOS
# =============================================================================

def _cargar_supervisores() -> list:
    """Retorna todos los supervisores registrados."""
    conexion = sqlite3.connect(DB_PATH)
    cursor = conexion.cursor()
    cursor.execute("SELECT id, nombre FROM supervisores")
    resultado = cursor.fetchall()
    conexion.close()
    return resultado


def _eliminar_supervisor(supervisor_id: int) -> None:
    """Elimina un supervisor de la base de datos por su ID."""
    conexion = sqlite3.connect(DB_PATH)
    cursor = conexion.cursor()
    cursor.execute("DELETE FROM supervisores WHERE id = ?", (supervisor_id,))
    conexion.commit()
    conexion.close()


# =============================================================================
# PANTALLA DE LISTADO DE SUPERVISORES
# =============================================================================

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
        self._cargar_tabla()

    def _cargar_tabla(self) -> None:
        """Carga todos los supervisores en la tabla."""
        supervisores = _cargar_supervisores()
        self.tabla.setRowCount(len(supervisores))

        for i, s in enumerate(supervisores):
            self.tabla.setItem(i, 0, QTableWidgetItem(s[1]))

            boton = QPushButton("Eliminar")
            boton.clicked.connect(lambda checked, sid=s[0], nombre=s[1]: self._eliminar(sid, nombre))
            self.tabla.setCellWidget(i, 1, boton)

    def _eliminar(self, supervisor_id: int, nombre: str) -> None:
        """Elimina un supervisor tras confirmación del usuario."""
        confirmar = QMessageBox.question(
            self, "Confirmar",
            "¿Seguro que querés eliminar este supervisor?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if confirmar == QMessageBox.StandardButton.Yes:
            from services.logger import registrar_accion
            from services.sesion import get_usuario_id
            _eliminar_supervisor(supervisor_id)
            registrar_accion(get_usuario_id(), f"Eliminó supervisor: {nombre}")
            self._cargar_tabla()