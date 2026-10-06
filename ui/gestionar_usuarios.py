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
    QTableWidgetItem, QComboBox, QMessageBox, QMenu, QHeaderView
)
from ui.components import GlassCard, PillButton, StatusBadge
from ui.components.base import wrap_content_in_glass_card

# =============================================================================
# CONSULTAS A BASE DE DATOS
# =============================================================================

def cargar_usuarios() -> list:
    """Retorna todos los usuarios registrados en el sistema."""
    conexion = sqlite3.connect(DB_PATH)
    cursor = conexion.cursor()
    cursor.execute("SELECT id, username, rol, debe_cambiar_password FROM usuarios")
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


def cambiar_rol_usuario(usuario_id: int, nuevo_rol: str) -> None:
    """Cambia el rol de un usuario."""
    conexion = sqlite3.connect(DB_PATH)
    cursor = conexion.cursor()
    cursor.execute(
        "UPDATE usuarios SET rol = ? WHERE id = ?",
        (nuevo_rol, usuario_id)
    )
    conexion.commit()
    conexion.close()


def resetear_password(usuario_id: int) -> None:
    """Resetea contraseña a 0000."""
    password_hash = bcrypt.hashpw(
        "0000".encode(),
        bcrypt.gensalt()
    ).decode()

    conexion = sqlite3.connect(DB_PATH)
    cursor = conexion.cursor()
    cursor.execute("""
        UPDATE usuarios
        SET password = ?, debe_cambiar_password = 1
        WHERE id = ?
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

        # Nuevo usuario
        layout.addWidget(QLabel("Nuevo usuario:"))

        fila = QHBoxLayout()

        self.input_username = QLineEdit()
        self.input_username.setPlaceholderText("Nombre de usuario")

        self.selector_rol = QComboBox()
        self.selector_rol.addItems([
            "operador",
            "supervisor",
            "auditor",
            "gerente",
            "admin"
        ])

        fila.addWidget(self.input_username)
        fila.addWidget(self.selector_rol)

        layout.addLayout(fila)

        boton_agregar = PillButton("Agregar usuario", "primary")
        boton_agregar.setObjectName("PrimaryButton")
        boton_agregar.clicked.connect(self._agregar)
        layout.addWidget(boton_agregar)

        layout.addSpacing(10)

        # Tabla
        layout.addWidget(QLabel("Usuarios registrados:"))

        self.tabla = QTableWidget()
        self.tabla.setColumnCount(4)
        self.tabla.setShowGrid(False)
        self.tabla.setAlternatingRowColors(False)
        self.tabla.verticalHeader().setVisible(False)
        self.tabla.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.tabla.horizontalHeader().setStretchLastSection(True)
        self.tabla.setHorizontalHeaderLabels([
            "Usuario",
            "Rol",
            "Estado",
            "Acciones"
        ])

        self.tabla.setColumnWidth(0, 150)
        self.tabla.setColumnWidth(1, 130)
        self.tabla.setColumnWidth(2, 110)
        self.tabla.setColumnWidth(3, 220)

        layout.addWidget(self.tabla)

        self.setLayout(layout)
        wrap_content_in_glass_card(self)

        self._cargar_tabla()

    # =========================================================================
    # TABLA
    # =========================================================================

    def _cargar_tabla(self) -> None:
        usuarios = cargar_usuarios()

        self.tabla.setRowCount(len(usuarios))

        for fila, usuario in enumerate(usuarios):

            usuario_id, username, rol, debe_cambiar = usuario

            # Usuario
            self.tabla.setItem(
                fila,
                0,
                QTableWidgetItem(username)
            )

            # Rol
            combo = QComboBox()
            combo.addItems([
                "operador",
                "supervisor",
                "auditor",
                "gerente",
                "admin"
            ])
            combo.setCurrentText(rol)

            combo.currentTextChanged.connect(
                lambda nuevo_rol, uid=usuario_id:
                self._cambiar_rol(uid, nuevo_rol)
            )

            self.tabla.setCellWidget(fila, 1, combo)

            # Estado
            estado = StatusBadge(
                "Cambiar contraseña" if debe_cambiar else "Activo",
                "warning" if debe_cambiar else "ok",
            )
            self.tabla.setCellWidget(fila, 2, estado)

            # Botones
            if username != "admin":

                menu = QMenu(self)
                menu.addAction(
                    "Resetear contraseña",
                    lambda checked=False, uid=usuario_id: self._resetear(uid),
                )
                accion_eliminar = menu.addAction(
                    "Eliminar usuario",
                    lambda checked=False, uid=usuario_id: self._eliminar(uid),
                )
                accion_eliminar.setProperty("danger", True)
                boton_acciones = QPushButton("⋯")
                boton_acciones.setObjectName("ObjectiveActions")
                boton_acciones.setToolTip("Acciones del usuario")
                boton_acciones.setMenu(menu)
                self.tabla.setCellWidget(fila, 3, boton_acciones)

    # =========================================================================
    # ACCIONES
    # =========================================================================

    def _agregar(self) -> None:

        username = self.input_username.text().strip()
        rol = self.selector_rol.currentText()

        if not username:
            QMessageBox.warning(
                self,
                "Error",
                "El nombre de usuario no puede estar vacío."
            )
            return

        password_hash = bcrypt.hashpw(
            "0000".encode(),
            bcrypt.gensalt()
        ).decode()

        try:
            conexion = sqlite3.connect(DB_PATH)
            cursor = conexion.cursor()

            cursor.execute("""
                INSERT INTO usuarios
                (username, password, rol, debe_cambiar_password)
                VALUES (?, ?, ?, 1)
            """, (username, password_hash, rol))

            conexion.commit()
            conexion.close()

            QMessageBox.information(
                self,
                "Listo",
                f"Usuario '{username}' creado con contraseña 0000."
            )

            self.input_username.clear()
            self._cargar_tabla()

        except sqlite3.IntegrityError:
            QMessageBox.warning(
                self,
                "Error",
                "Ese nombre de usuario ya existe."
            )

    def _resetear(self, usuario_id: int) -> None:

        confirmar = QMessageBox.question(
            self,
            "Confirmar",
            "¿Resetear la contraseña a 0000?",
            QMessageBox.StandardButton.Yes |
            QMessageBox.StandardButton.No
        )

        if confirmar == QMessageBox.StandardButton.Yes:

            resetear_password(usuario_id)

            QMessageBox.information(
                self,
                "Listo",
                "Contraseña reseteada."
            )

            self._cargar_tabla()

    def _eliminar(self, usuario_id: int) -> None:

        confirmar = QMessageBox.question(
            self,
            "Confirmar",
            "¿Desea eliminar este usuario?",
            QMessageBox.StandardButton.Yes |
            QMessageBox.StandardButton.No
        )

        if confirmar == QMessageBox.StandardButton.Yes:

            eliminar_usuario(usuario_id)

            QMessageBox.information(
                self,
                "Listo",
                "Usuario eliminado correctamente."
            )

            self._cargar_tabla()

    def _cambiar_rol(self, usuario_id: int, nuevo_rol: str) -> None:

        cambiar_rol_usuario(usuario_id, nuevo_rol)