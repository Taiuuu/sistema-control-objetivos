"""
normalizador.py

Fase 4: normalización de la HORA cruda de una PasadaCruda.
Fase 5: normalización del TURNO y determinación de fecha operativa/calendario.

Este módulo no sabe nada de Excel ni de PasadaCruda — toma valores crudos
de celdas (lo que haya devuelto openpyxl) y los convierte a tipos válidos.
"""

from __future__ import annotations

import datetime
import re
from datetime import date, time
from typing import Any, NamedTuple, Optional

from .modelos import Problema

# ---------------------------------------------------------------------------
# FASE 4 — Normalización de HORA
# ---------------------------------------------------------------------------
#
#     - `5`      -> 05:00   (1-2 dígitos: hora en punto)
#     - `205`    -> 02:05   (3-4 dígitos: los últimos 2 son minutos)
#     - `2149`   -> 21:49
#     - `"00;52"`-> 00:52   (texto con ';' en vez de ':')
#     - horas >= 24 (o minutos >= 60) -> error crítico (no se corrige solo)
#     - celda vacía / None -> no es una pasada, no es un error


class ResultadoHora(NamedTuple):
    hora: Optional[datetime.time]
    fue_normalizada: bool
    error: Optional[str]


def normalizar_hora(valor_crudo: Any) -> ResultadoHora:
    """Normaliza el valor crudo de una celda HORA a datetime.time.

    Devuelve (hora, fue_normalizada, error):
      - hora: datetime.time válido, o None si no hay pasada o hubo error.
      - fue_normalizada: True si se tuvo que convertir/reinterpretar el
        valor (número, texto con ';', texto "HH:MM"). False si ya venía
        como datetime.time listo para usar.
      - error: mensaje si el valor está fuera de rango o no se puede
        interpretar. None si todo OK (incluyendo el caso "sin pasada").

    Una celda vacía (None, "", o solo espacios) NO es un error: significa
    que no hubo pasada registrada en ese bloque para esa fila.
    """
    if valor_crudo is None:
        return ResultadoHora(None, False, None)

    if isinstance(valor_crudo, datetime.time):
        return ResultadoHora(valor_crudo, False, None)

    # datetime.datetime también puede venir de Excel si la celda combina
    # fecha+hora; se extrae solo la parte de hora.
    if isinstance(valor_crudo, datetime.datetime):
        return ResultadoHora(valor_crudo.time(), True, None)

    if isinstance(valor_crudo, bool):
        # bool es subclase de int en Python; nunca es una hora válida.
        return ResultadoHora(
            None, False, f"Hora '{valor_crudo}' inválida (tipo no reconocido)"
        )

    if isinstance(valor_crudo, (int, float)):
        return _normalizar_desde_texto_numerico(_numero_a_texto(valor_crudo), valor_crudo)

    if isinstance(valor_crudo, str):
        texto = valor_crudo.strip()
        if texto == "":
            return ResultadoHora(None, False, None)

        texto = texto.replace(";", ":")
        texto = re.sub(r"(?i)(?<=\d)\s*[A-Za-z]+\s*$", "", texto)

        if ":" in texto:
            return _normalizar_desde_hhmm(texto, valor_crudo)

        return _normalizar_desde_texto_numerico(texto, valor_crudo)

    return ResultadoHora(None, False, f"Hora '{valor_crudo}' inválida (tipo no reconocido)")


def _numero_a_texto(valor_crudo: float | int) -> Optional[str]:
    """Convierte un int/float de Excel a su representación en dígitos.

    Devuelve None si el número no representa dígitos enteros limpios
    (p. ej. viene con parte fraccionaria real, no solo el ".0" que agrega
    Excel a los enteros).
    """
    if isinstance(valor_crudo, float):
        if not valor_crudo.is_integer():
            return None
        valor_crudo = int(valor_crudo)
    if valor_crudo < 0:
        return None
    return str(valor_crudo)


def _normalizar_desde_texto_numerico(texto: Optional[str], original: Any) -> ResultadoHora:
    if texto is None or not texto.isdigit():
        return ResultadoHora(
            None, False, f"Hora '{original}' inválida (formato no reconocido)"
        )

    n = len(texto)
    if n == 0:
        return ResultadoHora(None, False, None)

    if n <= 2:
        # 1-2 dígitos: hora en punto.
        hora, minuto = int(texto), 0
    elif n <= 4:
        # 3-4 dígitos: los últimos 2 son minutos, el resto es la hora.
        texto = texto.zfill(4)
        hora, minuto = int(texto[:2]), int(texto[2:])
    else:
        return ResultadoHora(
            None, False, f"Hora '{original}' inválida (demasiados dígitos)"
        )

    return _validar_y_construir(hora, minuto, original)


def _normalizar_desde_hhmm(texto: str, original: Any) -> ResultadoHora:
    partes = texto.split(":")
    if len(partes) != 2 or not all(p.strip().isdigit() for p in partes):
        return ResultadoHora(
            None, False, f"Hora '{original}' inválida (formato no reconocido)"
        )
    hora, minuto = int(partes[0]), int(partes[1])
    return _validar_y_construir(hora, minuto, original)


def _validar_y_construir(hora: int, minuto: int, original: Any) -> ResultadoHora:
    if not (0 <= hora <= 23):
        return ResultadoHora(
            None, False, f"Hora '{original}' inválida (fuera de rango 00-23)"
        )
    if not (0 <= minuto <= 59):
        return ResultadoHora(
            None, False, f"Hora '{original}' inválida (fuera de rango 00-23)"
        )
    return ResultadoHora(datetime.time(hora, minuto), True, None)


# ---------------------------------------------------------------------------
# FASE 5 — Normalización de TURNO
# ---------------------------------------------------------------------------

# Variantes aceptadas. Se comparan sin tildes y en mayúsculas, así "DÍA" y
# "DIA" matchean igual.
_VARIANTES_DIURNO = {"D", "DIA", "DIURNO"}
_VARIANTES_NOCTURNO = {"N", "NOCHE", "NOCTURNO"}

_TABLA_TILDES = str.maketrans("ÁÉÍÓÚáéíóú", "AEIOUaeiou")


def _sin_tildes_mayus(texto: str) -> str:
    return texto.translate(_TABLA_TILDES).strip().upper()


class ResultadoTurno(NamedTuple):
    turno: Optional[str]  # "D" | "N" | None
    problema: Optional[Problema]


def normalizar_turno(
    valor: Any,
    hoja: Optional[str] = None,
    objetivo: Optional[str] = None,
    fila_excel: Optional[int] = None,
) -> ResultadoTurno:
    """Normaliza el texto de turno a "D" o "N".

    Acepta, case-insensitive y con o sin tilde:
        Diurno:   D, DIA, DÍA, DIURNO
        Nocturno: N, NOCHE, NOCTURNO

    Devuelve (turno, problema). Si el valor no matchea ninguna variante
    conocida (incluyendo vacío/None), turno es None y se genera un
    Problema de tipo "error_critico" con descripción "turno inválido".
    Los parámetros hoja/objetivo/fila_excel son opcionales y solo se usan
    para enriquecer ese Problema con contexto de dónde ocurrió.
    """
    texto = _sin_tildes_mayus(str(valor)) if valor is not None else ""

    if texto in _VARIANTES_DIURNO:
        return ResultadoTurno("D", None)
    if texto in _VARIANTES_NOCTURNO:
        return ResultadoTurno("N", None)

    problema = Problema(
        tipo="error_critico",
        descripcion="turno inválido",
        hoja=hoja,
        objetivo=objetivo,
        valor_problema=valor,
        fila_excel=fila_excel,
    )
    return ResultadoTurno(None, problema)


# ---------------------------------------------------------------------------
# Prioridad de datos: turno de la celda vs. turno del nombre de hoja
# ---------------------------------------------------------------------------
#
# El nombre de la hoja define el turno operativo real de la pasada. La celda
# TURNO puede estar equivocada (typo), pero ese dato no redefine la identidad
# de la pasada ni la fecha operativa asociada. La discrepancia se informa como
# advertencia para que quede visible en revisión, pero no gana la celda.


def resolver_turno_con_prioridad(
    turno_celda: Optional[str],
    turno_hoja: Optional[str],
    hoja: str,
    objetivo: Optional[str] = None,
    fila_excel: Optional[int] = None,
) -> tuple[Optional[str], Optional[Problema]]:
    """Decide el turno final de una pasada cuando hay dos fuentes posibles:
    el turno indicado en la celda TURNO de la propia pasada, y el turno
    que indica el nombre de la hoja (ambos ya normalizados a "D"/"N").

    Reglas:
      - Si la celda no trae turno (None), se usa el turno de la hoja sin
        generar ninguna advertencia (caso normal: la mayoría de las filas
        de una hoja no repiten el turno en cada pasada).
      - Si la celda sí trae turno y coincide con el de la hoja, se usa ese
        valor, sin advertencia.
      - Si la celda trae un turno que CONTRADICE al de la hoja, se usa el
        turno de la hoja y se genera un Problema de tipo "advertencia"
        señalando la inconsistencia (no bloquea la importación, pero deja
        visible que la celda estaba mal cargada).

    Devuelve (turno_final, problema_opcional).
    """
    if turno_celda is None:
        return turno_hoja, None

    if turno_celda == turno_hoja:
        return turno_celda, None

    problema = Problema(
        tipo="advertencia",
        descripcion=(
            f"El turno indicado en la celda de la pasada ('{turno_celda}') "
            f"no coincide con el turno del nombre de la hoja ('{turno_hoja}'). "
            "Se utilizó el turno de la hoja, porque define la identidad "
            "operativa de la pasada."
        ),
        hoja=hoja,
        objetivo=objetivo,
        valor_problema=turno_celda,
        fila_excel=fila_excel,
    )
    return turno_hoja, problema


# ---------------------------------------------------------------------------
# FASE 5 — Determinación de fecha operativa y fecha calendario
# ---------------------------------------------------------------------------
#
# Un turno nocturno puede atravesar dos fechas calendario, pero toda
# pasada de ese turno pertenece a la fecha operativa en la que comenzó el
# turno (la fecha de la hoja).
#
# Los turnos nocturnos observados arrancan a las 19:00 o a las 20:00 según
# el día, y terminan a las 07:00 u 08:00 del día siguiente. Para no atarse
# a un horario de inicio exacto (que varía), se usa el mediodía (12:00)
# como umbral: toda hora anterior a las 12:00 se interpreta como
# madrugada del día siguiente; toda hora desde las 12:00 en adelante se
# interpreta como parte de la noche de la fecha de la hoja. Esto cubre
# ambos horarios de inicio reales (19:00 y 20:00) sin ambigüedad, ya que
# no hay pasadas nocturnas esperables entre el mediodía y las 19:00.

_UMBRAL_MADRUGADA = time(12, 0)


def determinar_fecha_operativa_y_calendario(
    fecha_hoja: date, turno: str, hora: Optional[time]
) -> tuple[date, date]:
    """Determina la fecha operativa y la fecha calendario de una pasada.

    - Turno "D": fecha_operativa = fecha_calendario = fecha_hoja.
    - Turno "N": fecha_operativa = fecha_hoja siempre.
      fecha_calendario = fecha_hoja si la hora es >= 12:00 (noche de la
      fecha de la hoja), o fecha_hoja + 1 día si la hora es < 12:00
      (madrugada del día siguiente).

    Si `hora` es None (no debería ocurrir para una pasada real, ya que
    sin hora no hay pasada), se asume fecha_calendario = fecha_hoja como
    valor por defecto conservador.

    `turno` debe venir ya normalizado ("D" o "N"); un valor distinto
    levanta ValueError, ya que esta función no es responsable de manejar
    turnos inválidos (eso se resuelve antes, con normalizar_turno).
    """
    if turno not in ("D", "N"):
        raise ValueError(
            f"Turno '{turno}' inválido: se esperaba 'D' o 'N' ya normalizado."
        )

    if turno == "D":
        return fecha_hoja, fecha_hoja

    # Turno "N"
    if hora is None:
        return fecha_hoja, fecha_hoja

    if hora >= _UMBRAL_MADRUGADA:
        return fecha_hoja, fecha_hoja

    return fecha_hoja, fecha_hoja + datetime.timedelta(days=1)