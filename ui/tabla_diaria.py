import sys
from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout,
    QTableWidget, QTableWidgetItem, QLabel, QPushButton, QDateEdit, QComboBox
)
from PyQt6.QtCore import QDate
from PyQt6.QtGui import QColor
from services.reportes import obtener_objetivos_del_dia
from database.db import DB_PATH
from models.objetivos import dar_de_baja_objetivo
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
        self.cargar_tabla()

    def cargar_tabla(self):
        try:
            fecha = self.selector_fecha.date().toString("yyyy-MM-dd")
            objetivos = obtener_objetivos_del_dia(fecha)

            self.tabla.setUpdatesEnabled(False)
            self._limpiar_tabla()

            if objetivos:
                self.tabla.setRowCount(len(objetivos))

                for i, o in enumerate(objetivos):
                    pasadas = contar_pasadas(fecha, o[0])
                    estado = "OK" if pasadas > 0 else "FALTA"

                    self.tabla.setItem(i, 0, QTableWidgetItem(o[1]))
                    self.tabla.setItem(i, 1, QTableWidgetItem(str(pasadas)))
                    self.tabla.setItem(i, 2, QTableWidgetItem(estado))

                    combo_accion = QComboBox()
                    combo_accion.addItem("Seleccionar acción")
                    combo_accion.addItem("Dar de baja")
                    combo_accion.addItem("Editar")

                    combo_accion.currentIndexChanged.connect(
                        partial(self._ejecutar_accion, obj_id=o[0], obj_nombre=o[1], combo=combo_accion)
                    )
                    self.tabla.setCellWidget(i, 3, combo_accion)

                    color = QColor("#90EE90") if pasadas > 0 else QColor("#FF6B6B")
                    for col in range(3):
                        self.tabla.item(i, col).setBackground(color)

            self.tabla.setUpdatesEnabled(True)
            self.tabla.resizeColumnsToContents()
            self.tabla.resizeRowsToContents()
            self.tabla.update()
            self.tabla.viewport().repaint()
            QApplication.processEvents()
            self.update()

        except Exception as e:
            print(f"Error al cargar tabla: {e}")
            import traceback
            traceback.print_exc()

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
        elif index == 1:  # "Dar de baja"
            self._dar_de_baja(objetivo_id, objetivo_nombre)
            combo.setCurrentIndex(0)  # Reset combo
        elif index == 2:  # "Editar"
            self._editar_objetivo(objetivo_id)
            combo.setCurrentIndex(0)  # Reset combo

    def _dar_de_baja(self, objetivo_id: int, objetivo_nombre: str) -> None:
        """Da de baja un objetivo."""
        from PyQt6.QtWidgets import QMessageBox
        respuesta = QMessageBox.question(
            self, "Confirmar",
            f"¿Estás seguro de dar de baja el objetivo '{objetivo_nombre}'?\n\n"
            "Esto lo ocultará del control diario a partir de hoy.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if respuesta == QMessageBox.StandardButton.Yes:
            fecha_hoy = QDate.currentDate().toString("yyyy-MM-dd")
            dar_de_baja_objetivo(objetivo_id, fecha_hoy)
            QMessageBox.information(self, "Éxito", f"El objetivo '{objetivo_nombre}' ha sido dado de baja.")
            self.cargar_tabla()  # Recargar la tabla

    def _editar_objetivo(self, objetivo_id: int) -> None:
        """Abre el formulario para editar un objetivo."""
        # Obtener los datos del objetivo
        conexion = sqlite3.connect(DB_PATH)
        cursor = conexion.cursor()
        cursor.execute('''
            SELECT id, nombre, fecha_inicio, fecha_fin, descripcion, ubicacion,
                   zona, tipo, requiere_turno_doble
            FROM objetivos WHERE id = ?
        ''', (objetivo_id,))
        objetivo_data = cursor.fetchone()
        conexion.close()

        if objetivo_data:
            # Crear y mostrar el diálogo de edición
            dialogo = DialogoEditarObjetivo(objetivo_data, self)
            dialogo.exec()
            self.cargar_tabla()  # Recargar la tabla después de editar


def iniciar_interfaz():
    app = QApplication(sys.argv)
    ventana = TablaDiaria()
    ventana.show()
    sys.exit(app.exec())