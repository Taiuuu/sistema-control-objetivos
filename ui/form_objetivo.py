import sys
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel,
    QLineEdit, QPushButton, QCheckBox, QDateEdit, QMessageBox
)
from PyQt6.QtCore import QDate
from models.objetivos import agregar_objetivo


class FormObjetivo(QWidget):

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Agregar objetivo")
        self.setGeometry(300, 300, 400, 400)

        layout = QVBoxLayout()

        # Nombre
        layout.addWidget(QLabel("Nombre del objetivo:"))
        self.input_nombre = QLineEdit()
        layout.addWidget(self.input_nombre)

        # Fecha inicio
        layout.addWidget(QLabel("Fecha inicio:"))
        self.input_inicio = QDateEdit()
        self.input_inicio.setDate(QDate.currentDate())
        self.input_inicio.setCalendarPopup(True)
        layout.addWidget(self.input_inicio)

        # Dias de cobertura
        layout.addWidget(QLabel("Días de cobertura:"))
        self.dias = {
            "Lunes": QCheckBox("Lunes"),
            "Martes": QCheckBox("Martes"),
            "Miércoles": QCheckBox("Miércoles"),
            "Jueves": QCheckBox("Jueves"),
            "Viernes": QCheckBox("Viernes"),
            "Sábado": QCheckBox("Sábado"),
            "Domingo": QCheckBox("Domingo"),
        }
        for checkbox in self.dias.values():
            layout.addWidget(checkbox)

        # Boton guardar
        boton_guardar = QPushButton("Guardar objetivo")
        boton_guardar.clicked.connect(self.guardar)
        layout.addWidget(boton_guardar)

        self.setLayout(layout)

    def guardar(self):
        nombre = self.input_nombre.text().strip()
        inicio = self.input_inicio.date().toString("yyyy-MM-dd")

        dias_map = {
            "Lunes": "1", "Martes": "2", "Miércoles": "3",
            "Jueves": "4", "Viernes": "5", "Sábado": "6", "Domingo": "7"
        }

        dias_seleccionados = [
            dias_map[dia] for dia, cb in self.dias.items() if cb.isChecked()
        ]

        if not nombre:
            QMessageBox.warning(self, "Error", "El nombre no puede estar vacío.")
            return

        if not dias_seleccionados:
            QMessageBox.warning(self, "Error", "Seleccioná al menos un día.")
            return

        dias_str = ",".join(dias_seleccionados)
        agregar_objetivo(nombre, inicio, None, dias_str)

        from services.logger import registrar_accion
        from services.sesion import get_usuario_id
        registrar_accion(get_usuario_id(), f"Agregó objetivo: {nombre} | Inicio: {inicio} | Días: {dias_str}")

        QMessageBox.information(self, "Listo", f"Objetivo '{nombre}' guardado correctamente.")
        self.close()