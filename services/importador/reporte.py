"""
Orquestación del análisis completo (resumen numérico) y generación del
reporte detallado descargable.

Fase 10:
    - análisis completo del Excel
    - resumen numérico
    - pipeline read-only

Fase 17:
    - reporte detallado descargable en XLSX
"""

from __future__ import annotations

from io import BytesIO
from typing import Any

from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill
from openpyxl.utils import get_column_letter

from .modelos import ResultadoAnalisis
from .parser import leer_excel
from .normalizador import normalizar_pasadas
from .matcher import matchear_objetivo, matchear_supervisor
from .duplicados import (
    detectar_duplicados_internos,
    detectar_pasadas_existentes,
)
from .validador import validar


# ============================================================================
# Helpers internos
# ============================================================================


def _obtener_catalogos(conexion_bd):
    """
    Lee los catálogos de objetivos y supervisores.

    IMPORTANTE:
        Esta función solamente ejecuta SELECT.
        No hace INSERT, UPDATE, DELETE ni COMMIT.
    """
    cursor = conexion_bd.cursor()

    cursor.execute(
        """
        SELECT id, nombre
        FROM objetivos
        WHERE COALESCE(activo, 1) = 1
        ORDER BY nombre
        """
    )
    objetivos = cursor.fetchall()

    cursor.execute(
        """
        SELECT id, nombre
        FROM supervisores
        WHERE fecha_baja IS NULL OR fecha_baja = ''
        ORDER BY nombre
        """
    )
    supervisores = cursor.fetchall()

    return objetivos, supervisores


def _desempaquetar_lectura(resultado):
    """
    Normaliza el resultado de leer_excel().

    Se soportan estas formas:

        (hojas, pasadas)
        (hojas, pasadas, problemas)

    o un objeto/dict con atributos equivalentes.
    """
    if isinstance(resultado, tuple):
        if len(resultado) == 3:
            return resultado[0], resultado[1], list(resultado[2] or [])

        if len(resultado) == 2:
            return resultado[0], resultado[1], []

        raise ValueError(
            "leer_excel() devolvió una tupla con cantidad de elementos "
            f"inesperada: {len(resultado)}"
        )

    if isinstance(resultado, dict):
        hojas = resultado.get(
            "hojas",
            resultado.get("hojas_encontradas", []),
        )
        pasadas = resultado.get(
            "pasadas",
            resultado.get("pasadas_detectadas", []),
        )
        problemas = resultado.get("problemas", [])

        return hojas, pasadas, list(problemas or [])

    hojas = getattr(
        resultado,
        "hojas",
        getattr(resultado, "hojas_encontradas", []),
    )
    pasadas = getattr(
        resultado,
        "pasadas",
        getattr(resultado, "pasadas_detectadas", []),
    )
    problemas = getattr(resultado, "problemas", [])

    return hojas, pasadas, list(problemas or [])


def _desempaquetar_normalizacion(resultado):
    """
    Normaliza el resultado de normalizar_pasadas().

    Se soportan:

        pasadas
        (pasadas, problemas)

    o un objeto/dict equivalente.
    """
    if isinstance(resultado, tuple):
        if len(resultado) == 2:
            return list(resultado[0] or []), list(resultado[1] or [])

        if len(resultado) == 1:
            return list(resultado[0] or []), []

        raise ValueError(
            "normalizar_pasadas() devolvió una tupla inesperada"
        )

    if isinstance(resultado, dict):
        pasadas = resultado.get(
            "pasadas_normalizadas",
            resultado.get("pasadas", []),
        )
        problemas = resultado.get("problemas", [])
        return list(pasadas or []), list(problemas or [])

    if hasattr(resultado, "pasadas_normalizadas"):
        return (
            list(resultado.pasadas_normalizadas or []),
            list(getattr(resultado, "problemas", []) or []),
        )

    return list(resultado or []), []


def _resolver_matching(
    pasadas,
    objetivos_bd,
    supervisores_bd,
):
    """
    Ejecuta Fase 6-7 sobre cada pasada.

    Solamente un match de tipo "exacto" asigna el ID.

    Las sugerencias y los no reconocidos quedan con ID=None para que
    Fase 9 los pueda clasificar como pendientes/no reconocidos.

    Esto respeta el contrato del matcher: la decisión sobre una sugerencia
    no la toma automáticamente el pipeline. 
    """
    for pasada in pasadas:
        nombre_objetivo = (pasada.objetivo_nombre or "").strip()

        if nombre_objetivo:
            resultado_objetivo = matchear_objetivo(
                nombre_objetivo,
                objetivos_bd,
            )

            if resultado_objetivo.tipo == "exacto":
                pasada.objetivo_id = (
                    resultado_objetivo.objetivo_exacto.id
                )
            else:
                pasada.objetivo_id = None

        nombre_supervisor = (
            (pasada.supervisor_nombre or "").strip()
            if pasada.supervisor_nombre is not None
            else ""
        )

        if nombre_supervisor:
            resultado_supervisor = matchear_supervisor(
                nombre_supervisor,
                supervisores_bd,
            )

            if resultado_supervisor.tipo == "exacto":
                pasada.supervisor_id = (
                    resultado_supervisor.supervisor_exacto.id
                )
            else:
                pasada.supervisor_id = None

    return pasadas


def _crear_resultado(
    *,
    hojas,
    pasadas,
    pasadas_nuevas,
    pasadas_existentes,
    duplicados,
    problemas,
    forzar_sobrescritura,
):
    """
    Construye ResultadoAnalisis.

    Se intenta primero la construcción normal de dataclass.
    El fallback permite trabajar con una versión de ResultadoAnalisis
    que tenga campos inicializados por defecto.
    """
    datos = {
        "hojas": list(hojas),
        "pasadas": list(pasadas),
        "pasadas_nuevas": list(pasadas_nuevas),
        "pasadas_ya_existentes": list(pasadas_existentes),
        "duplicados_descartados": list(duplicados),
        "problemas": list(problemas),
        "forzar_sobrescritura": forzar_sobrescritura,
    }

    try:
        return ResultadoAnalisis(**datos)
    except TypeError:
        resultado = ResultadoAnalisis()

        for nombre, valor in datos.items():
            if hasattr(resultado, nombre):
                try:
                    setattr(resultado, nombre, valor)
                except AttributeError:
                    pass

        return resultado


def _es_error_critico(problema) -> bool:
    return getattr(problema, "tipo", None) == "error_critico"


def _es_advertencia(problema) -> bool:
    return getattr(problema, "tipo", None) == "advertencia"


def _descripcion(problema) -> str:
    return str(getattr(problema, "descripcion", "") or "")


def _es_objetivo_no_reconocido(problema) -> bool:
    texto = _descripcion(problema).lower()

    return (
        "objetivo" in texto
        and "no reconocido" in texto
    )


def _es_supervisor_no_reconocido(problema) -> bool:
    texto = _descripcion(problema).lower()

    return (
        "supervisor" in texto
        and "no reconocido" in texto
    )


# ============================================================================
# Fase 10 — Análisis completo
# ============================================================================


def analizar_excel_completo(
    path,
    anio: int,
    conexion_bd,
    forzar_sobrescritura: bool = False,
) -> ResultadoAnalisis:
    """
    Orquesta el pipeline completo:

        Fase 2-3 -> lectura
        Fase 4-5 -> normalización
        Fase 6-7 -> matching
        Fase 8   -> duplicados + existencia
        Fase 9   -> validación

    La función es estrictamente de análisis.

    NO:
        - crea objetivos
        - crea supervisores
        - inserta pasadas
        - actualiza pasadas
        - elimina registros
        - hace commit

    La única operación sobre la BD es lectura de catálogos y existencia
    de pasadas.
    """

    # ------------------------------------------------------------------
    # FASE 2-3 — Lectura
    # ------------------------------------------------------------------

    resultado_lectura = leer_excel(
        path,
        anio,
    )

    hojas, pasadas_crudas, problemas_lectura = (
        _desempaquetar_lectura(resultado_lectura)
    )

    problemas = list(problemas_lectura)

    # ------------------------------------------------------------------
    # FASE 4-5 — Normalización
    # ------------------------------------------------------------------

    resultado_normalizacion = normalizar_pasadas(
        pasadas_crudas,
        anio,
    )

    pasadas_normalizadas, problemas_normalizacion = (
        _desempaquetar_normalizacion(resultado_normalizacion)
    )

    problemas.extend(problemas_normalizacion)

    # ------------------------------------------------------------------
    # FASE 6-7 — Matching
    # ------------------------------------------------------------------

    objetivos_bd, supervisores_bd = _obtener_catalogos(
        conexion_bd
    )

    pasadas_normalizadas = _resolver_matching(
        pasadas_normalizadas,
        objetivos_bd,
        supervisores_bd,
    )

    # ------------------------------------------------------------------
    # FASE 8 — Duplicados internos
    # ------------------------------------------------------------------

    pasadas_sin_duplicados, duplicados_descartados = (
        detectar_duplicados_internos(
            pasadas_normalizadas
        )
    )

    # ------------------------------------------------------------------
    # FASE 8 — Existencia en BD
    # ------------------------------------------------------------------

    pasadas_nuevas, pasadas_existentes = (
        detectar_pasadas_existentes(
            pasadas_sin_duplicados,
            conexion_bd,
            forzar_sobrescritura=forzar_sobrescritura,
        )
    )

    # ------------------------------------------------------------------
    # FASE 9 — Validación
    # ------------------------------------------------------------------

    contexto = {
        "anio": anio,
        "hojas": hojas,
        "objetivos_bd": objetivos_bd,
        "supervisores_bd": supervisores_bd,
        "pasadas": pasadas_sin_duplicados,
        "pasadas_nuevas": pasadas_nuevas,
        "pasadas_existentes": pasadas_existentes,
        "duplicados_descartados": duplicados_descartados,
        "conexion_bd": conexion_bd,
        "forzar_sobrescritura": forzar_sobrescritura,
    }

    problemas_validacion = validar(
        pasadas_sin_duplicados,
        contexto,
    )

    problemas.extend(problemas_validacion)

    # ------------------------------------------------------------------
    # Resultado final
    # ------------------------------------------------------------------

    return _crear_resultado(
        hojas=hojas,
        pasadas=pasadas_normalizadas,
        pasadas_nuevas=pasadas_nuevas,
        pasadas_existentes=pasadas_existentes,
        duplicados=duplicados_descartados,
        problemas=problemas,
        forzar_sobrescritura=forzar_sobrescritura,
    )


def analizar_excel(
    path,
    anio: int,
    conexion_bd,
    forzar_sobrescritura: bool = False,
) -> ResultadoAnalisis:
    """
    API pública del análisis.

    __init__.py puede exportar esta función directamente.
    """
    return analizar_excel_completo(
        path,
        anio,
        conexion_bd,
        forzar_sobrescritura=forzar_sobrescritura,
    )


# ============================================================================
# Fase 17 — Reporte detallado
# ============================================================================


def _excel_value(valor: Any):
    """
    Convierte valores del modelo a valores aceptables por openpyxl.
    """
    if valor is None:
        return ""

    if isinstance(valor, (str, int, float, bool)):
        return valor

    return str(valor)


def _escribir_encabezado(ws, fila, columnas):
    for indice, nombre in enumerate(columnas, start=1):
        celda = ws.cell(fila, indice, nombre)
        celda.font = Font(bold=True)


def _ajustar_columnas(ws):
    """
    Ajusta anchos de columnas con un máximo razonable.
    """
    for columna in ws.columns:
        if not columna:
            continue

        indice = columna[0].column
        maximo = 0

        for celda in columna:
            if celda.value is None:
                continue

            largo = len(str(celda.value))
            maximo = max(maximo, largo)

        ws.column_dimensions[
            get_column_letter(indice)
        ].width = min(max(maximo + 2, 10), 60)


def _escribir_problemas(wb, problemas):
    ws = wb.create_sheet("Problemas")

    columnas = [
        "Tipo",
        "Descripción",
        "Hoja",
        "Fila Excel",
        "Objetivo",
        "Valor problemático",
    ]

    _escribir_encabezado(ws, 1, columnas)

    for fila, problema in enumerate(problemas, start=2):
        valores = [
            getattr(problema, "tipo", None),
            getattr(problema, "descripcion", None),
            getattr(problema, "hoja", None),
            getattr(problema, "fila_excel", None),
            getattr(problema, "objetivo", None),
            getattr(problema, "valor_problema", None),
        ]

        for columna, valor in enumerate(valores, start=1):
            ws.cell(
                fila,
                columna,
                _excel_value(valor),
            )

    ws.freeze_panes = "A2"
    ws.auto_filter.ref = ws.dimensions

    _ajustar_columnas(ws)


def _escribir_pasadas(wb, nombre_hoja, pasadas):
    ws = wb.create_sheet(nombre_hoja)

    columnas = [
        "Hoja",
        "Fila Excel",
        "Bloque",
        "Fecha operativa",
        "Fecha calendario",
        "Turno",
        "Hora",
        "Móvil",
        "Objetivo",
        "Objetivo ID",
        "Supervisor",
        "Supervisor ID",
        "Acción",
    ]

    _escribir_encabezado(ws, 1, columnas)

    for fila, pasada in enumerate(pasadas, start=2):
        valores = [
            getattr(pasada, "hoja", None),
            getattr(pasada, "fila_excel", None),
            getattr(pasada, "bloque_tabla", None),
            getattr(pasada, "fecha_operativa", None),
            getattr(pasada, "fecha_calendario", None),
            getattr(pasada, "turno", None),
            getattr(pasada, "hora", None),
            getattr(pasada, "movil", None),
            getattr(pasada, "objetivo_nombre", None),
            getattr(pasada, "objetivo_id", None),
            getattr(pasada, "supervisor_nombre", None),
            getattr(pasada, "supervisor_id", None),
            getattr(pasada, "accion", None),
        ]

        for columna, valor in enumerate(valores, start=1):
            ws.cell(
                fila,
                columna,
                _excel_value(valor),
            )

    ws.freeze_panes = "A2"
    ws.auto_filter.ref = ws.dimensions

    _ajustar_columnas(ws)


def _escribir_resumen(wb, resultado):
    ws = wb.active
    ws.title = "Resumen"

    hojas = getattr(resultado, "hojas", [])
    pasadas = getattr(resultado, "pasadas", [])
    nuevas = getattr(resultado, "pasadas_nuevas", [])
    existentes = getattr(resultado, "pasadas_ya_existentes", [])
    duplicados = getattr(resultado, "duplicados_descartados", [])
    problemas = getattr(resultado, "problemas", [])

    errores_criticos = sum(
        1 for problema in problemas
        if _es_error_critico(problema)
    )

    advertencias = sum(
        1 for problema in problemas
        if _es_advertencia(problema)
    )

    objetivos_no_reconocidos = sum(
        1 for problema in problemas
        if _es_objetivo_no_reconocido(problema)
    )

    supervisores_no_reconocidos = sum(
        1 for problema in problemas
        if _es_supervisor_no_reconocido(problema)
    )

    resumen = [
        ("ANÁLISIS DEL ARCHIVO", ""),
        ("Hojas encontradas", len(hojas)),
        ("Pasadas detectadas", len(pasadas)),
        ("Pasadas nuevas", len(nuevas)),
        ("Pasadas ya existentes", len(existentes)),
        ("Duplicados descartados", len(duplicados)),
        ("Objetivos no reconocidos", objetivos_no_reconocidos),
        ("Supervisores no reconocidos", supervisores_no_reconocidos),
        ("Errores críticos", errores_criticos),
        ("Advertencias", advertencias),
    ]

    for fila, (nombre, valor) in enumerate(resumen, start=1):
        ws.cell(fila, 1, nombre)
        ws.cell(fila, 2, valor)

    ws["A1"].font = Font(
        bold=True,
        size=14,
    )

    ws["A1"].fill = PatternFill(
        fill_type="solid",
        fgColor="D9EAF7",
    )

    ws.freeze_panes = "A2"

    _ajustar_columnas(ws)


def generar_reporte_detallado(
    resultado: ResultadoAnalisis,
) -> bytes:
    """
    Genera el reporte XLSX descargable del análisis.

    Contiene:

        Resumen
        Problemas
        Pasadas nuevas
        Ya existentes
        Duplicados

    No realiza ninguna consulta ni escritura en la BD.

    Devuelve:
        bytes del archivo XLSX.
    """
    wb = Workbook()

    problemas = list(
        getattr(resultado, "problemas", []) or []
    )

    pasadas_nuevas = list(
        getattr(resultado, "pasadas_nuevas", []) or []
    )

    pasadas_existentes = list(
        getattr(resultado, "pasadas_ya_existentes", []) or []
    )

    duplicados = list(
        getattr(resultado, "duplicados_descartados", []) or []
    )

    _escribir_resumen(
        wb,
        resultado,
    )

    _escribir_problemas(
        wb,
        problemas,
    )

    _escribir_pasadas(
        wb,
        "Pasadas nuevas",
        pasadas_nuevas,
    )

    _escribir_pasadas(
        wb,
        "Ya existentes",
        pasadas_existentes,
    )

    _escribir_pasadas(
        wb,
        "Duplicados",
        duplicados,
    )

    buffer = BytesIO()
    wb.save(buffer)

    return buffer.getvalue()