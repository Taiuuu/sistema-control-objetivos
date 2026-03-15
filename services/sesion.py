usuario_id_activo = None
rol_activo = None

def iniciar_sesion(usuario_id, rol):
    global usuario_id_activo, rol_activo
    usuario_id_activo = usuario_id
    rol_activo = rol

def cerrar_sesion():
    global usuario_id_activo, rol_activo
    usuario_id_activo = None
    rol_activo = None

def get_usuario_id():
    return usuario_id_activo

def get_rol():
    return rol_activo