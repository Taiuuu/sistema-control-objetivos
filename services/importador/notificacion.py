"""
Fases 15 y 16 — Notificación al finalizar una importación.

Responsabilidades:
    - Construir el resumen final de una importación.
    - Generar el mensaje que verá el usuario.
    - Proporcionar una notificación dentro de la aplicación.
    - Mantener preparado el enlace al reporte detallado.

No modifica la base de datos.
No guarda el archivo Excel original.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass
class ResultadoNotificacion:
    """
    Información necesaria para notificar al usuario el resultado
    de una importación.
    """

    exitosa: bool

    pasadas_importadas: int = 0
    pasadas_omitidas: int = 0
    correcciones_aplicadas: int = 0

    mensaje: str = ""

    # Ruta o URL al reporte detallado.
    reporte_url: Optional[str] = None

    # Texto de error, si la importación fue cancelada/falló.
    error: Optional[str] = None


def construir_mensaje_importacion(
    *,
    exitosa: bool,
    pasadas_importadas: int,
    pasadas_omitidas: int,
    correcciones_aplicadas: int,
    reporte_url: Optional[str] = None,
    error: Optional[str] = None,
) -> str:
    """
    Construye el mensaje final que se muestra al usuario.
    """

    if not exitosa:
        mensaje = (
            "La importación no se completó.\n\n"
            f"Pasadas importadas: {pasadas_importadas}\n"
            f"Pasadas omitidas: {pasadas_omitidas}\n"
            f"Correcciones aplicadas: {correcciones_aplicadas}"
        )

        if error:
            mensaje += f"\n\nMotivo: {error}"

        return mensaje

    mensaje = (
        "Importación finalizada correctamente.\n\n"
        f"Pasadas importadas: {pasadas_importadas}\n"
        f"Pasadas omitidas: {pasadas_omitidas}\n"
        f"Correcciones aplicadas: {correcciones_aplicadas}"
    )

    if reporte_url:
        mensaje += "\n\nReporte detallado disponible."

    return mensaje


def crear_resultado_notificacion(
    resumen: dict,
    reporte_url: Optional[str] = None,
) -> ResultadoNotificacion:
    """
    Convierte el resumen devuelto por importacion.py en un objeto
    preparado para la UI.
    """

    exitosa = bool(resumen.get("exitosa", False))

    pasadas_importadas = int(
        resumen.get(
            "pasadas_importadas",
            resumen.get("importadas", 0),
        )
    )

    pasadas_omitidas = int(
        resumen.get(
            "pasadas_omitidas",
            resumen.get("omitidas", 0),
        )
    )

    correcciones_aplicadas = int(
        resumen.get(
            "correcciones_aplicadas",
            resumen.get("correcciones", 0),
        )
    )

    error = resumen.get("error")

    mensaje = construir_mensaje_importacion(
        exitosa=exitosa,
        pasadas_importadas=pasadas_importadas,
        pasadas_omitidas=pasadas_omitidas,
        correcciones_aplicadas=correcciones_aplicadas,
        reporte_url=reporte_url,
        error=error,
    )

    return ResultadoNotificacion(
        exitosa=exitosa,
        pasadas_importadas=pasadas_importadas,
        pasadas_omitidas=pasadas_omitidas,
        correcciones_aplicadas=correcciones_aplicadas,
        mensaje=mensaje,
        reporte_url=reporte_url,
        error=error,
    )


def notificar_importacion(
    resumen: dict,
    *,
    mostrar_mensaje,
    reporte_url: Optional[str] = None,
) -> ResultadoNotificacion:
    """
    Punto de entrada de Fase 15/16.

    `mostrar_mensaje` es una función proporcionada por la UI.

    Ejemplo:

        notificar_importacion(
            resumen,
            mostrar_mensaje=lambda titulo, texto, url: ...
        )

    Si existe un sistema externo de notificaciones, puede conectarse
    posteriormente sin modificar la lógica de importación.
    """

    resultado = crear_resultado_notificacion(
        resumen,
        reporte_url=reporte_url,
    )

    mostrar_mensaje(
        resultado,
    )

    return resultado