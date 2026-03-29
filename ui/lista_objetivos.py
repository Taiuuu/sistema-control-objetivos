# =============================================================================
# VESP Organizations - Sistema de Control de Objetivos
# Pantalla de listado y gestión de objetivos
# =============================================================================

import sqlite3
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget,
    QTableWidgetItem, QPushButton, QMessageBox, QDialog,
    QLabel, QLineEdit, QDateEdit, QCheckBox, QDialogButtonBox
)
from PyQt6.QtCore import QDate
from database.db import DB_PATH
from models.objetivos import dar_de_baja_objetivo


DIAS_MAP = {
    "1": "Lun", "2": "Mar", "3": "Mié",
    "4": "Jue", "5": "Vie", "6": "Sáb", "7": "Dom"
}

DIAS_NOMBRES = {
    "Lunes": "1", "Martes": "2", "Miércoles": "3",
    "Jueves": "4", "Viernes": "5", "Sábado": "6", "Domingo": "7"
}


# =============================================================================
# CONSULTAS A BASE DE DATOS
# =============================================================================

def _cargar_objetivos() -> list:
    """Retorna todos los objetivos registrados con sus datos completos."""
    conexion = sqlite3.connect(DB_PATH)
    cursor = conexion.cursor()
    cursor.execute("SELECT id, nombre, fecha_inicio, fecha_fin, dias_semana FROM objetivos")
    resultado = cursor.fetchall()
    conexion.close()
    return resultado


def _actualizar_objetivo(objetivo_id: int, nombre: str, fecha_inicio: str, dias_semana: str) -> None:
    """Actualiza los datos de un objetivo existente."""
    conexion = sqlite3.connect(DB_PATH)
    cursor = conexion.cursor()
    cursor.execute("""
        UPDATE objetivos SET nombre = ?, fecha_inicio = ?, dias_semana = ?
        WHERE id = ?
    """, (nombre, fecha_inicio, dias_semana, objetivo_id))
    conexion.commit()
    conexion.close()


# =============================================================================
# DIÁLOGO DE EDICIÓN
# =============================================================================

class DialogoEditarObjetivo(QDialog):

    def __init__(self, objetivo: tuple, parent=None):
        super().__init__(parent)
        self.objetivo_id = objetivo[0]
        self.setWindowTitle("Editar objetivo")
        self.setFixedSize(380, 420)

        layout = QVBoxLayout()

        # Nombre
        layout.addWidget(QLabel("Nombre:"))
        self.input_nombre = QLineEdit(objetivo[1])
        layout.addWidget(self.input_nombre)

        # Fecha inicio
        layout.addWidget(QLabel("Fecha inicio:"))
        self.input_inicio = QDateEdit()
        self.input_inicio.setCalendarPopup(True)
        self.input_inicio.setDate(QDate.fromString(objetivo[2], "yyyy-MM-dd"))
        layout.addWidget(self.input_inicio)

        # Días de cobertura
        layout.addWidget(QLabel("Días de cobertura:"))
        dias_actuales = objetivo[4].split(",") if objetivo[4] else []
        self.dias = {}
        for nombre_dia, numero in DIAS_NOMBRES.items():
            cb = QCheckBox(nombre_dia)
            cb.setChecked(numero in dias_actuales)
            layout.addWidget(cb)
            self.dias[nombre_dia] = cb

        # Botones
        botones = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save |
            QDialogButtonBox.StandardButton.Cancel
        )
        botones.accepted.connect(self._guardar)
        botones.rejected.connect(self.reject)
        layout.addWidget(botones)

        self.setLayout(layout)

    def _guardar(self) -> None:
        """Valida y guarda los cambios del objetivo."""
        nombre = self.input_nombre.text().strip()
        inicio = self.input_inicio.date().toString("yyyy-MM-dd")
        dias_seleccionados = [
            DIAS_NOMBRES[dia] for dia, cb in self.dias.items() if cb.isChecked()
        ]

        if not nombre:
            QMessageBox.warning(self, "Error", "El nombre no puede estar vacío.")
            return

        if not dias_seleccionados:
            QMessageBox.warning(self, "Error", "Seleccioná al menos un día.")
            return

        dias_str = ",".join(dias_seleccionados)
        _actualizar_objetivo(self.objetivo_id, nombre, inicio, dias_str)

        from services.logger import registrar_accion
        from services.sesion import get_usuario_id
        registrar_accion(
            get_usuario_id(),
            f"Editó objetivo id={self.objetivo_id} - Nombre: {nombre} | Inicio: {inicio} | Días: {dias_str}"
        )

        QMessageBox.information(self, "Listo", "Objetivo actualizado correctamente.")
        self.accept()


# =============================================================================
# PANTALLA DE LISTADO DE OBJETIVOS
# =============================================================================

class ListaObjetivos(QWidget):

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Listado de objetivos")
        self.setGeometry(200, 200, 800, 400)

        layout = QVBoxLayout()

        self.tabla = QTableWidget()
        self.tabla.setColumnCount(6)
        self.tabla.setHorizontalHeaderLabels([
            "Nombre", "Inicio", "Fin", "Días", "Editar", "Dar de baja"
        ])
        self.tabla.setColumnWidth(0, 200)
        self.tabla.setColumnWidth(1, 100)
        self.tabla.setColumnWidth(2, 100)
        self.tabla.setColumnWidth(3, 180)
        self.tabla.setColumnWidth(4, 80)
        self.tabla.setColumnWidth(5, 100)
        layout.addWidget(self.tabla)

        self.setLayout(layout)
        self._cargar_tabla()

    def _cargar_tabla(self) -> None:
        """Carga todos los objetivos en la tabla."""
        objetivos = _cargar_objetivos()
        self.tabla.setRowCount(len(objetivos))

        for i, o in enumerate(objetivos):
            dias_texto = ", ".join([DIAS_MAP.get(d, d) for d in o[4].split(",")])
            fin_texto = o[3] if o[3] else "Activo"

            self.tabla.setItem(i, 0, QTableWidgetItem(o[1]))
            self.tabla.setItem(i, 1, QTableWidgetItem(o[2]))
            self.tabla.setItem(i, 2, QTableWidgetItem(fin_texto))
            self.tabla.setItem(i, 3, QTableWidgetItem(dias_texto))

            boton_editar = QPushButton("Editar")
            boton_editar.clicked.connect(lambda checked, obj=o: self._editar(obj))
            self.tabla.setCellWidget(i, 4, boton_editar)

            if not o[3]:
                boton_baja = QPushButton("Dar de baja")
                boton_baja.clicked.connect(lambda checked, obj_id=o[0], nombre=o[1]: self._dar_de_baja(obj_id, nombre))
                self.tabla.setCellWidget(i, 5, boton_baja)

    def _editar(self, objetivo: tuple) -> None:
        """Abre el diálogo de edición para el objetivo seleccionado."""
        dialogo = DialogoEditarObjetivo(objetivo, self)
        if dialogo.exec():
            self._cargar_tabla()

    def _dar_de_baja(self, objetivo_id: int, nombre: str) -> None:
        """Da de baja un objetivo tras confirmación."""
        confirmar = QMessageBox.question(
            self, "Confirmar",
            f"¿Seguro que querés dar de baja '{nombre}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if confirmar == QMessageBox.StandardButton.Yes:
            fecha_hoy = QDate.currentDate().toString("yyyy-MM-dd")
            dar_de_baja_objetivo(objetivo_id, fecha_hoy)

            from services.logger import registrar_accion
            from services.sesion import get_usuario_id
            registrar_accion(get_usuario_id(), f"Dio de baja objetivo: {nombre} | Fecha: {fecha_hoy}")

            QMessageBox.information(self, "Listo", "Objetivo dado de baja correctamente.")
            self._cargar_tabla()