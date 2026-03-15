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
    """Retorna todos los objetivos registrados."""
    conexion = sqlite3.connect('seguridad.db')
    cursor = conexion.cursor()
    cursor.execute("SELECT id, nombre FROM objetivos")
    resultado = cursor.fetchall()
    conexion.close()
    return resultado


def _cargar_supervisores_del_turno(fecha: str, turno: str) -> list:
    """
    Retorna los supervisores asignados al turno de una fecha dada.
    Si no hay equipo registrado para ese turno, retorna todos los supervisores.
    """
    conexion = sqlite3.connect('seguridad.db')
    cursor = conexion.cursor()

    cursor.execute("""
        SELECT s1.id, s1.nombre, s2.id, s2.nombre
        FROM equipos e
        JOIN supervisores s1 ON e.supervisor1_id = s1.id
        JOIN supervisores s2 ON e.supervisor2_id = s2.id
        WHERE e.fecha = ? AND e.turno = ?
    """, (fecha, turno))

    equipo = cursor.fetchone()
    conexion.close()

    if equipo:
        return [(equipo[0], equipo[1]), (equipo[2], equipo[3])]

    # Si no hay equipo registrado para ese turno retorna todos
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

        # Turno - al cambiar actualiza la lista de supervisores
        layout.addWidget(QLabel("Turno:"))
        self.input_turno = QComboBox()
        self.input_turno.addItems(["dia", "noche"])
        self.input_turno.currentTextChanged.connect(self._actualizar_supervisores)
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
        layout.addWidget(self.input_supervisor)

        boton_guardar = QPushButton("Registrar pasada")
        boton_guardar.clicked.connect(self._guardar)
        layout.addWidget(boton_guardar)

        self.setLayout(layout)

        # Cargar supervisores del turno inicial
        self._actualizar_supervisores()

        # Actualizar supervisores también al cambiar la fecha
        self.input_fecha.dateChanged.connect(lambda: self._actualizar_supervisores())

    def _actualizar_supervisores(self) -> None:
        """
        Actualiza la lista de supervisores según el turno y fecha seleccionados.
        Muestra solo los del equipo registrado para ese turno, o todos si no hay equipo.
        """
        fecha = self.input_fecha.date().toString("yyyy-MM-dd")
        turno = self.input_turno.currentText()
        supervisores = _cargar_supervisores_del_turno(fecha, turno)

        self.input_supervisor.clear()
        for s in supervisores:
            self.input_supervisor.addItem(s[1], s[0])

    def _guardar(self) -> None:
        """Registra la pasada en la base de datos y loguea la acción."""
        fecha = self.input_fecha.date().toString("yyyy-MM-dd")
        hora = self.input_hora.time().toString("HH:mm")
        turno = self.input_turno.currentText()
        objetivo_id = self.input_objetivo.currentData()
        supervisor_id = self.input_supervisor.currentData()
        objetivo_nombre = self.input_objetivo.currentText()
        supervisor_nombre = self.input_supervisor.currentText()

        if not objetivo_id or not supervisor_id:
            QMessageBox.warning(self, "Error", "Seleccioná un objetivo y un supervisor.")
            return

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