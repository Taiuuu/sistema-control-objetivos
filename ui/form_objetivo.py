# =============================================================================
# VESP Organizations - Sistema de Control de Objetivos
# Formulario para agregar objetivos
# =============================================================================

import sqlite3
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel,
    QLineEdit, QPushButton, QCheckBox, QDateEdit, QMessageBox
)
from PyQt6.QtCore import QDate
from ui.animaciones import animar_entrada
from models.objetivos import agregar_objetivo
from services.validaciones import validar_objetivo, ErrorValidacion


# Mapeo de días de la semana a su número (formato ISO: 1=lunes, 7=domingo)
DIAS_MAP = {
    "Lunes": "1", "Martes": "2", "Miércoles": "3",
    "Jueves": "4", "Viernes": "5", "Sábado": "6", "Domingo": "7"
}


# =============================================================================
# FORMULARIO DE OBJETIVO
# =============================================================================

class FormObjetivo(QWidget):

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Agregar objetivo")
        self.setGeometry(300, 300, 400, 420)

        layout = QVBoxLayout()

        # Nombre del objetivo
        layout.addWidget(QLabel("Nombre del objetivo:"))
        self.input_nombre = QLineEdit()
        layout.addWidget(self.input_nombre)

        # Fecha de inicio de cobertura
        layout.addWidget(QLabel("Fecha inicio:"))
        self.input_inicio = QDateEdit()
        self.input_inicio.setDate(QDate.currentDate())
        self.input_inicio.setCalendarPopup(True)
        layout.addWidget(self.input_inicio)

        # Días de cobertura semanal
        layout.addWidget(QLabel("Días de cobertura:"))
        self.dias = {dia: QCheckBox(dia) for dia in DIAS_MAP}
        for checkbox in self.dias.values():
            layout.addWidget(checkbox)

        boton_guardar = QPushButton("Guardar objetivo")
        boton_guardar.clicked.connect(self._guardar)
        layout.addWidget(boton_guardar)

        self.setLayout(layout)
        animar_entrada(self)

    def _guardar(self) -> None:
        """Valida los datos y registra el nuevo objetivo en la base de datos."""
        nombre = self.input_nombre.text().strip()
        inicio = self.input_inicio.date().toString("yyyy-MM-dd")
        dias_seleccionados = [
            DIAS_MAP[dia] for dia, cb in self.dias.items() if cb.isChecked()
        ]

        if not dias_seleccionados:
            QMessageBox.warning(self, "Error", "Seleccioná al menos un día.")
            return

        dias_str = ",".join(dias_seleccionados)
        
        try:
            validar_objetivo(nombre, dias_str)
        except ErrorValidacion as e:
            QMessageBox.warning(self, "Error de Validación", str(e))
            return
        
        agregar_objetivo(nombre, inicio, None, dias_str)

        from services.logger import registrar_accion
        from services.sesion import get_usuario_id
        registrar_accion(get_usuario_id(), f"Agregó objetivo: {nombre} | Inicio: {inicio} | Días: {dias_str}")

        QMessageBox.information(self, "Listo", f"Objetivo '{nombre}' guardado correctamente.")
        self.close()