# =============================================================================
# VESP Organizations - Sistema de Control de Objetivos
# Formulario para registrar el equipo de turno del día
# =============================================================================

import sqlite3
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel,
    QPushButton, QComboBox, QDateEdit, QMessageBox
)
from PyQt6.QtCore import QDate
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


def _guardar_equipo_turno(fecha: str, turno: str, sup1_id: int, sup2_id: int) -> None:
    """
    Registra los dos supervisores asignados a un turno en una fecha.
    Si ya existe un equipo para esa fecha y turno lo reemplaza.
    """
    conexion = sqlite3.connect(DB_PATH)
    cursor = conexion.cursor()
    cursor.execute("DELETE FROM equipos WHERE fecha = ? AND turno = ?", (fecha, turno))
    cursor.execute("""
        INSERT INTO equipos (fecha, turno, supervisor1_id, supervisor2_id)
        VALUES (?, ?, ?, ?)
    """, (fecha, turno, sup1_id, sup2_id))
    conexion.commit()
    conexion.close()


# =============================================================================
# FORMULARIO DE TURNO
# =============================================================================

class FormTurno(QWidget):

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Registrar turno")
        self.setGeometry(300, 300, 350, 280)

        layout = QVBoxLayout()

        # Fecha del turno
        layout.addWidget(QLabel("Fecha:"))
        self.input_fecha = QDateEdit()
        self.input_fecha.setDate(QDate.currentDate())
        self.input_fecha.setCalendarPopup(True)
        layout.addWidget(self.input_fecha)

        # Turno (día o noche)
        layout.addWidget(QLabel("Turno:"))
        self.input_turno = QComboBox()
        self.input_turno.addItems(["diurno", "nocturno"])
        layout.addWidget(self.input_turno)
        supervisores = _cargar_supervisores()

        # Primer supervisor del equipo
        layout.addWidget(QLabel("Supervisor 1:"))
        self.input_sup1 = QComboBox()
        for s in supervisores:
            self.input_sup1.addItem(s[1], s[0])
        layout.addWidget(self.input_sup1)

        # Segundo supervisor del equipo
        layout.addWidget(QLabel("Supervisor 2:"))
        self.input_sup2 = QComboBox()
        for s in supervisores:
            self.input_sup2.addItem(s[1], s[0])
        layout.addWidget(self.input_sup2)

        boton_guardar = QPushButton("Guardar turno")
        boton_guardar.clicked.connect(self._guardar)
        layout.addWidget(boton_guardar)

        self.setLayout(layout)

    def _guardar(self) -> None:
        """Valida y registra el equipo de turno en la base de datos."""
        fecha = self.input_fecha.date().toString("yyyy-MM-dd")
        turno = self.input_turno.currentText()
        sup1_id = self.input_sup1.currentData()
        sup2_id = self.input_sup2.currentData()

        if sup1_id == sup2_id:
            QMessageBox.warning(self, "Error", "Los dos supervisores deben ser distintos.")
            return

        _guardar_equipo_turno(fecha, turno, sup1_id, sup2_id)
        QMessageBox.information(self, "Listo", "Turno registrado correctamente.")
        self.close()