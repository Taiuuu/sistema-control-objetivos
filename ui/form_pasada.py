# =============================================================================
# VESP Organizations - Sistema de Control de Objetivos
# Formulario para registrar pasadas
# =============================================================================

import sqlite3
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel,
    QPushButton, QComboBox, QDateEdit, QTimeEdit, QMessageBox
)
from PyQt6.QtCore import QDate, QTime
from models.turnos import registrar_turno


# =============================================================================
# CONSULTAS A BASE DE DATOS
# =============================================================================

def _cargar_objetivos() -> list:
    """Retorna todos los objetivos activos (sin fecha de baja)."""
    conexion = sqlite3.connect('seguridad.db')
    cursor = conexion.cursor()
    cursor.execute("SELECT id, nombre FROM objetivos")
    resultado = cursor.fetchall()
    conexion.close()
    return resultado


def _cargar_supervisores() -> list:
    """Retorna todos los supervisores registrados."""
    conexion = sqlite3.connect('seguridad.db')
    cursor = conexion.cursor()
    cursor.execute("SELECT id, nombre FROM supervisores")
    resultado = cursor.fetchall()
    conexion.close()
    return resultado


# =============================================================================
# FORMULARIO DE PASADA
# =============================================================================

class FormPasada(QWidget):

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Registrar pasada")
        self.setGeometry(300, 300, 350, 350)

        layout = QVBoxLayout()

        # Fecha de la pasada
        layout.addWidget(QLabel("Fecha:"))
        self.input_fecha = QDateEdit()
        self.input_fecha.setDate(QDate.currentDate())
        self.input_fecha.setCalendarPopup(True)
        layout.addWidget(self.input_fecha)

        # Hora de la pasada
        layout.addWidget(QLabel("Hora:"))
        self.input_hora = QTimeEdit()
        self.input_hora.setTime(QTime.currentTime())
        layout.addWidget(self.input_hora)

        # Turno (día o noche)
        layout.addWidget(QLabel("Turno:"))
        self.input_turno = QComboBox()
        self.input_turno.addItems(["dia", "noche"])
        layout.addWidget(self.input_turno)

        # Objetivo controlado
        layout.addWidget(QLabel("Objetivo:"))
        self.input_objetivo = QComboBox()
        for o in _cargar_objetivos():
            self.input_objetivo.addItem(o[1], o[0])
        layout.addWidget(self.input_objetivo)

        # Supervisor que realizó la pasada
        layout.addWidget(QLabel("Supervisor:"))
        self.input_supervisor = QComboBox()
        for s in _cargar_supervisores():
            self.input_supervisor.addItem(s[1], s[0])
        layout.addWidget(self.input_supervisor)

        boton_guardar = QPushButton("Registrar pasada")
        boton_guardar.clicked.connect(self._guardar)
        layout.addWidget(boton_guardar)

        self.setLayout(layout)

    def _guardar(self) -> None:
        """Registra la pasada en la base de datos y loguea la acción."""
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
        registrar_accion(
            get_usuario_id(),
            f"Registró pasada - Objetivo: {objetivo_nombre} | "
            f"Supervisor: {supervisor_nombre} | Turno: {turno} | "
            f"Fecha: {fecha} | Hora: {hora}"
        )

        QMessageBox.information(self, "Listo", "Pasada registrada correctamente.")