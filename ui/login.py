# =============================================================================
# VESP Organizations - Sistema de Control de Objetivos
# Pantalla de inicio de sesión
# =============================================================================

import sqlite3
import bcrypt
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel,
    QLineEdit, QPushButton, QMessageBox, QHBoxLayout
)
from PyQt6.QtGui import QPixmap, QIcon
from PyQt6.QtCore import Qt
from database.db import DB_PATH
from services.assets import ruta_asset

# =============================================================================
# AUTENTICACIÓN
# =============================================================================

def verificar_login(username: str, password: str) -> tuple | None:
    """
    Verifica las credenciales del usuario contra la base de datos.
    Retorna (id, rol, debe_cambiar_password) si son correctas, None si no.
    """
    conexion = sqlite3.connect(DB_PATH)
    cursor = conexion.cursor()
    cursor.execute("""
        SELECT id, rol, debe_cambiar_password, password
        FROM usuarios WHERE username = ?
    """, (username,))
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


# =============================================================================
# COMPONENTE: CAMPO CONTRASEÑA CON OJITO
# =============================================================================

def campo_password_con_ojito(placeholder: str) -> tuple:
    """Retorna un contenedor con campo de contraseña y botón para mostrar/ocultar."""
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


# =============================================================================
# VENTANA DE LOGIN
# =============================================================================

class LoginWindow(QWidget):

    def __init__(self, on_login_exitoso):
        super().__init__()
        self.on_login_exitoso = on_login_exitoso
        self.setWindowTitle("V.E.S.P Organizations")
        self.setFixedSize(400, 540)
        self.setWindowIcon(QIcon(ruta_asset("assets/vesp.png")))

        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setSpacing(15)

        # Logo
        logo_label = QLabel()
        pixmap = QPixmap(ruta_asset("assets/vesp.png")).scaled(
            180, 180,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation
        )
        logo_label.setPixmap(pixmap)
        logo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(logo_label)

        # Nombre y subtítulo
        nombre_label = QLabel("V.E.S.P Organizations")
        nombre_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        nombre_label.setStyleSheet("font-size: 18px; font-weight: bold; color: #4CAF50;")
        layout.addWidget(nombre_label)

        subtitulo = QLabel("Seguridad Privada")
        subtitulo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitulo.setStyleSheet("font-size: 12px; color: #888;")
        layout.addWidget(subtitulo)

        # Versión actual
        try:
            version = open(ruta_asset("version.txt")).read().strip()
        except Exception:
            version = ""
        version_label = QLabel(f"v{version}")
        version_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        version_label.setStyleSheet("font-size: 10px; color: #555;")
        layout.addWidget(version_label)

        layout.addSpacing(10)

        # Campos de usuario y contraseña
        self.input_usuario = QLineEdit()
        self.input_usuario.setPlaceholderText("Usuario")
        self.input_usuario.setFixedHeight(40)
        layout.addWidget(self.input_usuario)

        contenedor_pw, self.input_password = campo_password_con_ojito("Contraseña")
        layout.addWidget(contenedor_pw)

        # Botón entrar
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
            QPushButton:hover { background-color: #45a049; }
        """)
        boton_entrar.clicked.connect(self.intentar_login)
        self.input_password.returnPressed.connect(self.intentar_login)
        layout.addWidget(boton_entrar)

        layout.addSpacing(10)
        self.setLayout(layout)

    def intentar_login(self) -> None:
        """Valida las credenciales y redirige según el estado del usuario."""
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
            self._pedir_nueva_password(usuario_id)
        else:
            self.on_login_exitoso(usuario_id, rol)
            self.close()

    def _pedir_nueva_password(self, usuario_id: int) -> None:
        """Abre la pantalla de cambio de contraseña obligatorio."""
        from ui.cambiar_password import CambiarPassword
        self.cambiar_pw = CambiarPassword(usuario_id, lambda: self._login_post_cambio(usuario_id))
        self.cambiar_pw.show()

    def _login_post_cambio(self, usuario_id: int) -> None:
        """Completa el login después de que el usuario cambió su contraseña."""
        conexion = sqlite3.connect(DB_PATH)
        cursor = conexion.cursor()
        cursor.execute("SELECT rol FROM usuarios WHERE id = ?", (usuario_id,))
        rol = cursor.fetchone()[0]
        conexion.close()
        self.on_login_exitoso(usuario_id, rol)
        self.close()