# =============================================================================
# VESP Organizations - Sistema de Control de Objetivos
# Pantalla de reporte mensual de cumplimiento por objetivo
# =============================================================================

import sqlite3
import datetime
import calendar
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QTableWidget, QTableWidgetItem, QComboBox, QFileDialog, QMessageBox, QScrollArea
)
from PyQt6.QtGui import QColor, QShortcut, QKeySequence
from PyQt6.QtWidgets import QHeaderView
from PyQt6.QtCore import Qt
from services.background_task import run_background_task
from services.exportar import exportar_excel, exportar_pdf
from services.reportes import generar_reporte_mensual, clasificar_cumplimiento
from services.queries_tabla import cargar_supervisores
from services.tema import obtener_tema_actual
from ui.animaciones import animar_aparecer
from ui.widgets.estilos import obtener_color
from database.db import DB_PATH


# =============================================================================
# PANTALLA DE REPORTE MENSUAL
# =============================================================================

class ReporteMensual(QWidget):

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Reporte mensual")
        self.resize(1000, 560)
        self.setMinimumSize(720, 440)

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
        self.boton_generar.clicked.connect(self._generar)

        self.boton_excel = QPushButton("Exportar Excel")
        self.boton_excel.clicked.connect(self._exportar_excel)

        self.boton_pdf = QPushButton("Exportar PDF")
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
        self.tabla.setColumnWidth(0, 220)
        self.tabla.setColumnWidth(1, 110)
        self.tabla.setColumnWidth(2, 120)
        self.tabla.setColumnWidth(3, 120)
        self.tabla.setColumnWidth(4, 100)
        self.tabla.setColumnWidth(5, 100)
        self.tabla.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.tabla)

        self.setLayout(layout)
        QShortcut(QKeySequence("Ctrl+Enter"), self).activated.connect(self._generar)
        QShortcut(QKeySequence("Ctrl+E"), self).activated.connect(self._exportar_excel)

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
            self.tabla.setItem(i, 5, QTableWidgetItem(estado))

            oscuro = obtener_tema_actual() == "oscuro"
            color = QColor(obtener_color(f"estado_{categoria}_bg", oscuro))
            foreground = QColor(obtener_color(f"estado_{categoria}_fg", oscuro))
            for col in range(6):
                self.tabla.item(i, col).setBackground(color)
                self.tabla.item(i, col).setForeground(foreground)

        self.tabla.setUpdatesEnabled(True)
        self.estado_label.setText(
            f"Reporte generado — Cumplimiento total: {resultados['cumplimiento_total']:.1f}%"
        )
        self._set_controls_enabled(True)

    def _on_error(self, mensaje: str) -> None:
        QMessageBox.critical(self, "Error", mensaje)
        self.estado_label.setText("Error al generar reporte")
        self._set_controls_enabled(True)

    def _filtros_dict(self) -> dict:
        return {
            "supervisor": self.selector_supervisor.currentText(),
            "turno": self.selector_turno.currentText(),
            "estado": self.selector_estado.currentText(),
        }

    def _exportar_excel(self) -> None:
        mes = self.selector_mes.currentIndex() + 1
        anio = int(self.selector_anio.currentText())
        ruta, _ = QFileDialog.getSaveFileName(
            self, "Guardar Excel",
            f"reporte_{anio}_{mes:02d}.xlsx",
            "Excel (*.xlsx)"
        )
        if ruta:
            self._set_controls_enabled(False)
            self.estado_label.setText("Exportando a Excel...")
            task = run_background_task(exportar_excel, anio, mes, ruta, self._reporte_actual, self._filtros_dict())
            task.signals.finished.connect(lambda _: self._on_export_exitoso(ruta))
            task.signals.error.connect(self._on_error)

    def _exportar_pdf(self) -> None:
        mes = self.selector_mes.currentIndex() + 1
        anio = int(self.selector_anio.currentText())
        ruta, _ = QFileDialog.getSaveFileName(
            self, "Guardar PDF",
            f"reporte_{anio}_{mes:02d}.pdf",
            "PDF (*.pdf)"
        )
        if ruta:
            self._set_controls_enabled(False)
            self.estado_label.setText("Exportando a PDF...")
            task = run_background_task(exportar_pdf, anio, mes, ruta, self._reporte_actual, self._filtros_dict())
            task.signals.finished.connect(lambda _: self._on_export_exitoso(ruta))
            task.signals.error.connect(self._on_error)

    def _on_export_exitoso(self, ruta: str) -> None:
        QMessageBox.information(self, "Exportación completa", f"Archivo guardado en: {ruta}")
        self.estado_label.setText("Exportación completada")
        self._set_controls_enabled(True)
        animar_aparecer(self.tabla, 180)