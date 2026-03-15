# =============================================================================
# VESP Organizations - Sistema de Control de Objetivos
# Pantalla de historial de acciones del sistema (solo admin)
# =============================================================================

import sqlite3
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QTableWidget, QTableWidgetItem, QDateEdit, QPushButton
)
from PyQt6.QtCore import QDate
from database.db import DB_PATH

# =============================================================================
# CONSULTAS A BASE DE DATOS
# =============================================================================

def _cargar_logs(fecha: str) -> list:
    """
    Retorna todos los logs de una fecha dada,
    incluyendo el nombre de usuario que realizó cada acción.
    """
    conexion = sqlite3.connect(DB_PATH)
    cursor = conexion.cursor()
    cursor.execute("""
        SELECT l.fecha, l.hora, u.username, l.accion
        FROM logs l
        JOIN usuarios u ON l.usuario_id = u.id
        WHERE l.fecha = ?
        ORDER BY l.hora DESC
    """, (fecha,))
    resultado = cursor.fetchall()
    conexion.close()
    return resultado


# =============================================================================
# PANTALLA DE HISTORIAL DE ACCIONES
# =============================================================================

class VistaLogs(QWidget):

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Historial de acciones")
        self.setGeometry(200, 200, 700, 400)

        layout = QVBoxLayout()

        # Selector de fecha
        fila = QHBoxLayout()
        self.selector_fecha = QDateEdit()
        self.selector_fecha.setDate(QDate.currentDate())
        self.selector_fecha.setCalendarPopup(True)
        boton_buscar = QPushButton("Buscar")
        boton_buscar.clicked.connect(self._cargar_tabla)
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
        self.tabla.setColumnWidth(3, 350)
        layout.addWidget(self.tabla)

        self.setLayout(layout)
        self._cargar_tabla()

    def _cargar_tabla(self) -> None:
        """Carga los logs de la fecha seleccionada en la tabla."""
        fecha = self.selector_fecha.date().toString("yyyy-MM-dd")
        logs = _cargar_logs(fecha)

        self.tabla.setRowCount(len(logs))
        for i, l in enumerate(logs):
            for j, valor in enumerate(l):
                self.tabla.setItem(i, j, QTableWidgetItem(str(valor)))