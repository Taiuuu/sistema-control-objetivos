from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel,
    QLineEdit, QPushButton, QMessageBox
)
import sqlite3
import bcrypt


class CambiarPassword(QWidget):

    def __init__(self, usuario_id, on_completado):
        super().__init__()
        self.usuario_id = usuario_id
        self.on_completado = on_completado
        self.setWindowTitle("Cambiar contraseña")
        self.setFixedSize(350, 250)

        layout = QVBoxLayout()

        layout.addWidget(QLabel("Ingresá tu nueva contraseña:"))
        self.input_nueva = QLineEdit()
        self.input_nueva.setEchoMode(QLineEdit.EchoMode.Password)
        self.input_nueva.setPlaceholderText("Nueva contraseña")
        self.input_nueva.setFixedHeight(40)
        layout.addWidget(self.input_nueva)

        layout.addWidget(QLabel("Repetí la contraseña:"))
        self.input_repetir = QLineEdit()
        self.input_repetir.setEchoMode(QLineEdit.EchoMode.Password)
        self.input_repetir.setPlaceholderText("Repetir contraseña")
        self.input_repetir.setFixedHeight(40)
        layout.addWidget(self.input_repetir)

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