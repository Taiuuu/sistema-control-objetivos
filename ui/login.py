from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel,
    QLineEdit, QPushButton, QMessageBox, QHBoxLayout
)
from PyQt6.QtGui import QPixmap, QIcon
from PyQt6.QtCore import Qt
import sqlite3
import bcrypt


def verificar_login(username, password):
    conexion = sqlite3.connect('seguridad.db')
    cursor = conexion.cursor()

    cursor.execute('''
        SELECT id, rol, debe_cambiar_password, password
        FROM usuarios
        WHERE username = ?
    ''', (username,))

    resultado = cursor.fetchone()
    conexion.close()

    if not resultado:
        return None

    try:
        if bcrypt.checkpw(password.encode(), resultado[3].encode()):
            return (resultado[0], resultado[1], resultado[2])
    except Exception:
        pass

    return None


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


class LoginWindow(QWidget):

    def __init__(self, on_login_exitoso):
        super().__init__()
        self.on_login_exitoso = on_login_exitoso
        self.setWindowTitle("V.E.S.P Organizations")
        self.setFixedSize(400, 540)
        self.setWindowIcon(QIcon("assets/vesp.png"))

        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setSpacing(15)

        # Logo
        logo_label = QLabel()
        pixmap = QPixmap("assets/vesp.png")
        pixmap = pixmap.scaled(180, 180, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
        logo_label.setPixmap(pixmap)
        logo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(logo_label)

        # Nombre empresa
        nombre_label = QLabel("V.E.S.P Organizations")
        nombre_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        nombre_label.setStyleSheet("font-size: 18px; font-weight: bold; color: #4CAF50;")
        layout.addWidget(nombre_label)

        subtitulo = QLabel("Seguridad Privada")
        subtitulo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitulo.setStyleSheet("font-size: 12px; color: #888;")
        layout.addWidget(subtitulo)

        # Version
        try:
            version = open("version.txt").read().strip()
        except Exception:
            version = ""
        version_label = QLabel(f"v{version}")
        version_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        version_label.setStyleSheet("font-size: 10px; color: #555;")
        layout.addWidget(version_label)

        layout.addSpacing(10)

        # Usuario
        self.input_usuario = QLineEdit()
        self.input_usuario.setPlaceholderText("Usuario")
        self.input_usuario.setFixedHeight(40)
        layout.addWidget(self.input_usuario)

        # Contraseña con ojito
        contenedor_pw, self.input_password = campo_password_con_ojito("Contraseña")
        layout.addWidget(contenedor_pw)

        # Boton entrar
        boton_entrar = QPushButton("Entrar")
        boton_entrar.setFixedHeight(40)
        boton_entrar.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                font-size: 14px;
                font-weight: bold;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        boton_entrar.clicked.connect(self.intentar_login)
        layout.addWidget(boton_entrar)

        self.input_password.returnPressed.connect(self.intentar_login)

        layout.addSpacing(10)
        self.setLayout(layout)

    def intentar_login(self):
        username = self.input_usuario.text().strip()
        password = self.input_password.text()

        if not username or not password:
            QMessageBox.warning(self, "Error", "Completá usuario y contraseña.")
            return

        resultado = verificar_login(username, password)

        if not resultado:
            QMessageBox.warning(self, "Error", "Usuario o contraseña incorrectos.")
            self.input_password.clear()
            return

        usuario_id, rol, debe_cambiar = resultado

        from services.logger import registrar_accion
        registrar_accion(usuario_id, "Inicio de sesión")

        if debe_cambiar:
            self.pedir_nueva_password(usuario_id)
        else:
            self.on_login_exitoso(usuario_id, rol)
            self.close()

    def pedir_nueva_password(self, usuario_id):
        from ui.cambiar_password import CambiarPassword
        self.cambiar_pw = CambiarPassword(usuario_id, lambda: self.login_post_cambio(usuario_id))
        self.cambiar_pw.show()

    def login_post_cambio(self, usuario_id):
        conexion = sqlite3.connect('seguridad.db')
        cursor = conexion.cursor()
        cursor.execute('SELECT rol FROM usuarios WHERE id = ?', (usuario_id,))
        rol = cursor.fetchone()[0]
        conexion.close()
        self.on_login_exitoso(usuario_id, rol)
        self.close()