# =============================================================================
# VESP Organizations - Sistema de Control de Objetivos
# Pantalla de cambio de contraseña con validación en tiempo real
# =============================================================================

import sqlite3
import bcrypt
from database.db import DB_PATH
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QLineEdit, QPushButton, QMessageBox
)
from ui.components import GlassCard, PillButton
from ui.theme.theme_manager import get_theme_manager


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

    boton_ojo = PillButton("👁", "ghost")
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
# VALIDACIÓN DE CONTRASEÑA
# =============================================================================

def verificar_requisitos(password: str) -> dict:
    """
    Verifica los requisitos de seguridad de una contraseña.
    Retorna un dict con el estado de cada requisito (True/False).
    """
    return {
        "longitud":     8 <= len(password) <= 18,
        "mayuscula":    any(c.isupper() for c in password),
        "minuscula":    any(c.islower() for c in password),
        "numero":       any(c.isdigit() for c in password),
        "sin_espacios": " " not in password and len(password) > 0,
    }


LABELS_REQUISITOS = {
    "longitud":     "Entre 8 y 18 caracteres",
    "mayuscula":    "Al menos una mayúscula",
    "minuscula":    "Al menos una minúscula",
    "numero":       "Al menos un número",
    "sin_espacios": "Sin espacios",
}


# =============================================================================
# PANTALLA DE CAMBIO DE CONTRASEÑA
# =============================================================================

class CambiarPassword(QWidget):

    def __init__(self, usuario_id: int, on_completado):
        super().__init__()
        self.usuario_id = usuario_id
        self.on_completado = on_completado
        self.setWindowTitle("Cambiar contraseña")
        self.setFixedSize(380, 420)
        self._theme_manager = get_theme_manager()

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        card = GlassCard(content_margins=16)
        contenido = card.content_layout

        contenido.addWidget(QLabel("Nueva contraseña:"))
        contenedor1, self.input_nueva = campo_password_con_ojito("Nueva contraseña")
        contenido.addWidget(contenedor1)
        self.input_nueva.textChanged.connect(self._actualizar_indicadores)

        contenido.addWidget(QLabel("Repetir contraseña:"))
        contenedor2, self.input_repetir = campo_password_con_ojito("Repetir contraseña")
        contenido.addWidget(contenedor2)

        contenido.addSpacing(8)
        contenido.addWidget(QLabel("Requisitos:"))

        # Indicadores visuales de requisitos
        self.indicadores = {}
        for clave, texto in LABELS_REQUISITOS.items():
            label = QLabel(f"✗  {texto}")
            label.setProperty("valid", False)
            contenido.addWidget(label)
            self.indicadores[clave] = label

        contenido.addSpacing(8)

        boton_guardar = PillButton("Guardar", "primary")
        boton_guardar.setFixedHeight(40)
        boton_guardar.clicked.connect(self._guardar)
        contenido.addWidget(boton_guardar)

        layout.addWidget(card)
        self._theme_manager.theme_changed.connect(self._aplicar_tema)
        self._aplicar_tema(self._theme_manager.current())

    def _aplicar_tema(self, theme_name: str) -> None:
        tokens = self._theme_manager.tokens(theme_name)
        for label in self.indicadores.values():
            color = (
                tokens["success_text"]
                if label.property("valid")
                else tokens["danger_text"]
            )
            label.setStyleSheet(
                f"color: {color}; font-size: {tokens['font_size_sm']};"
            )

    def _actualizar_indicadores(self, texto: str) -> None:
        """Actualiza los indicadores visuales de requisitos en tiempo real."""
        requisitos = verificar_requisitos(texto)
        textos_dinamicos = {
            "longitud":     f"Entre 8 y 18 caracteres (ahora: {len(texto)})",
            "mayuscula":    "Al menos una mayúscula",
            "minuscula":    "Al menos una minúscula",
            "numero":       "Al menos un número",
            "sin_espacios": "Sin espacios",
        }
        for clave, cumple in requisitos.items():
            label = self.indicadores[clave]
            texto_label = textos_dinamicos[clave]
            if cumple:
                label.setText(f"✓  {texto_label}")
            else:
                label.setText(f"✗  {texto_label}")
            label.setProperty("valid", cumple)
        self._aplicar_tema(self._theme_manager.current())

    def _guardar(self) -> None:
        """Valida y guarda la nueva contraseña en la base de datos."""
        nueva = self.input_nueva.text()
        repetir = self.input_repetir.text()

        if not nueva or not repetir:
            QMessageBox.warning(self, "Error", "Completá los dos campos.")
            return

        if not all(verificar_requisitos(nueva).values()):
            QMessageBox.warning(self, "Error", "La contraseña no cumple todos los requisitos.")
            return

        if nueva != repetir:
            QMessageBox.warning(self, "Error", "Las contraseñas no coinciden.")
            return

        password_hash = bcrypt.hashpw(nueva.encode(), bcrypt.gensalt()).decode()

        conexion = sqlite3.connect(DB_PATH)
        cursor = conexion.cursor()
        cursor.execute("""
            UPDATE usuarios SET password = ?, debe_cambiar_password = 0 WHERE id = ?
        """, (password_hash, self.usuario_id))
        conexion.commit()
        conexion.close()

        QMessageBox.information(self, "Listo", "Contraseña actualizada correctamente.")
        self.on_completado()
        self.close()