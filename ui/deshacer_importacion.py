# =============================================================================
# VESP Organizations - Deshacer Importación
# Pantalla para revertir importaciones eliminando pasadas en lote
# =============================================================================

from datetime import datetime, timedelta
import sqlite3

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget,
    QTableWidgetItem, QPushButton, QMessageBox, QDateEdit,
    QLabel, QComboBox, QSpinBox
)
from PyQt6.QtCore import QDate

from database.db import DB_PATH
from models.objetivos import listar_objetivos
from models.supervisores import listar_supervisores
from services.sesion import get_usuario_id, get_rol
from services.logger import registrar_accion


def _cargar_pasadas_recientes(dias: int = 1) -> list:
    """Carga todas las pasadas creadas en los últimos N días."""
    conexion = sqlite3.connect(DB_PATH)
    conexion.row_factory = sqlite3.Row
    cursor = conexion.cursor()
    
    fecha_limite = (datetime.now() - timedelta(days=dias)).strftime('%Y-%m-%d')
    
    cursor.execute("""
        SELECT 
            p.id, 
            p.fecha, 
            p.hora, 
            p.turno,
            s.nombre as supervisor_nombre,
            o.nombre as objetivo_nombre
        FROM pasadas p
        LEFT JOIN supervisores s ON p.supervisor_id = s.id
        LEFT JOIN objetivos o ON p.objetivo_id = o.id
        WHERE p.fecha >= ?
        ORDER BY p.fecha DESC, p.hora DESC
    """, (fecha_limite,))
    
    resultado = cursor.fetchall()
    conexion.close()
    return resultado


def _eliminar_pasadas(pasada_ids: list) -> int:
    """Elimina múltiples pasadas. Retorna cuántas se eliminaron."""
    if not pasada_ids:
        return 0
    
    conexion = sqlite3.connect(DB_PATH)
    cursor = conexion.cursor()
    
    placeholders = ','.join('?' * len(pasada_ids))
    cursor.execute(
        f"DELETE FROM pasadas WHERE id IN ({placeholders})",
        pasada_ids
    )
    
    eliminadas = cursor.rowcount
    conexion.commit()
    conexion.close()
    
    return eliminadas


class DeshacerImportacion(QWidget):
    """Pantalla para deshacer/revertir importaciones eliminando pasadas."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Deshacer importación")
        self.setGeometry(200, 200, 1000, 600)
        self.pasadas_seleccionadas = []

        layout = QVBoxLayout()

        # ================================================================
        # SECCIÓN DE FILTROS
        # ================================================================
        titulo = QLabel("🔄 Deshacer importación - Eliminar pasadas")
        titulo.setStyleSheet("font-size: 14px; font-weight: bold; color: #ff6b6b;")
        layout.addWidget(titulo)

        filtros_layout = QHBoxLayout()

        # Filtro: Días atrás
        filtros_layout.addWidget(QLabel("Últimos:"))
        self.spin_dias = QSpinBox()
        self.spin_dias.setMinimum(1)
        self.spin_dias.setMaximum(365)
        self.spin_dias.setValue(1)
        self.spin_dias.setSuffix(" día(s)")
        self.spin_dias.valueChanged.connect(self._actualizar_pasadas)
        filtros_layout.addWidget(self.spin_dias)

        # Filtro: Supervisor
        filtros_layout.addWidget(QLabel("Supervisor:"))
        self.combo_supervisor = QComboBox()
        self.combo_supervisor.addItem("-- Todos --", None)
        for sup in listar_supervisores():
            self.combo_supervisor.addItem(sup.nombre, sup.id)
        self.combo_supervisor.currentIndexChanged.connect(self._actualizar_pasadas)
        filtros_layout.addWidget(self.combo_supervisor)

        # Filtro: Objetivo
        filtros_layout.addWidget(QLabel("Objetivo:"))
        self.combo_objetivo = QComboBox()
        self.combo_objetivo.addItem("-- Todos --", None)
        for obj in listar_objetivos():
            self.combo_objetivo.addItem(obj.nombre, obj.id)
        self.combo_objetivo.currentIndexChanged.connect(self._actualizar_pasadas)
        filtros_layout.addWidget(self.combo_objetivo)

        boton_aplicar = QPushButton("🔍 Filtrar")
        boton_aplicar.clicked.connect(self._actualizar_pasadas)
        filtros_layout.addWidget(boton_aplicar)

        filtros_layout.addStretch()
        layout.addLayout(filtros_layout)

        # ================================================================
        # TABLA DE PASADAS
        # ================================================================
        self.tabla = QTableWidget()
        self.tabla.setColumnCount(7)
        self.tabla.setHorizontalHeaderLabels([
            "✓", "Fecha", "Hora", "Turno", "Supervisor", "Objetivo", "ID"
        ])
        self.tabla.setColumnWidth(0, 30)
        self.tabla.setColumnWidth(1, 100)
        self.tabla.setColumnWidth(2, 80)
        self.tabla.setColumnWidth(3, 80)
        self.tabla.setColumnWidth(4, 150)
        self.tabla.setColumnWidth(5, 150)
        self.tabla.setColumnWidth(6, 50)
        
        self.tabla.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.tabla.itemSelectionChanged.connect(self._actualizar_seleccion)
        
        layout.addWidget(self.tabla)

        # ================================================================
        # BOTONES DE ACCIÓN
        # ================================================================
        botones_layout = QHBoxLayout()

        boton_seleccionar_todo = QPushButton("✓ Seleccionar todo")
        boton_seleccionar_todo.clicked.connect(self._seleccionar_todo)
        botones_layout.addWidget(boton_seleccionar_todo)

        boton_deseleccionar_todo = QPushButton("✗ Deseleccionar todo")
        boton_deseleccionar_todo.clicked.connect(self._deseleccionar_todo)
        botones_layout.addWidget(boton_deseleccionar_todo)

        botones_layout.addStretch()

        boton_eliminar = QPushButton("🗑 Eliminar seleccionadas")
        boton_eliminar.setStyleSheet("background-color: #d32f2f; color: white; font-weight: bold;")
        boton_eliminar.clicked.connect(self._eliminar_seleccionadas)
        botones_layout.addWidget(boton_eliminar)

        boton_cerrar = QPushButton("Cerrar")
        boton_cerrar.clicked.connect(self.close)
        botones_layout.addWidget(boton_cerrar)

        layout.addLayout(botones_layout)

        self.setLayout(layout)
        self._actualizar_pasadas()

    def _actualizar_pasadas(self) -> None:
        """Recarga la tabla con pasadas filtradas."""
        dias = self.spin_dias.value()
        pasadas = _cargar_pasadas_recientes(dias)

        self.tabla.setRowCount(len(pasadas))

        for i, p in enumerate(pasadas):
            # Checkbox
            from PyQt6.QtWidgets import QCheckBox
            checkbox = QCheckBox()
            self.tabla.setCellWidget(i, 0, checkbox)

            # Datos
            self.tabla.setItem(i, 1, QTableWidgetItem(p['fecha']))
            self.tabla.setItem(i, 2, QTableWidgetItem(p['hora']))
            self.tabla.setItem(i, 3, QTableWidgetItem(p['turno'] or ''))
            self.tabla.setItem(i, 4, QTableWidgetItem(p['supervisor_nombre'] or ''))
            self.tabla.setItem(i, 5, QTableWidgetItem(p['objetivo_nombre'] or ''))
            self.tabla.setItem(i, 6, QTableWidgetItem(str(p['id'])))

    def _actualizar_seleccion(self) -> None:
        """Actualiza la lista de pasadas seleccionadas."""
        self.pasadas_seleccionadas = []
        for fila in range(self.tabla.rowCount()):
            checkbox = self.tabla.cellWidget(fila, 0)
            if checkbox and checkbox.isChecked():
                pasada_id = int(self.tabla.item(fila, 6).text())
                self.pasadas_seleccionadas.append(pasada_id)

    def _seleccionar_todo(self) -> None:
        """Marca todos los checkboxes."""
        for fila in range(self.tabla.rowCount()):
            checkbox = self.tabla.cellWidget(fila, 0)
            if checkbox:
                checkbox.setChecked(True)
        self._actualizar_seleccion()

    def _deseleccionar_todo(self) -> None:
        """Desmarca todos los checkboxes."""
        for fila in range(self.tabla.rowCount()):
            checkbox = self.tabla.cellWidget(fila, 0)
            if checkbox:
                checkbox.setChecked(False)
        self._actualizar_seleccion()

    def _eliminar_seleccionadas(self) -> None:
        """Elimina las pasadas seleccionadas."""
        if not self.pasadas_seleccionadas:
            QMessageBox.warning(
                self, "Nada seleccionado",
                "Seleccioná al menos una pasada para eliminar."
            )
            return

        cantidad = len(self.pasadas_seleccionadas)

        # Primera confirmación
        dialogo1 = QMessageBox.warning(
            self, "⚠ Advertencia",
            f"¿Seguro que querés ELIMINAR {cantidad} pasada(s)?\n\n"
            f"Esta acción:\n"
            f"• Elimina las pasadas de la base de datos\n"
            f"• NO se puede deshacer\n\n"
            f"Haz click en 'Sí' para confirmar.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if dialogo1 != QMessageBox.StandardButton.Yes:
            return

        # Segunda confirmación
        dialogo2 = QMessageBox.critical(
            self, "🗑 ELIMINAR - CONFIRMACIÓN FINAL",
            f"⚠️ CONFIRMACIÓN FINAL ⚠️\n\n"
            f"Vas a ELIMINAR DEFINITIVAMENTE {cantidad} pasada(s).\n\n"
            f"Escribe 'ELIMINAR' para confirmar:",
            QMessageBox.StandardButton.Ok | QMessageBox.StandardButton.Cancel
        )

        if dialogo2 != QMessageBox.StandardButton.Ok:
            return

        # Pedir confirmación escribiendo
        from PyQt6.QtWidgets import QInputDialog

        confirmacion, ok = QInputDialog.getText(
            self,
            "Confirmación de eliminación",
            "Escribí 'ELIMINAR' para confirmar la eliminación de las pasadas:"
        )

        if not ok or confirmacion != "ELIMINAR":
            QMessageBox.warning(
                self, "Cancelado",
                "La eliminación ha sido cancelada. Confirmación incorrecta."
            )
            return

        # Proceder con la eliminación
        try:
            eliminadas = _eliminar_pasadas(self.pasadas_seleccionadas)

            registrar_accion(
                get_usuario_id(),
                f"⚠️ Eliminó {eliminadas} pasada(s) - Deshizo importación"
            )

            QMessageBox.information(
                self, "✓ Eliminadas",
                f"{eliminadas} pasada(s) han sido eliminadas de la base de datos."
            )

            self._actualizar_pasadas()
            self.pasadas_seleccionadas = []

        except Exception as e:
            QMessageBox.critical(
                self, "Error",
                f"No se pudieron eliminar las pasadas: {str(e)}"
            )
