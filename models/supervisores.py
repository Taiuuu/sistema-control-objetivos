# =============================================================================
# VESP Organizations - Sistema de Control de Objetivos
# Módulo de gestión de supervisores OPTIMIZADO
# =============================================================================

from database.gestor_db import gestor_db
from services.cache import invalidar_supervisores
from services.sincronizacion import notificar_cambio


def agregar_supervisor(nombre: str, fecha_alta: str | None = None) -> None:
    """
    Registra un nuevo supervisor.
    OPTIMIZADO: Usa gestor_db con transacciones.
    """
    import datetime
    if not fecha_alta:
        fecha_alta = datetime.date.today().isoformat()
    
    with gestor_db.transaction() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO supervisores (nombre, fecha_alta) VALUES (?, ?)
        """, (nombre, fecha_alta))
        supervisor_id = cursor.lastrowid
    
    notificar_cambio("supervisores", "INSERT", {
        "id": supervisor_id,
        "nombre": nombre,
        "fecha_alta": fecha_alta
    })
    
    # Invalidar caché
    invalidar_supervisores()


def listar_supervisores(solo_activos: bool = False) -> list:
    """
    Retorna supervisores.
    OPTIMIZADO: Usa gestor_db con cache.
    """
    cache_key = f"listar_supervisores:{solo_activos}"
    
    if solo_activos:
        query = """
            SELECT id, nombre, fecha_alta, fecha_baja
            FROM supervisores
            WHERE fecha_baja IS NULL
            ORDER BY nombre
        """
    else:
        query = """
            SELECT id, nombre, fecha_alta, fecha_baja
            FROM supervisores
            ORDER BY fecha_baja IS NULL DESC, nombre
        """
    
    resultados = gestor_db.ejecutar(query)
    return [(r['id'], r['nombre'], r['fecha_alta'], r['fecha_baja']) for r in resultados]


def obtener_supervisor(supervisor_id: int) -> tuple | None:
    """Obtiene un supervisor por ID."""
    resultado = gestor_db.ejecutar(
        "SELECT id, nombre, fecha_alta, fecha_baja FROM supervisores WHERE id = ?",
        (supervisor_id,)
    )
    return (resultado[0]['id'], resultado[0]['nombre'], resultado[0]['fecha_alta'], resultado[0]['fecha_baja']) if resultado else None


def actualizar_supervisor(
    supervisor_id: int,
    nombre: str,
    fecha_alta: str | None = None,
    fecha_baja: str | None = None
) -> None:
    """Actualiza nombre, fecha_alta y/o fecha_baja de un supervisor."""
    with gestor_db.transaction() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE supervisores
            SET nombre = ?, fecha_alta = ?, fecha_baja = ?
            WHERE id = ?
        """, (nombre, fecha_alta, fecha_baja, supervisor_id))
    
    notificar_cambio("supervisores", "UPDATE", {
        "id": supervisor_id,
        "nombre": nombre,
        "fecha_alta": fecha_alta,
        "fecha_baja": fecha_baja
    })
    
    invalidar_supervisores()


def dar_de_baja_supervisor(supervisor_id: int, fecha_baja: str) -> None:
    """Marca la fecha de baja sin eliminar el registro."""
    with gestor_db.transaction() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE supervisores SET fecha_baja = ? WHERE id = ?
        """, (fecha_baja, supervisor_id))
    
    notificar_cambio("supervisores", "UPDATE", {
        "id": supervisor_id,
        "fecha_baja": fecha_baja
    })
    
    invalidar_supervisores()


def reactivar_supervisor(supervisor_id: int) -> None:
    """Borra la fecha de baja, reactivando al supervisor."""
    with gestor_db.transaction() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE supervisores SET fecha_baja = NULL WHERE id = ?
        """, (supervisor_id,))
    
    notificar_cambio("supervisores", "UPDATE", {
        "id": supervisor_id,
        "fecha_baja": None
    })
    
    invalidar_supervisores()