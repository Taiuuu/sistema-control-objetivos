"""Preferencias persistentes de visibilidad del menú por usuario."""

import json

from database.gestor_db import gestor_db


MENU_POR_DEFECTO = {
    "control_diario": True,
    "registrar_pasada": True,
    "registrar_turno": True,
    "agregar_objetivo": True,
    "ver_objetivos": True,
    "agregar_supervisor": True,
    "ver_supervisores": True,
    "ver_pasadas": True,
    "notas": True,
    "feriados": True,
    "reporte_mensual": True,
    "reporte_objetivo": True,
    "transferir_datos": True,
    "importar_excel": True,
    "ayuda": True,
    "gestionar_usuarios": True,
    "logs": True,
    "optimizacion": True,
    "validaciones": True,
    "auditoria": True,
    "sincronizacion": True,
}


def obtener_menu_usuario(usuario_id: int | None) -> dict[str, bool]:
    if not usuario_id:
        return MENU_POR_DEFECTO.copy()
    fila = gestor_db.ejecutar_dict(
        "SELECT valor FROM preferencias_usuario WHERE usuario_id = ? AND clave = ?",
        (usuario_id, "menu_visible"),
    )
    if not fila:
        return MENU_POR_DEFECTO.copy()
    try:
        configuracion = json.loads(fila["valor"])
    except (TypeError, json.JSONDecodeError):
        return MENU_POR_DEFECTO.copy()
    return {**MENU_POR_DEFECTO, **{k: bool(v) for k, v in configuracion.items() if k in MENU_POR_DEFECTO}}


def guardar_menu_usuario(usuario_id: int, configuracion: dict[str, bool]) -> None:
    valor = json.dumps({k: bool(v) for k, v in configuracion.items() if k in MENU_POR_DEFECTO})
    gestor_db.ejecutar(
        """INSERT INTO preferencias_usuario (usuario_id, clave, valor)
           VALUES (?, ?, ?)
           ON CONFLICT(usuario_id, clave) DO UPDATE SET valor = excluded.valor""",
        (usuario_id, "menu_visible", valor),
    )
