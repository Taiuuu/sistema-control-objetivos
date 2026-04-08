# =============================================================================
# VESP Organizations - Sistema de Control de Objetivos
# Módulo de validaciones exhaustivas
# =============================================================================

import sqlite3
import re
from typing import Optional, Tuple
from database.db import DB_PATH, conectar


class ErrorValidacion(Exception):
    """Excepción personalizada para errores de validación."""
    pass


# =============================================================================
# VALIDACIONES GENERALES
# =============================================================================

def validar_no_vacio(valor: str, campo: str) -> None:
    """Valida que un campo no esté vacío."""
    if not valor or not str(valor).strip():
        raise ErrorValidacion(f"El campo '{campo}' no puede estar vacío")


def validar_longitud(valor: str, minimo: int, maximo: int, campo: str) -> None:
    """Valida la longitud de un campo."""
    valor_str = str(valor).strip()
    largo = len(valor_str)
    if largo < minimo or largo > maximo:
        raise ErrorValidacion(
            f"'{campo}' debe tener entre {minimo} y {maximo} caracteres (actual: {largo})"
        )


def validar_formato_fecha(fecha: str) -> None:
    """Valida que la fecha esté en formato YYYY-MM-DD."""
    if not re.match(r'^\d{4}-\d{2}-\d{2}$', fecha):
        raise ErrorValidacion(f"Fecha inválida: '{fecha}'. Usar formato YYYY-MM-DD")


def validar_formato_hora(hora: str) -> None:
    """Valida que la hora esté en formato HH:MM"""
    if not re.match(r'^\d{2}:\d{2}(:\d{2})?$', hora):
        raise ErrorValidacion(f"Hora inválida: '{hora}'. Usar formato HH:MM")


def validar_dias_semana(dias_semana: str) -> None:
    """Valida que los días de la semana sean válidos (1-7 separados por comas)."""
    if not dias_semana:
        raise ErrorValidacion("Debe seleccionar al menos un día de la semana")
    
    try:
        dias = [int(d.strip()) for d in str(dias_semana).split(',')]
        if not all(1 <= d <= 7 for d in dias):
            raise ValueError
    except (ValueError, AttributeError):
        raise ErrorValidacion("Días de la semana inválidos. Usar números 1-7 separados por comas")


# =============================================================================
# VALIDACIONES DE INTEGRIDAD REFERENCIAL
# =============================================================================

def validar_usuario_existe(usuario_id: int) -> None:
    """Valida que un usuario exista en la BD."""
    try:
        conn = conectar()
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM usuarios WHERE id = ?", (usuario_id,))
        if not cursor.fetchone():
            raise ErrorValidacion(f"Usuario con ID {usuario_id} no existe")
        conn.close()
    except ErrorValidacion:
        raise
    except Exception as e:
        raise ErrorValidacion(f"Error validando usuario: {e}")


def validar_objetivo_existe(objetivo_id: int) -> None:
    """Valida que un objetivo exista en la BD."""
    try:
        conn = conectar()
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM objetivos WHERE id = ?", (objetivo_id,))
        if not cursor.fetchone():
            raise ErrorValidacion(f"Objetivo con ID {objetivo_id} no existe")
        conn.close()
    except ErrorValidacion:
        raise
    except Exception as e:
        raise ErrorValidacion(f"Error validando objetivo: {e}")


def validar_supervisor_existe(supervisor_id: int) -> None:
    """Valida que un supervisor exista en la BD."""
    try:
        conn = conectar()
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM supervisores WHERE id = ?", (supervisor_id,))
        if not cursor.fetchone():
            raise ErrorValidacion(f"Supervisor con ID {supervisor_id} no existe")
        conn.close()
    except ErrorValidacion:
        raise
    except Exception as e:
        raise ErrorValidacion(f"Error validando supervisor: {e}")


# =============================================================================
# VALIDACIONES DE DUPLICADOS
# =============================================================================

def validar_objetivo_no_duplicado(nombre: str, excluir_id: Optional[int] = None) -> None:
    """Valida que no exista otro objetivo con el mismo nombre."""
    try:
        nombre_normalized = str(nombre).strip().lower()
        conn = conectar()
        cursor = conn.cursor()
        
        query = "SELECT id FROM objetivos WHERE LOWER(nombre) = ?"
        params = [nombre_normalized]
        
        if excluir_id:
            query += " AND id != ?"
            params.append(excluir_id)
        
        cursor.execute(query, params)
        if cursor.fetchone():
            raise ErrorValidacion(f"Ya existe un objetivo con el nombre '{nombre}'")
        conn.close()
    except ErrorValidacion:
        raise
    except Exception as e:
        raise ErrorValidacion(f"Error validando duplicado de objetivo: {e}")


def validar_supervisor_no_duplicado(nombre: str, excluir_id: Optional[int] = None) -> None:
    """Valida que no exista otro supervisor con el mismo nombre."""
    try:
        nombre_normalized = str(nombre).strip().lower()
        conn = conectar()
        cursor = conn.cursor()
        
        query = "SELECT id FROM supervisores WHERE LOWER(nombre) = ?"
        params = [nombre_normalized]
        
        if excluir_id:
            query += " AND id != ?"
            params.append(excluir_id)
        
        cursor.execute(query, params)
        if cursor.fetchone():
            raise ErrorValidacion(f"Ya existe un supervisor con el nombre '{nombre}'")
        conn.close()
    except ErrorValidacion:
        raise
    except Exception as e:
        raise ErrorValidacion(f"Error validando duplicado de supervisor: {e}")


def validar_usuario_no_duplicado(username: str, excluir_id: Optional[int] = None) -> None:
    """Valida que no exista otro usuario con el mismo username."""
    try:
        username_normalized = str(username).strip().lower()
        conn = conectar()
        cursor = conn.cursor()
        
        query = "SELECT id FROM usuarios WHERE LOWER(username) = ?"
        params = [username_normalized]
        
        if excluir_id:
            query += " AND id != ?"
            params.append(excluir_id)
        
        cursor.execute(query, params)
        if cursor.fetchone():
            raise ErrorValidacion(f"Ya existe un usuario con el nombre '{username}'")
        conn.close()
    except ErrorValidacion:
        raise
    except Exception as e:
        raise ErrorValidacion(f"Error validando duplicado de usuario: {e}")


def validar_equipo_no_duplicado(fecha: str, turno: str, excluir_id: Optional[int] = None) -> None:
    """Valida que no exista otro equipo en la misma fecha y turno."""
    try:
        conn = conectar()
        cursor = conn.cursor()
        
        query = "SELECT id FROM equipos WHERE fecha = ? AND turno = ?"
        params = [fecha, turno]
        
        if excluir_id:
            query += " AND id != ?"
            params.append(excluir_id)
        
        cursor.execute(query, params)
        if cursor.fetchone():
            raise ErrorValidacion(f"Ya existe un equipo para {fecha} turno {turno}")
        conn.close()
    except ErrorValidacion:
        raise
    except Exception as e:
        raise ErrorValidacion(f"Error validando duplicado de equipo: {e}")


def validar_pasada_no_duplicada(
    fecha: str,
    hora: str,
    objetivo_id: int,
    turno: str,
    supervisor_id: int,
    excluir_id: Optional[int] = None,
    minutos_minimos: int = 5
) -> None:
    """Bloquea solo si hay otra pasada del mismo supervisor/objetivo/turno
    dentro de la ventana de minutos_minimos."""
    try:
        from datetime import datetime, timedelta

        hora_nueva = datetime.strptime(hora, "%H:%M:%S")
        ventana_desde = (hora_nueva - timedelta(minutes=minutos_minimos)).strftime("%H:%M:%S")
        ventana_hasta = (hora_nueva + timedelta(minutes=minutos_minimos)).strftime("%H:%M:%S")

        conn = conectar()
        cursor = conn.cursor()

        query = """
            SELECT id FROM pasadas
            WHERE fecha = ? AND objetivo_id = ? AND turno = ? AND supervisor_id = ?
            AND hora BETWEEN ? AND ?
        """
        params = [fecha, objetivo_id, turno, supervisor_id, ventana_desde, ventana_hasta]

        if excluir_id:
            query += " AND id != ?"
            params.append(excluir_id)

        cursor.execute(query, params)
        if cursor.fetchone():
            raise ErrorValidacion(
                f"Ya registraste una pasada para este objetivo con el mismo supervisor "
                f"hace menos de {minutos_minimos} minutos."
            )
        conn.close()
    except ErrorValidacion:
        raise
    except Exception as e:
        raise ErrorValidacion(f"Error validando duplicado de pasada: {e}")

# =============================================================================
# VALIDACIONES DE OBJETIVOS
# =============================================================================

def validar_objetivo(nombre: str, dias_semana: str, excluir_id: Optional[int] = None) -> None:
    """Valida todos los campos de un objetivo."""
    validar_no_vacio(nombre, "Nombre del objetivo")
    validar_longitud(nombre, 1, 255, "Nombre del objetivo")
    validar_dias_semana(dias_semana)
    validar_objetivo_no_duplicado(nombre, excluir_id)


# =============================================================================
# VALIDACIONES DE SUPERVISORES
# =============================================================================

def validar_supervisor(nombre: str, excluir_id: Optional[int] = None) -> None:
    """Valida todos los campos de un supervisor."""
    validar_no_vacio(nombre, "Nombre del supervisor")
    validar_longitud(nombre, 1, 255, "Nombre del supervisor")
    validar_supervisor_no_duplicado(nombre, excluir_id)


# =============================================================================
# VALIDACIONES DE PASADAS
# =============================================================================

def validar_pasada(
    fecha: str,
    hora: str,
    turno: str,
    objetivo_id: int,
    supervisor_id: Optional[int] = None,
    excluir_pasada_id: Optional[int] = None
) -> None:
    """Valida todos los campos de una pasada."""
    validar_no_vacio(fecha, "Fecha")
    validar_formato_fecha(fecha)
    
    validar_no_vacio(hora, "Hora")
    if len(hora) == 5:
        hora = hora + ":00"
    validar_formato_hora(hora)
    
    
    if turno not in ["diurno", "nocturno"]:
        raise ErrorValidacion(f"Turno inválido: '{turno}'. Debe ser 'diurno' o 'nocturno'")
    
    validar_objetivo_existe(objetivo_id)
    
    if supervisor_id:
        validar_supervisor_existe(supervisor_id)
    
    validar_pasada_no_duplicada(fecha, hora, objetivo_id, turno, supervisor_id, excluir_pasada_id)


# =============================================================================
# VALIDACIONES DE EQUIPOS
# =============================================================================

def validar_equipo(
    fecha: str,
    turno: str,
    supervisor1_id: int,
    supervisor2_id: int,
    excluir_id: Optional[int] = None
) -> None:
    """Valida todos los campos de un equipo."""
    validar_no_vacio(fecha, "Fecha")
    validar_formato_fecha(fecha)
    
    if turno not in ["diurno", "nocturno"]:
        raise ErrorValidacion(f"Turno inválido: '{turno}'")
    
    validar_supervisor_existe(supervisor1_id)
    validar_supervisor_existe(supervisor2_id)
    
    if supervisor1_id == supervisor2_id:
        raise ErrorValidacion("Los dos supervisores del equipo no pueden ser el mismo")
    
    validar_equipo_no_duplicado(fecha, turno, excluir_id)


# =============================================================================
# VALIDACIONES DE USUARIOS
# =============================================================================

def validar_username(username: str) -> None:
    """Valida el formato del username."""
    validar_no_vacio(username, "Username")
    validar_longitud(username, 3, 50, "Username")
    
    if not re.match(r'^[a-zA-Z0-9_.-]+$', username):
        raise ErrorValidacion("Username solo puede contener letras, números, guiones y puntos")


def validar_password_fuerte(password: str) -> None:
    """Valida que la contraseña sea suficientemente fuerte."""
    if len(password) < 4:
        raise ErrorValidacion("La contraseña debe tener al menos 4 caracteres")
    
    # Futura: agregar requisitos más estrictos (mayúsculas, números, etc.)


def validar_usuario(username: str, password: str, rol: str, excluir_id: Optional[int] = None) -> None:
    """Valida todos los campos de un usuario."""
    validar_username(username)
    validar_usuario_no_duplicado(username, excluir_id)
    validar_password_fuerte(password)
    
    if rol not in ["admin", "operador"]:
        raise ErrorValidacion(f"Rol inválido: '{rol}'. Debe ser 'admin' u 'operador'")


# =============================================================================
# VALIDACIONES DE INTEGRIDAD GLOBAL
# =============================================================================

def validar_integridad_bd() -> dict:
    """
    Realiza validaciones de integridad en toda la BD.
    Retorna un dict con resultados de validaciones.
    """
    resultados = {
        "es_valido": True,
        "errores": [],
        "advertencias": []
    }

    try:
        conn = conectar()
        cursor = conn.cursor()

        # 1. Validar que no haya pasadas huérfanas (sin objetivo)
        cursor.execute("""
            SELECT COUNT(*) FROM pasadas p
            WHERE NOT EXISTS (SELECT 1 FROM objetivos o WHERE o.id = p.objetivo_id)
        """)
        if cursor.fetchone()[0] > 0:
            resultados["errores"].append("Existen pasadas sin objetivo correspondiente")
            resultados["es_valido"] = False

        # 2. Validar que no haya pasadas huérfanas (sin supervisor)
        cursor.execute("""
            SELECT COUNT(*) FROM pasadas p
            WHERE p.supervisor_id IS NOT NULL 
            AND NOT EXISTS (SELECT 1 FROM supervisores s WHERE s.id = p.supervisor_id)
        """)
        if cursor.fetchone()[0] > 0:
            resultados["errores"].append("Existen pasadas con supervisor inválido")
            resultados["es_valido"] = False

        # 3. Validar que no haya equipos huérfanos
        cursor.execute("""
            SELECT COUNT(*) FROM equipos e
            WHERE NOT EXISTS (SELECT 1 FROM supervisores s WHERE s.id = e.supervisor1_id)
            OR NOT EXISTS (SELECT 1 FROM supervisores s WHERE s.id = e.supervisor2_id)
        """)
        if cursor.fetchone()[0] > 0:
            resultados["errores"].append("Existen equipos con supervisores inválidos")
            resultados["es_valido"] = False

        # 4. Validar que no haya logs huérfanos (sin usuario)
        cursor.execute("""
            SELECT COUNT(*) FROM logs l
            WHERE l.usuario_id IS NOT NULL 
            AND NOT EXISTS (SELECT 1 FROM usuarios u WHERE u.id = l.usuario_id)
        """)
        if cursor.fetchone()[0] > 0:
            resultados["advertencias"].append("Existen logs con usuario eliminado")

        # 5. Validar duplicados de objetivos
        cursor.execute("""
            SELECT nombre, COUNT(*) as cnt FROM objetivos
            GROUP BY LOWER(nombre) HAVING cnt > 1
        """)
        if cursor.fetchone():
            resultados["errores"].append("Existen objetivos duplicados")
            resultados["es_valido"] = False

        # 6. Validar duplicados de supervisores
        cursor.execute("""
            SELECT nombre, COUNT(*) as cnt FROM supervisores
            GROUP BY LOWER(nombre) HAVING cnt > 1
        """)
        if cursor.fetchone():
            resultados["errores"].append("Existen supervisores duplicados")
            resultados["es_valido"] = False

        conn.close()

    except Exception as e:
        resultados["errores"].append(f"Error validando integridad: {e}")
        resultados["es_valido"] = False

    return resultados
