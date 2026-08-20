"""
Normalización de horas y turnos, y determinación de fecha operativa.

Se implementa en la Fase 4 (horas) y Fase 5 (turno + fecha operativa).
"""

from __future__ import annotations

from datetime import date, time
from typing import Optional


def normalizar_hora(valor_crudo) -> tuple[Optional[time], bool, Optional[str]]:
    """
    Normaliza un valor de hora tal como viene del Excel a un objeto
    `time` en formato 24hs.

    Acepta: datetime.time nativo, números/strings numéricos (5, "05",
    205, 2149) y strings con ";" en vez de ":" (ej. "00;52").

    Devuelve una tupla (hora, fue_normalizada, error):
        - hora: el `time` resultante, o None si no había pasada
          (valor vacío) o si hubo un error irrecuperable.
        - fue_normalizada: True si se tuvo que reinterpretar el
          formato (ej. 205 -> 02:05), para marcarlo como advertencia
          informativa en el reporte.
        - error: mensaje de error si el valor es inválido (ej. hora
          >= 24), None si está todo bien.

    Se implementa en la Fase 4.
    """
    pass


def normalizar_turno(valor) -> Optional[str]:
    """
    Normaliza el texto de turno (D, DIA, DÍA, DIURNO / N, NOCHE,
    NOCTURNO, case-insensitive y sin tildes) a "D" o "N".

    Devuelve None si el valor no matchea ninguna variante conocida
    (se debe generar un Problema de tipo error_critico en ese caso,
    responsabilidad de validador.py).

    Se implementa en la Fase 5.
    """
    pass


def determinar_fecha_operativa_y_calendario(
    fecha_hoja: date, turno: str, hora: Optional[time]
) -> tuple[date, date]:
    """
    Determina la fecha operativa y la fecha calendario de una pasada.

    - Turno D: fecha_operativa = fecha_calendario = fecha_hoja.
    - Turno N: fecha_operativa = fecha_hoja siempre. fecha_calendario
      depende de si la hora corresponde a la noche de fecha_hoja o a
      la madrugada del día siguiente.

    Se implementa en la Fase 5.
    """
    pass