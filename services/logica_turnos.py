from datetime import datetime, timedelta, time
from services.pasadas.calculo_pasadas import (
    HORA_CORTE_TURNO,
    HORA_FIN_DIURNO_MAXIMO,
    HORA_INICIO_DIURNO,
    HORA_INICIO_NOCHE,
    fecha_de_turno,
    normalizar_turno,
)


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


def calcular_turno_y_fecha_operativa(
    fecha: str, hora: str, turno: str | None = None
):
    """
    Devuelve:
    - turno (diurno/nocturno)
    - fecha operativa (la que se usa para reportes)

    Si el turno está declarado, se respeta. Sin ese dato no se infiere
    automáticamente entre las 07:00 y las 08:00 ni entre las 19:00 y las
    20:00, donde ambos ciclos pueden coincidir.
    """

    fecha_obj = datetime.strptime(fecha, "%Y-%m-%d").date()
    hora_obj = _parsear_hora(hora)

    if turno is None:
        if (
            HORA_INICIO_DIURNO <= hora_obj < HORA_CORTE_TURNO
            or HORA_INICIO_NOCHE <= hora_obj < HORA_FIN_DIURNO_MAXIMO
        ):
            raise ValueError(
                "La hora puede corresponder a DIA o NOCHE; indique el turno."
            )
        turno_normalizado = (
            "diurno"
            if HORA_CORTE_TURNO <= hora_obj < HORA_INICIO_NOCHE
            else "nocturno"
        )
    else:
        turno_normalizado = normalizar_turno(turno)

    fecha_turno = fecha_de_turno(
        datetime.combine(fecha_obj, hora_obj), turno_normalizado
    )
    return turno_normalizado, fecha_turno