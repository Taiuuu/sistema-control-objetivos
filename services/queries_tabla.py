# =============================================================================
# VESP Organizations - Queries para Tabla Principal
# Consultas a BD para la tabla de cobertura diaria
# =============================================================================

import sqlite3
from database.db import DB_PATH


def contar_pasadas(fecha: str, objetivo_id: int, turno: str = None, supervisor_id: int = None) -> int:
    """Cuenta pasadas registradas para un objetivo en una fecha."""
    conexion = sqlite3.connect(DB_PATH)
    cursor = conexion.cursor()
    query = 'SELECT COUNT(*) FROM pasadas WHERE fecha = ? AND objetivo_id = ?'
    params = [fecha, objetivo_id]
    if turno:
        query += ' AND turno = ?'
        params.append(turno)
    if supervisor_id:
        query += ' AND supervisor_id = ?'
        params.append(supervisor_id)
    cursor.execute(query, params)
    resultado = cursor.fetchone()[0]
    conexion.close()
    return resultado


def obtener_equipo(fecha: str, turno: str) -> str:
    """Obtiene los supervisores asignados a un turno en una fecha."""
    conexion = sqlite3.connect(DB_PATH)
    cursor = conexion.cursor()
    cursor.execute("""
        SELECT s1.nombre, s2.nombre,
               CASE WHEN e.supervisor3_id IS NOT NULL THEN s3.nombre ELSE NULL END
        FROM equipos e
        JOIN supervisores s1 ON e.supervisor1_id = s1.id
        JOIN supervisores s2 ON e.supervisor2_id = s2.id
        LEFT JOIN supervisores s3 ON e.supervisor3_id = s3.id
        WHERE e.fecha = ? AND e.turno = ?
    """, (fecha, turno))
    resultado = cursor.fetchone()
    conexion.close()
    if not resultado:
        return "—"
    nombres = [n for n in resultado if n is not None]
    if len(nombres) == 1:
        return nombres[0]
    return ", ".join(nombres[:-1]) + " y " + nombres[-1]


def cargar_supervisores() -> list:
    """Carga lista de (id, nombre) de supervisores."""
    conexion = sqlite3.connect(DB_PATH)
    cursor = conexion.cursor()
    cursor.execute('SELECT id, nombre FROM supervisores')
    resultado = cursor.fetchall()
    conexion.close()
    return resultado


def obtener_todas_pasadas_por_turno(fecha: str, supervisor_id: int = None) -> tuple:
    """
    Obtiene conteo de pasadas por objetivo y turno.
    Retorna (pasadas_dia, pasadas_noche) donde cada una es un dict {objetivo_id: count}.
    """
    conexion = sqlite3.connect(DB_PATH)
    cursor = conexion.cursor()
    query = """
        SELECT objetivo_id, turno, COUNT(*)
        FROM pasadas WHERE fecha = ?
    """
    params = [fecha]
    if supervisor_id:
        query += " AND supervisor_id = ?"
        params.append(supervisor_id)
    query += " GROUP BY objetivo_id, turno"
    cursor.execute(query, params)
    resultados = cursor.fetchall()
    conexion.close()
    
    pasadas_dia = {}
    pasadas_noche = {}
    for obj_id, turno, count in resultados:
        if turno == "diurno":
            pasadas_dia[obj_id] = count
        elif turno == "nocturno":
            pasadas_noche[obj_id] = count
    return pasadas_dia, pasadas_noche
