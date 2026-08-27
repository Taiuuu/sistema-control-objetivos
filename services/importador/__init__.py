"""
Importador Universal de Control de Recorridos.

Punto de entrada público del módulo. El resto de la aplicación solo
debería depender de estas dos funciones, no de los submódulos internos
(parser, normalizador, matcher, duplicados, validador, reporte,
importacion), para poder reorganizar la implementación interna sin
romper al resto del sistema.

Uso típico:

    from importador_universal import analizar_excel, confirmar_importacion

    resultado = analizar_excel(path, anio=2026, conexion_bd=db)
    # ... el usuario revisa y resuelve problemas en la UI ...
    resumen = confirmar_importacion(resultado, resoluciones, usuario, conexion_bd)
"""

from . import reporte
from .modelos import (
    PasadaCruda,
    PasadaNormalizada,
    Problema,
    ResultadoAnalisis,
)

__all__ = [
    "analizar_excel",
    "confirmar_importacion",
    "PasadaCruda",
    "PasadaNormalizada",
    "Problema",
    "ResultadoAnalisis",
]


def analizar_excel(path, anio, conexion_bd, forzar_sobrescritura: bool = False) -> ResultadoAnalisis:
    """
    Lee y analiza un Excel de control de recorridos sin escribir nada
    en la base de datos. Orquesta parser -> normalizador -> matcher ->
    duplicados -> validador (se implementa completo en la Fase 10).

    Parámetros:
        path: ruta al archivo .xlsx a analizar.
        anio: año a aplicar sobre las fechas de las hojas (el Excel no
              trae año, ver Fase 3).
        conexion_bd: conexión/sesión para consultar objetivos,
              supervisores y pasadas existentes.
        forzar_sobrescritura: si True, permite que pasadas "ya
              existentes" con datos distintos se marquen para
              actualizar en vez de omitirse (ver Fase 8).

    Devuelve:
        ResultadoAnalisis con las pasadas clasificadas y la lista de
        problemas detectados, listo para mostrar en la pantalla de
        análisis (Fase 11).
    """
    return reporte.analizar_excel(
        path, anio, conexion_bd, forzar_sobrescritura=forzar_sobrescritura
    )


def confirmar_importacion(analisis: ResultadoAnalisis, resoluciones, usuario) -> dict:
    """
    Toma un ResultadoAnalisis ya revisado y con todos sus problemas
    bloqueantes resueltos, y ejecuta la importación real en una única
    transacción (se implementa completo en la Fase 13).

    Parámetros:
        analisis: el ResultadoAnalisis devuelto por analizar_excel().
        resoluciones: las decisiones del usuario tomadas en la
              pantalla de revisión (correcciones de hora, matching de
              objetivos/supervisores, decisiones sobre advertencias).
        usuario: usuario autenticado que confirma la importación (para
              auditoría y control de permisos).

    Devuelve:
        Un resumen de la importación (pasadas importadas, omitidas,
        correcciones aplicadas).
    """
    pass