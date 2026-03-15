# =============================================================================
# VESP Organizations - Sistema de Control de Objetivos
# Módulo de conexión y creación de base de datos (SQLite)
# =============================================================================

import sqlite3
import os
import bcrypt


# =============================================================================
# CONEXIÓN
# =============================================================================

# Base de datos guardada en la carpeta del usuario para evitar problemas de permisos
DB_PATH = os.path.join(os.path.expanduser("~"), "VESP Control", "seguridad.db")
os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)


def conectar() -> sqlite3.Connection:
    """Retorna una conexión activa a la base de datos."""
    return sqlite3.connect(DB_PATH)


# =============================================================================
# CREACIÓN DE TABLAS
# =============================================================================

def crear_base_datos() -> None:
    """
    Crea todas las tablas del sistema si no existen.
    También inserta el usuario admin por defecto en el primer uso.
    """
    conexion = conectar()
    cursor = conexion.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS objetivos (
            id           INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre       TEXT    NOT NULL,
            fecha_inicio TEXT,
            fecha_fin    TEXT,
            dias_semana  TEXT
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS supervisores (
            id     INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS pasadas (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            fecha         TEXT,
            hora          TEXT,
            turno         TEXT,
            objetivo_id   INTEGER,
            supervisor_id INTEGER,
            FOREIGN KEY (objetivo_id)   REFERENCES objetivos(id),
            FOREIGN KEY (supervisor_id) REFERENCES supervisores(id)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS equipos (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            fecha           TEXT,
            turno           TEXT,
            supervisor1_id  INTEGER,
            supervisor2_id  INTEGER,
            FOREIGN KEY (supervisor1_id) REFERENCES supervisores(id),
            FOREIGN KEY (supervisor2_id) REFERENCES supervisores(id)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS notas (
            id    INTEGER PRIMARY KEY AUTOINCREMENT,
            fecha TEXT,
            nota  TEXT
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS usuarios (
            id                    INTEGER PRIMARY KEY AUTOINCREMENT,
            username              TEXT    NOT NULL UNIQUE,
            password              TEXT    NOT NULL,
            rol                   TEXT    NOT NULL DEFAULT 'operador',
            debe_cambiar_password INTEGER DEFAULT 1
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS logs (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            fecha      TEXT,
            hora       TEXT,
            usuario_id INTEGER,
            accion     TEXT,
            FOREIGN KEY (usuario_id) REFERENCES usuarios(id)
        )
    """)

    _crear_admin_si_no_existe(cursor)

    conexion.commit()
    conexion.close()
    print("Base de datos iniciada correctamente.")


# =============================================================================
# USUARIO ADMIN POR DEFECTO
# =============================================================================

def _crear_admin_si_no_existe(cursor: sqlite3.Cursor) -> None:
    """
    Crea el usuario admin con contraseña 0000 si no hay ningún usuario registrado.
    El admin no necesita cambiar la contraseña al primer inicio.
    """
    cursor.execute("SELECT COUNT(*) FROM usuarios")
    if cursor.fetchone()[0] == 0:
        password_hash = bcrypt.hashpw(b"0000", bcrypt.gensalt()).decode()
        cursor.execute("""
            INSERT INTO usuarios (username, password, rol, debe_cambiar_password)
            VALUES (?, ?, ?, ?)
        """, ("admin", password_hash, "admin", 0))