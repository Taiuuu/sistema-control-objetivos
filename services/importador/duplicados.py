"""
Detección de duplicados dentro del propio Excel y de pasadas que ya
existen en la base de datos (idempotencia de la importación).

Fase 8 del pipeline de importación.
"""

from __future__ import annotations

from itertools import groupby
import logging

try:
    from .modelos import PasadaNormalizada
    from .matcher import normalizar_nombre
except ImportError:
    from modelos import PasadaNormalizada
    from matcher import normalizar_nombre


logger = logging.getLogger(__name__)


# =============================================================================
# CLAVES DE COMPARACIÓN
# =============================================================================

def _clave_pasada(p: PasadaNormalizada) -> tuple:
    """
    Clave natural de una pasada:
    fecha_operativa + hora + objetivo + supervisor.

    El turno no forma parte de la clave: una hora concreta de un objetivo
    y supervisor no debe duplicarse por una discrepancia de turno.
    """
    objetivo = p.objetivo_id
    if objetivo is None:
        objetivo = (
            "nombre",
            normalizar_nombre(p.objetivo_nombre or ""),
        )
    else:
        objetivo = ("id", str(objetivo))

    return (
        p.fecha_operativa,
        objetivo,
        p.hora,
        _clave_supervisor(p),
    )


def _clave_pasada_sql(p: PasadaNormalizada) -> tuple:
    """
    Clave natural SQL; supervisor NULL se representa con -1.
    """
    return (
        p.fecha_operativa.isoformat(),
        p.objetivo_id,
        p.hora.strftime("%H:%M"),
        p.supervisor_id if p.supervisor_id is not None else -1,
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

    nombre = normalizar_nombre(p.supervisor_nombre or "")
    return ("nombre", nombre)


# =============================================================================
# DUPLICADOS INTERNOS DEL EXCEL
# =============================================================================

def detectar_duplicados_internos(
    pasadas: list[PasadaNormalizada],
) -> tuple[list[PasadaNormalizada], list[PasadaNormalizada]]:
    """
    Detecta duplicados dentro del mismo archivo importado.

    Agrupa por la clave natural, incluyendo supervisor. Si dos registros
    de la misma clave aparecen en el Excel, se conserva la primera fila.

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
        key=lambda p: (_clave_pasada(p), p.fila_excel),
    )

    for _, grupo_iter in groupby(
        ordenadas,
        key=_clave_pasada,
    ):
        grupo = list(grupo_iter)

        if len(grupo) == 1:
            finales.append(grupo[0])
            continue

        grupo_ordenado = sorted(grupo, key=lambda p: p.fila_excel)
        finales.append(grupo_ordenado[0])
        descartadas.extend(grupo_ordenado[1:])
        for descartada in grupo_ordenado[1:]:
            logger.warning(
                "Pasada descartada por duplicado: hoja=%s fila=%d bloque=%d objetivo=%r motivo=misma fecha operativa, hora, objetivo y supervisor",
                descartada.hoja,
                descartada.fila_excel,
                descartada.bloque_tabla,
                descartada.objetivo_nombre,
            )

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

    Clave natural:
        fecha_operativa + objetivo_id + hora + supervisor_id

    - Si la pasada no existe:
        accion = "nueva"

    - Si existe con la clave natural:
        accion = "omitir"

    - Si existe con otro supervisor, solo se sobrescribe cuando se pidió
      explícitamente forzar_sobrescritura.

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

    claves_sql = {_clave_pasada_sql(p) for p in pasadas_consultables}

    # SQLite soporta comparaciones por tuplas:
    #
    # (fecha_operativa, objetivo_id, hora, supervisor_id) IN ((?, ?, ?, ?), ...)
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
            objetivo_id,
            substr(hora, 1, 5),
            COALESCE(supervisor_id, -1)
        FROM pasadas
        WHERE (
            fecha_operativa,
            objetivo_id,
            substr(hora, 1, 5),
            COALESCE(supervisor_id, -1)
        ) IN ({placeholders})
        """,
        parametros,
    )

    filas_bd = cursor.fetchall()

    # Mapa:
    #
    claves_naturales_bd = {tuple(fila) for fila in filas_bd}
    claves_con_fecha_hora_objetivo = set()
    if forzar_sobrescritura:
        cursor.execute(
            f"""
            SELECT DISTINCT fecha_operativa, objetivo_id, substr(hora, 1, 5)
            FROM pasadas
            WHERE (fecha_operativa, objetivo_id, substr(hora, 1, 5))
            IN ({", ".join("(?, ?, ?)" for _ in claves_sql)})
            """,
            [
                valor
                for fecha, objetivo_id, hora, _ in claves_sql
                for valor in (fecha, objetivo_id, hora)
            ],
        )
        claves_con_fecha_hora_objetivo = {
            tuple(fila) for fila in cursor.fetchall()
        }

    # -------------------------------------------------------------------------
    # Clasificar cada pasada.
    # -------------------------------------------------------------------------

    for pasada in pasadas_consultables:
        clave = _clave_pasada_sql(pasada)

        # -----------------------------------------------------
        # No existe todavía.
        # -----------------------------------------------------
        if clave not in claves_naturales_bd:
            clave_sin_supervisor = clave[:3]
            if forzar_sobrescritura and clave_sin_supervisor in claves_con_fecha_hora_objetivo:
                pasada.accion = "actualizar"
                existentes.append(pasada)
            else:
                pasada.accion = "nueva"
                nuevas.append(pasada)
            continue

        # -----------------------------------------------------
        # Ya existe.
        # -----------------------------------------------------

        pasada.accion = "omitir"

        existentes.append(pasada)

    return nuevas, existentes