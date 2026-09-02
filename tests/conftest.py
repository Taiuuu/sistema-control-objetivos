# =============================================================================
# VESP Testing Configuration - pytest
# =============================================================================

import pytest
import sqlite3
import os
import tempfile
import shutil
from pathlib import Path


os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")


# Override database path for testing
@pytest.fixture
def test_db():
    """Crea una base de datos temporal para tests."""
    temp_dir = tempfile.mkdtemp()
    db_path = os.path.join(temp_dir, "test.db")
    
    # Parchear la ruta de BD antes de cualquier import
    os.environ["TEST_DB_PATH"] = db_path
    
    yield db_path
    
    # Limpiar después de los tests
    if os.path.exists(temp_dir):
        # Intentar cerrar cualquier conexión abierta y reintentar eliminación (Windows lock)
        try:
            import gc
            from database import gestor_db as gd
            try:
                gd.cerrar_conexion()
            except Exception:
                pass
            try:
                from database import db as db_module
                try:
                    db_module.gestor_db.cerrar_conexion()
                except Exception:
                    pass
            except Exception:
                pass
            gc.collect()
        except Exception:
            pass

        # Reintentar rmtree hasta 3 veces
        import time
        for _ in range(3):
            try:
                shutil.rmtree(temp_dir)
                break
            except PermissionError:
                time.sleep(0.1)
        else:
            # Último intento forzado
            try:
                shutil.rmtree(temp_dir)
            except Exception:
                pass


@pytest.fixture
def db_initialized(test_db):
    """Base de datos inicializada con esquema."""
    import sys
    sys.path.insert(0, str(Path(__file__).parent.parent))
    
    from database import db as db_module
    import database.gestor_db as gestor_db_module

    # Cerrar cualquier conexión previa y parchear DB_PATH
    try:
        gestor_db_module.gestor_db.cerrar_conexion()
    except Exception:
        pass

    original_path = db_module.DB_PATH
    db_module.DB_PATH = test_db

    # Crear tablas
    db_module.crear_base_datos()

    yield test_db

    # Cerrar conexiones y restaurar
    try:
        gestor_db_module.gestor_db.cerrar_conexion()
    except Exception:
        pass
    db_module.DB_PATH = original_path


@pytest.fixture
def admin_user(db_initialized):
    """Crea un usuario admin para tests."""
    import sys
    sys.path.insert(0, str(Path(__file__).parent.parent))
    
    from services.usuarios import crear_usuario
    try:
        user = crear_usuario("admin_test", "Prueba123!", "admin", debe_cambiar_password=False)
        user_id = user['id']
    except Exception:
        # Si ya existe, leerlo directamente desde la DB de pruebas
        import sqlite3
        conexion = sqlite3.connect(db_initialized)
        cur = conexion.cursor()
        cur.execute("SELECT id FROM usuarios WHERE username = ?", ("admin_test",))
        row = cur.fetchone()
        conexion.close()
        user_id = row[0] if row else None

    return {"id": user_id, "username": "admin_test", "password": "Prueba123!", "rol": "admin"}


@pytest.fixture
def operador_user(db_initialized):
    """Crea un usuario operador para tests."""
    import sys
    sys.path.insert(0, str(Path(__file__).parent.parent))
    
    from services.usuarios import crear_usuario
    try:
        user = crear_usuario("operador_test", "Prueba123!", "operador", debe_cambiar_password=False)
        user_id = user['id']
    except Exception:
        import sqlite3
        conexion = sqlite3.connect(db_initialized)
        cur = conexion.cursor()
        cur.execute("SELECT id FROM usuarios WHERE username = ?", ("operador_test",))
        row = cur.fetchone()
        conexion.close()
        user_id = row[0] if row else None

    return {"id": user_id, "username": "operador_test", "password": "Prueba123!", "rol": "operador"}


@pytest.fixture
def test_objetivo(db_initialized, admin_user):
    """Crea un objetivo de prueba."""
    import sys
    sys.path.insert(0, str(Path(__file__).parent.parent))
    
    import sqlite3
    
    db_path = db_initialized
    conexion = sqlite3.connect(db_path)
    cursor = conexion.cursor()
    
    cursor.execute("""
        INSERT INTO objetivos (nombre, dias_semana)
        VALUES (?, ?)
    """, ("Objetivo Test", "1,2,3,4,5"))
    
    conexion.commit()
    obj_id = cursor.lastrowid
    conexion.close()
    
    return {"id": obj_id, "nombre": "Objetivo Test", "dias_semana": "1,2,3,4,5"}


@pytest.fixture
def test_supervisor(db_initialized):
    """Crea un supervisor de prueba."""
    import sys
    sys.path.insert(0, str(Path(__file__).parent.parent))
    
    import sqlite3
    
    db_path = db_initialized
    conexion = sqlite3.connect(db_path)
    cursor = conexion.cursor()
    
    cursor.execute("INSERT INTO supervisores (nombre) VALUES (?)", ("Supervisor Test",))
    conexion.commit()
    sup_id = cursor.lastrowid
    conexion.close()
    
    return {"id": sup_id, "nombre": "Supervisor Test"}
