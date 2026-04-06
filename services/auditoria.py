# =============================================================================
# VESP Organizations - Sistema de Control de Objetivos
# Módulo de auditoría detallada y segura
# =============================================================================

import sqlite3
import datetime
import json
from enum import Enum
from typing import Any, Optional
from database.db import DB_PATH


class TipoOperacion(Enum):
    """Tipos de operaciones que pueden ser auditadas."""
    CREATE = "CREATE"
    UPDATE = "UPDATE"
    DELETE = "DELETE"
    LOGIN = "LOGIN"
    LOGOUT = "LOGOUT"
    ACCESO = "ACCESO"
    ERROR = "ERROR"
    CAMBIO_PERMISOS = "CAMBIO_PERMISOS"
    EXPORTACION = "EXPORTACION"
    IMPORTACION = "IMPORTACION"


# =============================================================================
# AUDITORÍA DETALLADA
# =============================================================================

def registrar_auditoria(
    usuario_id: Optional[int],
    tipo_operacion: TipoOperacion,
    tabla: Optional[str] = None,
    registro_id: Optional[int] = None,
    valores_anteriores: Optional[dict] = None,
    valores_nuevos: Optional[dict] = None,
    detalles: Optional[str] = None,
    estado: str = "EXITOSO"
) -> None:
    """
    Registra una operación detallada en la auditoría.
    
    Args:
        usuario_id: ID del usuario que realiza la operación (None si es sistema)
        tipo_operacion: Tipo de operación (CREATE, UPDATE, DELETE, etc.)
        tabla: Nombre de la tabla afectada
        registro_id: ID del registro afectado
        valores_anteriores: Dict con valores antes del cambio (para UPDATE)
        valores_nuevos: Dict con valores después del cambio
        detalles: Descripción adicional de la operación
        estado: EXITOSO, FALLIDO, PENDIENTE
    """
    try:
        conexion = sqlite3.connect(DB_PATH)
        cursor = conexion.cursor()

        ahora = datetime.datetime.now()
        fecha = ahora.strftime("%Y-%m-%d")
        hora = ahora.strftime("%H:%M:%S")

        # Serializar dicts a JSON para almacenamiento
        valores_ant_json = json.dumps(valores_anteriores) if valores_anteriores else None
        valores_nuev_json = json.dumps(valores_nuevos) if valores_nuevos else None

        cursor.execute("""
            INSERT INTO auditoria (
                fecha, hora, usuario_id, tipo_operacion,
                tabla, registro_id, valores_anteriores, valores_nuevos,
                detalles, estado
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            fecha, hora, usuario_id, tipo_operacion.value,
            tabla, registro_id, valores_ant_json, valores_nuev_json,
            detalles, estado
        ))

        conexion.commit()
        conexion.close()

    except Exception as e:
        print(f"Error registrando auditoría: {e}")


def obtener_auditoria_usuario(usuario_id: int, dias: int = 30) -> list:
    """Obtiene el historial de auditoría de un usuario en los últimos N días."""
    try:
        conexion = sqlite3.connect(DB_PATH)
        cursor = conexion.cursor()

        fecha_limite = (datetime.datetime.now() - datetime.timedelta(days=dias)).strftime("%Y-%m-%d")

        cursor.execute("""
            SELECT id, fecha, hora, tipo_operacion, tabla, registro_id,
                   valores_anteriores, valores_nuevos, detalles, estado
            FROM auditoria
            WHERE usuario_id = ? AND fecha >= ?
            ORDER BY fecha DESC, hora DESC
            LIMIT 1000
        """, (usuario_id, fecha_limite))

        resultados = cursor.fetchall()
        conexion.close()
        return resultados

    except Exception as e:
        print(f"Error obteniendo auditoría: {e}")
        return []


def obtener_auditoria_tabla(tabla: str, dias: int = 30) -> list:
    """Obtiene el historial de cambios de una tabla específica."""
    try:
        conexion = sqlite3.connect(DB_PATH)
        cursor = conexion.cursor()

        fecha_limite = (datetime.datetime.now() - datetime.timedelta(days=dias)).strftime("%Y-%m-%d")

        cursor.execute("""
            SELECT id, fecha, hora, usuario_id, tipo_operacion,
                   registro_id, valores_anteriores, valores_nuevos,
                   detalles, estado
            FROM auditoria
            WHERE tabla = ? AND fecha >= ?
            ORDER BY fecha DESC, hora DESC
            LIMIT 1000
        """, (tabla, fecha_limite))

        resultados = cursor.fetchall()
        conexion.close()
        return resultados

    except Exception as e:
        print(f"Error obteniendo auditoría de tabla: {e}")
        return []


def obtener_auditoria_registro(tabla: str, registro_id: int) -> list:
    """Obtiene el historial completo de cambios de un registro específico."""
    try:
        conexion = sqlite3.connect(DB_PATH)
        cursor = conexion.cursor()

        cursor.execute("""
            SELECT id, fecha, hora, usuario_id, tipo_operacion,
                   valores_anteriores, valores_nuevos, detalles, estado
            FROM auditoria
            WHERE tabla = ? AND registro_id = ?
            ORDER BY fecha DESC, hora DESC
        """, (tabla, registro_id))

        resultados = cursor.fetchall()
        conexion.close()
        return resultados

    except Exception as e:
        print(f"Error obteniendo historial del registro: {e}")
        return []


def obtener_cambios_por_fecha(fecha: str) -> list:
    """Obtiene todos los cambios realizados en una fecha específica."""
    try:
        conexion = sqlite3.connect(DB_PATH)
        cursor = conexion.cursor()

        cursor.execute("""
            SELECT id, hora, usuario_id, tipo_operacion, tabla,
                   registro_id, detalles, estado
            FROM auditoria
            WHERE fecha = ?
            ORDER BY hora DESC
        """, (fecha,))

        resultados = cursor.fetchall()
        conexion.close()
        return resultados

    except Exception as e:
        print(f"Error obteniendo cambios del día: {e}")
        return []


# =============================================================================
# INTEGRIDAD Y PROTECCIÓN
# =============================================================================

def validar_integridad_auditoria() -> dict:
    """
    Valida que la auditoría no haya sido alterada.
    Comprueba inconsistencias y anomalías.
    """
    try:
        conexion = sqlite3.connect(DB_PATH)
        cursor = conexion.cursor()

        resultado = {
            "total_registros": 0,
            "registros_validados": 0,
            "anomalias": [],
            "es_valido": True
        }

        # Contar registros totales
        cursor.execute("SELECT COUNT(*) FROM auditoria")
        resultado["total_registros"] = cursor.fetchone()[0]

        # Validar que no haya secuencias perdidas de IDs
        cursor.execute("""
            SELECT id FROM auditoria
            ORDER BY id ASC
        """)
        ids = [row[0] for row in cursor.fetchall()]

        if ids:
            for i, id_val in enumerate(ids[:-1], 1):
                if ids[i] != id_val + 1:
                    resultado["anomalias"].append(
                        f"Salto detectado en los IDs: {id_val} -> {ids[i]}"
                    )
                    resultado["es_valido"] = False

        resultado["registros_validados"] = len(ids)

        conexion.close()
        return resultado

    except Exception as e:
        print(f"Error validando integridad: {e}")
        return {"es_valido": False, "error": str(e)}


def exportar_auditoria_csv(fecha_inicio: str, fecha_fin: str, ruta_csv: str) -> bool:
    """
    Exporta el registro de auditoría a un archivo CSV para análisis externo.
    No modifica la auditoría, solo la extrae para respaldo.
    """
    try:
        import csv

        conexion = sqlite3.connect(DB_PATH)
        cursor = conexion.cursor()

        cursor.execute("""
            SELECT fecha, hora, usuario_id, tipo_operacion, tabla,
                   registro_id, detalles, estado
            FROM auditoria
            WHERE fecha BETWEEN ? AND ?
            ORDER BY fecha DESC, hora DESC
        """, (fecha_inicio, fecha_fin))

        registros = cursor.fetchall()
        conexion.close()

        with open(ruta_csv, 'w', newline='', encoding='utf-8') as archivo:
            escritor = csv.writer(archivo)
            escritor.writerow([
                "Fecha", "Hora", "Usuario ID", "Tipo Operación",
                "Tabla", "Registro ID", "Detalles", "Estado"
            ])
            escritor.writerows(registros)

        return True

    except Exception as e:
        print(f"Error exportando auditoría: {e}")
        return False
