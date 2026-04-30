from datetime import datetime, timedelta, time

def calcular_turno_y_fecha_operativa(fecha: str, hora: str):
    """
    Devuelve:
    - turno (diurno/nocturno)
    - fecha operativa (la que se usa para reportes)
    """

    fecha_obj = datetime.strptime(fecha, "%Y-%m-%d").date()
    hora_obj = datetime.strptime(hora, "%H:%M:%S").time()

    # Diurno: 07:00 - 18:59
    if time(7, 0) <= hora_obj < time(19, 0):
        return "diurno", fecha_obj

    # Nocturno:
    # 19:00 - 23:59 -> mismo día
    if hora_obj >= time(19, 0):
        return "nocturno", fecha_obj

    # 00:00 - 06:59 -> día anterior
    return "nocturno", fecha_obj - timedelta(days=1)