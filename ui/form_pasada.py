# =============================================================================
# VESP Organizations - Sistema de Control de Objetivos
# Formulario para registrar pasadas
# =============================================================================

import sqlite3
from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QLabel,
    QPushButton,
    QComboBox,
    QDateEdit,
    QTimeEdit,
    QMessageBox
)
from PyQt6.QtCore import QDate, QTime, pyqtSignal

from models.turnos import registrar_turno
from ui.animaciones import animar_entrada
from database.db import DB_PATH
from services.validaciones import validar_pasada, ErrorValidacion
from services.cache import (
    obtener_objetivos_cache,
    obtener_supervisores_cache
)


# =============================================================================
# FUNCIONES AUXILIARES
# =============================================================================

def _cargar_objetivos(fecha: str = None) -> list:
    """Retorna objetivos activos según fecha."""
    objetivos = obtener_objetivos_cache(generar_si_falta=True)

    if not fecha:
        return objetivos

    objetivos_filtrados = []

    try:
        conexion = sqlite3.connect(DB_PATH)
        cursor = conexion.cursor()

        for obj in objetivos:
            obj_id = obj[0]

            cursor.execute("""
                SELECT fecha_inicio, fecha_fin
                FROM objetivos
                WHERE id = ?
            """, (obj_id,))

            resultado = cursor.fetchone()

            if resultado:
                fecha_inicio, fecha_fin = resultado

                if (
                    (not fecha_inicio or fecha >= fecha_inicio)
                    and
                    (fecha_fin is None or fecha <= fecha_fin)
                ):
                    objetivos_filtrados.append(obj)

        conexion.close()

    except Exception as e:
        print("Error cargando objetivos:", e)
        return objetivos

    return objetivos_filtrados


def _cargar_supervisores_del_turno(fecha: str, turno: str) -> list:
    """Retorna supervisores asignados al turno."""
    try:
        conexion = sqlite3.connect(DB_PATH)
        cursor = conexion.cursor()

        cursor.execute("""
            SELECT s.id, s.nombre
            FROM supervisores s
            WHERE s.id IN (
                SELECT supervisor1_id FROM equipos
                WHERE fecha = ? AND turno = ?

                UNION

                SELECT supervisor2_id FROM equipos
                WHERE fecha = ? AND turno = ?

                UNION

                SELECT supervisor3_id FROM equipos
                WHERE fecha = ? AND turno = ?
            )
            ORDER BY s.nombre
        """, (
            fecha, turno,
            fecha, turno,
            fecha, turno
        ))

        supervisores = cursor.fetchall()
        conexion.close()

        if supervisores:
            return supervisores

    except Exception as e:
        print("Error cargando supervisores:", e)

    return obtener_supervisores_cache(generar_si_falta=True)


# =============================================================================
# MEMORIA DEL ÚLTIMO TURNO
# =============================================================================

_ultimo_turno = "diurno"


# =============================================================================
# FORMULARIO
# =============================================================================

class FormPasada(QWidget):

    pasada_registrada = pyqtSignal()

    def __init__(self, fecha_inicial: str = None):
        super().__init__()

        global _ultimo_turno

        self.setWindowTitle("Registrar pasada")
        self.setGeometry(300, 300, 360, 320)

        layout = QVBoxLayout()

        # ---------------------------------------------------------------------
        # FECHA
        # ---------------------------------------------------------------------
        layout.addWidget(QLabel("Fecha:"))

        self.input_fecha = QDateEdit()
        self.input_fecha.setCalendarPopup(True)

        if fecha_inicial:
            self.input_fecha.setDate(
                QDate.fromString(fecha_inicial, "yyyy-MM-dd")
            )
        else:
            self.input_fecha.setDate(QDate.currentDate())

        layout.addWidget(self.input_fecha)

        # ---------------------------------------------------------------------
        # HORA
        # ---------------------------------------------------------------------
        layout.addWidget(QLabel("Hora:"))

        self.input_hora = QTimeEdit()
        self.input_hora.setDisplayFormat("HH:mm")
        self.input_hora.setTime(QTime.currentTime())

        layout.addWidget(self.input_hora)

        # ---------------------------------------------------------------------
        # TURNO
        # ---------------------------------------------------------------------
        layout.addWidget(QLabel("Turno:"))

        self.input_turno = QComboBox()
        self.input_turno.addItems(["diurno", "nocturno"])
        self.input_turno.setCurrentText(_ultimo_turno)

        layout.addWidget(self.input_turno)

        # ---------------------------------------------------------------------
        # OBJETIVO
        # ---------------------------------------------------------------------
        layout.addWidget(QLabel("Objetivo:"))

        self.input_objetivo = QComboBox()
        layout.addWidget(self.input_objetivo)

        # ---------------------------------------------------------------------
        # SUPERVISOR
        # ---------------------------------------------------------------------
        layout.addWidget(QLabel("Supervisor:"))

        self.input_supervisor = QComboBox()
        layout.addWidget(self.input_supervisor)

        # ---------------------------------------------------------------------
        # BOTÓN
        # ---------------------------------------------------------------------
        self.boton_guardar = QPushButton("Registrar pasada")
        self.boton_guardar.clicked.connect(self._guardar)

        layout.addWidget(self.boton_guardar)

        self.setLayout(layout)

        # ---------------------------------------------------------------------
        # EVENTOS
        # ---------------------------------------------------------------------
        self.input_fecha.dateChanged.connect(self._actualizar_listas)
        self.input_turno.currentTextChanged.connect(self._actualizar_listas)

        # ---------------------------------------------------------------------
        # CARGA INICIAL
        # ---------------------------------------------------------------------
        self._actualizar_listas()
        animar_entrada(self)

    # =========================================================================
    # ACTUALIZAR COMBOS
    # =========================================================================
    def _actualizar_listas(self):
        fecha = self.input_fecha.date().toString("yyyy-MM-dd")
        turno = self.input_turno.currentText()

        # Objetivos
        self.input_objetivo.clear()

        objetivos = _cargar_objetivos(fecha)

        for obj in objetivos:
            self.input_objetivo.addItem(obj[1], obj[0])

        # Supervisores
        self.input_supervisor.clear()

        supervisores = _cargar_supervisores_del_turno(fecha, turno)

        for sup in supervisores:
            self.input_supervisor.addItem(sup[1], sup[0])

    # =========================================================================
    # GUARDAR
    # =========================================================================
    def _guardar(self):
        global _ultimo_turno

        fecha = self.input_fecha.date().toString("yyyy-MM-dd")
        hora = self.input_hora.time().toString("HH:mm")
        turno = self.input_turno.currentText()

        objetivo_id = self.input_objetivo.currentData()
        supervisor_id = self.input_supervisor.currentData()

        objetivo_nombre = self.input_objetivo.currentText()
        supervisor_nombre = self.input_supervisor.currentText()

        if not objetivo_id or not supervisor_id:
            QMessageBox.warning(
                self,
                "Error",
                "Seleccioná un objetivo y un supervisor."
            )
            return

        try:
            validar_pasada(
                fecha,
                hora,
                turno,
                objetivo_id,
                supervisor_id
            )

        except ErrorValidacion as e:
            QMessageBox.warning(
                self,
                "Error de validación",
                str(e)
            )
            return

        try:
            registrar_turno(
                fecha=fecha,
                turno=turno,
                objetivo_id=objetivo_id,
                supervisor_id=supervisor_id,
                hora=hora
            )

        except Exception as e:
            QMessageBox.critical(
                self,
                "Error",
                str(e)
            )
            return

        _ultimo_turno = turno

        # Log
        try:
            from services.logger import registrar_accion
            from services.sesion import get_usuario_id

            registrar_accion(
                get_usuario_id(),
                f"Registró pasada - "
                f"Objetivo: {objetivo_nombre} | "
                f"Supervisor: {supervisor_nombre} | "
                f"Turno: {turno} | "
                f"Fecha: {fecha} | "
                f"Hora: {hora}"
            )

        except Exception:
            pass

        self.pasada_registrada.emit()

        QMessageBox.information(
            self,
            "Correcto",
            f"Pasada registrada en {objetivo_nombre}"
        )

        # Reiniciar hora actual
        self.input_hora.setTime(QTime.currentTime())