# =============================================================================
# VESP Organizations - Sistema de Control de Objetivos
# Formulario para agregar supervisores
# =============================================================================

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel,
    QLineEdit, QPushButton, QMessageBox
)
from models.supervisores import agregar_supervisor
from services.validaciones import validar_supervisor, ErrorValidacion


# =============================================================================
# FORMULARIO DE SUPERVISOR
# =============================================================================

class FormSupervisor(QWidget):

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Agregar supervisor")
        self.setGeometry(300, 300, 300, 150)

        layout = QVBoxLayout()

        layout.addWidget(QLabel("Nombre del supervisor:"))
        self.input_nombre = QLineEdit()
        layout.addWidget(self.input_nombre)

        boton_guardar = QPushButton("Guardar supervisor")
        boton_guardar.clicked.connect(self._guardar)
        layout.addWidget(boton_guardar)

        self.setLayout(layout)

    def _guardar(self) -> None:
        """Valida y registra el nuevo supervisor en la base de datos."""
        nombre = self.input_nombre.text().strip()

        try:
            validar_supervisor(nombre)
        except ErrorValidacion as e:
            QMessageBox.warning(self, "Error de Validación", str(e))
            return

        agregar_supervisor(nombre)
        from services.logger import registrar_accion
        from services.sesion import get_usuario_id
        registrar_accion(get_usuario_id(), f"Agregó supervisor: {nombre}")     

        QMessageBox.information(self, "Listo", f"Supervisor '{nombre}' guardado correctamente.")
        self.input_nombre.clear()