"""
matcher.py

Fase 6-7: matching de nombres de objetivo y supervisor (tal como vienen
escritos en el Excel) contra los registros ya existentes en la base.

Este módulo NO EXISTÍA en el pipeline entregado hasta ahora; se crea acá
para poder completar `analizar_excel()` (Fase 10). Documento cada decisión
de diseño porque no había especificación previa de fase 6-7 en la
conversación — son criterios propios, no confirmados por el usuario:

  - Normalización de nombres: mayúsculas, sin tildes, espacios colapsados.
  - Match "exacto": igualdad de nombres ya normalizados.
  - Si no hay exacto: se calculan sugerencias con similitud de texto
    (difflib.SequenceMatcher), con un pequeño bonus de orden si coincide
    el último "token" del nombre (por apellidos compuestos o nombres
    invertidos, ej. "PEREZ, JUAN" vs "JUAN PEREZ").
  - Umbral de sugerencia: similitud >= 0.5. Por debajo de eso, se
    considera "no_reconocido" directamente (no tiene sentido sugerir
    algo con menos de la mitad de las letras en común).
  - Máximo 5 sugerencias, ordenadas por (similitud + bonus) descendente.

Contrato asumido de `conexion_bd` (definido acá, no venía dado):
  Un `sqlite3.Connection` (o cualquier objeto DB-API compatible con
  `.cursor()`), con dos tablas ya existentes:
    - objetivos(id, nombre, ...)
    - supervisores(id, nombre, ...)
  Es consistente con duplicados.py, que ya asume esta misma API
  (`conexion_bd.cursor()` + SQL crudo) para la tabla `pasadas`.
"""

from __future__ import annotations

import difflib
from typing import Optional

from .modelos import (
    ObjetivoBD,
    PasadaNormalizada,
    ResultadoMatchObjetivo,
    ResultadoMatchSupervisor,
    SugerenciaObjetivo,
    SugerenciaSupervisor,
    SupervisorBD,
)

_TABLA_TILDES = str.maketrans("ÁÉÍÓÚáéíóú", "AEIOUaeiou")

_UMBRAL_SUGERENCIA = 0.5
_MAX_SUGERENCIAS = 5


def _normalizar_nombre(nombre: str) -> str:
    """Mayúsculas, sin tildes, espacios colapsados. Base de comparación
    tanto para el match exacto como para calcular similitud."""
    texto = (nombre or "").translate(_TABLA_TILDES).strip().upper()
    return " ".join(texto.split())

def normalizar_nombre(nombre: str) -> str:
    """Versión pública de _normalizar_nombre(), para que reporte.py pueda
    mapear resultados de matching por nombre sin tocar un símbolo privado."""
    return _normalizar_nombre(nombre)

def _similitud(a: str, b: str) -> float:
    return difflib.SequenceMatcher(None, a, b).ratio()


def _coincide_sufijo(a: str, b: str) -> bool:
    tokens_a = a.split()
    tokens_b = b.split()
    if not tokens_a or not tokens_b:
        return False
    return tokens_a[-1] == tokens_b[-1]


# ---------------------------------------------------------------------------
# Lectura de catálogos desde la base
# ---------------------------------------------------------------------------


def obtener_objetivos_bd(conexion_bd) -> list[ObjetivoBD]:
    cursor = conexion_bd.cursor()
    cursor.execute("SELECT id, nombre FROM objetivos")
    return [ObjetivoBD(id=fila[0], nombre=fila[1]) for fila in cursor.fetchall()]


def obtener_supervisores_bd(conexion_bd) -> list[SupervisorBD]:
    cursor = conexion_bd.cursor()
    cursor.execute("SELECT id, nombre FROM supervisores")
    return [SupervisorBD(id=fila[0], nombre=fila[1]) for fila in cursor.fetchall()]


# ---------------------------------------------------------------------------
# Matching individual (una sola búsqueda)
# ---------------------------------------------------------------------------


def matchear_objetivo(
    nombre_excel: str,
    objetivos_bd: list[ObjetivoBD],
) -> ResultadoMatchObjetivo:
    nombre_norm = _normalizar_nombre(nombre_excel)

    for obj in objetivos_bd:
        if _normalizar_nombre(obj.nombre) == nombre_norm:
            return ResultadoMatchObjetivo(
                nombre_excel=nombre_excel,
                tipo="exacto",
                objetivo_exacto=obj,
            )

    candidatos: list[SugerenciaObjetivo] = []
    for obj in objetivos_bd:
        obj_norm = _normalizar_nombre(obj.nombre)
        sim = _similitud(nombre_norm, obj_norm)
        if sim >= _UMBRAL_SUGERENCIA:
            candidatos.append(
                SugerenciaObjetivo(
                    objetivo=obj,
                    similitud=sim,
                    coincide_sufijo=_coincide_sufijo(nombre_norm, obj_norm),
                )
            )

    if candidatos:
        candidatos.sort(
            key=lambda c: c.similitud + (0.1 if c.coincide_sufijo else 0.0),
            reverse=True,
        )
        return ResultadoMatchObjetivo(
            nombre_excel=nombre_excel,
            tipo="sugerencias",
            sugerencias=candidatos[:_MAX_SUGERENCIAS],
            nombre_sugerido_nuevo=nombre_excel.strip(),
        )

    return ResultadoMatchObjetivo(
        nombre_excel=nombre_excel,
        tipo="no_reconocido",
        nombre_sugerido_nuevo=nombre_excel.strip(),
    )


def matchear_supervisor(
    nombre_excel: str,
    supervisores_bd: list[SupervisorBD],
) -> ResultadoMatchSupervisor:
    nombre_norm = _normalizar_nombre(nombre_excel)

    for sup in supervisores_bd:
        if _normalizar_nombre(sup.nombre) == nombre_norm:
            return ResultadoMatchSupervisor(
                nombre_excel=nombre_excel,
                tipo="exacto",
                supervisor_exacto=sup,
            )

    candidatos: list[SugerenciaSupervisor] = []
    for sup in supervisores_bd:
        sup_norm = _normalizar_nombre(sup.nombre)
        sim = _similitud(nombre_norm, sup_norm)
        if sim >= _UMBRAL_SUGERENCIA:
            candidatos.append(
                SugerenciaSupervisor(
                    supervisor=sup,
                    similitud=sim,
                    coincide_sufijo=_coincide_sufijo(nombre_norm, sup_norm),
                )
            )

    if candidatos:
        candidatos.sort(
            key=lambda c: c.similitud + (0.1 if c.coincide_sufijo else 0.0),
            reverse=True,
        )
        return ResultadoMatchSupervisor(
            nombre_excel=nombre_excel,
            tipo="sugerencias",
            sugerencias=candidatos[:_MAX_SUGERENCIAS],
            nombre_sugerido_nuevo=nombre_excel.strip(),
        )

    return ResultadoMatchSupervisor(
        nombre_excel=nombre_excel,
        tipo="no_reconocido",
        nombre_sugerido_nuevo=nombre_excel.strip(),
    )


# ---------------------------------------------------------------------------
# Matching en lote sobre una lista de pasadas normalizadas
# ---------------------------------------------------------------------------
#
# Se agrupa por nombre normalizado para no repetir el mismo matching una
# vez por cada pasada que comparte el mismo objetivo/supervisor (una hoja
# puede tener decenas de pasadas del mismo objetivo). El resultado se
# aplica a todas las pasadas de ese grupo por igual.


def aplicar_matching_objetivos(
    pasadas: list[PasadaNormalizada],
    objetivos_bd: list[ObjetivoBD],
) -> list[ResultadoMatchObjetivo]:
    """Corre matchear_objetivo() una vez por nombre distinto presente en
    `pasadas`, y completa `objetivo_id` in-place en cada PasadaNormalizada
    cuando el match es exacto.

    Pasadas con objetivo_nombre vacío se excluyen (ya las reporta
    validador.py como "objetivo sin nombre"; no tiene sentido matchear
    una cadena vacía).

    Devuelve la lista de ResultadoMatchObjetivo, uno por nombre distinto
    (no uno por pasada), para poder contar `objetivos_para_revisar` como
    cantidad de OBJETIVOS pendientes, no de pasadas afectadas.
    """
    por_nombre: dict[str, list[PasadaNormalizada]] = {}
    for p in pasadas:
        if not p.objetivo_nombre or not p.objetivo_nombre.strip():
            continue
        clave = _normalizar_nombre(p.objetivo_nombre)
        por_nombre.setdefault(clave, []).append(p)

    resultados: list[ResultadoMatchObjetivo] = []
    for grupo in por_nombre.values():
        nombre_excel = grupo[0].objetivo_nombre
        resultado = matchear_objetivo(nombre_excel, objetivos_bd)
        resultados.append(resultado)
        if resultado.tipo == "exacto":
            for p in grupo:
                p.objetivo_id = resultado.objetivo_exacto.id

    return resultados


def aplicar_matching_supervisores(
    pasadas: list[PasadaNormalizada],
    supervisores_bd: list[SupervisorBD],
) -> list[ResultadoMatchSupervisor]:
    """Análogo a aplicar_matching_objetivos(), pero para supervisor_nombre
    -> supervisor_id. Pasadas sin supervisor (móvil sin supervisor cargado)
    se excluyen; ya las reporta validador.py."""
    por_nombre: dict[str, list[PasadaNormalizada]] = {}
    for p in pasadas:
        if not p.supervisor_nombre or not p.supervisor_nombre.strip():
            continue
        clave = _normalizar_nombre(p.supervisor_nombre)
        por_nombre.setdefault(clave, []).append(p)

    resultados: list[ResultadoMatchSupervisor] = []
    for grupo in por_nombre.values():
        nombre_excel = grupo[0].supervisor_nombre
        resultado = matchear_supervisor(nombre_excel, supervisores_bd)
        resultados.append(resultado)
        if resultado.tipo == "exacto":
            for p in grupo:
                p.supervisor_id = resultado.supervisor_exacto.id

    return resultados