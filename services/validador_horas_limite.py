# =============================================================================
# VESP Organizations - Validador de horarios de turno
# =============================================================================

import datetime
from typing import Tuple, Optional
from services.pasadas.calculo_pasadas import hora_corresponde_a_turno


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
    Valida si la hora pertenece a alguno de los ciclos compatibles con el
    turno declarado.
    
    DIA admite 07:00-20:00 y NOCHE 19:00-08:00, con los extremos superiores
    excluidos. Las horas compartidas se resuelven con el turno declarado.
    
    Args:
        fecha: Fecha en formato YYYY-MM-DD
        hora: Hora en formato HH:MM o HH:MM:SS
        turno: 'diurno' o 'nocturno'
    
    Returns:
        Tupla (es_valida, sugerencia_dict)
        - es_valida: bool - True si está en rango válido
        - sugerencia_dict: dict con:
            - Si la hora es válida para NOCHE, retorna (True, None).
            - Si no, retorna una sugerencia de tipo 'hora_invalida'.
    
    Ejemplos:
        >>> validar_hora_turno_nocturno("2026-04-21", "07:12", "nocturno")
        (True, None)  # Ciclo NOCHE 20:00-08:00
        
        >>> validar_hora_turno_nocturno("2026-04-21", "03:00", "nocturno")
        (True, None)  # Válida, está en 00:00-06:59
    """
    
    try:
        datetime.datetime.strptime(fecha, "%Y-%m-%d")
        hora_obj = _parsear_hora(hora)
        
        if hora_corresponde_a_turno(hora_obj, turno):
            return True, None

        return False, {
            'tipo': 'hora_invalida',
            'hora': hora,
            'razon': f'Hora {hora} no corresponde al turno {turno}. '
                     'DIA admite 07:00-19:59 o NOCHE 19:00-07:59, '
                     'segun el ciclo que figure en el registro.'
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
    
    hora_obj = _parsear_hora(hora)
    fecha_obj = datetime.datetime.strptime(fecha, "%Y-%m-%d").date()
    return fecha_de_turno(
        datetime.datetime.combine(fecha_obj, hora_obj), turno
    ).isoformat()


# Constantes para rangos
RANGO_NOCTURNO_TEMPRANO = (datetime.time(0, 0), datetime.time(7, 59, 59))  # Nocturno madrugada
RANGO_NOCTURNO_NOCHE = (datetime.time(19, 0), datetime.time(23, 59, 59))    # Nocturno noche

RANGO_DIURNO = (datetime.time(7, 0), datetime.time(19, 59, 59))  # DIA: 07-19 o 08-20 según supervisor
