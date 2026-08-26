"""
validador.py

Validaciones de negocio sobre pasadas ya normalizadas (Fase 9).

IMPORTANTE — alcance reducido tras revisar normalizador.py, duplicados.py y
parser.py: los siguientes checks que pedía el prompt original de FASE 9 NO
se resuelven acá porque ya están cubiertos en fases anteriores, o no son
responsabilidad de este módulo:

  - "Turno inválido no reconocido"        -> normalizador.normalizar_turno() (fase 5)
  - "Inconsistencia turno celda/hoja"     -> normalizador.resolver_turno_con_prioridad() (fase 5)
  - "Hora inválida no corregida"          -> pendiente de cerrar en parser.py/normalizador.py (fase 4),
                                              PasadaNormalizada.hora es time obligatorio, así que acá
                                              nunca puede llegar una hora inválida.
  - "Hora normalizada automáticamente"    -> ídem, pendiente en fase 4, no en validador.
  - "Matching pendiente / aproximado"     -> se calcula en fase 10 desde
                                              ResultadoMatchObjetivo.tipo / ResultadoMatchSupervisor.tipo,
                                              nunca pasa por Problema ni por validar().

Lo que sí valida este módulo, con los datos que ya trae PasadaNormalizada:

  1. Objetivo sin nombre.
  2. Datos parciales inconsistentes: móvil sin supervisor, o supervisor sin móvil.
  3. Hora fuera del rango horario esperado para el turno (D: 07:00-19:00,
     N: 19:00-07:00, configurable vía `contexto`).
  4. Posible pasada en bloque de tabla incorrecto: dentro de una misma fila
     original, un bloque vacío seguido de un bloque no vacío más a la derecha.
     Requiere que PasadaNormalizada exponga un identificador de fila original
     (se asume `fila_excel`, heredado de PasadaCruda; ver nota en el código).
  5. Ambigüedad móvil -> supervisor: un mismo móvil aparece con más de un
     supervisor distinto dentro de la misma hoja.

`contexto` queda solo para configuración opcional (pisar los rangos horarios
por turno); la gran mayoría de los checks no lo necesitan.
"""

from __future__ import annotations

from collections import defaultdict
from datetime import time
from typing import Iterable, Optional

from .modelos import PasadaNormalizada, Problema

# ---------------------------------------------------------------------------
# Configuración de rangos horarios por turno (punto 3)
# ---------------------------------------------------------------------------

# Turno D: 07:00 a 19:00 (no cruza medianoche).
# Turno N: 19:00 a 07:00 (cruza medianoche).
_RANGO_HORARIO_DEFAULT: dict[str, tuple[time, time]] = {
    "D": (time(7, 0), time(19, 0)),
    "N": (time(19, 0), time(7, 0)),
}


def _hora_dentro_de_rango(hora: time, inicio: time, fin: time) -> bool:
    """True si `hora` cae dentro de [inicio, fin], contemplando turnos
    que cruzan medianoche (cuando inicio > fin)."""
    if inicio <= fin:
        return inicio <= hora <= fin
    # Rango que cruza medianoche (ej. 19:00 a 07:00).
    return hora >= inicio or hora <= fin


def _rangos_horarios(contexto: Optional[dict]) -> dict[str, tuple[time, time]]:
    if contexto and "rangos_horarios_por_turno" in contexto:
        # Permite pisar los rangos default sin tocar código.
        return {**_RANGO_HORARIO_DEFAULT, **contexto["rangos_horarios_por_turno"]}
    return _RANGO_HORARIO_DEFAULT


# ---------------------------------------------------------------------------
# Helpers de acceso a campos "posiblemente ausentes" con nombre incierto
# ---------------------------------------------------------------------------

def _valor_no_vacio(v: Optional[str]) -> bool:
    return v is not None and str(v).strip() != ""


def _supervisor_de(p: PasadaNormalizada) -> Optional[str]:
    """Devuelve un identificador de supervisor comparable.

    Se asume que PasadaNormalizada trae `supervisor_id` y/o
    `supervisor_nombre` (mencionados en el análisis de fase 9/10). Se
    prioriza `supervisor_id` si existe; si no, se cae a `supervisor_nombre`.
    Si el modelo real usa otro nombre de campo, ajustar acá.
    """
    sid = getattr(p, "supervisor_id", None)
    if _valor_no_vacio(sid):
        return str(sid).strip()
    snombre = getattr(p, "supervisor_nombre", None)
    if _valor_no_vacio(snombre):
        return str(snombre).strip().upper()
    return None


def _fila_original_de(p: PasadaNormalizada) -> Optional[int]:
    """Identificador de la fila original del Excel, para el check 4.

    Se asume que sobrevive la normalización como `fila_excel` (viene de
    PasadaCruda.fila_excel). Si el campo no existe en PasadaNormalizada,
    el check 4 se salta silenciosamente para esa pasada en vez de romper
    (mejor no reportar un falso patrón que asumir mal el nombre del campo).
    """
    return getattr(p, "fila_excel", None)


# ---------------------------------------------------------------------------
# Checks individuales
# ---------------------------------------------------------------------------

def _check_objetivo_sin_nombre(pasadas: Iterable[PasadaNormalizada]) -> list[Problema]:
    problemas: list[Problema] = []
    for p in pasadas:
        if not _valor_no_vacio(getattr(p, "objetivo_nombre", None)):
            problemas.append(
                Problema(
                    tipo="advertencia",
                    descripcion=(
                        f"Pasada sin nombre de objetivo en la hoja '{p.hoja}' "
                        f"(bloque {p.bloque_tabla})."
                    ),
                    hoja=p.hoja,
                    valor_problema=getattr(p, "objetivo_nombre", None),
                    fila_excel=p.fila_excel,
                )
            )
    return problemas


def _check_datos_parciales_movil_supervisor(
    pasadas: Iterable[PasadaNormalizada],
) -> list[Problema]:
    problemas: list[Problema] = []
    for p in pasadas:
        movil = getattr(p, "movil", None)
        supervisor = _supervisor_de(p)
        tiene_movil = _valor_no_vacio(movil)
        tiene_supervisor = supervisor is not None

        if tiene_movil and not tiene_supervisor:
            problemas.append(
                Problema(
                    tipo="advertencia",
                    descripcion=(
                        f"Pasada con móvil '{movil}' pero sin supervisor, "
                        f"en la hoja '{p.hoja}' (bloque {p.bloque_tabla})."
                    ),
                    hoja=p.hoja,
                    valor_problema=movil,
                    fila_excel=p.fila_excel,
                )
            )
        elif tiene_supervisor and not tiene_movil:
            problemas.append(
                Problema(
                    tipo="advertencia",
                    descripcion=(
                        f"Pasada con supervisor '{supervisor}' pero sin móvil, "
                        f"en la hoja '{p.hoja}' (bloque {p.bloque_tabla})."
                    ),
                    hoja=p.hoja,
                    valor_problema=supervisor,
                    fila_excel=p.fila_excel,
                )
            )
    return problemas


def _turno_operativo_de(p: PasadaNormalizada) -> Optional[str]:
    """Turno real que trabajó la cuadrilla, para efectos de plausibilidad
    horaria: el de la HOJA, no el resuelto por prioridad de celda.

    Una celda TURNO que contradice a la hoja ya se reporta como
    advertencia aparte (normalizador.resolver_turno_con_prioridad, fase 5)
    y gana en `p.turno` para fines de identidad/persistencia — pero eso
    no significa que la cuadrilla haya cambiado de turno esa fila puntual;
    lo más probable es un error de tipeo. Para saber si una hora es
    plausible (ej. 06:40 en una hoja "12-7 (N)"), lo que importa es el
    turno de la hoja. Si `turno_hoja` no está disponible (por compatibilidad
    con datos viejos), se cae a `p.turno`.
    """
    turno_hoja = getattr(p, "turno_hoja", None)
    return turno_hoja if turno_hoja is not None else p.turno


def _check_hora_fuera_de_rango(
    pasadas: Iterable[PasadaNormalizada], contexto: Optional[dict]
) -> list[Problema]:
    rangos = _rangos_horarios(contexto)
    problemas: list[Problema] = []
    for p in pasadas:
        turno_operativo = _turno_operativo_de(p)
        rango = rangos.get(turno_operativo)
        if rango is None:
            # Turno no contemplado en la configuración de rangos; no debería
            # pasar (turno ya viene validado como "D"|"N" en fase 5), pero
            # se ignora en vez de asumir un default arbitrario.
            continue
        inicio, fin = rango
        if not _hora_dentro_de_rango(p.hora, inicio, fin):
            problemas.append(
                Problema(
                    tipo="advertencia",
                    descripcion=(
                        f"Hora {p.hora.strftime('%H:%M')} fuera del rango esperado "
                        f"para turno {turno_operativo} ({inicio.strftime('%H:%M')}-"
                        f"{fin.strftime('%H:%M')}), en la hoja '{p.hoja}' "
                        f"(bloque {p.bloque_tabla})."
                    ),
                    hoja=p.hoja,
                    valor_problema=p.hora.strftime("%H:%M"),
                    fila_excel=p.fila_excel,
                )
            )
    return problemas


def _check_bloque_tabla_incorrecto(
    pasadas: Iterable[PasadaNormalizada],
) -> list[Problema]:
    """Detecta, dentro de una misma fila original, un bloque vacío seguido
    de un bloque no vacío en una posición posterior.

    Se agrupa por (hoja, fila_excel). Si `fila_excel` no está disponible en
    PasadaNormalizada para alguna pasada, esa pasada se excluye del check
    (no se puede saber a qué fila original pertenece).
    """
    por_fila: dict[tuple[str, int], list[PasadaNormalizada]] = defaultdict(list)
    for p in pasadas:
        fila = _fila_original_de(p)
        if fila is None:
            continue
        por_fila[(p.hoja, fila)].append(p)

    problemas: list[Problema] = []
    for (hoja, fila), grupo in por_fila.items():
        grupo_ordenado = sorted(grupo, key=lambda p: p.bloque_tabla)

        def _pasada_vacia(p: PasadaNormalizada) -> bool:
            return not any(
                _valor_no_vacio(v)
                for v in (
                    getattr(p, "movil", None),
                    _supervisor_de(p),
                )
            )

        vacios = [_pasada_vacia(p) for p in grupo_ordenado]
        # Si en algún punto hay un bloque vacío y más adelante uno lleno,
        # es sospechoso de estar corrido de tabla.
        hubo_vacio = False
        for p, vacio in zip(grupo_ordenado, vacios):
            if vacio:
                hubo_vacio = True
                continue
            if hubo_vacio:
                problemas.append(
                    Problema(
                        tipo="advertencia",
                        descripcion=(
                            f"Posible pasada en tabla incorrecta: en la hoja '{hoja}' "
                            f"(fila {fila}), el bloque {p.bloque_tabla} tiene datos "
                            "pero un bloque anterior de la misma fila está vacío."
                        ),
                        hoja=hoja,
                        valor_problema=p.bloque_tabla,
                        fila_excel=fila,
                    )
                )
    return problemas


def _check_ambiguedad_movil_supervisor(
    pasadas: Iterable[PasadaNormalizada],
) -> list[Problema]:
    """Un mismo móvil con más de un supervisor distinto dentro de la misma
    hoja: se reporta como ambigüedad."""
    por_movil: dict[tuple[str, str], set[str]] = defaultdict(set)
    for p in pasadas:
        movil = getattr(p, "movil", None)
        supervisor = _supervisor_de(p)
        if not _valor_no_vacio(movil) or supervisor is None:
            continue
        por_movil[(p.hoja, str(movil).strip())].add(supervisor)

    problemas: list[Problema] = []
    for (hoja, movil), supervisores in por_movil.items():
        if len(supervisores) > 1:
            problemas.append(
                Problema(
                    tipo="advertencia",
                    descripcion=(
                        f"Ambigüedad móvil->supervisor: el móvil '{movil}' aparece "
                        f"con más de un supervisor distinto ({', '.join(sorted(supervisores))}) "
                        f"en la hoja '{hoja}'."
                    ),
                    hoja=hoja,
                    valor_problema=movil,
                )
            )
    return problemas


# ---------------------------------------------------------------------------
# Punto de entrada
# ---------------------------------------------------------------------------

def validar(
    pasadas_normalizadas: list[PasadaNormalizada],
    contexto: Optional[dict] = None,
) -> list[Problema]:
    """Corre los 5 checks de negocio sobre las pasadas ya normalizadas.

    `contexto` es opcional y solo se usa hoy para pisar los rangos horarios
    por turno vía contexto["rangos_horarios_por_turno"] = {"D": (time, time), "N": (time, time)}.
    """
    problemas: list[Problema] = []
    problemas += _check_objetivo_sin_nombre(pasadas_normalizadas)
    problemas += _check_datos_parciales_movil_supervisor(pasadas_normalizadas)
    problemas += _check_hora_fuera_de_rango(pasadas_normalizadas, contexto)
    problemas += _check_bloque_tabla_incorrecto(pasadas_normalizadas)
    problemas += _check_ambiguedad_movil_supervisor(pasadas_normalizadas)
    return problemas