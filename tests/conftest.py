# =============================================================================
# VESP Testing Configuration - pytest
# =============================================================================

import pytest
import sqlite3
import os
import tempfile
import shutil
from pathlib import Path


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
        shutil.rmtree(temp_dir)


@pytest.fixture
def db_initialized(test_db):
    """Base de datos inicializada con esquema."""
    import sys
    sys.path.insert(0, str(Path(__file__).parent.parent))
    
    from database import db as db_module
    
    # Monkeypatch DB_PATH
    original_path = db_module.DB_PATH
    db_module.DB_PATH = test_db
    
    # Crear tablas
    db_module.crear_base_datos()
    
    yield test_db
    
    # Restaurar
    db_module.DB_PATH = original_path


@pytest.fixture
def admin_user(db_initialized):
    """Crea un usuario admin para tests."""
    import sys
    sys.path.insert(0, str(Path(__file__).parent.parent))
    
    from services.usuarios import crear_usuario
    
    user_id = crear_usuario("admin_test", "Prueba123!", "admin", debe_cambiar_password=False)
    return {"id": user_id, "username": "admin_test", "password": "Prueba123!", "rol": "admin"}


@pytest.fixture
def operador_user(db_initialized):
    """Crea un usuario operador para tests."""
    import sys
    sys.path.insert(0, str(Path(__file__).parent.parent))
    
    from services.usuarios import crear_usuario
    
    user_id = crear_usuario("operador_test", "Prueba123!", "operador", debe_cambiar_password=False)
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
    
    conectar.commit()
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
