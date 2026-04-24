# =============================================================================
# VESP Organizations - Sistema de Control de Objetivos
# Módulo de registro de pasadas (turnos) OPTIMIZADO
# =============================================================================

from database.gestor_db import gestor_db
from services.cache import invalidar_pasadas
from services.sincronizacion import notificar_cambio


def registrar_turno(fecha: str, hora: str | None, turno: str, objetivo_id: int, supervisor_id: int) -> None:
    """
    Registra una pasada/turno.
    OPTIMIZADO: Usa gestor_db con transacciones.
    """
    with gestor_db.transaction() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO pasadas (fecha, hora, turno, objetivo_id, supervisor_id)
            VALUES (?, ?, ?, ?, ?)
        """, (fecha, hora, turno, objetivo_id, supervisor_id))
        pasada_id = cursor.lastrowid

    notificar_cambio("pasadas", "INSERT", {
        "id": pasada_id,
        "fecha": fecha,
        "hora": hora,
        "turno": turno,
        "objetivo_id": objetivo_id,
        "supervisor_id": supervisor_id
    })
    
    # Invalidar caché de pasadas
    invalidar_pasadas()


def registrar_turno_ambos(fecha: str, hora: str | None, turno: str, objetivo_id: int,
                          supervisor1_id: int, supervisor2_id: int) -> None:
    """
    Registra una pasada para los dos supervisores del turno al mismo tiempo.
    OPTIMIZADO: Usa una sola transacción para ambas inserts.
    """
    with gestor_db.transaction() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO pasadas (fecha, hora, turno, objetivo_id, supervisor_id)
            VALUES (?, ?, ?, ?, ?)
        """, (fecha, hora, turno, objetivo_id, supervisor1_id))
        pasada1_id = cursor.lastrowid
        
        cursor.execute("""
            INSERT INTO pasadas (fecha, hora, turno, objetivo_id, supervisor_id)
            VALUES (?, ?, ?, ?, ?)
        """, (fecha, hora, turno, objetivo_id, supervisor2_id))
        pasada2_id = cursor.lastrowid

    # Notificar cambio para sincronización (dos pasadas)
    notificar_cambio("pasadas", "INSERT", {
        "id": pasada1_id,
        "fecha": fecha,
        "hora": hora,
        "turno": turno,
        "objetivo_id": objetivo_id,
        "supervisor_id": supervisor1_id
    })
    notificar_cambio("pasadas", "INSERT", {
        "id": pasada2_id,
        "fecha": fecha,
        "hora": hora,
        "turno": turno,
        "objetivo_id": objetivo_id,
        "supervisor_id": supervisor2_id
    })
    
    invalidar_pasadas()


def listar_turnos_del_dia(fecha: str) -> list:
    """
    Lista los turnos de un día.
    OPTIMIZADO: Usa gestor_db con cache.
    """
    query = """
        SELECT p.id, p.hora, p.turno, o.nombre, s.nombre
        FROM pasadas p
        JOIN objetivos o ON p.objetivo_id = o.id
        JOIN supervisores s ON p.supervisor_id = s.id
        WHERE p.fecha = ?
        ORDER BY p.hora
    """
    
    resultados = gestor_db.ejecutar(query, (fecha,))
    return [(r['id'], r['hora'], r['turno'], r['o.nombre'], r['s.nombre']) for r in resultados]