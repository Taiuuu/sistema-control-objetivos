# =============================================================================
# VESP Organizations - Sistema de Control de Objetivos
# Pantalla de reporte mensual de cumplimiento por objetivo
# =============================================================================

import datetime
import calendar
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QTableWidget, QTableWidgetItem, QComboBox, QMessageBox, QScrollArea
)
from PyQt6.QtWidgets import QHeaderView
from PyQt6.QtCore import Qt
from services.background_task import run_background_task
from services.reportes import generar_reporte_mensual, clasificar_cumplimiento
from services.queries_tabla import (
    cargar_equipos_reportables,
    cargar_objetivos_reportables,
    cargar_supervisores,
)
from services.reportes_unificados.consultas import crear_datos_para_exportar
from services.reportes_unificados.datos import (
    COLUMNAS_DIARIAS,
    COLUMNAS_MENSUALES,
)
from ui.animaciones import animar_aparecer
from ui.components import StatusBadge
from ui.components.base import wrap_content_in_glass_card
from ui.reportes.acciones_exportacion import mostrar_dialogo_exportar
from ui.atajos import registrar_atajo


# =============================================================================
# PANTALLA DE REPORTE MENSUAL
# =============================================================================

class ReporteMensual(QWidget):

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Reporte mensual")
        self.resize(1000, 680)
        self.setMinimumSize(560, 360)

        layout = QVBoxLayout()

        fila = QHBoxLayout()

        self.selector_mes = QComboBox()
        meses = [
            "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
            "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"
        ]
        for m in meses:
            self.selector_mes.addItem(m)
        self.selector_mes.setCurrentIndex(datetime.datetime.now().month - 1)

        self.selector_anio = QComboBox()
        anio_actual = datetime.datetime.now().year
        for a in range(anio_actual - 2, anio_actual + 2):
            self.selector_anio.addItem(str(a))
        self.selector_anio.setCurrentText(str(anio_actual))

        self.selector_supervisor = QComboBox()
        self.selector_supervisor.addItem("Todos", None)
        for supervisor_id, nombre in cargar_supervisores():
            self.selector_supervisor.addItem(nombre, supervisor_id)
        self.selector_turno = QComboBox()
        self.selector_turno.addItems(["Todos", "diurno", "nocturno"])
        self.selector_estado = QComboBox()
        self.selector_estado.addItems(["Todos", "CUMPLE", "NO CUMPLE"])

        self.boton_generar = QPushButton("Generar reporte")
        self.boton_generar.setObjectName("PrimaryButton")
        self.boton_generar.setToolTip("Generar reporte (Ctrl+Enter)")
        self.boton_generar.clicked.connect(self._generar)

        self.boton_excel = QPushButton("Exportar Excel")
        self.boton_excel.setToolTip("Abrir opciones de exportación (Ctrl+E)")
        self.boton_excel.clicked.connect(self._exportar_excel)

        self.boton_pdf = QPushButton("Exportar PDF")
        self.boton_pdf.setToolTip("Abrir opciones de exportación")
        self.boton_pdf.clicked.connect(self._exportar_pdf)

        fila.addWidget(QLabel("Mes:"))
        fila.addWidget(self.selector_mes)
        fila.addWidget(QLabel("Año:"))
        fila.addWidget(self.selector_anio)
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

        self.estado_label = QLabel("Listo")
        self._reporte_actual = None
        layout.addWidget(self.estado_label)

        self.tabla = QTableWidget()
        self.tabla.setColumnCount(6)
        self.tabla.setHorizontalHeaderLabels([
            "Objetivo", "Días esperados", "Días con pasada",
            "Días sin pasada", "Cumplimiento", "Estado"
        ])
        header = self.tabla.horizontalHeader()
        header.setMinimumSectionSize(58)
        header.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        for columna in (1, 2, 3, 4, 5):
            header.setSectionResizeMode(
                columna, QHeaderView.ResizeMode.ResizeToContents
            )
        self.tabla.setWordWrap(True)
        layout.addWidget(self.tabla)

        self.setLayout(layout)
        wrap_content_in_glass_card(self)
        registrar_atajo(self, "Ctrl+Enter", self._generar)
        registrar_atajo(self, "Ctrl+E", self._exportar_excel)
        registrar_atajo(self, "F5", self._generar)

    def _set_controls_enabled(self, enabled: bool) -> None:
        self.selector_mes.setEnabled(enabled)
        self.selector_anio.setEnabled(enabled)
        self.selector_supervisor.setEnabled(enabled)
        self.selector_turno.setEnabled(enabled)
        self.selector_estado.setEnabled(enabled)
        self.boton_generar.setEnabled(enabled)
        self.boton_excel.setEnabled(enabled)
        self.boton_pdf.setEnabled(enabled)

    def _generar(self) -> None:
        """Calcula y muestra el reporte en la tabla."""
        mes = self.selector_mes.currentIndex() + 1
        anio = int(self.selector_anio.currentText())

        self._set_controls_enabled(False)
        self.estado_label.setText("Generando reporte...")

        turno = self.selector_turno.currentText()
        task = run_background_task(
            generar_reporte_mensual,
            anio,
            mes,
            self.selector_supervisor.currentData(),
            None if turno == "Todos" else turno,
            self.selector_estado.currentText(),
        )
        task.signals.finished.connect(self._on_reporte_generado)
        task.signals.error.connect(self._on_error)

    def _on_reporte_generado(self, resultados: dict) -> None:
        self._reporte_actual = resultados
        self.tabla.setUpdatesEnabled(False)
        self.tabla.clearContents()
        self.tabla.setRowCount(len(resultados['objetivos']))

        for i, r in enumerate(resultados['objetivos']):
            cumplimiento = r['cumplimiento_porcentaje']
            estado, categoria = clasificar_cumplimiento(cumplimiento)

            self.tabla.setItem(i, 0, QTableWidgetItem(r['nombre']))
            self.tabla.setItem(i, 1, QTableWidgetItem(str(r['dias_esperados'])))
            self.tabla.setItem(i, 2, QTableWidgetItem(str(r['dias_con_pasada'])))
            self.tabla.setItem(i, 3, QTableWidgetItem(str(r['dias_sin_pasada'])))
            self.tabla.setItem(i, 4, QTableWidgetItem(f"{cumplimiento:.1f}%"))
            status = {"verde": "ok", "amarillo": "warning", "rojo": "danger"}.get(
                categoria, "info"
            )
            self.tabla.setCellWidget(i, 5, StatusBadge(estado, status))

        self.tabla.resizeRowsToContents()
        self.tabla.setUpdatesEnabled(True)
        self.estado_label.setText(
            f"Reporte generado — Cumplimiento total: {resultados['cumplimiento_total']:.1f}%"
        )
        self._set_controls_enabled(True)

    def _on_error(self, mensaje: str) -> None:
        QMessageBox.critical(self, "Error", mensaje)
        self.estado_label.setText("Error al generar reporte")
        self._set_controls_enabled(True)

    def _exportar_excel(self) -> None:
        self._abrir_dialogo_exportar("excel")

    def _exportar_pdf(self) -> None:
        self._abrir_dialogo_exportar("pdf")

    def _abrir_dialogo_exportar(self, formato: str) -> None:
        mes = self.selector_mes.currentIndex() + 1
        anio = int(self.selector_anio.currentText())
        inicio = datetime.date(anio, mes, 1)
        fin = datetime.date(
            anio, mes, calendar.monthrange(anio, mes)[1]
        )
        filtros = {
            "supervisor_id": self.selector_supervisor.currentData(),
            "turno": (
                None
                if self.selector_turno.currentText() == "Todos"
                else self.selector_turno.currentText()
            ),
            "estado": self.selector_estado.currentText(),
        }
        catalogo = {
            columna.id: columna
            for columna in (*COLUMNAS_MENSUALES, *COLUMNAS_DIARIAS)
        }
        mostrar_dialogo_exportar(
            self,
            "mensual",
            inicio,
            fin,
            crear_datos_para_exportar,
            tuple(catalogo.values()),
            filtros_iniciales=filtros,
            objetivos=cargar_objetivos_reportables(),
            supervisores=cargar_supervisores(),
            equipos=cargar_equipos_reportables(),
            formato_inicial=formato,
        )
