"""Reglas puras y compartidas para atribuir y contar pasadas."""

from __future__ import annotations

import calendar
import unicodedata
from collections.abc import Iterable, Mapping
from datetime import date, datetime, time, timedelta
from typing import Any


HORA_INICIO_DIURNO = time(7, 0)
HORA_CORTE_TURNO = time(8, 0)
HORA_INICIO_NOCHE = time(19, 0)
HORA_FIN_DIURNO_MAXIMO = time(20, 0)


def normalizar_turno(turno: str) -> str:
    """Devuelve ``diurno`` o ``nocturno`` para las variantes persistidas y del Excel."""
    if not isinstance(turno, str):
        raise ValueError(f"Turno inválido: {turno!r}")
    texto = "".join(
        caracter
        for caracter in unicodedata.normalize("NFD", turno.strip().upper())
        if unicodedata.category(caracter) != "Mn"
    )
    if texto in {"D", "DIA", "DIURNO"}:
        return "diurno"
    if texto in {"N", "NOCHE", "NOCTURNO"}:
        return "nocturno"
    raise ValueError(f"Turno inválido: {turno!r}")


def fecha_de_turno(fecha_hora: datetime, turno: str) -> date:
    """Calcula el día operativo; la madrugada N pertenece al turno iniciado el día previo.

    Se usan valores de hora local sin zona (como las fechas almacenadas por
    SQLite); se rechazan fechas con zona para evitar conversiones implícitas
    que puedan mover una pasada de día.
    """
    if not isinstance(fecha_hora, datetime):
        raise TypeError("fecha_hora debe ser datetime")
    if fecha_hora.tzinfo is not None and fecha_hora.utcoffset() is not None:
        raise ValueError(
            "fecha_hora debe ser hora local de Argentina sin conversión UTC"
        )

    turno_normalizado = normalizar_turno(turno)
    if turno_normalizado == "nocturno" and fecha_hora.time() < HORA_CORTE_TURNO:
        return fecha_hora.date() - timedelta(days=1)
    return fecha_hora.date()


def mes_de_pasada(fecha_hora: datetime, turno: str) -> tuple[int, int]:
    """Devuelve (año, mes) de la fecha de turno, no de la fecha calendario."""
    fecha_turno = fecha_de_turno(fecha_hora, turno)
    return mes_de_fecha_turno(fecha_turno)


def mes_de_fecha_turno(fecha_turno: date) -> tuple[int, int]:
    """Devuelve el año y mes de una fecha que ya está atribuida al turno."""
    return fecha_turno.year, fecha_turno.month


def hora_corresponde_a_turno(hora: time, turno: str) -> bool:
    """Comprueba el rango compatible con el turno declarado.

    DIA puede ser 07:00-19:00 o 08:00-20:00 según el supervisor; el ciclo
    NOCHE correspondiente puede ser 19:00-07:00 o 20:00-08:00. Las ventanas
    07:00-08:00 y 19:00-20:00 se superponen; la columna/hoja debe resolver
    el turno y cada pasada nocturna de madrugada se atribuye al día anterior.
    """
    turno_normalizado = normalizar_turno(turno)
    if turno_normalizado == "diurno":
        return HORA_INICIO_DIURNO <= hora < HORA_FIN_DIURNO_MAXIMO
    return hora >= HORA_INICIO_NOCHE or hora < HORA_CORTE_TURNO


def rango_datetime_de_mes(
    anio: int, mes: int, turno_noche_cruza: bool
) -> tuple[datetime, datetime]:
    """Devuelve un rango semiabierto de horas calendario que corresponden al mes.

    Cuando NOCHE cruza medianoche, el rango empieza a las 08:00 del primer
    día (la madrugada previa aún es del mes anterior) y termina a las 08:00
    del día primero siguiente, incluyendo así la madrugada del último turno
    noche del mes. El ciclo noche puede terminar a las 07:00 o 08:00; las
    08:00 cubren ambos turnos sin duplicar fechas operativas. Los límites no sustituyen la
    validación del turno declarado en cada registro.
    """
    if not 1 <= mes <= 12:
        raise ValueError(f"Mes inválido: {mes}")
    primer_dia = date(anio, mes, 1)
    if mes == 12:
        primer_dia_siguiente = date(anio + 1, 1, 1)
    else:
        primer_dia_siguiente = date(anio, mes + 1, 1)

    if turno_noche_cruza:
        return (
            datetime.combine(primer_dia, HORA_CORTE_TURNO),
            datetime.combine(primer_dia_siguiente, HORA_CORTE_TURNO),
        )
    return (
        datetime.combine(primer_dia, time.min),
        datetime.combine(primer_dia_siguiente, time.min),
    )


def fecha_calendario_de_turno(
    fecha_turno: date, hora: time, turno: str
) -> date:
    """Infiere el día calendario de una fila Excel cuya hoja nombra el turno.

    En una hoja N, una hora anterior al corte es la madrugada del día
    calendario siguiente. Se valida el resultado con la misma función que
    consumen los reportes, para mantener una única regla de atribución.
    """
    turno_normalizado = normalizar_turno(turno)
    fecha_calendario = fecha_turno
    if turno_normalizado == "nocturno" and hora < HORA_CORTE_TURNO:
        fecha_calendario += timedelta(days=1)
    fecha_calculada = fecha_de_turno(
        datetime.combine(fecha_calendario, hora), turno_normalizado
    )
    if fecha_calculada != fecha_turno:
        raise ValueError(
            "La fecha calendario inferida no coincide con la fecha de turno"
        )
    return fecha_calendario


def fecha_hora_de_registro(fecha: str, hora: str) -> datetime:
    """Combina fecha ISO y hora SQLite como hora local sin zona."""
    try:
        return datetime.fromisoformat(f"{fecha}T{hora}")
    except (TypeError, ValueError) as error:
        raise ValueError(
            f"Fecha/hora de pasada inválida: fecha={fecha!r}, hora={hora!r}"
        ) from error


def fecha_hora_desde_fecha_turno(
    fecha_turno: str, hora: str, turno: str
) -> datetime:
    """Reconstruye una hora local desde fecha de turno persistida y hora.

    La base contiene filas antiguas donde `fecha` ya era operativa y filas
    importadas donde `fecha` es calendario; se usa `fecha_turno` explícita
    como autoridad y se reconstruye la fecha calendario para que los
    consumidores vuelvan a aplicar la regla central sin desplazar dos veces
    las filas nocturnas de madrugada.
    """
    try:
        fecha_operativa = date.fromisoformat(fecha_turno)
        hora_obj = time.fromisoformat(hora)
    except (TypeError, ValueError) as error:
        raise ValueError(
            f"Fecha de turno/hora inválida: {fecha_turno!r} {hora!r}"
        ) from error
    fecha_calendario = fecha_calendario_de_turno(
        fecha_operativa, hora_obj, turno
    )
    return datetime.combine(fecha_calendario, hora_obj)


def _registros_de_objetivo(
    pasadas: Iterable[Mapping[str, Any]],
    objetivo_id: Any,
    anio: int,
    mes: int,
    turno: str | None = None,
):
    """Itera registros del objetivo/mes sin duplicar su clave natural."""
    turno_filtro = normalizar_turno(turno) if turno is not None else None
    vistos: set[tuple[Any, date, int, int, Any]] = set()
    for pasada in pasadas:
        if pasada.get("objetivo_id") != objetivo_id:
            continue
        if "fecha_hora" not in pasada or "turno" not in pasada:
            raise ValueError("Cada pasada debe tener fecha_hora y turno")
        fecha_hora = pasada["fecha_hora"]
        if not isinstance(fecha_hora, datetime):
            raise TypeError("fecha_hora de cada pasada debe ser datetime")
        turno_pasada = normalizar_turno(pasada["turno"])
        fecha_turno = fecha_de_turno(fecha_hora, turno_pasada)
        if (fecha_turno.year, fecha_turno.month) != (anio, mes):
            continue
        if turno_filtro is not None and turno_pasada != turno_filtro:
            continue

        clave = (
            objetivo_id,
            fecha_turno,
            fecha_hora.hour,
            fecha_hora.minute,
            pasada.get("supervisor_id"),
        )
        if clave in vistos:
            continue
        vistos.add(clave)
        yield fecha_hora, fecha_turno, turno_pasada


def contar_pasadas_por_objetivo(
    pasadas: Iterable[Mapping[str, Any]],
    objetivo_id: Any,
    anio: int,
    mes: int,
    turno: str | None = None,
) -> int:
    """Cuenta pasadas naturales únicas del objetivo en el mes y turno pedidos.

    La clave natural conserva la regla de importación: objetivo, fecha de
    turno, minuto y supervisor. Una copia idéntica no infla el conteo; dos
    visitas distintas a diferente hora sí se cuentan.
    """
    if not 1 <= mes <= 12:
        raise ValueError(f"Mes inválido: {mes}")
    return sum(
        1
        for _ in _registros_de_objetivo(
            pasadas, objetivo_id, anio, mes, turno
        )
    )


def contar_pasadas_por_objetivo_en_fecha(
    pasadas: Iterable[Mapping[str, Any]],
    objetivo_id: Any,
    fecha_turno: date,
    turno: str | None = None,
) -> int:
    """Cuenta pasadas naturales únicas de un objetivo en una fecha de turno."""
    turno_filtro = normalizar_turno(turno) if turno is not None else None
    registros = list(
        _registros_de_objetivo(
            pasadas,
            objetivo_id,
            fecha_turno.year,
            fecha_turno.month,
            turno_filtro,
        )
    )
    return sum(1 for _, fecha, _ in registros if fecha == fecha_turno)


def indexar_pasadas_por_objetivo(
    pasadas: Iterable[Mapping[str, Any]],
    anio: int,
    mes: int,
    supervisor_id: Any | None = None,
    turno: str | None = None,
) -> dict[Any, dict[str, set[date]]]:
    """Indexa por objetivo/turno las fechas de turno con al menos una pasada."""
    if not 1 <= mes <= 12:
        raise ValueError(f"Mes inválido: {mes}")
    turno_filtro = normalizar_turno(turno) if turno is not None else None
    resultado: dict[Any, dict[str, set[date]]] = {}
    vistos: set[tuple[Any, date, int, int, Any]] = set()

    for pasada in pasadas:
        objetivo_id = pasada.get("objetivo_id")
        if objetivo_id is None:
            raise ValueError("Cada pasada debe tener objetivo_id")
        if "fecha_hora" not in pasada or "turno" not in pasada:
            raise ValueError("Cada pasada debe tener fecha_hora y turno")
        if supervisor_id is not None and pasada.get("supervisor_id") != supervisor_id:
            continue

        fecha_hora = pasada["fecha_hora"]
        if not isinstance(fecha_hora, datetime):
            raise TypeError("fecha_hora de cada pasada debe ser datetime")
        turno_pasada = normalizar_turno(pasada["turno"])
        fecha_turno = fecha_de_turno(fecha_hora, turno_pasada)
        if (fecha_turno.year, fecha_turno.month) != (anio, mes):
            continue
        if turno_filtro is not None and turno_pasada != turno_filtro:
            continue

        clave = (
            objetivo_id,
            fecha_turno,
            fecha_hora.hour,
            fecha_hora.minute,
            pasada.get("supervisor_id"),
        )
        if clave in vistos:
            continue
        vistos.add(clave)
        resultado.setdefault(
            objetivo_id, {"diurno": set(), "nocturno": set()}
        )[turno_pasada].add(fecha_turno)

    return resultado


def resumen_mensual_objetivo(
    anio: int,
    mes: int,
    fecha_inicio: str | None,
    fecha_fin: str | None,
    dias_semana: str | None,
) -> tuple[int, list[date]]:
    """Devuelve días de servicio esperados y sus fechas activas en el mes.

    `dias_semana` usa la convención ISO existente (1=lunes..7=domingo;
    8=feriado requiere una consulta externa y no se infiere aquí).
    """
    if not 1 <= mes <= 12:
        raise ValueError(f"Mes inválido: {mes}")
    cantidad_dias = calendar.monthrange(anio, mes)[1]
    dias_configurados = {
        int(valor.strip())
        for valor in (dias_semana or "").split(",")
        if valor.strip() and valor.strip().isdigit()
    }
    fechas_activas = []
    for numero_dia in range(1, cantidad_dias + 1):
        fecha = date(anio, mes, numero_dia)
        fecha_iso = fecha.isoformat()
        if fecha_inicio and fecha_iso < fecha_inicio:
            continue
        if fecha_fin and fecha_iso > fecha_fin:
            continue
        if fecha.isoweekday() in dias_configurados:
            fechas_activas.append(fecha)
    return len(fechas_activas), fechas_activas
