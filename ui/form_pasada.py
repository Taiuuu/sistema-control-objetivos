# =============================================================================
# VESP Organizations - Sistema de Control de Objetivos
# Formulario para registrar pasadas
# =============================================================================

import sqlite3
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel,
    QPushButton, QComboBox, QDateEdit, QTimeEdit, QMessageBox, QCheckBox
)
from PyQt6.QtCore import QDate, QTime
from models.turnos import registrar_turno, registrar_turno_ambos
from database.db import DB_PATH


def _cargar_objetivos() -> list:
    conexion = sqlite3.connect(DB_PATH)
    cursor = conexion.cursor()
    cursor.execute("SELECT id, nombre FROM objetivos WHERE fecha_fin IS NULL OR fecha_fin >= date('now')")
    resultado = cursor.fetchall()
    conexion.close()
    return resultado


def _cargar_supervisores_del_turno(fecha: str, turno: str) -> list:
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

    conexion = sqlite3.connect(DB_PATH)
    cursor = conexion.cursor()
    cursor.execute("SELECT id, nombre FROM supervisores")
    resultado = cursor.fetchall()
    conexion.close()
    return resultado


def _tiene_equipo_registrado(fecha: str, turno: str) -> bool:
    conexion = sqlite3.connect(DB_PATH)
    cursor = conexion.cursor()
    cursor.execute("SELECT COUNT(*) FROM equipos WHERE fecha = ? AND turno = ?", (fecha, turno))
    resultado = cursor.fetchone()[0]
    conexion.close()
    return resultado > 0


class FormPasada(QWidget):

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Registrar pasada")
        self.setGeometry(300, 300, 370, 420)

        layout = QVBoxLayout()

        layout.addWidget(QLabel("Fecha:"))
        self.input_fecha = QDateEdit()
        self.input_fecha.setDate(QDate.currentDate())
        self.input_fecha.setCalendarPopup(True)
        layout.addWidget(self.input_fecha)

        self.check_hora = QCheckBox("Registrar hora")
        self.check_hora.setChecked(True)
        self.check_hora.toggled.connect(self._toggle_hora)
        layout.addWidget(self.check_hora)

        self.input_hora = QTimeEdit()
        self.input_hora.setTime(QTime.currentTime())
        layout.addWidget(self.input_hora)

        layout.addWidget(QLabel("Turno:"))
        self.input_turno = QComboBox()
        self.input_turno.addItems(["dia", "noche"])
        self.input_turno.currentTextChanged.connect(self._actualizar_supervisores)
        layout.addWidget(self.input_turno)

        layout.addWidget(QLabel("Objetivo:"))
        self.input_objetivo = QComboBox()
        for o in _cargar_objetivos():
            self.input_objetivo.addItem(o[1], o[0])
        layout.addWidget(self.input_objetivo)

        layout.addWidget(QLabel("Supervisor:"))
        self.input_supervisor = QComboBox()
        layout.addWidget(self.input_supervisor)

        self.label_ambos_info = QLabel("")
        self.label_ambos_info.setStyleSheet("color: #888; font-size: 11px;")
        layout.addWidget(self.label_ambos_info)

        boton_guardar = QPushButton("Registrar pasada")
        boton_guardar.setFixedHeight(40)
        boton_guardar.clicked.connect(self._guardar)
        layout.addWidget(boton_guardar)

        self.setLayout(layout)
        self._actualizar_supervisores()
        self.input_fecha.dateChanged.connect(lambda: self._actualizar_supervisores())

    def _toggle_hora(self, checked: bool) -> None:
        self.input_hora.setVisible(checked)

    def _actualizar_supervisores(self) -> None:
        fecha = self.input_fecha.date().toString("yyyy-MM-dd")
        turno = self.input_turno.currentText()
        supervisores = _cargar_supervisores_del_turno(fecha, turno)
        tiene_equipo = _tiene_equipo_registrado(fecha, turno)

        self.input_supervisor.clear()
        self.label_ambos_info.setText("")

        if tiene_equipo and len(supervisores) == 2:
            self.input_supervisor.addItem(
                f"Ambos ({supervisores[0][1]} y {supervisores[1][1]})",
                ("ambos", supervisores[0][0], supervisores[1][0])
            )
            self.label_ambos_info.setText("↑ Seleccioná 'Ambos' si fueron juntos")

        for s in supervisores:
            self.input_supervisor.addItem(s[1], s[0])

    def _guardar(self) -> None:
        fecha = self.input_fecha.date().toString("yyyy-MM-dd")
        hora = self.input_hora.time().toString("HH:mm") if self.check_hora.isChecked() else None
        turno = self.input_turno.currentText()
        objetivo_id = self.input_objetivo.currentData()
        supervisor_data = self.input_supervisor.currentData()
        objetivo_nombre = self.input_objetivo.currentText()

        if not objetivo_id or supervisor_data is None:
            QMessageBox.warning(self, "Error", "Seleccioná un objetivo y un supervisor.")
            return

        from services.logger import registrar_accion
        from services.sesion import get_usuario_id

        hora_log = hora if hora else "sin hora"

        if isinstance(supervisor_data, tuple) and supervisor_data[0] == "ambos":
            _, sup1_id, sup2_id = supervisor_data
            registrar_turno_ambos(fecha, hora, turno, objetivo_id, sup1_id, sup2_id)
            registrar_accion(
                get_usuario_id(),
                f"Registró pasada (ambos) - Objetivo: {objetivo_nombre} | "
                f"Turno: {turno} | Fecha: {fecha} | Hora: {hora_log}"
            )
            QMessageBox.information(self, "Listo", "Pasada registrada para los dos supervisores.")
        else:
            supervisor_id = supervisor_data
            supervisor_nombre = self.input_supervisor.currentText()
            registrar_turno(fecha, hora, turno, objetivo_id, supervisor_id)
            registrar_accion(
                get_usuario_id(),
                f"Registró pasada - Objetivo: {objetivo_nombre} | "
                f"Supervisor: {supervisor_nombre} | Turno: {turno} | "
                f"Fecha: {fecha} | Hora: {hora_log}"
            )
            QMessageBox.information(self, "Listo", "Pasada registrada correctamente.")