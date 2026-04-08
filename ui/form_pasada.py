# =============================================================================
# VESP Organizations - Sistema de Control de Objetivos
# Formulario para registrar pasadas
# =============================================================================

import sqlite3
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel,
    QPushButton, QComboBox, QDateEdit, QTimeEdit, QMessageBox
)
from PyQt6.QtCore import QDate, QTime, pyqtSignal
from models.turnos import registrar_turno
from ui.animaciones import animar_entrada
from database.db import DB_PATH
from services.validaciones import validar_pasada, ErrorValidacion
from services.cache import obtener_objetivos_cache, obtener_supervisores_cache


def _cargar_objetivos() -> list:
    """Retorna todos los objetivos registrados (usa caché)."""
    return obtener_objetivos_cache(generar_si_falta=True)


def _cargar_supervisores_del_turno(fecha: str, turno: str) -> list:
    """
    Retorna los supervisores del equipo asignado al turno de esa fecha.
    Si no hay equipo registrado retorna todos los supervisores (usa caché).
    """
    try:
        conexion = sqlite3.connect(DB_PATH)
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
    except:
        pass

    # Usar caché para supervisores
    supervisores = obtener_supervisores_cache(generar_si_falta=True)
    return supervisores


# Turno recordado entre registros
_ultimo_turno = "diurno"


class FormPasada(QWidget):

    # Señal que se emite cuando se registra una pasada exitosamente
    pasada_registrada = pyqtSignal()

    def __init__(self, fecha_inicial: str = None):
        super().__init__()
        global _ultimo_turno
        self.setWindowTitle("Registrar pasada")
        self.setGeometry(300, 300, 350, 320)

        layout = QVBoxLayout()

        # Fecha
        layout.addWidget(QLabel("Fecha:"))
        self.input_fecha = QDateEdit()
        if fecha_inicial:
            self.input_fecha.setDate(QDate.fromString(fecha_inicial, "yyyy-MM-dd"))
        else:
            self.input_fecha.setDate(QDate.currentDate())
        self.input_fecha.setCalendarPopup(True)
        layout.addWidget(self.input_fecha)

        # Hora
        layout.addWidget(QLabel("Hora:"))
        self.input_hora = QTimeEdit()
        self.input_hora.setTime(QTime.currentTime())
        layout.addWidget(self.input_hora)

        # Turno - mantiene el último usado
        layout.addWidget(QLabel("Turno:"))
        self.input_turno = QComboBox()
        self.input_turno.addItems(["diurno", "nocturno"])
        self.input_turno.setCurrentText(_ultimo_turno)
        self.input_turno.currentTextChanged.connect(self._actualizar_supervisores)
        layout.addWidget(self.input_turno)

        # Objetivo
        layout.addWidget(QLabel("Objetivo:"))
        self.input_objetivo = QComboBox()
        for o in _cargar_objetivos():
            self.input_objetivo.addItem(o[1], o[0])
        layout.addWidget(self.input_objetivo)

        # Supervisor filtrado por turno
        layout.addWidget(QLabel("Supervisor:"))
        self.input_supervisor = QComboBox()
        layout.addWidget(self.input_supervisor)

        boton_guardar = QPushButton("Registrar pasada")
        boton_guardar.clicked.connect(self._guardar)
        layout.addWidget(boton_guardar)

        self.setLayout(layout)
        animar_entrada(self)
        self._actualizar_supervisores()
        self.input_fecha.dateChanged.connect(lambda: self._actualizar_supervisores())

    def _actualizar_supervisores(self) -> None:
        """Actualiza la lista de supervisores según el turno y fecha seleccionados."""
        fecha = self.input_fecha.date().toString("yyyy-MM-dd")
        turno = self.input_turno.currentText()
        supervisores = _cargar_supervisores_del_turno(fecha, turno)
        self.input_supervisor.clear()
        for s in supervisores:
            self.input_supervisor.addItem(s[1], s[0])

    def _guardar(self) -> None:
        """Registra la pasada, actualiza la tabla principal y mantiene el formulario abierto."""
        global _ultimo_turno

        fecha = self.input_fecha.date().toString("yyyy-MM-dd")
        hora = self.input_hora.time().toString("HH:mm:ss")
        turno = self.input_turno.currentText()
        objetivo_id = self.input_objetivo.currentData()
        supervisor_id = self.input_supervisor.currentData()
        objetivo_nombre = self.input_objetivo.currentText()
        supervisor_nombre = self.input_supervisor.currentText()

        if not objetivo_id or not supervisor_id:
            QMessageBox.warning(self, "Error", "Seleccioná un objetivo y un supervisor.")
            return

        try:
            validar_pasada(fecha, hora, turno, objetivo_id, supervisor_id)
        except ErrorValidacion as e:
            QMessageBox.warning(self, "Error de Validación", str(e))
            return

        registrar_turno(fecha, hora, turno, objetivo_id, supervisor_id)

        # Recordar el turno para la próxima pasada
        _ultimo_turno = turno

        from services.logger import registrar_accion
        from services.sesion import get_usuario_id
        registrar_accion(
            get_usuario_id(),
            f"Registró pasada - Objetivo: {objetivo_nombre} | "
            f"Supervisor: {supervisor_nombre} | Turno: {turno} | "
            f"Fecha: {fecha} | Hora: {hora}"
        )

        # Emitir señal para actualizar la tabla principal
        self.pasada_registrada.emit()

        QMessageBox.information(self, "Listo", f"Pasada de {objetivo_nombre} registrada.")

        # Actualizar hora para la siguiente pasada
        self.input_hora.setTime(QTime.currentTime())