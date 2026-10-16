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
    "auditoria": True,
    "sincronizacion": True,
}

MENU_PERMISOS = {
    "control_diario": ("objetivos.ver", "pasadas.ver"),
    "registrar_pasada": ("pasadas.crear",),
    "registrar_turno": ("equipos.crear",),
    "agregar_objetivo": ("objetivos.crear",),
    "ver_objetivos": ("objetivos.ver",),
    "agregar_supervisor": ("supervisores.crear",),
    "ver_supervisores": ("supervisores.ver",),
    "ver_pasadas": ("pasadas.ver",),
    "notas": ("notas.ver",),
    "reporte_mensual": ("reportes.ver",),
    "reporte_objetivo": ("reportes.ver",),
    "gestionar_usuarios": ("usuarios.ver",),
    "logs": ("config.logs",),
    "auditoria": ("auditoria.ver",),
    "sincronizacion": ("config.sincronizacion",),
}

MENU_ROLES = {
    "optimizacion": frozenset({"admin"}),
    "transferir_datos": frozenset({"admin"}),
    "importar_excel": frozenset({"admin", "supervisor"}),
}


def obtener_claves_menu_permitidas(rol: str | None, permisos: set[str]) -> set[str]:
    """Devuelve módulos visibles según permisos existentes y su rol."""
    rol_normalizado = (rol or "").casefold()
    return {
        clave
        for clave in MENU_POR_DEFECTO
        if (
            not MENU_PERMISOS.get(clave)
            or any(permiso in permisos for permiso in MENU_PERMISOS[clave])
        )
        and (
            clave not in MENU_ROLES
            or rol_normalizado in MENU_ROLES[clave]
        )
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
