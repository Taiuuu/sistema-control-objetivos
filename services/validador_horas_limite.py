# =============================================================================
# VESP Organizations - Validador de Horas Límite de Turno Nocturno
# Detecta horas críticas (07:00-07:59) y sugiere correcciones
# =============================================================================

import datetime
from typing import Tuple, Optional


def _parsear_hora(hora: str) -> datetime.time:
    """Acepta formatos HH:MM y HH:MM:SS."""
    for formato in ("%H:%M:%S", "%H:%M"):
        try:
            return datetime.datetime.strptime(hora, formato).time()
        except ValueError:
            continue
    raise ValueError(f"Formato de hora inválido: {hora}")


def validar_hora_turno_nocturno(
    fecha: str,
    hora: str,
    turno: str
) -> Tuple[bool, Optional[dict]]:
    """
    Valida si una pasada nocturna está en el rango correcto.
    
    Detecta horas límite (07:00-07:59) y sugiere mover al día anterior.
    
    Args:
        fecha: Fecha en formato YYYY-MM-DD
        hora: Hora en formato HH:MM o HH:MM:SS
        turno: 'diurno' o 'nocturno'
    
    Returns:
        Tupla (es_valida, sugerencia_dict)
        - es_valida: bool - True si está en rango válido
        - sugerencia_dict: dict con:
            - 'tipo': 'hora_limite'
            - 'fecha_sugerida': fecha del día anterior
            - 'razon': explicación
            - 'pregunta': texto de la pregunta
    
    Ejemplos:
        >>> validar_hora_turno_nocturno("2026-04-21", "07:12", "nocturno")
        (False, {
            'tipo': 'hora_limite',
            'fecha_sugerida': '2026-04-20',
            'razon': 'Hora fuera del rango nocturno estándar (00:00-06:59)',
            'pregunta': '¿Deseas mover esta pasada al 20/04/2026?'
        })
        
        >>> validar_hora_turno_nocturno("2026-04-21", "03:00", "nocturno")
        (True, None)  # Válida, está en 00:00-06:59
    """
    
    if turno != 'nocturno':
        return True, None
    
    try:
        fecha_obj = datetime.datetime.strptime(fecha, "%Y-%m-%d").date()
        hora_obj = _parsear_hora(hora)
        
        # Rango válido: 00:00-06:59:59
        if datetime.time(0, 0) <= hora_obj <= datetime.time(6, 59, 59):
            return True, None
        
        # Rango límite: 07:00-07:59:59
        if datetime.time(7, 0) <= hora_obj < datetime.time(8, 0):
            fecha_anterior = fecha_obj - datetime.timedelta(days=1)
            
            return False, {
                'tipo': 'hora_limite',
                'fecha_actual': fecha,
                'fecha_sugerida': fecha_anterior.strftime("%Y-%m-%d"),
                'hora': hora,
                'razon': 'Esta pasada se registró a las 7+ AM, que típicamente corresponde al turno nocturno anterior',
                'pregunta': f'¿Pertenece este registro al turno nocturno del {fecha_anterior.strftime("%d/%m/%Y")}?'
            }
        
        # Fuera de rango completamente
        return False, {
            'tipo': 'hora_invalida',
            'hora': hora,
            'razon': f'Hora {hora} está fuera del rango de turno nocturno (19:00-23:59 o 00:00-07:59)'
        }
        
    except Exception as e:
        raise ValueError(f"Error validando hora: {str(e)}")


def sugerir_fecha_operativa(fecha: str, hora: str, turno: str) -> str:
    """
    Calcula la fecha operativa correcta para una pasada.
    
    Basada en la lógica de turnos nocturnos que cruzan medianoche.
    
    Args:
        fecha: Fecha de registro en YYYY-MM-DD
        hora: Hora en HH:MM o HH:MM:SS
        turno: 'diurno' o 'nocturno'
    
    Returns:
        Fecha operativa en formato YYYY-MM-DD
    """
    
    if turno == 'diurno':
        return fecha
    
    fecha_obj = datetime.datetime.strptime(fecha, "%Y-%m-%d").date()
    hora_obj = _parsear_hora(hora)
    
    # Nocturno 19:00-23:59 → mismo día
    if datetime.time(19, 0) <= hora_obj <= datetime.time(23, 59, 59):
        return fecha
    
    # Nocturno 00:00-07:59 → día anterior (incluyendo horas límite)
    if datetime.time(0, 0) <= hora_obj < datetime.time(8, 0):
        fecha_anterior = fecha_obj - datetime.timedelta(days=1)
        return fecha_anterior.strftime("%Y-%m-%d")
    
    # Si está fuera de rango, retornar fecha actual
    return fecha


# Constantes para rangos
RANGO_NOCTURNO_TEMPRANO = (datetime.time(0, 0), datetime.time(6, 59, 59))  # Nocturno madrugada
RANGO_NOCTURNO_LIMITE = (datetime.time(7, 0), datetime.time(7, 59, 59))     # Horas límite (necesita validación)
RANGO_NOCTURNO_NOCHE = (datetime.time(19, 0), datetime.time(23, 59, 59))    # Nocturno noche

RANGO_DIURNO = (datetime.time(7, 0), datetime.time(18, 59, 59))  # Diurno
