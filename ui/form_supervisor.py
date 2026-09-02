# =============================================================================
# VESP Organizations - Sistema de Control de Objetivos
# Formulario para agregar supervisores
# =============================================================================

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QFormLayout, QLabel,
    QLineEdit, QPushButton, QMessageBox, QFrame
)
from PyQt6.QtCore import Qt
from models.supervisores import agregar_supervisor
from services.validaciones import validar_supervisor, ErrorValidacion


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

        self.boton_guardar = QPushButton("Guardar supervisor")
        self.boton_guardar.setCursor(Qt.CursorShape.PointingHandCursor)
        self.boton_guardar.setFixedHeight(40)
        self.boton_guardar.clicked.connect(self._guardar)

        form_layout = QFormLayout()
        form_layout.setLabelAlignment(Qt.AlignmentFlag.AlignLeft)
        form_layout.setFormAlignment(Qt.AlignmentFlag.AlignLeft)
        form_layout.setContentsMargins(0, 0, 0, 0)
        form_layout.setSpacing(12)
        form_layout.addRow(QLabel("Nombre del supervisor"), self.input_nombre)

        card = QFrame()
        card.setObjectName("CardContenedor")
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(18, 18, 18, 18)
        card_layout.setSpacing(16)
        card_layout.addLayout(form_layout)
        card_layout.addWidget(self.boton_guardar)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(14)
        layout.addWidget(self._titulo)
        layout.addWidget(self._subtitulo)
        layout.addWidget(card)

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