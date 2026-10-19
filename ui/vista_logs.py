# =============================================================================
# VESP Organizations - Sistema de Control de Objetivos
# Pantalla de historial de acciones del sistema (solo admin)
# =============================================================================

import sqlite3
import logging
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QTableWidget, QTableWidgetItem, QDateEdit, QPushButton, QHeaderView,
    QProgressBar,
)
from PyQt6.QtCore import QDate
from ui.components.calendar import configure_calendar_theme
from database.db import DB_PATH
from ui.components import GlassCard, PillButton
from ui.components.base import wrap_content_in_glass_card
from services.background_task import run_background_task
from ui.atajos import registrar_atajo
from ui.tabla_lotes import cargar_tabla_en_lotes

logger = logging.getLogger(__name__)

# =============================================================================
# CONSULTAS A BASE DE DATOS
# =============================================================================

def _cargar_logs(fecha: str) -> list:
    """
    Retorna todos los logs de una fecha dada,
    incluyendo el nombre de usuario que realizó cada acción.
    """
    conexion = sqlite3.connect(DB_PATH)
    try:
        cursor = conexion.cursor()
        cursor.execute("""
            SELECT l.fecha, l.hora, u.username, l.accion
            FROM logs l
            JOIN usuarios u ON l.usuario_id = u.id
            WHERE l.fecha = ?
            ORDER BY l.hora DESC
        """, (fecha,))
        return cursor.fetchall()
    finally:
        conexion.close()


# =============================================================================
# PANTALLA DE HISTORIAL DE ACCIONES
# =============================================================================

class VistaLogs(QWidget):

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Historial de acciones")
        self.resize(850, 520)
        self.setMinimumSize(500, 320)
        self._carga_id = 0
        self._tareas_carga = {}

        layout = QVBoxLayout()

        # Selector de fecha
        fila = QHBoxLayout()
        self.selector_fecha = QDateEdit()
        self.selector_fecha.setDate(QDate.currentDate())
        self.selector_fecha.setCalendarPopup(True)
        configure_calendar_theme(self.selector_fecha)
        boton_buscar = PillButton("Buscar", "primary")
        boton_buscar.setObjectName("PrimaryButton")
        boton_buscar.clicked.connect(self._cargar_tabla)
        fila.addWidget(QLabel("Fecha:"))
        fila.addWidget(self.selector_fecha)
        fila.addWidget(boton_buscar)
        fila.addStretch()
        layout.addLayout(fila)

        self.tabla = QTableWidget()
        self.tabla.setColumnCount(4)
        self.tabla.setHorizontalHeaderLabels(["Fecha", "Hora", "Usuario", "Acción"])
        header = self.tabla.horizontalHeader()
        header.setMinimumSectionSize(56)
        header.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        for columna in (0, 1):
            header.setSectionResizeMode(
                columna, QHeaderView.ResizeMode.ResizeToContents
            )
        self.tabla.setWordWrap(True)
        layout.addWidget(self.tabla)
        self.estado_carga = QLabel()
        layout.addWidget(self.estado_carga)
        self.barra_carga = QProgressBar()
        self.barra_carga.setRange(0, 0)
        self.barra_carga.setTextVisible(False)
        self.barra_carga.setMaximumHeight(5)
        self.barra_carga.hide()
        layout.addWidget(self.barra_carga)

        self.setLayout(layout)
        wrap_content_in_glass_card(self)
        registrar_atajo(self, "F5", self._cargar_tabla)
        self._cargar_tabla()

    def _cargar_tabla(self, *_args) -> None:
        """Carga los logs de la fecha seleccionada en la tabla."""
        self._cancelar_renderizado()
        self._carga_id += 1
        solicitud = self._carga_id
        fecha = self.selector_fecha.date().toString("yyyy-MM-dd")
        self.estado_carga.setText("Cargando historial…")
        self.barra_carga.show()
        self.tabla.setEnabled(False)
        tarea = run_background_task(_cargar_logs, fecha)
        self._tareas_carga[solicitud] = tarea
        tarea.signals.finished.connect(
            lambda logs, id_solicitud=solicitud:
                self._mostrar_logs(id_solicitud, logs)
        )
        tarea.signals.error.connect(
            lambda mensaje, id_solicitud=solicitud:
                self._error_carga(id_solicitud, mensaje)
        )

    def _mostrar_logs(self, solicitud: int, logs: list) -> None:
        self._tareas_carga.pop(solicitud, None)
        if solicitud != self._carga_id:
            return

        def poblar_fila(fila: int) -> None:
            registro = logs[fila]
            for columna, valor in enumerate(registro):
                item = QTableWidgetItem(str(valor))
                item.setToolTip(str(valor))
                self.tabla.setItem(
                    fila, columna, item
                )

        self._timer_render = cargar_tabla_en_lotes(
            self.tabla,
            len(logs),
            poblar_fila,
            lambda: self._finalizar_render(solicitud, logs),
        )

    def _finalizar_render(self, solicitud: int, logs: list) -> None:
        if solicitud != self._carga_id:
            return
        self._timer_render = None
        self.tabla.setEnabled(True)
        self.barra_carga.hide()
        self.estado_carga.setText(
            "" if logs else "Todavía no hay acciones para esta fecha."
        )

    def _cancelar_renderizado(self) -> None:
        timer = getattr(self, "_timer_render", None)
        if timer is not None:
            timer.stop()
            timer.deleteLater()
            self._timer_render = None

    def _error_carga(self, solicitud: int, mensaje: str) -> None:
        self._tareas_carga.pop(solicitud, None)
        if solicitud != self._carga_id:
            return
        self.tabla.setEnabled(True)
        self.barra_carga.hide()
        self.estado_carga.setText("No se pudo cargar el historial.")
        logger.error("No se pudo cargar el historial de acciones: %s", mensaje)