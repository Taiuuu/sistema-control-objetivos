# =============================================================================
# VESP Organizations - Sistema de Control de Objetivos
# Formulario para agregar supervisores
# =============================================================================

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QFormLayout, QLabel,
    QLineEdit, QMessageBox
)
from PyQt6.QtCore import Qt
from models.supervisores import agregar_supervisor
from services.validaciones import validar_supervisor, ErrorValidacion
from ui.components import GlassCard, PillButton


# =============================================================================
# FORMULARIO DE SUPERVISOR
# =============================================================================

class FormSupervisor(QWidget):

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Agregar supervisor")
        self.setMinimumSize(360, 180)

        self._titulo = QLabel("Agregar supervisor")
        self._titulo.setObjectName("TituloPrincipal")

        self._subtitulo = QLabel("Ingresa el nombre del supervisor y guarda.")
        self._subtitulo.setObjectName("Subtitulo")
        self._subtitulo.setWordWrap(True)

        self.input_nombre = QLineEdit()
        self.input_nombre.setFixedHeight(34)

        self.boton_guardar = PillButton("Guardar supervisor", "primary")
        self.boton_guardar.setObjectName("PrimaryButton")
        self.boton_guardar.setCursor(Qt.CursorShape.PointingHandCursor)
        self.boton_guardar.setFixedHeight(40)
        self.boton_guardar.clicked.connect(self._guardar)

        form_layout = QFormLayout()
        form_layout.setLabelAlignment(Qt.AlignmentFlag.AlignLeft)
        form_layout.setFormAlignment(Qt.AlignmentFlag.AlignLeft)
        form_layout.setContentsMargins(0, 0, 0, 0)
        form_layout.setSpacing(12)
        form_layout.addRow(QLabel("Nombre del supervisor"), self.input_nombre)

        formulario = GlassCard()
        formulario.add_widget(self._titulo)
        formulario.add_widget(self._subtitulo)
        formulario.add_layout(form_layout)
        formulario.add_widget(self.boton_guardar)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.addWidget(formulario)

    def _guardar(self) -> None:
        """Valida y registra el nuevo supervisor en la base de datos."""
        nombre = self.input_nombre.text().strip()

        try:
            validar_supervisor(nombre)
        except ErrorValidacion as e:
            QMessageBox.warning(self, "Error de Validación", str(e))
            return

        try:
            agregar_supervisor(nombre)
        except Exception as error:
            QMessageBox.critical(self, "Error", f"No se pudo guardar el supervisor: {error}")
            return
        from services.logger import registrar_accion
        from services.sesion import get_usuario_id
        registrar_accion(get_usuario_id(), f"Agregó supervisor: {nombre}")     

        QMessageBox.information(self, "Listo", f"Supervisor '{nombre}' guardado correctamente.")
        self.input_nombre.clear()