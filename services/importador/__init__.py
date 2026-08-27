from . import reporte
from .importacion import confirmar_importacion_completa
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


def analizar_excel(
    path,
    anio,
    conexion_bd,
    forzar_sobrescritura: bool = False,
) -> ResultadoAnalisis:

    return reporte.analizar_excel(
        path,
        anio,
        conexion_bd,
        forzar_sobrescritura=forzar_sobrescritura,
    )


def confirmar_importacion(
    analisis: ResultadoAnalisis,
    resoluciones,
    usuario,
    conexion_bd,
) -> dict:
    """
    Ejecuta la importación real.

    Fase 13:
        - validación final
        - transacción
        - persistencia

    Fase 14:
        - auditoría

    Fase 15/16:
        - notificación
    """

    return confirmar_importacion_completa(
        analisis=analisis,
        resoluciones=resoluciones,
        usuario=usuario,
        conexion_bd=conexion_bd,
    )