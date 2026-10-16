from services.menu_config import obtener_claves_menu_permitidas
from services.permisos import obtener_permisos_rol


def test_menu_items_respect_operational_permissions_by_role():
    operator_items = obtener_claves_menu_permitidas(
        "operador", obtener_permisos_rol("operador")
    )
    supervisor_items = obtener_claves_menu_permitidas(
        "supervisor", obtener_permisos_rol("supervisor")
    )

    assert "control_diario" in operator_items
    assert "registrar_pasada" in operator_items
    assert "registrar_turno" not in operator_items
    assert "agregar_objetivo" not in operator_items
    assert "registrar_turno" in supervisor_items
    assert "agregar_objetivo" in supervisor_items


def test_menu_admin_and_auditor_views_follow_existing_permissions():
    admin_items = obtener_claves_menu_permitidas("admin", obtener_permisos_rol("admin"))
    auditor_items = obtener_claves_menu_permitidas(
        "auditor", obtener_permisos_rol("auditor")
    )

    assert {"gestionar_usuarios", "sincronizacion", "optimizacion"} <= admin_items
    assert {"gestionar_usuarios", "logs", "auditoria"} <= auditor_items
    assert "sincronizacion" not in auditor_items
    assert "optimizacion" not in auditor_items
    assert "agregar_supervisor" not in auditor_items


def test_manager_keeps_read_only_workflows_without_write_actions():
    manager_items = obtener_claves_menu_permitidas(
        "gerente", obtener_permisos_rol("gerente")
    )

    assert {"control_diario", "ver_objetivos", "ver_pasadas", "reporte_mensual"} <= manager_items
    assert "registrar_pasada" not in manager_items
    assert "agregar_objetivo" not in manager_items
