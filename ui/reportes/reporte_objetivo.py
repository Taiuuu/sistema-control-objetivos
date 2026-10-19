# =============================================================================
# VESP Organizations - Sistema de Control de Objetivos
# Reporte detallado por objetivo: día a día con cobertura diurna/nocturna
# =============================================================================

import sqlite3
import datetime
import calendar
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QTableWidget, QTableWidgetItem,
    QComboBox, QMessageBox, QScrollArea
)
from PyQt6.QtGui import QShortcut, QKeySequence
from PyQt6.QtWidgets import QHeaderView
from PyQt6.QtCore import Qt
from services.background_task import run_background_task
from services.reportes import clasificar_cumplimiento
from database.db import DB_PATH
from services.queries_tabla import (
    cargar_equipos_reportables,
    cargar_supervisores,
)
from services.reportes_unificados.consultas import crear_datos_para_exportar
from services.reportes_unificados.datos import COLUMNAS_OBJETIVO
from services.reportes_unificados.datos import crear_datos_objetivo
from services.reportes_unificados.objetivo import (
    calcular_reporte_objetivo as _calcular_reporte_objetivo_compartido,
)
from ui.components import StatusBadge
from ui.components.base import wrap_content_in_glass_card
from ui.reportes.acciones_exportacion import mostrar_dialogo_exportar


# =============================================================================
# CÁLCULO DEL REPORTE POR OBJETIVO
# =============================================================================

def calcular_reporte_objetivo(
    anio: int,
    mes: int,
    objetivo_id: int,
    supervisor_id: int | None = None,
    turno: str | None = None,
    estado_filtro: str = "Todos",
    supervisor_ids: list[int] | None = None,
    turnos: list[str] | None = None,
    equipo_id: int | None = None,
) -> dict:
    """Conserva la API de la pantalla y delega el cálculo al servicio común."""
    return _calcular_reporte_objetivo_compartido(
        anio,
        mes,
        objetivo_id,
        supervisor_id=supervisor_id,
        turno=turno,
        estado_filtro=estado_filtro,
        supervisor_ids=supervisor_ids,
        turnos=turnos,
        equipo_id=equipo_id,
        ruta_db=DB_PATH,
    )


def cargar_objetivos_del_mes(anio: int, mes: int) -> list:
    """
    Devuelve lista de (id, nombre) de objetivos activos en ese mes.
    """
    conexion = sqlite3.connect(DB_PATH)
    cursor = conexion.cursor()
    primer_dia = f"{anio}-{mes:02d}-01"
    ultimo_dia = f"{anio}-{mes:02d}-{calendar.monthrange(anio, mes)[1]:02d}"

    cursor.execute("""
        SELECT o.id, o.nombre FROM objetivos o
        WHERE EXISTS (
            SELECT 1 FROM objetivo_periodos p
            WHERE p.objetivo_id = o.id
              AND p.fecha_inicio <= ?
              AND (p.fecha_fin IS NULL OR p.fecha_fin >= ?)
        )
        OR (
            NOT EXISTS (SELECT 1 FROM objetivo_periodos p0 WHERE p0.objetivo_id = o.id)
            AND (o.fecha_fin IS NULL OR o.fecha_fin >= ?)
            AND (o.fecha_inicio IS NULL OR o.fecha_inicio <= ?)
        )
        ORDER BY o.nombre
    """, (ultimo_dia, primer_dia, primer_dia, ultimo_dia))
    objetivos = cursor.fetchall()
    conexion.close()
    return objetivos

# =============================================================================
# PANTALLA
# =============================================================================

class ReporteObjetivo(QWidget):

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Reporte por objetivo")
        self.resize(1000, 680)
        self.setMinimumSize(560, 360)
        self._objetivos = []   # lista de (id, nombre)
        self._datos = None     # último reporte generado

        layout = QVBoxLayout()

        # --- Fila de selección ---
        fila = QHBoxLayout()

        self.selector_mes = QComboBox()
        meses = ["Enero","Febrero","Marzo","Abril","Mayo","Junio",
                 "Julio","Agosto","Septiembre","Octubre","Noviembre","Diciembre"]
        for m in meses:
            self.selector_mes.addItem(m)
        self.selector_mes.setCurrentIndex(datetime.datetime.now().month - 1)
        self.selector_mes.currentIndexChanged.connect(self._actualizar_objetivos)

        self.selector_anio = QComboBox()
        anio_actual = datetime.datetime.now().year
        for a in range(anio_actual - 2, anio_actual + 2):
            self.selector_anio.addItem(str(a))
        self.selector_anio.setCurrentText(str(anio_actual))
        self.selector_anio.currentIndexChanged.connect(self._actualizar_objetivos)

        self.selector_objetivo = QComboBox()
        self.selector_objetivo.setMinimumWidth(200)

        self.selector_supervisor = QComboBox()
        self.selector_supervisor.addItem("Todos", None)
        for supervisor_id, nombre in cargar_supervisores():
            self.selector_supervisor.addItem(nombre, supervisor_id)
        self.selector_turno = QComboBox()
        self.selector_turno.addItems(["Todos", "diurno", "nocturno"])
        self.selector_estado = QComboBox()
        self.selector_estado.addItems(["Todos", "Completo", "Solo diurno", "Solo nocturno", "Sin control"])

        self.boton_generar = QPushButton("Generar reporte")
        self.boton_generar.setObjectName("PrimaryButton")
        self.boton_generar.clicked.connect(self._generar)

        self.boton_excel = QPushButton("Exportar Excel")
        self.boton_excel.clicked.connect(self._exportar_excel)
        self.boton_excel.setEnabled(False)

        self.boton_pdf = QPushButton("Exportar PDF")
        self.boton_pdf.clicked.connect(self._exportar_pdf)
        self.boton_pdf.setEnabled(False)

        fila.addWidget(QLabel("Mes:"))
        fila.addWidget(self.selector_mes)
        fila.addWidget(QLabel("Año:"))
        fila.addWidget(self.selector_anio)
        fila.addWidget(QLabel("Objetivo:"))
        fila.addWidget(self.selector_objetivo)
        fila.addWidget(QLabel("Supervisor:"))
        fila.addWidget(self.selector_supervisor)
        fila.addWidget(QLabel("Turno:"))
        fila.addWidget(self.selector_turno)
        fila.addWidget(QLabel("Estado:"))
        fila.addWidget(self.selector_estado)
        fila.addWidget(self.boton_generar)
        fila.addWidget(self.boton_excel)
        fila.addWidget(self.boton_pdf)
        controles = QWidget()
        controles.setLayout(fila)
        scroll_controles = QScrollArea()
        scroll_controles.setWidgetResizable(True)
        scroll_controles.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll_controles.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll_controles.setFixedHeight(62)
        scroll_controles.setWidget(controles)
        layout.addWidget(scroll_controles)

        self.estado_label = QLabel("Seleccioná un objetivo y generá el reporte.")
        layout.addWidget(self.estado_label)

        # --- Tabla ---
        self.tabla = QTableWidget()
        self.tabla.setColumnCount(5)
        self.tabla.setHorizontalHeaderLabels(
            ["Fecha", "Día", "Diurno", "Nocturno", "Estado"]
        )
        header = self.tabla.horizontalHeader()
        header.setMinimumSectionSize(58)
        header.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        for columna in (0, 1, 4):
            header.setSectionResizeMode(
                columna, QHeaderView.ResizeMode.ResizeToContents
            )
        self.tabla.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.tabla.setWordWrap(True)
        layout.addWidget(self.tabla)

        # --- Resumen ---
        self.resumen_label = StatusBadge("", "info")
        layout.addWidget(self.resumen_label)

        self.setLayout(layout)
        wrap_content_in_glass_card(self)
        self._actualizar_objetivos()
        QShortcut(QKeySequence("Ctrl+Enter"), self).activated.connect(self._generar)
        QShortcut(QKeySequence("Ctrl+E"), self).activated.connect(self._exportar_excel)

    # ------------------------------------------------------------------
    def _get_mes_anio(self):
        return (
            self.selector_mes.currentIndex() + 1,
            int(self.selector_anio.currentText())
        )

    def _actualizar_objetivos(self) -> None:
        mes, anio = self._get_mes_anio()
        self._objetivos = cargar_objetivos_del_mes(anio, mes)
        self.selector_objetivo.clear()
        for obj_id, nombre in self._objetivos:
            self.selector_objetivo.addItem(nombre, userData=obj_id)
        self.boton_excel.setEnabled(False)
        self.boton_pdf.setEnabled(False)
        self._datos = None

    def _set_controls_enabled(self, enabled: bool) -> None:
        self.selector_mes.setEnabled(enabled)
        self.selector_anio.setEnabled(enabled)
        self.selector_objetivo.setEnabled(enabled)
        self.selector_supervisor.setEnabled(enabled)
        self.selector_turno.setEnabled(enabled)
        self.selector_estado.setEnabled(enabled)
        self.boton_generar.setEnabled(enabled)

    def _get_objetivo_id(self) -> int | None:
        idx = self.selector_objetivo.currentIndex()
        if idx < 0:
            return None
        return self.selector_objetivo.itemData(idx)

    # ------------------------------------------------------------------
    def _generar(self) -> None:
        mes, anio = self._get_mes_anio()
        objetivo_id = self._get_objetivo_id()
        if objetivo_id is None:
            QMessageBox.warning(self, "Atención", "No hay objetivos disponibles para ese mes.")
            return

        self._set_controls_enabled(False)
        self.boton_excel.setEnabled(False)
        self.boton_pdf.setEnabled(False)
        self.estado_label.setText("Generando reporte...")

        turno = self.selector_turno.currentText()
        task = run_background_task(
            calcular_reporte_objetivo,
            anio,
            mes,
            objetivo_id,
            self.selector_supervisor.currentData(),
            None if turno == "Todos" else turno,
            self.selector_estado.currentText(),
        )
        task.signals.finished.connect(self._on_reporte_generado)
        task.signals.error.connect(self._on_error)

    def _on_reporte_generado(self, datos: dict) -> None:
        self._datos = datos
        dias = datos["dias"]
        r = datos["resumen"]

        self.tabla.setUpdatesEnabled(False)
        for row in range(self.tabla.rowCount()):
            badge = self.tabla.cellWidget(row, 4)
            if badge:
                self.tabla.removeCellWidget(row, 4)
                badge.deleteLater()
        self.tabla.clearContents()
        self.tabla.setRowCount(len(dias))

        for i, d in enumerate(dias):
            valores = [d["fecha"], d["dia_semana"], d["diurno"], d["nocturno"], d["estado"]]
            for col, val in enumerate(valores[:4]):
                self.tabla.setItem(i, col, QTableWidgetItem(val))
            estado_status = {
                "Completo": "ok",
                "Solo diurno": "warning",
                "Solo nocturno": "warning",
            }.get(d["estado"], "danger")
            self.tabla.setCellWidget(
                i, 4, StatusBadge(d["estado"], estado_status)
            )

        self.tabla.resizeRowsToContents()
        self.tabla.setUpdatesEnabled(True)

        self.resumen_label.setText(
            f"Días esperados: {r['dias_esperados']}  |  "
            f"Con diurno: {r['dias_con_dia']}  |  "
            f"Con nocturno: {r['dias_con_noche']}  |  "
            f"Sin control: {r['dias_sin_control']}  |  "
            f"Cumplimiento: {r['porcentaje']:.1f}%"
        )
        _, categoria = clasificar_cumplimiento(r["porcentaje"])
        self.resumen_label.set_status(
            {"verde": "ok", "amarillo": "warning", "rojo": "danger"}.get(
                categoria, "info"
            )
        )
        self.estado_label.setText(f"Reporte generado: {datos['nombre']}")
        self._set_controls_enabled(True)
        self.boton_excel.setEnabled(True)
        self.boton_pdf.setEnabled(True)

    def _on_error(self, mensaje: str) -> None:
        QMessageBox.critical(self, "Error", mensaje)
        self.estado_label.setText("Error al generar reporte")
        self._set_controls_enabled(True)

    # ------------------------------------------------------------------
    def _exportar_excel(self) -> None:
        self._abrir_dialogo_exportar("excel")

    def _exportar_pdf(self) -> None:
        self._abrir_dialogo_exportar("pdf")

    def _abrir_dialogo_exportar(self, formato: str) -> None:
        mes, anio = self._get_mes_anio()
        objetivo_id = self._get_objetivo_id()
        if objetivo_id is None:
            QMessageBox.warning(
                self, "Sin objetivos", "No hay un objetivo seleccionado para exportar."
            )
            return
        filtros_iniciales = {
            "objetivo_id": objetivo_id,
            "supervisor_id": self.selector_supervisor.currentData(),
            "turno": (
                None
                if self.selector_turno.currentText() == "Todos"
                else self.selector_turno.currentText()
            ),
            "estado": self.selector_estado.currentText(),
        }
        estado = self.selector_estado.currentText()

        def proveedor(seleccion: dict):
            inicio = seleccion["fecha_inicio"]
            fin = seleccion["fecha_fin"]
            if (
                inicio != inicio.replace(day=1)
                or fin.day != calendar.monthrange(fin.year, fin.month)[1]
                or (inicio.year, inicio.month) != (fin.year, fin.month)
            ):
                raise ValueError(
                    "El reporte por objetivo requiere el mes calendario completo."
                )
            objetivos_seleccionados = seleccion["objetivo_ids"]
            ids_objetivo = (
                [objetivo_id]
                if objetivos_seleccionados is None
                else objetivos_seleccionados
            )
            if len(ids_objetivo) != 1:
                raise ValueError(
                    "El reporte por objetivo debe incluir exactamente un objetivo."
                )
            supervisores = seleccion["supervisor_ids"]
            turnos = seleccion["turnos"]
            turno_unico = turnos[0] if len(turnos) == 1 else None
            reporte = calcular_reporte_objetivo(
                inicio.year,
                inicio.month,
                int(ids_objetivo[0]),
                supervisor_ids=[int(valor) for valor in supervisores],
                turnos=turnos,
                equipo_id=seleccion["equipo_id"],
                turno=turno_unico,
                estado_filtro=estado,
            )
            return crear_datos_objetivo(
                inicio.year,
                inicio.month,
                reporte,
                {
                    **filtros_iniciales,
                    "objetivo_id": int(ids_objetivo[0]),
                    "supervisor_ids": supervisores,
                    "turnos": turnos,
                    "equipo_id": seleccion["equipo_id"],
                    "agrupacion": seleccion["agrupacion"],
                },
            )

        mostrar_dialogo_exportar(
            self,
            "objetivo",
            datetime.date(anio, mes, 1),
            datetime.date(anio, mes, calendar.monthrange(anio, mes)[1]),
            proveedor,
            COLUMNAS_OBJETIVO,
            filtros_iniciales=filtros_iniciales,
            objetivos=self._objetivos,
            supervisores=cargar_supervisores(),
            equipos=cargar_equipos_reportables(),
            formato_inicial=formato,
        )
