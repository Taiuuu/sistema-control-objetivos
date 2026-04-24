# =============================================================================
# VESP Organizations - Sistema de Control de Objetivos
# Módulo de gestión de objetivos OPTIMIZADO
# =============================================================================

from database.gestor_db import gestor_db
from services.cache import invalidar_objetivos, cache_global
from services.sincronizacion import notificar_cambio


# =============================================================================
# ALTA
# =============================================================================

def agregar_objetivo(nombre: str, fecha_inicio: str, fecha_fin: str | None, dias_semana: str) -> None:
    """
    Registra un nuevo objetivo en el sistema.
    OPTIMIZADO: Usa gestor_db con transacciones.
    """
    with gestor_db.transaction() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO objetivos (nombre, fecha_inicio, fecha_fin, dias_semana)
            VALUES (?, ?, ?, ?)
        """, (nombre, fecha_inicio, fecha_fin, dias_semana))
        objetivo_id = cursor.lastrowid
    
    # Notificar cambio para sincronización
    notificar_cambio("objetivos", "INSERT", {
        "id": objetivo_id,
        "nombre": nombre,
        "fecha_inicio": fecha_inicio,
        "fecha_fin": fecha_fin,
        "dias_semana": dias_semana
    })
    
    # Invalidar caché
    invalidar_objetivos()


# =============================================================================
# CONSULTA CON CACHÉ
# =============================================================================

@cache_global.auto_cache(ttl=60)
def listar_objetivos() -> list:
    """
    Retorna todos los objetivos registrados en el sistema.
    OPTIMIZADO: Cacheado por 60 segundos.
    """
    return gestor_db.ejecutar("SELECT * FROM objetivos")


def obtener_objetivo(objetivo_id: int) -> tuple | None:
    """Retorna un objetivo específico por ID."""
    resultado = gestor_db.ejecutar(
        "SELECT * FROM objetivos WHERE id = ?", 
        (objetivo_id,)
    )
    return resultado[0] if resultado else None


# =============================================================================
# MODIFICACIÓN
# =============================================================================

def actualizar_objetivo(objetivo_id: int, nombre: str, fecha_inicio: str, fecha_fin: str | None, dias_semana: str) -> None:
    """Actualiza los datos de un objetivo."""
    with gestor_db.transaction() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE objetivos SET nombre = ?, fecha_inicio = ?, fecha_fin = ?, dias_semana = ?
            WHERE id = ?
        """, (nombre, fecha_inicio, fecha_fin, dias_semana, objetivo_id))
    
    # Notificar cambio para sincronización
    notificar_cambio("objetivos", "UPDATE", {
        "id": objetivo_id,
        "nombre": nombre,
        "fecha_inicio": fecha_inicio,
        "fecha_fin": fecha_fin,
        "dias_semana": dias_semana
    })
    
    # Invalidar caché
    invalidar_objetivos()


# =============================================================================
# BAJA
# =============================================================================

def dar_de_baja_objetivo(objetivo_id: int, fecha_fin: str | None = None) -> None:
    """
    Registra la fecha de finalización de un objetivo.
    OPTIMIZADO: Usa gestor_db.
    """
    if fecha_fin is None:
        from datetime import datetime
        fecha_fin = datetime.now().strftime('%Y-%m-%d')
    
    with gestor_db.transaction() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE objetivos SET fecha_fin = ? WHERE id = ?
        """, (fecha_fin, objetivo_id))
    
    # Notificar cambio para sincronización
    notificar_cambio("objetivos", "UPDATE", {
        "id": objetivo_id,
        "fecha_fin": fecha_fin
    })
    
    # Invalidar caché
    invalidar_objetivos()