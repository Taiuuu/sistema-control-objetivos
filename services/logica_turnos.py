from datetime import datetime, timedelta, time


def _parsear_hora(hora: str) -> time:
    """
    Acepta formatos:
    - HH:MM
    - HH:MM:SS
    """
    for formato in ("%H:%M:%S", "%H:%M"):
        try:
            return datetime.strptime(hora, formato).time()
        except ValueError:
            continue
    raise ValueError(f"Formato de hora inválido: {hora}")


def calcular_turno_y_fecha_operativa(fecha: str, hora: str):
    """
    Devuelve:
    - turno (diurno/nocturno)
    - fecha operativa (la que se usa para reportes)
    """

    fecha_obj = datetime.strptime(fecha, "%Y-%m-%d").date()
    hora_obj = _parsear_hora(hora)

    # Diurno: 07:00 - 18:59
    if time(7, 0) <= hora_obj < time(19, 0):
        return "diurno", fecha_obj

    # Nocturno:
    # 19:00 - 23:59 -> mismo día
    if hora_obj >= time(19, 0):
        return "nocturno", fecha_obj

    # 00:00 - 06:59 -> día anterior
    return "nocturno", fecha_obj - timedelta(days=1)