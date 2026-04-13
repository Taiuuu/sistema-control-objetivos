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

DB_PATH = os.path.join(os.path.expanduser("~"), "VESP Control", "seguridad.db")
os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)


def conectar() -> sqlite3.Connection:
    """Retorna una conexión activa a la base de datos."""
    return sqlite3.connect(DB_PATH)


# =============================================================================
# CREACIÓN DE TABLAS
# =============================================================================

def crear_base_datos() -> None:
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
            supervisor3_id  INTEGER,
            FOREIGN KEY (supervisor1_id) REFERENCES supervisores(id),
            FOREIGN KEY (supervisor2_id) REFERENCES supervisores(id),
            FOREIGN KEY (supervisor3_id) REFERENCES supervisores(id)
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

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS auditoria (
            id                   INTEGER PRIMARY KEY AUTOINCREMENT,
            fecha                TEXT        NOT NULL,
            hora                 TEXT        NOT NULL,
            usuario_id           INTEGER,
            tipo_operacion       TEXT        NOT NULL,
            tabla                TEXT,
            registro_id          INTEGER,
            valores_anteriores   TEXT,
            valores_nuevos       TEXT,
            detalles             TEXT,
            estado               TEXT        DEFAULT 'EXITOSO',
            timestamp_creacion   TIMESTAMP   DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (usuario_id) REFERENCES usuarios(id)
        )
    """)

    cursor.execute("CREATE INDEX IF NOT EXISTS idx_auditoria_fecha ON auditoria(fecha DESC)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_auditoria_usuario ON auditoria(usuario_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_auditoria_tabla ON auditoria(tabla, registro_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_pasadas_fecha ON pasadas(fecha DESC)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_pasadas_objetivo_id ON pasadas(objetivo_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_pasadas_fecha_objetivo ON pasadas(fecha, objetivo_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_pasadas_supervisor_id ON pasadas(supervisor_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_pasadas_turno ON pasadas(turno)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_equipos_fecha ON equipos(fecha)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_equipos_fecha_turno ON equipos(fecha, turno)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_equipos_supervisor1_id ON equipos(supervisor1_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_equipos_supervisor2_id ON equipos(supervisor2_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_auditoria_fecha_usuario ON auditoria(fecha DESC, usuario_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_objetivos_fecha_fin ON objetivos(fecha_fin)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_supervisores_nombre ON supervisores(nombre)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_logs_usuario_id ON logs(usuario_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_logs_fecha ON logs(fecha DESC)")

    _crear_admin_si_no_existe(cursor)

    conexion.commit()
    conexion.close()
    print("Base de datos iniciada correctamente.")


# =============================================================================
# MIGRACIÓN — supervisor3_id
# =============================================================================

def migrar_supervisor3() -> None:
    """Agrega supervisor3_id a equipos si no existe (migración segura)."""
    conexion = conectar()
    cursor = conexion.cursor()
    try:
        cursor.execute(
            "ALTER TABLE equipos ADD COLUMN supervisor3_id INTEGER REFERENCES supervisores(id)"
        )
        conexion.commit()
        print("Migración: supervisor3_id agregado a equipos.")
    except sqlite3.OperationalError:
        pass  # La columna ya existe, no hacer nada
    conexion.close()


# =============================================================================
# USUARIO ADMIN POR DEFECTO
# =============================================================================

def _crear_admin_si_no_existe(cursor: sqlite3.Cursor) -> None:
    cursor.execute("SELECT COUNT(*) FROM usuarios")
    if cursor.fetchone()[0] == 0:
        password_hash = bcrypt.hashpw(b"0000", bcrypt.gensalt()).decode()
        cursor.execute("""
            INSERT INTO usuarios (username, password, rol, debe_cambiar_password)
            VALUES (?, ?, ?, ?)
        """, ("admin", password_hash, "admin", 0))