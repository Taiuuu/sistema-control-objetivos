# =============================================================================
# VESP Organizations - Sistema de Control de Objetivos
# Módulo de gestión de objetivos
# =============================================================================

import sqlite3
from database.db import DB_PATH
from services.cache import invalidar_objetivos
from services.sincronizacion import notificar_cambio


# =============================================================================
# ALTA
# =============================================================================

def agregar_objetivo(nombre: str, fecha_inicio: str, fecha_fin: str | None, dias_semana: str) -> None:
    """
    Registra un nuevo objetivo en el sistema.
    dias_semana: string con números separados por coma (ej: '1,2,3' = lunes, martes, miércoles)
    fecha_fin: puede ser None si el objetivo no tiene fecha de finalización definida
    """
    conexion = sqlite3.connect(DB_PATH)
    cursor = conexion.cursor()
    cursor.execute("""
        INSERT INTO objetivos (nombre, fecha_inicio, fecha_fin, dias_semana)
        VALUES (?, ?, ?, ?)
    """, (nombre, fecha_inicio, fecha_fin, dias_semana))
    objetivo_id = cursor.lastrowid
    conexion.commit()
    conexion.close()
    
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
# CONSULTA
# =============================================================================

def listar_objetivos() -> list:
    """Retorna todos los objetivos registrados en el sistema."""
    conexion = sqlite3.connect(DB_PATH)
    cursor = conexion.cursor()
    cursor.execute("SELECT * FROM objetivos")
    resultado = cursor.fetchall()
    conexion.close()
    return resultado


# =============================================================================
# BAJA
# =============================================================================

def dar_de_baja_objetivo(objetivo_id: int, fecha_fin: str) -> None:
    """
    Registra la fecha de finalización de un objetivo.
    A partir de esa fecha el objetivo deja de aparecer en el control diario.
    """
    conexion = sqlite3.connect(DB_PATH)
    cursor = conexion.cursor()
    cursor.execute("""
        UPDATE objetivos SET fecha_fin = ? WHERE id = ?
    """, (fecha_fin, objetivo_id))
    conexion.commit()
    conexion.close()
    
    # Notificar cambio para sincronización
    notificar_cambio("objetivos", "UPDATE", {
        "id": objetivo_id,
        "fecha_fin": fecha_fin
    })
    
    # Invalidar caché
    invalidar_objetivos()