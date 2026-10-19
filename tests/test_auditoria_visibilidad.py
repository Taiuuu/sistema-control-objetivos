def test_ocultar_acceso_auditoria_no_desactiva_el_registro(
    db_initialized, admin_user
):
    from services.auditoria import (
        TipoOperacion,
        obtener_auditoria_usuario,
        registrar_auditoria,
    )
    from services.menu_config import guardar_menu_usuario, obtener_menu_usuario

    usuario_id = admin_user["id"]
    guardar_menu_usuario(usuario_id, {"auditoria": False})

    assert obtener_menu_usuario(usuario_id)["auditoria"] is False

    registrar_auditoria(
        usuario_id,
        TipoOperacion.CREATE,
        tabla="objetivos",
        detalles="Prueba de auditoría independiente de visibilidad",
    )
    registros = obtener_auditoria_usuario(usuario_id, dias=3650)

    assert any(
        registro[8] == "Prueba de auditoría independiente de visibilidad"
        for registro in registros
    )
