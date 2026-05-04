# =============================================================================
# VESP Organizations - Sistema de Control de Objetivos
# Pantalla de inicio de sesión
# =============================================================================

import sqlite3
import bcrypt
import re
import time
import hashlib
from collections import defaultdict
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel,
    QLineEdit, QPushButton, QMessageBox, QHBoxLayout
)
from PyQt6.QtGui import QPixmap, QIcon
from PyQt6.QtCore import Qt
from database.db import DB_PATH
from services.assets import ruta_asset
from ui.animaciones import animar_entrada
from services.tema import obtener_tema_actual


# =============================================================================
# RATE LIMITING Y SEGURIDAD
# =============================================================================

# Rate limiting: máximo 5 intentos por IP/usuario en 15 minutos
_rate_limits = defaultdict(list)
MAX_INTENTOS = 5
VENTANA_TIEMPO = 15 * 60  # 15 minutos en segundos

def _limpiar_rate_limits():
    """Limpia entradas expiradas del rate limiting."""
    ahora = time.time()
    for key in list(_rate_limits.keys()):
        _rate_limits[key] = [t for t in _rate_limits[key] if ahora - t < VENTANA_TIEMPO]
        if not _rate_limits[key]:
            del _rate_limits[key]

def _verificar_rate_limit(username: str, ip_address: str = "localhost") -> bool:
    """
    Verifica si el usuario/IP ha excedido el límite de intentos.
    Retorna True si está permitido, False si debe bloquearse.
    """
    _limpiar_rate_limits()
    key = f"{username}:{ip_address}"
    ahora = time.time()

    # Contar intentos en la ventana de tiempo
    intentos_recientes = [t for t in _rate_limits[key] if ahora - t < VENTANA_TIEMPO]

    if len(intentos_recientes) >= MAX_INTENTOS:
        return False

    # Registrar este intento
    _rate_limits[key].append(ahora)
    return True

def _sanitizar_input(texto: str, max_longitud: int = 100) -> str:
    """
    Sanitiza input de usuario eliminando caracteres peligrosos.
    """
    if not texto:
        return ""

    # Remover caracteres de control y espacios extra
    texto = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', texto.strip())

    # Limitar longitud
    if len(texto) > max_longitud:
        texto = texto[:max_longitud]

    return texto

def _validar_username(username: str) -> bool:
    """
    Valida formato del nombre de usuario.
    Solo letras, números, guiones y puntos. 3-50 caracteres.
    """
    if not username or len(username) < 3 or len(username) > 50:
        return False

    patron = r'^[a-zA-Z0-9._-]+$'
    return bool(re.match(patron, username))

def _validar_password(password: str) -> bool:
    """
    Valida fortaleza básica de contraseña.
    Mínimo 8 caracteres, al menos una letra y un número.
    """
    if len(password) < 8:
        return False

    tiene_letra = bool(re.search(r'[a-zA-Z]', password))
    tiene_numero = bool(re.search(r'[0-9]', password))

    return tiene_letra and tiene_numero


# =============================================================================
# AUTENTICACIÓN
# =============================================================================

def verificar_login(username: str, password: str, ip_address: str = "localhost") -> tuple | None:
    """
    Verifica las credenciales del usuario contra la base de datos con validaciones de seguridad.
    Retorna (id, rol, debe_cambiar_password) si son correctas, None si no.

    Args:
        username: Nombre de usuario (será sanitizado)
        password: Contraseña sin encriptar
        ip_address: Dirección IP del cliente para rate limiting

    Returns:
        Tupla (usuario_id, rol, debe_cambiar_password) o None si fallan credenciales

    Raises:
        Logs de error para intentos fallidos de seguridad
    """
    # Sanitizar inputs
    username = _sanitizar_input(username, 50)
    password = _sanitizar_input(password, 128)  # bcrypt tiene límite de 72 bytes, pero sanitizamos

    # Validar formato básico
    if not _validar_username(username):
        from services.logger import registrar_accion
        registrar_accion(None, f"Intento de login con username inválido: '{username}'")
        return None

    # Verificar rate limiting
    if not _verificar_rate_limit(username, ip_address):
        from services.logger import registrar_accion
        registrar_accion(None, f"Rate limit excedido para usuario: '{username}' desde {ip_address}")
        time.sleep(2)  # Delay adicional para disuadir ataques
        return None

    try:
        conexion = sqlite3.connect(DB_PATH)
        cursor = conexion.cursor()
        cursor.execute("""
            SELECT id, rol, debe_cambiar_password, password
            FROM usuarios WHERE username = ? AND activo = 1
        """, (username,))
        resultado = cursor.fetchone()
        conexion.close()

        if not resultado:
            from services.logger import registrar_accion
            registrar_accion(None, f"Intento de login fallido: usuario no existe o inactivo '{username}' desde {ip_address}")
            return None

        try:
            # Validar contraseña con bcrypt
            if bcrypt.checkpw(password.encode('utf-8'), resultado[3].encode('utf-8')):
                # Login exitoso - limpiar rate limit para este usuario
                key = f"{username}:{ip_address}"
                if key in _rate_limits:
                    del _rate_limits[key]

                from services.logger import registrar_accion
                registrar_accion(resultado[0], f"Login exitoso desde {ip_address}")
                return (resultado[0], resultado[1], resultado[2])
            else:
                # Contraseña incorrecta
                from services.logger import registrar_accion
                registrar_accion(resultado[0], f"Intento de login fallido: contraseña incorrecta desde {ip_address}")
                return None
        except ValueError as e:
            # Error en validación de hash bcrypt - posible corrupción de datos
            from services.logger import registrar_accion
            registrar_accion(resultado[0], f"⚠️ Error bcrypt en login desde {ip_address}: {e}")
            print(f"❌ Error bcrypt para usuario {username}: {e}")
            return None

    except sqlite3.Error as e:
        print(f"❌ Error BD en verificar_login: {e}")
        from services.logger import registrar_accion
        registrar_accion(None, f"Error BD en login desde {ip_address}: {e}")
        return None
    except Exception as e:
        print(f"❌ Error inesperado en verificar_login: {e}")
        import traceback
        traceback.print_exc()
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
        self.move(100, 100)
        self.resize(400, 540)
        self.setMinimumSize(360, 520)
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
        nombre_color = "#4CAF50" if obtener_tema_actual() == "oscuro" else "#2E7D32"
        nombre_label.setStyleSheet(f"font-size: 18px; font-weight: bold; color: {nombre_color};")
        layout.addWidget(nombre_label)

        subtitulo = QLabel("Seguridad Privada")
        subtitulo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitulo_color = "#888" if obtener_tema_actual() == "oscuro" else "#666"
        subtitulo.setStyleSheet(f"font-size: 12px; color: {subtitulo_color};")
        layout.addWidget(subtitulo)

        # Versión actual
        try:
            version = open(ruta_asset("version.txt")).read().strip()
        except Exception:
            version = ""
        version_label = QLabel(f"v{version}")
        version_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        version_color = "#555" if obtener_tema_actual() == "oscuro" else "#777"
        version_label.setStyleSheet(f"font-size: 10px; color: {version_color};")
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
        if obtener_tema_actual() == "oscuro":
            boton_bg = "#4CAF50"
            boton_hover = "#45a049"
        else:
            boton_bg = "#2E7D32"
            boton_hover = "#1B5E20"
        boton_entrar.setStyleSheet(f"""
            QPushButton {{
                background-color: {boton_bg};
                color: white;
                font-size: 14px;
                font-weight: bold;
                border-radius: 4px;
            }}
            QPushButton:hover {{ background-color: {boton_hover}; }}
        """)
        boton_entrar.clicked.connect(self.intentar_login)
        self.input_password.returnPressed.connect(self.intentar_login)
        layout.addWidget(boton_entrar)

        layout.addSpacing(10)
        self.setLayout(layout)
        animar_entrada(self)

    def _validar_entrada_login(self, username: str, password: str) -> bool:
        """
        Valida la entrada del usuario según políticas de seguridad.
        
        Args:
            username: Nombre de usuario ingresado
            password: Contraseña ingresada
            
        Returns:
            True si la entrada es válida, False si hay error (muestra mensaje)
        """
        # ✅ Validación de vacío
        if not username or not password:
            QMessageBox.warning(self, "Error", "Completá usuario y contraseña.")
            return False
        
        # ✅ Validación de largo mínimo/máximo
        if len(username) < 3:
            QMessageBox.warning(self, "Error", "Usuario debe tener mínimo 3 caracteres.")
            return False
        
        if len(username) > 50:
            QMessageBox.warning(self, "Error", "Usuario no puede exceder 50 caracteres.")
            return False
        
        if len(password) < 4:
            QMessageBox.warning(self, "Error", "Contraseña debe tener mínimo 4 caracteres.")
            return False
        
        if len(password) > 100:
            QMessageBox.warning(self, "Error", "Contraseña no puede exceder 100 caracteres.")
            return False
        
        # ✅ Validación de caracteres (username solo alfanuméricos + underscore)
        if not all(c.isalnum() or c == '_' for c in username):
            QMessageBox.warning(
                self, 
                "Error", 
                "Usuario solo puede contener letras, números y guiones bajos (_)."
            )
            return False
        
        # ✅ No permitir espacios en username
        if ' ' in username:
            QMessageBox.warning(self, "Error", "Usuario no puede contener espacios.")
            return False
        
        return True

    def intentar_login(self) -> None:
        """Valida las credenciales y redirige según el estado del usuario."""
        username = self.input_usuario.text().strip()
        password = self.input_password.text()

        # ✅ Validar entrada antes de intentar login
        if not self._validar_entrada_login(username, password):
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
        """
        Completa el login después de que el usuario cambió su contraseña.
        
        Args:
            usuario_id: ID del usuario que cambió la contraseña
            
        Raises:
            Maneja casos donde el usuario fue eliminado entre cambio de password y login
        """
        try:
            conexion = sqlite3.connect(DB_PATH)
            cursor = conexion.cursor()
            cursor.execute("SELECT rol FROM usuarios WHERE id = ?", (usuario_id,))
            resultado = cursor.fetchone()
            conexion.close()
            
            if resultado is None:
                # Usuario fue eliminado - caso raro pero posible en entorno multi-usuario
                QMessageBox.warning(
                    self, 
                    "Error", 
                    "El usuario fue eliminado. Por favor, contacte al administrador."
                )
                print(f"⚠️ Usuario {usuario_id} no encontrado post-cambio password")
                return
            
            rol = resultado[0]
            self.on_login_exitoso(usuario_id, rol)
            self.close()
        except sqlite3.Error as e:
            QMessageBox.critical(self, "Error", f"Error al recuperar datos del usuario: {e}")
            print(f"❌ Error BD en _login_post_cambio: {e}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error inesperado: {e}")
            print(f"❌ Error inesperado en _login_post_cambio: {e}")