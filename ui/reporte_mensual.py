# =============================================================================
# VESP Organizations - Sistema de Control de Objetivos
# Pantalla de reporte mensual de cumplimiento por objetivo
# =============================================================================

import sqlite3
import datetime
import calendar
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QTableWidget, QTableWidgetItem, QComboBox, QFileDialog
)
from PyQt6.QtGui import QColor
from services.exportar import exportar_excel, exportar_pdf
from database.db import DB_PATH


# =============================================================================
# CÁLCULO DEL REPORTE
# =============================================================================

def calcular_reporte(anio: int, mes: int) -> list:
    """
    Calcula el cumplimiento mensual por objetivo con pasadas diurnas y nocturnas separadas.
    Retorna lista de (nombre, dias_controlados_dia, dias_controlados_noche, dias_sin_control, porcentaje).
    """
    conexion = sqlite3.connect(DB_PATH)
    cursor = conexion.cursor()
    cursor.execute("SELECT id, nombre, fecha_inicio, fecha_fin, dias_semana FROM objetivos")
    objetivos = cursor.fetchall()

    resultados = []
    total_dias = calendar.monthrange(anio, mes)[1]

    for o in objetivos:
        obj_id, nombre, inicio, fin, dias_str = o
        dias_semana = [int(d) for d in dias_str.split(",")]
        dias_esperados = 0
        dias_con_dia = 0
        dias_con_noche = 0
        dias_sin_control = 0

        for dia in range(1, total_dias + 1):
            fecha = f"{anio}-{mes:02d}-{dia:02d}"
            fecha_dt = datetime.datetime.strptime(fecha, "%Y-%m-%d")

            if inicio and fecha < inicio:
                continue
            if fin and fecha > fin:
                continue
            if fecha_dt.isoweekday() not in dias_semana:
                continue

            dias_esperados += 1

            cursor.execute("""
                SELECT COUNT(*) FROM pasadas
                WHERE fecha = ? AND objetivo_id = ? AND turno = 'diurno'
            """, (fecha, obj_id))
            tuvo_dia = cursor.fetchone()[0] > 0

            cursor.execute("""
                SELECT COUNT(*) FROM pasadas
                WHERE fecha = ? AND objetivo_id = ? AND turno = 'nocturno'
            """, (fecha, obj_id))
            tuvo_noche = cursor.fetchone()[0] > 0

            if tuvo_dia:
                dias_con_dia += 1
            if tuvo_noche:
                dias_con_noche += 1
            if not tuvo_dia and not tuvo_noche:
                dias_sin_control += 1

        if dias_esperados > 0:
            dias_controlados = dias_esperados - dias_sin_control
            porcentaje = (dias_controlados / dias_esperados) * 100
            resultados.append((nombre, dias_con_dia, dias_con_noche, dias_sin_control, porcentaje))

    conexion.close()
    return resultados


# =============================================================================
# PANTALLA DE REPORTE MENSUAL
# =============================================================================

class ReporteMensual(QWidget):

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Reporte mensual")
        self.setGeometry(200, 200, 800, 450)

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

        boton_generar = QPushButton("Generar reporte")
        boton_generar.clicked.connect(self._generar)

        boton_excel = QPushButton("Exportar Excel")
        boton_excel.clicked.connect(self._exportar_excel)

        boton_pdf = QPushButton("Exportar PDF")
        boton_pdf.clicked.connect(self._exportar_pdf)

        fila.addWidget(QLabel("Mes:"))
        fila.addWidget(self.selector_mes)
        fila.addWidget(QLabel("Año:"))
        fila.addWidget(self.selector_anio)
        fila.addWidget(boton_generar)
        fila.addWidget(boton_excel)
        fila.addWidget(boton_pdf)
        layout.addLayout(fila)

        self.tabla = QTableWidget()
        self.tabla.setColumnCount(6)
        self.tabla.setHorizontalHeaderLabels([
            "Objetivo", "Días c/ diurno", "Días c/ nocturno",
            "Días sin control", "Porcentaje", "Estado"
        ])
        self.tabla.setColumnWidth(0, 220)
        self.tabla.setColumnWidth(1, 110)
        self.tabla.setColumnWidth(2, 120)
        self.tabla.setColumnWidth(3, 120)
        self.tabla.setColumnWidth(4, 90)
        self.tabla.setColumnWidth(5, 100)
        layout.addWidget(self.tabla)

        self.setLayout(layout)

    def _generar(self) -> None:
        """Calcula y muestra el reporte en la tabla."""
        mes = self.selector_mes.currentIndex() + 1
        anio = int(self.selector_anio.currentText())
        resultados = calcular_reporte(anio, mes)

        self.tabla.setRowCount(len(resultados))
        for i, r in enumerate(resultados):
            estado = "CUMPLE" if r[4] >= 80 else "NO CUMPLE"
            self.tabla.setItem(i, 0, QTableWidgetItem(r[0]))
            self.tabla.setItem(i, 1, QTableWidgetItem(str(r[1])))
            self.tabla.setItem(i, 2, QTableWidgetItem(str(r[2])))
            self.tabla.setItem(i, 3, QTableWidgetItem(str(r[3])))
            self.tabla.setItem(i, 4, QTableWidgetItem(f"{r[4]:.1f}%"))
            self.tabla.setItem(i, 5, QTableWidgetItem(estado))

            color = QColor("#90EE90") if r[4] >= 80 else QColor("#FF6B6B")
            for col in range(6):
                self.tabla.item(i, col).setBackground(color)
                self.tabla.item(i, col).setForeground(QColor("#000000"))

    def _exportar_excel(self) -> None:
        mes = self.selector_mes.currentIndex() + 1
        anio = int(self.selector_anio.currentText())
        ruta, _ = QFileDialog.getSaveFileName(
            self, "Guardar Excel",
            f"reporte_{anio}_{mes:02d}.xlsx",
            "Excel (*.xlsx)"
        )
        if ruta:
            exportar_excel(anio, mes, ruta)

    def _exportar_pdf(self) -> None:
        mes = self.selector_mes.currentIndex() + 1
        anio = int(self.selector_anio.currentText())
        ruta, _ = QFileDialog.getSaveFileName(
            self, "Guardar PDF",
            f"reporte_{anio}_{mes:02d}.pdf",
            "PDF (*.pdf)"
        )
        if ruta:
            exportar_pdf(anio, mes, ruta)