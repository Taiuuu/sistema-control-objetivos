"""
matcher.py

Fase 6: matching de un nombre de objetivo tal como viene en el Excel
contra el catálogo de objetivos ya existentes en la base.

Esta etapa NO escribe nada en la base — solo arma la estructura de
sugerencias que consume la pantalla de "Matching" (punto 19 de las reglas
confirmadas). La decisión de qué objetivo usar, o si crear uno nuevo,
siempre la toma el usuario. La escritura real (crear objetivo nuevo o
asociar el existente) es de las fases 12/13.
"""

from __future__ import annotations

import difflib
import re
from datetime import date
from typing import Any, Iterable

try:
    from .modelos import (
        ObjetivoBD,
        ResultadoMatchObjetivo,
        SugerenciaObjetivo,
        SupervisorBD,
        ResultadoMatchSupervisor,
        SugerenciaSupervisor,
    )
except ImportError:
    from modelos import (
        ObjetivoBD,
        ResultadoMatchObjetivo,
        SugerenciaObjetivo,
        SupervisorBD,
        ResultadoMatchSupervisor,
        SugerenciaSupervisor,
    )

# Umbral mínimo de similitud de texto plano para que un candidato entre al
# ranking de sugerencias (salvo que comparta sufijo, ver más abajo). Se
# calibró contra el catálogo real: por debajo de esto empiezan a aparecer
# "sugerencias" que en la práctica son ruido (objetivos sin relación real,
# que solo comparten algunas letras sueltas).
_UMBRAL_SIMILITUD = 0.5

# Cuántos tokens finales se comparan para el bonus de "coincide sufijo".
# 2 alcanza para distinguir casos como "OBRA R1003 (P1) MERLO" vs
# "OBRA R1003 (P2) MERLO", donde el último token solo ("MERLO") es igual
# en ambos y no alcanza para diferenciarlos.
_TOKENS_SUFIJO = 2

# Bonus que se suma al ratio de similitud cuando el candidato comparte el
# sufijo con el nombre del Excel. Es deliberadamente alto: existe
# justamente para que un candidato con sufijo compartido pero ratio de
# texto plano algo menor le gane en el ranking a otro con ratio más alto
# pero sufijo distinto (el caso "CORTIJO - RUTA 202" vs "CORTIJO - RUTA 8").
_BONUS_SUFIJO = 0.30

_TABLA_TILDES = str.maketrans("ÁÉÍÓÚáéíóúÑñ", "AEIOUaeiouNn")
_RE_SEPARADORES = re.compile(r"[^A-Z0-9]+")


def _normalizar_texto(texto: str) -> str:
    texto = texto.translate(_TABLA_TILDES).strip().upper()
    texto = re.sub(r"\s+", " ", texto)
    return texto


def _tokenizar(texto_normalizado: str) -> list[str]:
    tokens = _RE_SEPARADORES.split(texto_normalizado)
    return [t for t in tokens if t]


def _sufijo(tokens: list[str], n: int = _TOKENS_SUFIJO) -> tuple[str, ...]:
    if not tokens:
        return ()
    largo = min(n, len(tokens))
    return tuple(tokens[-largo:])


def _normalizar_objetivos_bd(objetivos_bd: Iterable[Any]) -> list[ObjetivoBD]:
    """Acepta el catálogo en varias formas cómodas para el llamador:
    lista de ObjetivoBD, de dicts {"id":..., "nombre":...}, de tuplas
    (id, nombre), o de strings sueltos (se les asigna id=None).
    """
    resultado: list[ObjetivoBD] = []
    for item in objetivos_bd:
        if isinstance(item, ObjetivoBD):
            resultado.append(item)
        elif isinstance(item, dict):
            resultado.append(ObjetivoBD(id=item.get("id"), nombre=item["nombre"]))
        elif isinstance(item, (tuple, list)) and len(item) == 2:
            resultado.append(ObjetivoBD(id=item[0], nombre=item[1]))
        elif isinstance(item, str):
            resultado.append(ObjetivoBD(id=None, nombre=item))
        else:
            raise TypeError(
                f"No se pudo interpretar el objetivo de catálogo {item!r}: "
                "se espera ObjetivoBD, dict, tupla (id, nombre) o str."
            )
    return resultado


def matchear_objetivo(
    nombre_excel: str, objetivos_bd: Iterable[Any]
) -> ResultadoMatchObjetivo:
    """Matchea `nombre_excel` contra el catálogo `objetivos_bd`.

    1. Match exacto (case-insensitive, ignorando espacios/tildes) -> tipo
       "exacto", con `objetivo_exacto` resuelto y sin permitir crear
       nuevo (ya existe).
    2. Si no hay exacto, se buscan hasta 5 candidatos por similitud de
       texto, priorizando en el ranking a los que además comparten el
       sufijo (los últimos 1-2 tokens) con el nombre del Excel, para no
       confundir objetivos que solo comparten un prefijo genérico (OBRA,
       BARRIO, POLI, CAM) pero son lugares distintos.
    3. Si ningún candidato alcanza un mínimo de similitud (y ninguno
       comparte sufijo), tipo "no_reconocido": se ofrece crear un
       objetivo nuevo con ese nombre y fecha_inicio = hoy.

    En los tres casos `permite_crear_nuevo` indica si corresponde ofrecer
    la opción de alta (False solo cuando ya hubo match exacto).
    """
    catalogo = _normalizar_objetivos_bd(objetivos_bd)
    nombre_norm = _normalizar_texto(nombre_excel)
    tokens_excel = _tokenizar(nombre_norm)
    sufijo_excel = _sufijo(tokens_excel)

    # --- 1. match exacto ---
    for objetivo in catalogo:
        if _normalizar_texto(objetivo.nombre) == nombre_norm:
            return ResultadoMatchObjetivo(
                nombre_excel=nombre_excel,
                tipo="exacto",
                objetivo_exacto=objetivo,
                permite_crear_nuevo=False,
            )

    # --- 2. candidatos por similitud, con bonus de sufijo compartido ---
    candidatos: list[tuple[float, float, bool, ObjetivoBD]] = []
    for objetivo in catalogo:
        nombre_obj_norm = _normalizar_texto(objetivo.nombre)
        ratio = difflib.SequenceMatcher(None, nombre_norm, nombre_obj_norm).ratio()

        tokens_obj = _tokenizar(nombre_obj_norm)
        sufijo_obj = _sufijo(tokens_obj)
        coincide_sufijo = bool(sufijo_excel) and sufijo_excel == sufijo_obj

        score = ratio + (_BONUS_SUFIJO if coincide_sufijo else 0.0)
        candidatos.append((score, ratio, coincide_sufijo, objetivo))

    # ordenar por score (con el bonus aplicado) y, a igualdad, por ratio puro
    candidatos.sort(key=lambda c: (c[0], c[1]), reverse=True)

    # se conserva un candidato si tiene similitud razonable de texto plano,
    # o si comparte sufijo (aunque el texto completo difiera bastante, p.
    # ej. nombres largos con un prefijo distinto pero mismo sufijo puntual)
    relevantes = [c for c in candidatos if c[1] >= _UMBRAL_SIMILITUD or c[2]]
    top5 = relevantes[:5]

    if not top5:
        return ResultadoMatchObjetivo(
            nombre_excel=nombre_excel,
            tipo="no_reconocido",
            permite_crear_nuevo=True,
            nombre_sugerido_nuevo=nombre_excel.strip(),
            fecha_inicio_sugerida=date.today(),
        )

    sugerencias = [
        SugerenciaObjetivo(
            objetivo=objetivo,
            similitud=round(ratio, 3),
            coincide_sufijo=coincide_sufijo,
        )
        for _score, ratio, coincide_sufijo, objetivo in top5
    ]

    return ResultadoMatchObjetivo(
            nombre_excel=nombre_excel,
            tipo="sugerencias",
            sugerencias=sugerencias,
            permite_crear_nuevo=True,
            nombre_sugerido_nuevo=nombre_excel.strip(),
            fecha_inicio_sugerida=date.today(),
        )

    # ---------------------------------------------------------------------------
    # Matching de SUPERVISORES
    # ---------------------------------------------------------------------------

    def _normalizar_supervisores_bd(supervisores_bd: Iterable[Any]) -> list[SupervisorBD]:
        """Acepta el catálogo en varias formas cómodas para el llamador:
        lista de SupervisorBD, de dicts {"id":..., "nombre":...}, de tuplas
        (id, nombre), o de strings sueltos (se les asigna id=None).
        """
        resultado: list[SupervisorBD] = []
        for item in supervisores_bd:
            if isinstance(item, SupervisorBD):
                resultado.append(item)
            elif isinstance(item, dict):
                resultado.append(SupervisorBD(id=item.get("id"), nombre=item["nombre"]))
            elif isinstance(item, (tuple, list)) and len(item) == 2:
                resultado.append(SupervisorBD(id=item[0], nombre=item[1]))
            elif isinstance(item, str):
                resultado.append(SupervisorBD(id=None, nombre=item))
            else:
                raise TypeError(
                    f"No se pudo interpretar el supervisor de catálogo {item!r}: "
                    "se espera SupervisorBD, dict, tupla (id, nombre) o str."
                )
        return resultado

    def matchear_supervisor(
        nombre_excel: str, supervisores_bd: Iterable[Any]
    ) -> ResultadoMatchSupervisor:
        """Matchea `nombre_excel` contra el catálogo `supervisores_bd`.

        Soporta el formato habitual "APELLIDO, NOMBRE" y variantes como
        "NOMBRE APELLIDO": la comparación exacta se hace tanto por texto
        normalizado como por conjunto de tokens, de modo que "GARCIA, JUAN"
        matchea exacto con "JUAN GARCIA" (y viceversa).

        1. Match exacto (case-insensitive, sin tildes, o mismo conjunto de
           tokens) -> tipo "exacto", con `supervisor_exacto` resuelto y sin
           permitir crear nuevo (ya existe).
        2. Si no hay exacto, se buscan hasta 5 candidatos por similitud de
           texto, con bonus por sufijo compartido y por tokens en común
           (un apellido o nombre que coincida sube el score).
        3. Si ningún candidato alcanza el umbral -> tipo "no_reconocido":
           se ofrece crear un supervisor nuevo con ese nombre.

        En los tres casos `permite_crear_nuevo` indica si corresponde ofrecer
        la opción de alta (False solo cuando ya hubo match exacto).
        """
        catalogo = _normalizar_supervisores_bd(supervisores_bd)
        nombre_norm = _normalizar_texto(nombre_excel)
        tokens_excel = _tokenizar(nombre_norm)
        set_tokens_excel = set(tokens_excel)
        sufijo_excel = _sufijo(tokens_excel)

        # --- 1. match exacto (texto idéntico O mismos tokens en cualquier orden) ---
        for supervisor in catalogo:
            nombre_sup_norm = _normalizar_texto(supervisor.nombre)
            tokens_sup = _tokenizar(nombre_sup_norm)

            if nombre_sup_norm == nombre_norm or (
                set_tokens_excel and set_tokens_excel == set(tokens_sup)
            ):
                return ResultadoMatchSupervisor(
                    nombre_excel=nombre_excel,
                    tipo="exacto",
                    supervisor_exacto=supervisor,
                    permite_crear_nuevo=False,
                )

        # --- 2. candidatos por similitud, con bonus de sufijo y tokens comunes ---
        candidatos: list[tuple[float, float, bool, SupervisorBD]] = []
        for supervisor in catalogo:
            nombre_sup_norm = _normalizar_texto(supervisor.nombre)
            ratio = difflib.SequenceMatcher(
                None, nombre_norm, nombre_sup_norm
            ).ratio()

            tokens_sup = _tokenizar(nombre_sup_norm)
            sufijo_sup = _sufijo(tokens_sup)
            coincide_sufijo = bool(sufijo_excel) and sufijo_excel == sufijo_sup

            # bonus por tokens compartidos (apellido o nombre que coincida)
            tokens_comunes = set_tokens_excel & set(tokens_sup)
            bonus_tokens = 0.15 if tokens_comunes and tokens_excel else 0.0

            score = ratio + (_BONUS_SUFIJO if coincide_sufijo else 0.0) + bonus_tokens
            candidatos.append((score, ratio, coincide_sufijo, supervisor))

        candidatos.sort(key=lambda c: (c[0], c[1]), reverse=True)

        relevantes = [
            c for c in candidatos
            if c[1] >= _UMBRAL_SIMILITUD or c[2]
        ]
        top5 = relevantes[:5]

        if not top5:
            return ResultadoMatchSupervisor(
                nombre_excel=nombre_excel,
                tipo="no_reconocido",
                permite_crear_nuevo=True,
                nombre_sugerido_nuevo=nombre_excel.strip(),
            )

        sugerencias = [
            SugerenciaSupervisor(
                supervisor=supervisor,
                similitud=round(ratio, 3),
                coincide_sufijo=coincide_sufijo,
            )
            for _score, ratio, coincide_sufijo, supervisor in top5
        ]

        return ResultadoMatchSupervisor(
            nombre_excel=nombre_excel,
            tipo="sugerencias",
            sugerencias=sugerencias,
            permite_crear_nuevo=True,
            nombre_sugerido_nuevo=nombre_excel.strip(),
        )

    # ---------------------------------------------------------------------------
    # Inferencia de supervisor faltante
    # ---------------------------------------------------------------------------

    def inferir_supervisor_faltante(
        pasadas_o_supervisor: Any,
        supervisor_anterior: str | None = None,
        supervisor_siguiente: str | None = None,
    ) -> Any:
        """Infiere el supervisor faltante en una pasada individual o en una
        lista/secuencia de pasadas.

        Formas de uso:

        1. **Lista de pasadas** (PasadaCruda, PasadaNormalizada, dicts, o
           cualquier objeto con atributo/clave ``supervisor``):

           ``inferir_supervisor_faltante(pasadas)``

           Recorre la lista en dos pasadas:

           - *Forward pass*: propaga hacia adelante el último supervisor
             no vacío observado, rellenando los huecos intermedios.
           - *Backward pass*: si las primeras pasadas de la lista estaban
             vacías (antes de encontrar el primer supervisor), las rellena
             con el primer supervisor válido encontrado.

           Devuelve la misma lista (mutada in-place).

        2. **Valor puntual** (str o None):

           ``inferir_supervisor_faltante(sup_actual, supervisor_anterior, supervisor_siguiente)``

           - Si ``sup_actual`` no está vacío, lo devuelve (strip).
           - Si está vacío, devuelve ``supervisor_anterior`` si existe, o
             ``supervisor_siguiente`` en su defecto.
           - Si todo es None/vacío, devuelve None.
        """
        # --- Caso 1: lista/tupla de pasadas ---
        if isinstance(pasadas_o_supervisor, (list, tuple)):
            pasadas = list(pasadas_o_supervisor)
            if not pasadas:
                return pasadas

            def _get_sup(item: Any) -> str | None:
                if isinstance(item, dict):
                    return item.get("supervisor")
                return getattr(item, "supervisor", None)

            def _set_sup(item: Any, val: str) -> None:
                if isinstance(item, dict):
                    item["supervisor"] = val
                elif hasattr(item, "supervisor"):
                    try:
                        setattr(item, "supervisor", val)
                    except AttributeError:
                        pass  # frozen dataclass u objeto inmutable

            def _es_vacio(val: Any) -> bool:
                return val is None or str(val).strip() == ""

            # Forward pass: propagar último supervisor conocido
            ultimo_sup: str | None = None
            for p in pasadas:
                sup = _get_sup(p)
                if not _es_vacio(sup):
                    ultimo_sup = sup
                elif ultimo_sup is not None:
                    _set_sup(p, ultimo_sup)

            # Backward pass: rellenar pasadas iniciales huérfanas
            primer_sup: str | None = None
            for p in pasadas:
                sup = _get_sup(p)
                if not _es_vacio(sup):
                    primer_sup = sup
                    break

            if primer_sup is not None:
                for p in pasadas:
                    sup = _get_sup(p)
                    if _es_vacio(sup):
                        _set_sup(p, primer_sup)
                    else:
                        break  # ya llegamos al primer supervisor real

            return pasadas

        # --- Caso 2: valor puntual ---
        supervisor_actual = pasadas_o_supervisor
        if supervisor_actual is not None and str(supervisor_actual).strip() != "":
            return str(supervisor_actual).strip()

        if supervisor_anterior is not None and str(supervisor_anterior).strip() != "":
            return str(supervisor_anterior).strip()

        if supervisor_siguiente is not None and str(supervisor_siguiente).strip() != "":
            return str(supervisor_siguiente).strip()

        return None