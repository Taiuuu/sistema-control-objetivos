# =============================================================================
# VESP Organizations - Sistema de Control de Objetivos
# Módulo de encriptación AES-256 para datos sensibles
# =============================================================================

import os
import base64
import hashlib
import bcrypt
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import padding
from dotenv import load_dotenv
import secrets

# =============================================================================
# CONFIGURACIÓN DE ENCRIPTACIÓN
# =============================================================================

# Clave maestra para derivar claves (debe estar en variable de entorno en producción)
load_dotenv()

_clave_raw = os.environ.get('VESP_ENCRYPTION_KEY')

if not _clave_raw:
    raise RuntimeError(
        "Falta el archivo .env con VESP_ENCRYPTION_KEY.\n"
        "Copiá .env.example como .env y completá la clave."
    )

_clave_bytes = hashlib.sha256(_clave_raw.encode()).digest()
MASTER_KEY = base64.urlsafe_b64encode(_clave_bytes)

# Algoritmo y parámetros
KEY_LENGTH = 32  # 256 bits para AES-256
SALT_LENGTH = 16
IV_LENGTH = 16

# =============================================================================
# FUNCIONES DE DERIVACIÓN DE CLAVES
# =============================================================================

def _derive_key(password, salt):
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=100000,
    )
    password_bytes = password if isinstance(password, bytes) else password.encode()
    return kdf.derive(password_bytes)

def _generate_salt() -> bytes:
    """Genera un salt aleatorio."""
    return secrets.token_bytes(SALT_LENGTH)


# =============================================================================
# FUNCIONES DE ENCRIPTACIÓN/DESENCRIPTACIÓN
# =============================================================================

def encriptar_datos(datos: str) -> str:
    """
    Encripta datos sensibles usando AES-256.
    Args:
        datos: String a encriptar
    Returns:
        String base64 con salt + IV + datos encriptados
    """
    # Generar salt e IV
    salt = _generate_salt()
    iv = secrets.token_bytes(IV_LENGTH)

    # Derivar clave
    key = _derive_key(MASTER_KEY, salt)

    # Preparar datos para encriptación (PKCS7 padding)
    padder = padding.PKCS7(algorithms.AES.block_size).padder()
    datos_padded = padder.update(datos.encode()) + padder.finalize()

    # Encriptar
    cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend())
    encryptor = cipher.encryptor()
    datos_encriptados = encryptor.update(datos_padded) + encryptor.finalize()

    # Combinar salt + IV + datos encriptados y codificar en base64
    combined = salt + iv + datos_encriptados
    return base64.b64encode(combined).decode()


def desencriptar_datos(datos_encriptados: str) -> str:
    """
    Desencripta datos previamente encriptados con AES-256.
    Args:
        datos_encriptados: String base64 con los datos encriptados
    Returns:
        String desencriptado original
    """
    try:
        # Decodificar de base64
        combined = base64.b64decode(datos_encriptados)

        # Extraer salt, IV y datos encriptados
        salt = combined[:SALT_LENGTH]
        iv = combined[SALT_LENGTH:SALT_LENGTH + IV_LENGTH]
        datos_encriptados_puros = combined[SALT_LENGTH + IV_LENGTH:]

        # Derivar clave
        key = _derive_key(MASTER_KEY, salt)

        # Desencriptar
        cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend())
        decryptor = cipher.decryptor()
        datos_padded = decryptor.update(datos_encriptados_puros) + decryptor.finalize()

        # Remover padding
        unpadder = padding.PKCS7(algorithms.AES.block_size).unpadder()
        datos_originales = unpadder.update(datos_padded) + unpadder.finalize()

        return datos_originales.decode()

    except Exception as e:
        raise ValueError(f"Error al desencriptar datos: {e}")


# =============================================================================
# FUNCIONES DE VALIDACIÓN DE CONTRASEÑAS
# =============================================================================

def validar_contrasena_fuerte(contrasena: str) -> tuple[bool, str]:
    """
    Valida que una contraseña cumpla con políticas de seguridad.
    Args:
        contrasena: Contraseña a validar
    Returns:
        (válida: bool, mensaje: str)
    """
    if len(contrasena) < 8:
        return False, "La contraseña debe tener al menos 8 caracteres"

    if not any(c.isupper() for c in contrasena):
        return False, "La contraseña debe contener al menos una letra mayúscula"

    if not any(c.islower() for c in contrasena):
        return False, "La contraseña debe contener al menos una letra minúscula"

    if not any(c.isdigit() for c in contrasena):
        return False, "La contraseña debe contener al menos un número"

    if not any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in contrasena):
        return False, "La contraseña debe contener al menos un carácter especial"

    return True, "Contraseña válida"


def generar_contrasena_segura(longitud: int = 12) -> str:
    """
    Genera una contraseña segura aleatoria.
    Args:
        longitud: Longitud deseada (mínimo 8)
    Returns:
        Contraseña segura
    """
    longitud = max(longitud, 8)

    # Caracteres disponibles
    minusculas = "abcdefghijklmnopqrstuvwxyz"
    mayusculas = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    digitos = "0123456789"
    especiales = "!@#$%^&*()_+-=[]{}|;:,.<>?"

    # Asegurar al menos un carácter de cada tipo
    contrasena = [
        secrets.choice(minusculas),
        secrets.choice(mayusculas),
        secrets.choice(digitos),
        secrets.choice(especiales)
    ]

    # Completar con caracteres aleatorios
    todos_caracteres = minusculas + mayusculas + digitos + especiales
    while len(contrasena) < longitud:
        contrasena.append(secrets.choice(todos_caracteres))

    # Mezclar
    secrets.SystemRandom().shuffle(contrasena)

    return ''.join(contrasena)


# =============================================================================
# FUNCIONES DE HASHING DE CONTRASEÑAS CON BCRYPT
# =============================================================================

def hashear_contrasena(contrasena: str) -> str:
    """
    Hashea una contraseña usando bcrypt para almacenamiento seguro.
    Args:
        contrasena: Contraseña en texto plano
    Returns:
        Hash bcrypt de la contraseña
    """
    if not contrasena:
        raise ValueError("La contraseña no puede estar vacía")

    # Convertir a bytes si es necesario
    if isinstance(contrasena, str):
        contrasena = contrasena.encode('utf-8')

    # Generar salt y hashear
    salt = bcrypt.gensalt(rounds=12)  # 12 rounds = ~2^12 iteraciones
    hash_bytes = bcrypt.hashpw(contrasena, salt)

    # Retornar como string para almacenamiento en BD
    return hash_bytes.decode('utf-8')


def verificar_contrasena(contrasena: str, hash_almacenado: str) -> bool:
    """
    Verifica una contraseña contra su hash almacenado.
    Args:
        contrasena: Contraseña en texto plano
        hash_almacenado: Hash bcrypt almacenado
    Returns:
        True si la contraseña es correcta
    """
    if not contrasena or not hash_almacenado:
        return False

    try:
        # Convertir a bytes
        contrasena_bytes = contrasena.encode('utf-8')
        hash_bytes = hash_almacenado.encode('utf-8')

        # Verificar con bcrypt
        return bcrypt.checkpw(contrasena_bytes, hash_bytes)
    except (ValueError, TypeError):
        # Hash corrupto o formato inválido
        return False


def necesita_rehash(hash_almacenado: str, rounds_actuales: int = 12) -> bool:
    """
    Verifica si un hash necesita ser actualizado (nueva política de seguridad).
    Args:
        hash_almacenado: Hash bcrypt actual
        rounds_actuales: Número de rounds que debería tener
    Returns:
        True si necesita rehash
    """
    try:
        # bcrypt incluye el número de rounds en el hash
        # Formato: $2b$rounds$salt$hash
        partes = hash_almacenado.split('$')
        if len(partes) >= 4:
            rounds_hash = int(partes[2])
            return rounds_hash < rounds_actuales
        return True  # Formato desconocido, mejor rehash
    except (ValueError, IndexError):
        return True  # Error al parsear, mejor rehash