from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel,
    QLineEdit, QPushButton, QMessageBox, QHBoxLayout
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


class CambiarPassword(QWidget):

    def __init__(self, usuario_id, on_completado):
        super().__init__()
        self.usuario_id = usuario_id
        self.on_completado = on_completado
        self.setWindowTitle("Cambiar contraseña")
        self.setFixedSize(350, 280)

        layout = QVBoxLayout()

        layout.addWidget(QLabel("Ingresá tu nueva contraseña:"))
        contenedor1, self.input_nueva = campo_password_con_ojito("Nueva contraseña")
        layout.addWidget(contenedor1)

        layout.addWidget(QLabel("Repetí la contraseña:"))
        contenedor2, self.input_repetir = campo_password_con_ojito("Repetir contraseña")
        layout.addWidget(contenedor2)

        boton_guardar = QPushButton("Guardar")
        boton_guardar.setFixedHeight(40)
        boton_guardar.clicked.connect(self.guardar)
        layout.addWidget(boton_guardar)

        self.setLayout(layout)

    def guardar(self):
        nueva = self.input_nueva.text()
        repetir = self.input_repetir.text()

        if not nueva or not repetir:
            QMessageBox.warning(self, "Error", "Completá los dos campos.")
            return

        if nueva != repetir:
            QMessageBox.warning(self, "Error", "Las contraseñas no coinciden.")
            return

        if len(nueva) < 4:
            QMessageBox.warning(self, "Error", "La contraseña debe tener al menos 4 caracteres.")
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