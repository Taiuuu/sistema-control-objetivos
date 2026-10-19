"""Modelos inmutables que comparten los exportadores de informes."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Mapping


@dataclass(frozen=True)
class ColumnaReporte:
    """Describe una columna disponible y su presentación en ambos formatos."""

    id: str
    etiqueta: str
    tipo_dato: str
    formato: str | None
    ancho_sugerido: float
    alineacion: str = "izquierda"


@dataclass(frozen=True)
class MetadatosReporte:
    """Identifica el informe y conserva el contexto usado al generarlo."""

    titulo: str
    tipo_informe: str
    periodo: str
    filtros_aplicados: Mapping[str, Any]
    criterio_conteo_turnos: str
    generado_en: datetime
    usuario: str
    version_aplicacion: str


@dataclass(frozen=True)
class ReporteDatos:
    """Contiene las filas, el catálogo de columnas y los totales ya calculados."""

    metadatos: MetadatosReporte
    columnas: tuple[ColumnaReporte, ...]
    filas: tuple[Mapping[str, Any], ...]
    totales: Mapping[str, Any] = field(default_factory=dict)
    columnas_detalle: tuple[ColumnaReporte, ...] = ()
    filas_detalle: tuple[Mapping[str, Any], ...] = ()
    totales_incluidos: bool = True
    notas: tuple[Mapping[str, Any], ...] = ()
    subtotales: tuple[Mapping[str, Any], ...] = ()

    def __post_init__(self) -> None:
        ids = [columna.id for columna in self.columnas]
        if len(ids) != len(set(ids)):
            raise ValueError("El catálogo del informe contiene IDs de columna repetidos")
        ids_detalle = [columna.id for columna in self.columnas_detalle]
        if len(ids_detalle) != len(set(ids_detalle)):
            raise ValueError("El catálogo del detalle contiene IDs repetidos")
        for fila in self.filas:
            faltantes = set(ids) - fila.keys()
            if faltantes:
                raise ValueError(
                    "Faltan valores para las columnas del informe: "
                    + ", ".join(sorted(faltantes))
                )
        for fila in self.filas_detalle:
            faltantes = set(ids_detalle) - fila.keys()
            if faltantes:
                raise ValueError(
                    "Faltan valores para las columnas del detalle: "
                    + ", ".join(sorted(faltantes))
                )
