from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QLineEdit, QPushButton, QMessageBox
)
import sqlite3
import bcrypt


def campo_password_con_ojito(placeholder):
    contenedor = QWidget()
    layout = QHBoxLayout(contenedor)
    layout.setContentsMargins(0, 0, 0, 0)

    input_pw = QLineEdit()
    input_pw.setPlaceholderText(placeholder)
    input_pw.setEchoMode(QLineEdit.EchoMode.Password)
    input_pw.setFixedHeight(40)

    boton_ojo = QPushButton("👁")
    boton_ojo.setFixedSize(40, 40)
    boton_ojo.setCheckable(True)
    boton_ojo.toggled.connect(
        lambda checked: input_pw.setEchoMode(
            QLineEdit.EchoMode.Normal if checked else QLineEdit.EchoMode.Password
        )
    )

    layout.addWidget(input_pw)
    layout.addWidget(boton_ojo)

    return contenedor, input_pw


def verificar_requisitos(password):
    return {
        "longitud": 8 <= len(password) <= 18,
        "mayuscula": any(c.isupper() for c in password),
        "minuscula": any(c.islower() for c in password),
        "numero": any(c.isdigit() for c in password),
        "sin_espacios": " " not in password and len(password) > 0,
    }


LABELS_REQUISITOS = {
    "longitud": "Entre 8 y 18 caracteres",
    "mayuscula": "Al menos una mayúscula",
    "minuscula": "Al menos una minúscula",
    "numero": "Al menos un número",
    "sin_espacios": "Sin espacios",
}


class CambiarPassword(QWidget):

    def __init__(self, usuario_id, on_completado):
        super().__init__()
        self.usuario_id = usuario_id
        self.on_completado = on_completado
        self.setWindowTitle("Cambiar contraseña")
        self.setFixedSize(380, 420)

        layout = QVBoxLayout()

        layout.addWidget(QLabel("Nueva contraseña:"))
        contenedor1, self.input_nueva = campo_password_con_ojito("Nueva contraseña")
        layout.addWidget(contenedor1)
        self.input_nueva.textChanged.connect(self.actualizar_indicadores)

        layout.addWidget(QLabel("Repetir contraseña:"))
        contenedor2, self.input_repetir = campo_password_con_ojito("Repetir contraseña")
        layout.addWidget(contenedor2)

        layout.addSpacing(8)
        layout.addWidget(QLabel("Requisitos:"))

        self.indicadores = {}
        for clave, texto in LABELS_REQUISITOS.items():
            label = QLabel(f"✗  {texto}")
            label.setStyleSheet("color: #FF6B6B; font-size: 12px;")
            layout.addWidget(label)
            self.indicadores[clave] = label

        layout.addSpacing(8)

        boton_guardar = QPushButton("Guardar")
        boton_guardar.setFixedHeight(40)
        boton_guardar.clicked.connect(self.guardar)
        layout.addWidget(boton_guardar)

        self.setLayout(layout)

    def actualizar_indicadores(self, texto):
        requisitos = verificar_requisitos(texto)
        textos_dinamicos = {
            "longitud": f"Entre 8 y 18 caracteres (ahora: {len(texto)})",
            "mayuscula": "Al menos una mayúscula",
            "minuscula": "Al menos una minúscula",
            "numero": "Al menos un número",
            "sin_espacios": "Sin espacios",
        }
        for clave, cumple in requisitos.items():
            label = self.indicadores[clave]
            texto_label = textos_dinamicos[clave]
            if cumple:
                label.setText(f"✓  {texto_label}")
                label.setStyleSheet("color: #90EE90; font-size: 12px;")
            else:
                label.setText(f"✗  {texto_label}")
                label.setStyleSheet("color: #FF6B6B; font-size: 12px;")

    def guardar(self):
        nueva = self.input_nueva.text()
        repetir = self.input_repetir.text()

        if not nueva or not repetir:
            QMessageBox.warning(self, "Error", "Completá los dos campos.")
            return

        requisitos = verificar_requisitos(nueva)
        if not all(requisitos.values()):
            QMessageBox.warning(self, "Error", "La contraseña no cumple todos los requisitos.")
            return

        if nueva != repetir:
            QMessageBox.warning(self, "Error", "Las contraseñas no coinciden.")
            return

        password_hash = bcrypt.hashpw(nueva.encode(), bcrypt.gensalt()).decode()

        conexion = sqlite3.connect('seguridad.db')
        cursor = conexion.cursor()
        cursor.execute('''
            UPDATE usuarios SET password = ?, debe_cambiar_password = 0
            WHERE id = ?
        ''', (password_hash, self.usuario_id))
        conexion.commit()
        conexion.close()

        QMessageBox.information(self, "Listo", "Contraseña actualizada correctamente.")
        self.on_completado()
        self.close()