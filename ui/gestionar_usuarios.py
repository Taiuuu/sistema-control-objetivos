# =============================================================================
# VESP Organizations - Sistema de Control de Objetivos
# Pantalla de gestión de usuarios (solo admin)
# =============================================================================

import sqlite3
import bcrypt
from database.db import DB_PATH
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QLineEdit, QPushButton, QTableWidget,
    QTableWidgetItem, QComboBox, QMessageBox
)

# =============================================================================
# CONSULTAS A BASE DE DATOS
# =============================================================================

def cargar_usuarios() -> list:
    """Retorna todos los usuarios registrados en el sistema."""
    conexion = sqlite3.connect(DB_PATH)
    cursor = conexion.cursor()
    cursor.execute("SELECT id, username, rol FROM usuarios")
    resultado = cursor.fetchall()
    conexion.close()
    return resultado


def eliminar_usuario(usuario_id: int) -> None:
    """Elimina un usuario del sistema por su ID."""
    conexion = sqlite3.connect(DB_PATH)
    cursor = conexion.cursor()
    cursor.execute("DELETE FROM usuarios WHERE id = ?", (usuario_id,))
    conexion.commit()
    conexion.close()


def resetear_password(usuario_id: int) -> None:
    """Resetea la contraseña de un usuario a 0000 y lo obliga a cambiarla al próximo login."""
    password_hash = bcrypt.hashpw("0000".encode(), bcrypt.gensalt()).decode()
    conexion = sqlite3.connect(DB_PATH)
    cursor = conexion.cursor()
    cursor.execute("""
        UPDATE usuarios SET password = ?, debe_cambiar_password = 1 WHERE id = ?
    """, (password_hash, usuario_id))
    conexion.commit()
    conexion.close()


# =============================================================================
# PANTALLA DE GESTIÓN DE USUARIOS
# =============================================================================

class GestionarUsuarios(QWidget):

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Gestionar usuarios")
        self.setGeometry(300, 300, 550, 400)

        layout = QVBoxLayout()

        # Formulario para agregar nuevo usuario
        layout.addWidget(QLabel("Nuevo usuario:"))
        fila = QHBoxLayout()
        self.input_username = QLineEdit()
        self.input_username.setPlaceholderText("Nombre de usuario")
        self.selector_rol = QComboBox()
        self.selector_rol.addItems(["operador", "admin"])
        fila.addWidget(self.input_username)
        fila.addWidget(self.selector_rol)
        layout.addLayout(fila)

        boton_agregar = QPushButton("Agregar usuario")
        boton_agregar.clicked.connect(self._agregar)
        layout.addWidget(boton_agregar)

        layout.addSpacing(10)

        # Tabla de usuarios registrados
        layout.addWidget(QLabel("Usuarios registrados:"))
        self.tabla = QTableWidget()
        self.tabla.setColumnCount(3)
        self.tabla.setHorizontalHeaderLabels(["Usuario", "Rol", "Acciones"])
        self.tabla.setColumnWidth(0, 180)
        self.tabla.setColumnWidth(1, 100)
        self.tabla.setColumnWidth(2, 200)
        layout.addWidget(self.tabla)

        self.setLayout(layout)
        self._cargar_tabla()

    def _cargar_tabla(self) -> None:
        """Carga la lista de usuarios en la tabla."""
        usuarios = cargar_usuarios()
        self.tabla.setRowCount(len(usuarios))

        for i, u in enumerate(usuarios):
            self.tabla.setItem(i, 0, QTableWidgetItem(u[1]))
            self.tabla.setItem(i, 1, QTableWidgetItem(u[2]))

            # El usuario admin no puede ser eliminado
            if u[1] != "admin":
                fila_botones = QWidget()
                fila_layout = QHBoxLayout(fila_botones)
                fila_layout.setContentsMargins(0, 0, 0, 0)

                boton_reset = QPushButton("Resetear")
                boton_reset.clicked.connect(lambda checked, uid=u[0]: self._resetear(uid))

                boton_eliminar = QPushButton("Eliminar")
                boton_eliminar.clicked.connect(lambda checked, uid=u[0]: self._eliminar(uid))

                fila_layout.addWidget(boton_reset)
                fila_layout.addWidget(boton_eliminar)
                self.tabla.setCellWidget(i, 2, fila_botones)

    def _agregar(self) -> None:
        """Crea un nuevo usuario con contraseña 0000 por defecto."""
        username = self.input_username.text().strip()
        rol = self.selector_rol.currentText()

        if not username:
            QMessageBox.warning(self, "Error", "El nombre de usuario no puede estar vacío.")
            return

        password_hash = bcrypt.hashpw("0000".encode(), bcrypt.gensalt()).decode()

        try:
            conexion = sqlite3.connect(DB_PATH)
            cursor = conexion.cursor()
            cursor.execute("""
                INSERT INTO usuarios (username, password, rol, debe_cambiar_password)
                VALUES (?, ?, ?, 1)
            """, (username, password_hash, rol))
            conexion.commit()
            conexion.close()
            QMessageBox.information(self, "Listo", f"Usuario '{username}' creado con contraseña 0000.")
            self.input_username.clear()
            self._cargar_tabla()
        except sqlite3.IntegrityError:
            QMessageBox.warning(self, "Error", "Ese nombre de usuario ya existe.")

    def _resetear(self, usuario_id: int) -> None:
        """Resetea la contraseña del usuario a 0000."""
        confirmar = QMessageBox.question(
            self, "Confirmar", "¿Resetear la contraseña a 0000?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if confirmar == QMessageBox.StandardButton.Yes:
            resetear_password(usuario_id)
            QMessageBox.information(self, "Listo", "Contraseña reseteada. El usuario deberá cambiarla al próximo inicio.")

    def _eliminar(self, usuario_id: int) -> None:
        """Elimina un usuario del sistema."""
        confirmar = QMessageBox.question(
            self, "Confirmar", "¿Seguro que querés eliminar este usuario?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if confirmar == QMessageBox.StandardButton.Yes:
            eliminar_usuario(usuario_id)
            self._cargar_tabla()