"""
Detección de duplicados dentro del propio Excel y de pasadas que ya
existen en la base de datos (idempotencia de la importación).

Fase 8 del pipeline de importación.
"""

from __future__ import annotations

from itertools import groupby
from typing import Any

try:
    from .modelos import PasadaNormalizada
except ImportError:
    from modelos import PasadaNormalizada


# =============================================================================
# CLAVES DE COMPARACIÓN
# =============================================================================

def _clave_pasada(p: PasadaNormalizada) -> tuple:
    """
    Clave principal de una pasada dentro del Excel.

    Una pasada se identifica por:
        fecha_operativa + turno + objetivo_id + hora

    El supervisor NO forma parte de la identidad principal porque puede
    cambiar posteriormente y una pasada existente puede requerir actualización.
    """
    return (
        p.fecha_operativa,
        p.turno,
        p.objetivo_id,
        p.hora,
    )


def _clave_pasada_sql(p: PasadaNormalizada) -> tuple:
    """
    Misma clave que _clave_pasada(), pero convertida a tipos compatibles
    con sqlite3.

    SQLite guarda fecha_operativa y hora como TEXT en este proyecto.
    """
    return (
        p.fecha_operativa.isoformat(),
        p.turno,
        p.objetivo_id,
        p.hora.isoformat(),
    )


def _clave_supervisor(p: PasadaNormalizada) -> tuple:
    """
    Devuelve una clave estable para comparar supervisores.

    Prioridad:
    1. supervisor_id si ya fue resuelto por matching.
    2. nombre normalizado como fallback.

    El fallback permite detectar duplicados internos antes de que todos
    los IDs estén completamente resueltos.
    """
    if p.supervisor_id is not None:
        return ("id", p.supervisor_id)

    nombre = (p.supervisor_nombre or "").strip().upper()
    return ("nombre", nombre)


# =============================================================================
# DUPLICADOS INTERNOS DEL EXCEL
# =============================================================================

def detectar_duplicados_internos(
    pasadas: list[PasadaNormalizada],
) -> tuple[list[PasadaNormalizada], list[PasadaNormalizada]]:
    """
    Detecta duplicados dentro del mismo archivo importado.

    Agrupa por:
        fecha_operativa + turno + objetivo_id + hora

    Dentro de cada grupo:

    - Si todas las pasadas tienen el mismo supervisor:
      se consideran duplicados reales y se conserva una sola.

    - Si existen supervisores diferentes:
      se conservan todas, porque pueden representar móviles/supervisores
      distintos registrados a la misma hora.

    La pasada conservada en caso de duplicado es siempre la que tenga
    menor fila_excel, preservando la primera aparición del Excel.

    Devuelve:
        (
            pasadas_finales,
            descartadas_por_duplicado
        )
    """

    if not pasadas:
        return [], []

    finales: list[PasadaNormalizada] = []
    descartadas: list[PasadaNormalizada] = []

    # Ordenamos por clave y luego por fila para que la primera aparición
    # del Excel sea siempre la que se conserve.
    ordenadas = sorted(
        pasadas,
        key=lambda p: (
            _clave_pasada(p),
            p.fila_excel,
        ),
    )

    for _clave, grupo_iter in groupby(
        ordenadas,
        key=_clave_pasada,
    ):
        grupo = list(grupo_iter)

        # No hay posibilidad de duplicado.
        if len(grupo) == 1:
            finales.append(grupo[0])
            continue

        supervisores = {
            _clave_supervisor(p)
            for p in grupo
        }

        # Mismo supervisor repetido:
        # conservar primera fila y descartar las demás.
        if len(supervisores) == 1:
            grupo_ordenado = sorted(
                grupo,
                key=lambda p: p.fila_excel,
            )

            finales.append(grupo_ordenado[0])
            descartadas.extend(grupo_ordenado[1:])
            continue

        # Supervisores distintos:
        # no se consideran duplicados.
        finales.extend(grupo)

    return finales, descartadas


# =============================================================================
# DETECCIÓN DE PASADAS YA EXISTENTES EN LA BASE
# =============================================================================

def detectar_pasadas_existentes(
    pasadas: list[PasadaNormalizada],
    conexion_bd,
    forzar_sobrescritura: bool = False,
) -> tuple[list[PasadaNormalizada], list[PasadaNormalizada]]:
    """
    Detecta cuáles de las pasadas importadas ya existen en la base.

    Identidad de una pasada:
        fecha_operativa + turno + objetivo_id + hora

    El supervisor es un dato secundario:

    - Si la pasada no existe:
        accion = "nueva"

    - Si existe y el supervisor coincide:
        accion = "omitir"

    - Si existe y el supervisor difiere:
        accion = "actualizar" si forzar_sobrescritura=True
        accion = "omitir" en caso contrario

    Las pasadas sin objetivo_id NO se consultan contra la base.
    Se devuelven dentro de las nuevas para no perderlas, pero su
    accion queda en None.

    La validación posterior debe impedir que una pasada sin matching
    confirmado llegue a la persistencia final.

    Devuelve:
        (
            pasadas_nuevas,
            pasadas_ya_existentes
        )
    """

    if not pasadas:
        return [], []

    nuevas: list[PasadaNormalizada] = []
    existentes: list[PasadaNormalizada] = []

    # -------------------------------------------------------------------------
    # Separar registros que todavía no tienen objetivo resuelto.
    #
    # No es seguro consultar contra la BD usando objetivo_id=None porque
    # conceptualmente todavía no sabemos contra qué objetivo comparar.
    # -------------------------------------------------------------------------

    pasadas_consultables: list[PasadaNormalizada] = []

    for pasada in pasadas:
        if pasada.objetivo_id is None:
            pasada.accion = None
            nuevas.append(pasada)
        else:
            pasadas_consultables.append(pasada)

    if not pasadas_consultables:
        return nuevas, existentes

    # -------------------------------------------------------------------------
    # Construir claves únicas para evitar parámetros SQL duplicados.
    # -------------------------------------------------------------------------

    claves_sql = {
        _clave_pasada_sql(p)
        for p in pasadas_consultables
    }

    # SQLite soporta comparaciones por tuplas:
    #
    # (fecha_operativa, turno, objetivo_id, hora) IN ((?, ?, ?, ?), ...)
    #
    # Los valores se aplanan para pasarlos como parámetros.
    placeholders = ", ".join(
        "(?, ?, ?, ?)"
        for _ in claves_sql
    )

    parametros = [
        valor
        for clave in claves_sql
        for valor in clave
    ]

    cursor = conexion_bd.cursor()

    cursor.execute(
        f"""
        SELECT
            fecha_operativa,
            turno,
            objetivo_id,
            hora,
            supervisor_id
        FROM pasadas
        WHERE (
            fecha_operativa,
            turno,
            objetivo_id,
            hora
        ) IN ({placeholders})
        """,
        parametros,
    )

    filas_bd = cursor.fetchall()

    # Mapa:
    #
    # (fecha_operativa, turno, objetivo_id, hora)
    #       ->
    # supervisor_id existente
    #
    supervisor_bd_por_clave: dict[tuple, Any] = {
        (
            fecha_operativa,
            turno,
            objetivo_id,
            hora,
        ): supervisor_id
        for (
            fecha_operativa,
            turno,
            objetivo_id,
            hora,
            supervisor_id,
        ) in filas_bd
    }

    # -------------------------------------------------------------------------
    # Clasificar cada pasada.
    # -------------------------------------------------------------------------

    for pasada in pasadas_consultables:
        clave = _clave_pasada_sql(pasada)

        # -----------------------------------------------------
        # No existe todavía.
        # -----------------------------------------------------
        if clave not in supervisor_bd_por_clave:
            pasada.accion = "nueva"
            nuevas.append(pasada)
            continue

        # -----------------------------------------------------
        # Ya existe.
        # -----------------------------------------------------

        supervisor_id_bd = supervisor_bd_por_clave[clave]

        supervisor_difiere = (
            supervisor_id_bd != pasada.supervisor_id
        )

        if supervisor_difiere and forzar_sobrescritura:
            pasada.accion = "actualizar"
        else:
            pasada.accion = "omitir"

        existentes.append(pasada)

    return nuevas, existentes