# importador/resolucion.py
"""
Fase 12: estado de las resoluciones tomadas en la pantalla de revisión.

Este módulo NO toca la base de datos ni el Excel original. Junta las
decisiones del usuario (correcciones puntuales, advertencias
aceptadas/corregidas, matching de objetivos/supervisores) en un único
objeto `EstadoResolucion`, que Fase 13 (`confirmar_importacion`) recibe
como el parámetro `resoluciones`.

Cada decisión queda preparada para auditoría, con:
usuario, hoja, objetivo, valor_antes, valor_despues.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Literal

TipoResolucion = Literal["correccion", "aceptado", "match_existente", "crear_nuevo", "crear_alias"]


@dataclass
class RegistroAuditoria:
    """Un registro individual, listo para loguear en auditoría."""
    usuario: str
    hoja: str | None
    objetivo: str | None
    campo: str
    valor_antes: str
    valor_despues: str
    tipo: TipoResolucion
    timestamp: datetime = field(default_factory=datetime.now)


class EstadoResolucion:
    """Junta todas las resoluciones tomadas sobre un ResultadoAnalisis.

    Cada Problema se identifica por su posición (índice) dentro de
    `resultado.problemas`, ya que Problema no tiene id propio todavía
    (ver supuesto al final). Si eso cambia, actualizar `id_problema` acá.
    """

    def __init__(self, usuario: str):
        self.usuario = usuario
        self._resoluciones: dict[int, RegistroAuditoria] = {}

    def registrar_correccion(self, id_problema, hoja, objetivo, campo, valor_antes, valor_despues) -> None:
        """Errores críticos y advertencias 'corregir': valor puntual reemplazado."""
        self._resoluciones[id_problema] = RegistroAuditoria(
            usuario=self.usuario, hoja=hoja, objetivo=objetivo,
            campo=campo, valor_antes=valor_antes, valor_despues=valor_despues,
            tipo="correccion",
        )

    def registrar_aceptado(self, id_problema, hoja, objetivo, descripcion) -> None:
        """Advertencias 'dejar como está': sin cambiar ningún valor."""
        self._resoluciones[id_problema] = RegistroAuditoria(
            usuario=self.usuario, hoja=hoja, objetivo=objetivo,
            campo="(sin cambios)", valor_antes=descripcion, valor_despues=descripcion,
            tipo="aceptado",
        )

    def registrar_match(self, id_problema, hoja, objetivo, coincidencia_elegida) -> None:
        """Matching: el usuario eligió una sugerencia existente."""
        self._resoluciones[id_problema] = RegistroAuditoria(
            usuario=self.usuario, hoja=hoja, objetivo=objetivo,
            campo="matching", valor_antes=objetivo, valor_despues=coincidencia_elegida,
            tipo="match_existente",
        )

    def registrar_creacion(self, id_problema, hoja, objetivo, nombre_nuevo) -> None:
        """Matching: el usuario decidió crear un objetivo/supervisor nuevo."""
        self._resoluciones[id_problema] = RegistroAuditoria(
            usuario=self.usuario, hoja=hoja, objetivo=objetivo,
            campo="matching", valor_antes=objetivo, valor_despues=f"(nuevo) {nombre_nuevo}",
            tipo="crear_nuevo",
        )

    def registrar_alias(self, id_problema, hoja, objetivo, objetivo_existente) -> None:
        """Asocia el nombre del Excel como alias de un objetivo existente."""
        self._resoluciones[id_problema] = RegistroAuditoria(
            usuario=self.usuario, hoja=hoja, objetivo=objetivo,
            campo="alias", valor_antes=objetivo,
            valor_despues=objetivo_existente, tipo="crear_alias",
        )

    def resuelto(self, id_problema: int) -> bool:
        return id_problema in self._resoluciones

    def todos_los_registros(self) -> list[RegistroAuditoria]:
        return list(self._resoluciones.values())

    def pendientes_bloqueantes(self, ids_bloqueantes: list[int]) -> list[int]:
        """Índices de problemas bloqueantes que todavía faltan resolver."""
        return [i for i in ids_bloqueantes if i not in self._resoluciones]