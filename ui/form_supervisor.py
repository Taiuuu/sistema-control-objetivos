from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel,
    QLineEdit, QPushButton, QMessageBox
)
from models.supervisores import agregar_supervisor


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
        boton_guardar.clicked.connect(self.guardar)
        layout.addWidget(boton_guardar)

        self.setLayout(layout)

    def guardar(self):
        nombre = self.input_nombre.text().strip()

        if not nombre:
            QMessageBox.warning(self, "Error", "El nombre no puede estar vacío.")
            return

        agregar_supervisor(nombre)

        from services.logger import registrar_accion
        from services.sesion import get_usuario_id
        registrar_accion(get_usuario_id(), f"Agregó supervisor: {nombre}")

        QMessageBox.information(self, "Listo", f"Supervisor '{nombre}' guardado correctamente.")
        self.input_nombre.clear()