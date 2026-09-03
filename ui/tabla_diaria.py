import sys
from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout,
    QTableWidget, QTableWidgetItem, QLabel, QPushButton, QDateEdit, QComboBox
)
from PyQt6.QtCore import QDate
from PyQt6.QtGui import QColor
from services.reportes import obtener_objetivos_del_dia
from services.background_task import run_background_task
from database.db import DB_PATH
from ui.form_objetivo import FormObjetivo
from ui.lista_objetivos import DialogoEditarObjetivo
import sqlite3
from functools import partial

def contar_pasadas(fecha, objetivo_id):
    conexion = sqlite3.connect(DB_PATH)
    cursor = conexion.cursor()
    cursor.execute('''
        SELECT COUNT(*) FROM pasadas
        WHERE fecha = ? AND objetivo_id = ?
    ''', (fecha, objetivo_id))
    resultado = cursor.fetchone()[0]
    conexion.close()
    return resultado


class TablaDiaria(QWidget):

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Control diario de objetivos")
        self.setGeometry(200, 200, 700, 400)

        layout = QVBoxLayout()

        # Selector de fecha
        fecha_layout = QHBoxLayout()
        self.selector_fecha = QDateEdit()
        self.selector_fecha.setDate(QDate.currentDate())
        self.selector_fecha.setCalendarPopup(True)
        self.selector_fecha.dateChanged.connect(self.cargar_tabla)  # Auto-reload when date changes
        boton_buscar = QPushButton("Buscar")
        boton_buscar.clicked.connect(self.cargar_tabla)
        fecha_layout.addWidget(QLabel("Fecha:"))
        fecha_layout.addWidget(self.selector_fecha)
        fecha_layout.addWidget(boton_buscar)
        layout.addLayout(fecha_layout)

        # Tabla
        self.tabla = QTableWidget()
        self.tabla.setColumnCount(4)
        self.tabla.setHorizontalHeaderLabels(["Objetivo", "Pasadas", "Estado", "Acción"])
        self.tabla.setColumnWidth(0, 250)
        self.tabla.setColumnWidth(1, 80)
        self.tabla.setColumnWidth(2, 80)
        self.tabla.setColumnWidth(3, 120)
        self.tabla.setMinimumSize(600, 200)
        self.tabla.setShowGrid(True)
        self.tabla.setAlternatingRowColors(True)
        self.tabla.horizontalHeader().setStretchLastSection(True)
        layout.addWidget(self.tabla)

        self.setLayout(layout)
        self.estado = QLabel("Listo")
        layout.insertWidget(1, self.estado)
        self.cargar_tabla()

    def cargar_tabla(self):
        fecha = self.selector_fecha.date().toString("yyyy-MM-dd")
        self.estado.setText("Cargando objetivos...")
        self.tabla.setEnabled(False)
        task = run_background_task(self._obtener_datos, fecha)
        task.signals.finished.connect(self._mostrar_datos)
        task.signals.error.connect(self._mostrar_error)

    @staticmethod
    def _obtener_datos(fecha):
        objetivos = obtener_objetivos_del_dia(fecha)
        conexion = sqlite3.connect(DB_PATH)
        cursor = conexion.cursor()
        cursor.execute(
            "SELECT objetivo_id, COUNT(*) FROM pasadas WHERE fecha = ? GROUP BY objetivo_id",
            (fecha,),
        )
        pasadas = dict(cursor.fetchall())
        conexion.close()
        return objetivos, pasadas

    def _mostrar_datos(self, datos):
        try:
            objetivos, pasadas_por_objetivo = datos

            self.tabla.setUpdatesEnabled(False)
            self._limpiar_tabla()

            if objetivos:
                self.tabla.setRowCount(len(objetivos))

                for i, o in enumerate(objetivos):
                    pasadas = pasadas_por_objetivo.get(o[0], 0)
                    estado = "OK" if pasadas > 0 else "FALTA"

                    self.tabla.setItem(i, 0, QTableWidgetItem(o[1]))
                    self.tabla.setItem(i, 1, QTableWidgetItem(str(pasadas)))
                    self.tabla.setItem(i, 2, QTableWidgetItem(estado))

                    combo_accion = QComboBox()
                    combo_accion.addItem("Seleccionar acción")
                    combo_accion.addItem("Editar")

                    combo_accion.currentIndexChanged.connect(
                        partial(self._ejecutar_accion, obj_id=o[0], obj_nombre=o[1], combo=combo_accion)
                    )
                    self.tabla.setCellWidget(i, 3, combo_accion)

                    color = QColor("#90EE90") if pasadas > 0 else QColor("#FF6B6B")
                    foreground = QColor("#14532D") if pasadas > 0 else QColor("#7F1D1D")
                    for col in range(3):
                        self.tabla.item(i, col).setBackground(color)
                        self.tabla.item(i, col).setForeground(foreground)

            sorting_enabled = self.tabla.isSortingEnabled()
            self.tabla.setSortingEnabled(False)
            self.tabla.setUpdatesEnabled(True)
            self.tabla.setSortingEnabled(sorting_enabled)
            self.tabla.update()
            self.tabla.setEnabled(True)
            self.estado.setText(f"{len(objetivos)} objetivos cargados")

        except Exception as e:
            self._mostrar_error(str(e))

    def _mostrar_error(self, mensaje):
        self.tabla.setEnabled(True)
        self.estado.setText(f"Error al cargar: {mensaje}")

    def _limpiar_tabla(self):
        """Elimina widgets y contenido previo de la tabla sin romper el renderizado."""
        row_count = self.tabla.rowCount()
        for row in range(row_count):
            widget = self.tabla.cellWidget(row, 3)
            if widget is not None:
                self.tabla.removeCellWidget(row, 3)
                widget.deleteLater()

        self.tabla.clearContents()
        self.tabla.setRowCount(0)

    def _ejecutar_accion(self, index: int, objetivo_id: int, objetivo_nombre: str, combo: QComboBox) -> None:
        """Ejecuta la acción seleccionada para un objetivo."""
        if index == 0:  # "Seleccionar acción"
            return
        elif index == 1:  # "Editar"
            self._editar_objetivo(objetivo_id)
            combo.setCurrentIndex(0)  # Reset combo

    def _editar_objetivo(self, objetivo_id: int) -> None:
        """Abre el formulario para editar un objetivo."""
        # Obtener los datos del objetivo
        from models.objetivos import obtener_objetivo
        objetivo = obtener_objetivo(objetivo_id)
        dialogo = DialogoEditarObjetivo(objetivo, self)
        dialogo.exec()
        self.cargar_tabla()


def iniciar_interfaz():
    app = QApplication(sys.argv)
    ventana = TablaDiaria()
    ventana.show()
    sys.exit(app.exec())