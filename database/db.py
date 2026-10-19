# =============================================================================
# VESP Organizations - Sistema de Control de Objetivos
# Módulo de conexión y creación de base de datos (SQLite)
# =============================================================================

import sqlite3
import os
import bcrypt
import logging
import threading
import weakref
import json
from core.configuracion import DB_PATH


DB_PATH = str(DB_PATH)
os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
SCHEMA_VERSION = 2
logger = logging.getLogger(__name__)


def configurar_conexion_sqlite(conexion: sqlite3.Connection) -> sqlite3.Connection:
    """Aplica siempre los límites de concurrencia e integridad de la app."""
    conexion.execute("PRAGMA foreign_keys=ON")
    conexion.execute("PRAGMA journal_mode=WAL")
    # NORMAL equilibra durabilidad y rendimiento; los commits confirmados se
    # recuperan mediante WAL y evita el costo de sincronizar cada escritura.
    conexion.execute("PRAGMA synchronous=NORMAL")
    conexion.execute("PRAGMA busy_timeout=5000")
    return conexion

_sqlite3_connect_original = sqlite3.connect
_conexiones_abiertas: weakref.WeakSet[sqlite3.Connection] = weakref.WeakSet()
_conexiones_lock = threading.RLock()


class _ConexionSeguida(sqlite3.Connection):
    """Permite cerrar conexiones abiertas antes de reemplazar la base."""

    __slots__ = ("__weakref__",)

    def close(self) -> None:
        try:
            super().close()
        except Exception:
            raise
        else:
            with _conexiones_lock:
                _conexiones_abiertas.discard(self)

def _sqlite3_connect_with_pragmas(*args, **kwargs):
    kwargs.setdefault("factory", _ConexionSeguida)
    conexion = _sqlite3_connect_original(*args, **kwargs)
    with _conexiones_lock:
        _conexiones_abiertas.add(conexion)
    try:
        return configurar_conexion_sqlite(conexion)
    except Exception:
        conexion.close()
        raise

sqlite3.connect = _sqlite3_connect_with_pragmas


def cerrar_todas_las_conexiones() -> None:
    """Cierra las conexiones de la app antes de reemplazar el archivo SQLite."""
    with _conexiones_lock:
        conexiones = tuple(_conexiones_abiertas)
    errores = []
    for conexion in conexiones:
        try:
            conexion.close()
        except sqlite3.Error as error:
            errores.append(error)
            logger.exception("No se pudo cerrar una conexión SQLite")
    if errores:
        raise RuntimeError(
            f"No se pudieron cerrar {len(errores)} conexión(es) SQLite"
        ) from errores[0]


def cerrar_conexiones_de(ruta: str | os.PathLike[str]) -> None:
    """Cierra solo las conexiones que mantienen abierto el archivo indicado."""
    objetivo = os.path.normcase(os.path.abspath(ruta))
    with _conexiones_lock:
        conexiones = tuple(_conexiones_abiertas)
    for conexion in conexiones:
        try:
            rutas = conexion.execute("PRAGMA database_list").fetchall()
            if any(
                nombre and os.path.normcase(os.path.abspath(nombre)) == objetivo
                for _, _, nombre in rutas
            ):
                conexion.close()
        except sqlite3.Error:
            logger.exception("No se pudo identificar una conexión SQLite abierta")


def conectar() -> sqlite3.Connection:
    return sqlite3.connect(DB_PATH)


def verificar_integridad(ruta: str | None = None) -> tuple[bool, list[str]]:
    """Ejecuta las comprobaciones SQLite sin modificar el contenido."""
    try:
        conexion = sqlite3.connect(ruta or DB_PATH)
    except sqlite3.DatabaseError as error:
        logger.exception("No se pudo abrir la base para comprobar su integridad")
        return False, [f"integrity_check: {error}"]
    try:
        resultado = [
            fila[0] for fila in conexion.execute("PRAGMA integrity_check").fetchall()
        ]
        claves_foraneas = conexion.execute("PRAGMA foreign_key_check").fetchall()
        errores = []
        if resultado != ["ok"]:
            errores.extend(f"integrity_check: {mensaje}" for mensaje in resultado)
        if claves_foraneas:
            errores.extend(
                f"foreign_key_check: tabla={fila[0]} fila={fila[1]} "
                f"referencia={fila[2]}"
                for fila in claves_foraneas
            )
        return not errores, errores
    finally:
        conexion.close()


def crear_base_datos() -> None:
    _respaldar_duplicados_naturales_antes_de_migrar()
    conexion = conectar()
    cursor = conexion.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS objetivos (
            id           INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre       TEXT    NOT NULL,
            descripcion  TEXT,
            fecha_inicio TEXT,
            fecha_fin    TEXT,
            dias_semana  TEXT,
            activo       INTEGER DEFAULT 1,
            es_placeholder INTEGER NOT NULL DEFAULT 0
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS objetivos_aliases (
            id                       INTEGER PRIMARY KEY AUTOINCREMENT,
            objetivo_id              INTEGER NOT NULL,
            nombre_alias             TEXT NOT NULL,
            nombre_alias_normalizado TEXT NOT NULL UNIQUE,
            FOREIGN KEY (objetivo_id) REFERENCES objetivos(id)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS objetivo_periodos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            objetivo_id INTEGER NOT NULL,
            fecha_inicio TEXT NOT NULL,
            fecha_fin TEXT,
            FOREIGN KEY (objetivo_id) REFERENCES objetivos(id) ON DELETE CASCADE
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS feriados (
            id           INTEGER PRIMARY KEY AUTOINCREMENT,
            fecha        TEXT NOT NULL UNIQUE,
            descripcion  TEXT
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS supervisores (
            id           INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre       TEXT NOT NULL,
            fecha_alta   TEXT,
            fecha_baja   TEXT,
            es_placeholder INTEGER NOT NULL DEFAULT 0
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
            notas         TEXT,
            fecha_operativa TEXT,
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
            debe_cambiar_password INTEGER DEFAULT 1,
            activo                INTEGER DEFAULT 1
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
        CREATE TABLE IF NOT EXISTS preferencias_usuario (
            usuario_id INTEGER NOT NULL,
            clave TEXT NOT NULL,
            valor TEXT NOT NULL,
            PRIMARY KEY (usuario_id, clave),
            FOREIGN KEY (usuario_id) REFERENCES usuarios(id) ON DELETE CASCADE
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
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_objetivos_aliases_objetivo ON objetivos_aliases(objetivo_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_objetivo_periodos_objetivo_fechas ON objetivo_periodos(objetivo_id, fecha_inicio, fecha_fin)")
    cursor.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_feriados_fecha ON feriados(fecha)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_supervisores_nombre ON supervisores(nombre)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_logs_usuario_id ON logs(usuario_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_logs_fecha ON logs(fecha DESC)")

    migrar_supervisores_placeholder(cursor)
    migrar_objetivos_campos(cursor)
    migrar_pasadas_campos(cursor)
    migrar_clave_natural_pasadas(cursor)
    cursor.execute("""
        CREATE TRIGGER IF NOT EXISTS trg_pasadas_no_placeholder_insert
        BEFORE INSERT ON pasadas
        WHEN EXISTS (
            SELECT 1 FROM objetivos
            WHERE id = NEW.objetivo_id AND es_placeholder = 1
        ) OR EXISTS (
            SELECT 1 FROM supervisores
            WHERE id = NEW.supervisor_id AND es_placeholder = 1
        )
        BEGIN
            SELECT RAISE(ABORT, 'No se puede registrar una pasada con fichas históricas incompletas');
        END
    """)
    cursor.execute("""
        CREATE TRIGGER IF NOT EXISTS trg_pasadas_no_placeholder_update
        BEFORE UPDATE OF objetivo_id, supervisor_id ON pasadas
        WHEN EXISTS (
            SELECT 1 FROM objetivos
            WHERE id = NEW.objetivo_id AND es_placeholder = 1
        ) OR EXISTS (
            SELECT 1 FROM supervisores
            WHERE id = NEW.supervisor_id AND es_placeholder = 1
        )
        BEGIN
            SELECT RAISE(ABORT, 'No se puede asociar una pasada nueva a fichas históricas incompletas');
        END
    """)
    cursor.execute("""
        CREATE TRIGGER IF NOT EXISTS trg_supervisores_preservar_historial
        BEFORE DELETE ON supervisores
        WHEN EXISTS (SELECT 1 FROM pasadas WHERE supervisor_id = OLD.id)
          OR EXISTS (
              SELECT 1 FROM equipos
              WHERE supervisor1_id = OLD.id
                 OR supervisor2_id = OLD.id
                 OR supervisor3_id = OLD.id
          )
        BEGIN
            SELECT RAISE(ABORT, 'No se puede eliminar un supervisor con historial asociado');
        END
    """)
    cursor.execute("""
        CREATE TRIGGER IF NOT EXISTS trg_objetivos_preservar_historial
        BEFORE DELETE ON objetivos
        WHEN EXISTS (SELECT 1 FROM pasadas WHERE objetivo_id = OLD.id)
        BEGIN
            SELECT RAISE(ABORT, 'No se puede eliminar un objetivo con pasadas asociadas');
        END
    """)
    _crear_admin_si_no_existe(cursor)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS schema_version (
            version INTEGER PRIMARY KEY,
            fecha_aplicacion TEXT NOT NULL
        )
    """)
    cursor.execute(
        "INSERT OR IGNORE INTO schema_version (version, fecha_aplicacion) VALUES (?, date('now'))",
        (SCHEMA_VERSION,),
    )

    conexion.commit()
    conexion.close()
    print("Base de datos iniciada correctamente.")


# =============================================================================
# MIGRACIONES
# =============================================================================

def migrar_supervisores_placeholder(cursor: sqlite3.Cursor) -> None:
    """Marca supervisores creados para conservar relaciones históricas incompletas."""
    columnas = {
        fila[1] for fila in cursor.execute("PRAGMA table_info(supervisores)")
    }
    if "es_placeholder" not in columnas:
        cursor.execute(
            "ALTER TABLE supervisores "
            "ADD COLUMN es_placeholder INTEGER NOT NULL DEFAULT 0"
        )


def _respaldar_duplicados_naturales_antes_de_migrar() -> None:
    """Respalda la BD antes de archivar duplicados que impiden el índice único."""
    if not os.path.exists(DB_PATH):
        return

    conexion = _sqlite3_connect_original(DB_PATH)
    try:
        tabla = conexion.execute(
            "SELECT 1 FROM sqlite_master WHERE type='table' AND name='pasadas'"
        ).fetchone()
        if not tabla:
            return
        columnas = {
            fila[1] for fila in conexion.execute("PRAGMA table_info(pasadas)")
        }
        requeridas = {"id", "objetivo_id", "fecha", "hora", "supervisor_id"}
        if not requeridas.issubset(columnas):
            return
        fecha_expr = (
            "COALESCE(fecha_operativa, fecha)"
            if "fecha_operativa" in columnas
            else "fecha"
        )
        duplicados = conexion.execute(
            f"""
            SELECT 1
            FROM pasadas
            WHERE objetivo_id IS NOT NULL
              AND {fecha_expr} IS NOT NULL
              AND hora IS NOT NULL
            GROUP BY objetivo_id, {fecha_expr}, substr(hora, 1, 5),
                     COALESCE(supervisor_id, -1)
            HAVING COUNT(*) > 1
            LIMIT 1
            """
        ).fetchone()
    finally:
        conexion.close()

    if duplicados:
        from services.backup import crear_backup

        conexion_respaldo = _sqlite3_connect_original(DB_PATH)
        try:
            crear_backup("pre_migracion", conexion_origen=conexion_respaldo)
        finally:
            conexion_respaldo.close()


def migrar_clave_natural_pasadas(cursor: sqlite3.Cursor) -> int:
    """Archiva copias históricas duplicadas y establece unicidad natural."""
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS pasadas_duplicados_migracion (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            pasada_original_id INTEGER NOT NULL,
            pasada_conservada_id INTEGER NOT NULL,
            datos_originales TEXT NOT NULL,
            fecha_archivo TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    duplicados = cursor.execute(
        """
        SELECT objetivo_id, fecha_operativa, substr(hora, 1, 5),
               COALESCE(supervisor_id, -1), MIN(id)
        FROM pasadas
        WHERE objetivo_id IS NOT NULL
          AND fecha_operativa IS NOT NULL
          AND hora IS NOT NULL
        GROUP BY objetivo_id, fecha_operativa, substr(hora, 1, 5),
                 COALESCE(supervisor_id, -1)
        HAVING COUNT(*) > 1
        """
    ).fetchall()
    archivadas = 0
    nombres_columnas = [
        fila[1] for fila in cursor.execute("PRAGMA table_info(pasadas)")
    ]
    for objetivo_id, fecha, hora, supervisor_id, id_conservado in duplicados:
        ids_duplicados = cursor.execute(
            """
            SELECT id
            FROM pasadas
            WHERE objetivo_id = ?
              AND fecha_operativa = ?
              AND substr(hora, 1, 5) = ?
              AND COALESCE(supervisor_id, -1) = ?
              AND id <> ?
            ORDER BY id
            """,
            (objetivo_id, fecha, hora, supervisor_id, id_conservado),
        ).fetchall()
        for (id_duplicado,) in ids_duplicados:
            fila = cursor.execute(
                "SELECT * FROM pasadas WHERE id = ?", (id_duplicado,)
            ).fetchone()
            datos = dict(zip(nombres_columnas, fila))
            cursor.execute(
                """
                INSERT INTO pasadas_duplicados_migracion (
                    pasada_original_id, pasada_conservada_id, datos_originales
                ) VALUES (?, ?, ?)
                """,
                (
                    id_duplicado,
                    id_conservado,
                    json.dumps(datos, ensure_ascii=False, default=str),
                ),
            )
            cursor.execute("DELETE FROM pasadas WHERE id = ?", (id_duplicado,))
            archivadas += 1
        logger.warning(
            "Migración de identidad de pasadas: clave duplicada objetivo=%s fecha=%s hora=%s supervisor=%s; se conserva id=%s y se archivan %s registros",
            objetivo_id,
            fecha,
            hora,
            supervisor_id,
            id_conservado,
            len(ids_duplicados),
        )

    cursor.execute(
        """
        CREATE UNIQUE INDEX IF NOT EXISTS idx_pasadas_clave_natural
        ON pasadas (
            objetivo_id,
            fecha_operativa,
            substr(hora, 1, 5),
            COALESCE(supervisor_id, -1)
        )
        WHERE objetivo_id IS NOT NULL
          AND fecha_operativa IS NOT NULL
          AND hora IS NOT NULL
        """
    )
    return archivadas


def migrar_feriados() -> None:
    """Crea la tabla de feriados si no existe para bases de datos antiguas."""
    conexion = conectar()
    cursor = conexion.cursor()
    try:
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS feriados (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                fecha       TEXT NOT NULL UNIQUE,
                descripcion TEXT
            )
        """)
        cursor.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_feriados_fecha ON feriados(fecha)")
        conexion.commit()
        logger.info("Migración feriados completada")
    except sqlite3.OperationalError as e:
        if "already exists" in str(e).lower() or "duplicate" in str(e).lower():
            logger.info("La tabla feriados ya existe")
        else:
            logger.exception("Error en migración de feriados")
            conexion.rollback()
    except Exception:
        logger.exception("Error inesperado en migrar_feriados")
        conexion.rollback()
    finally:
        conexion.close()


def migrar_supervisor3() -> None:
    """
    Agrega supervisor3_id a equipos si no existe.

    Note:
        Maneja gracefully si la columna ya existe
    """
    conexion = conectar()
    cursor = conexion.cursor()
    try:
        cursor.execute(
            "ALTER TABLE equipos ADD COLUMN supervisor3_id INTEGER REFERENCES supervisores(id)"
        )
        conexion.commit()
        logger.info("Migración supervisor3 completada")
    except sqlite3.OperationalError as e:
        if "duplicate column" in str(e).lower():
            logger.info("La columna supervisor3_id ya existe")
        else:
            logger.exception("Error en migración supervisor3")
            conexion.rollback()
    except Exception:
        logger.exception("Error inesperado en migrar_supervisor3")
        conexion.rollback()
    finally:
        conexion.close()


def migrar_supervisores_alta_baja() -> None:
    """
    Agrega fecha_alta y fecha_baja a supervisores si no existen.

    Note:
        Maneja gracefully si las columnas ya existen
    """
    conexion = conectar()
    cursor = conexion.cursor()
    migraciones_completadas = []

    for columna_def in ("fecha_alta TEXT", "fecha_baja TEXT"):
        try:
            cursor.execute(f"ALTER TABLE supervisores ADD COLUMN {columna_def}")
            conexion.commit()
            migraciones_completadas.append(columna_def.split()[0])
        except sqlite3.OperationalError as e:
            if "duplicate column" in str(e).lower():
                logger.info("La columna %s ya existe", columna_def.split()[0])
            else:
                logger.exception("Error en migración de columna %s", columna_def)
                conexion.rollback()
        except Exception:
            logger.exception("Error inesperado en migración de columna %s", columna_def)
            conexion.rollback()

    if migraciones_completadas:
        logger.info(
            "Migraciones de columnas completadas: %s",
            ", ".join(migraciones_completadas),
        )

    conexion.close()


def migrar_usuarios_activo() -> None:
    """
    Agrega la columna activo a usuarios si no existe.

    Bases de datos nuevas ya la tienen por el CREATE TABLE.
    Bases de datos existentes (creadas antes de esta migración)
    necesitan este ALTER TABLE para poder hacer login.

    Note:
        Maneja gracefully si la columna ya existe
    """
    conexion = conectar()
    cursor = conexion.cursor()
    try:
        cursor.execute("ALTER TABLE usuarios ADD COLUMN activo INTEGER DEFAULT 1")
        conexion.commit()
        # Marcar todos los usuarios existentes como activos
        cursor.execute("UPDATE usuarios SET activo = 1 WHERE activo IS NULL")
        conexion.commit()
        logger.info("Migración usuarios_activo completada")
    except sqlite3.OperationalError as e:
        if "duplicate column" in str(e).lower():
            logger.info("La columna activo ya existe")
        else:
            logger.exception("Error en migración usuarios_activo")
            conexion.rollback()
    except Exception:
        logger.exception("Error inesperado en migrar_usuarios_activo")
        conexion.rollback()
    finally:
        conexion.close()


def migrar_pasadas_campos(cursor: sqlite3.Cursor | None = None) -> None:
    """Añade columnas esperadas en pasadas y rellena valores por defecto."""
    conexion = None
    actualizar_cursor = cursor

    if actualizar_cursor is None:
        conexion = conectar()
        actualizar_cursor = conexion.cursor()

    try:
        for columna_def in (
            "notas TEXT",
            "fecha_operativa TEXT",
        ):
            try:
                actualizar_cursor.execute(f"ALTER TABLE pasadas ADD COLUMN {columna_def}")
            except sqlite3.OperationalError as e:
                if "duplicate column" not in str(e).lower():
                    raise

        actualizar_cursor.execute(
            "UPDATE pasadas SET notas = COALESCE(notas, '') WHERE notas IS NULL"
        )
        actualizar_cursor.execute(
            "UPDATE pasadas SET fecha_operativa = COALESCE(fecha_operativa, fecha) WHERE fecha_operativa IS NULL OR fecha_operativa = ''"
        )
        if conexion is not None:
            conexion.commit()
    except Exception as e:
        if conexion is not None:
            conexion.rollback()
        raise
    finally:
        if conexion is not None:
            conexion.close()


def migrar_objetivos_campos(cursor: sqlite3.Cursor | None = None) -> None:
    """Añade columnas esperadas en objetivos y rellena valores por defecto."""
    conexion = None
    actualizar_cursor = cursor

    if actualizar_cursor is None:
        conexion = conectar()
        actualizar_cursor = conexion.cursor()

    try:
        for columna_def in (
            "descripcion TEXT",
            "activo INTEGER DEFAULT 1",
            "es_placeholder INTEGER NOT NULL DEFAULT 0",
            "tipo_objetivo TEXT DEFAULT 'puntual'",
            "pendiente_revision INTEGER DEFAULT 0",
        ):
            try:
                actualizar_cursor.execute(f"ALTER TABLE objetivos ADD COLUMN {columna_def}")
            except sqlite3.OperationalError as e:
                if "duplicate column" not in str(e).lower():
                    raise

        actualizar_cursor.execute(
            "UPDATE objetivos SET descripcion = COALESCE(descripcion, '') WHERE descripcion IS NULL"
        )
        actualizar_cursor.execute(
            "UPDATE objetivos SET activo = 1 WHERE activo IS NULL"
        )
        actualizar_cursor.execute(
            "UPDATE objetivos SET es_placeholder = 0 WHERE es_placeholder IS NULL"
        )
        actualizar_cursor.execute(
            "UPDATE objetivos SET tipo_objetivo = 'puntual' WHERE tipo_objetivo IS NULL OR tipo_objetivo = ''"
        )
        actualizar_cursor.execute(
            "UPDATE objetivos SET pendiente_revision = 0 WHERE pendiente_revision IS NULL"
        )
        actualizar_cursor.execute(
            "UPDATE objetivos SET activo = 0 WHERE fecha_fin IS NOT NULL AND fecha_fin < date('now')"
        )
        actualizar_cursor.execute("""
            CREATE TABLE IF NOT EXISTS objetivo_periodos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                objetivo_id INTEGER NOT NULL,
                fecha_inicio TEXT NOT NULL,
                fecha_fin TEXT,
                FOREIGN KEY (objetivo_id) REFERENCES objetivos(id) ON DELETE CASCADE
            )
        """)
        actualizar_cursor.execute("""
            INSERT INTO objetivo_periodos (objetivo_id, fecha_inicio, fecha_fin)
            SELECT o.id, o.fecha_inicio, o.fecha_fin
            FROM objetivos o
            WHERE NOT EXISTS (
                SELECT 1 FROM objetivo_periodos p WHERE p.objetivo_id = o.id
            ) AND o.fecha_inicio IS NOT NULL
        """)
        actualizar_cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_objetivo_periodos_objetivo_fechas ON objetivo_periodos(objetivo_id, fecha_inicio, fecha_fin)"
        )
        if conexion is not None:
            conexion.commit()
    except Exception as e:
        if conexion is not None:
            conexion.rollback()
        raise
    finally:
        if conexion is not None:
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
        """, ("admin", password_hash, "admin", 1))