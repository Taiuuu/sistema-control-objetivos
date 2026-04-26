# =============================================================================
# VESP Organizations - Queries para Tabla Principal OPTIMIZADAS
# =============================================================================

from database.gestor_db import gestor_db, con_cache


# =============================================================================
# CONTADORES
# =============================================================================

def contar_pasadas(fecha: str, objetivo_id: int, turno: str = None, supervisor_id: int = None) -> int:
    query = 'SELECT COUNT(*) FROM pasadas WHERE fecha = ? AND objetivo_id = ?'
    params = [fecha, objetivo_id]
    
    if turno:
        query += ' AND turno = ?'
        params.append(turno)
    if supervisor_id:
        query += ' AND supervisor_id = ?'
        params.append(supervisor_id)
    
    return gestor_db.ejecutar_scalar(query, tuple(params))


# =============================================================================
# EQUIPO
# =============================================================================

def obtener_equipo(fecha: str, turno: str) -> str:
    query = """
        SELECT 
            s1.nombre AS supervisor1,
            s2.nombre AS supervisor2,
            s3.nombre AS supervisor3
        FROM equipos e
        JOIN supervisores s1 ON e.supervisor1_id = s1.id
        JOIN supervisores s2 ON e.supervisor2_id = s2.id
        LEFT JOIN supervisores s3 ON e.supervisor3_id = s3.id
        WHERE e.fecha = ? AND e.turno = ?
    """
    
    resultado = gestor_db.ejecutar(query, (fecha, turno))
    
    if not resultado:
        return "—"
    
    fila = resultado[0]

    nombres = [
        n for n in [
            fila.get('supervisor1'),
            fila.get('supervisor2'),
            fila.get('supervisor3')
        ]
        if n is not None
    ]

    if not nombres:
        return "—"
    if len(nombres) == 1:
        return nombres[0]

    return ", ".join(nombres[:-1]) + " y " + nombres[-1]


# =============================================================================
# SUPERVISORES
# =============================================================================

@con_cache(ttl=60)
def cargar_supervisores() -> list:
    query = 'SELECT id, nombre FROM supervisores WHERE fecha_baja IS NULL ORDER BY nombre'
    resultados = gestor_db.ejecutar(query)
    return [(r['id'], r['nombre']) for r in resultados]


# =============================================================================
# PASADAS POR TURNO
# =============================================================================

def obtener_todas_pasadas_por_turno(fecha: str, supervisor_id: int = None) -> tuple:
    query = """
        SELECT objetivo_id, turno, COUNT(*) as total
        FROM pasadas 
        WHERE fecha = ?
    """
    params = [fecha]
    
    if supervisor_id:
        query += " AND supervisor_id = ?"
        params.append(supervisor_id)
    
    query += " GROUP BY objetivo_id, turno"
    
    resultados = gestor_db.ejecutar(query, tuple(params))
    
    pasadas_dia = {}
    pasadas_noche = {}
    
    for fila in resultados:
        obj_id = fila['objetivo_id']
        turno = fila['turno']
        count = fila['total']
        
        if turno == "diurno":
            pasadas_dia[obj_id] = count
        elif turno == "nocturno":
            pasadas_noche[obj_id] = count
    
    return pasadas_dia, pasadas_noche


# =============================================================================
# CONSULTAS AVANZADAS
# =============================================================================

def obtener_pasadas_fecha_rango(fecha_inicio: str, fecha_fin: str, objetivo_id: int = None) -> list:
    query = """
        SELECT 
            p.id, p.fecha, p.hora, p.turno, p.objetivo_id, p.supervisor_id,
            o.nombre as objetivo_nombre, 
            s.nombre as supervisor_nombre
        FROM pasadas p
        JOIN objetivos o ON p.objetivo_id = o.id
        JOIN supervisores s ON p.supervisor_id = s.id
        WHERE p.fecha BETWEEN ? AND ?
    """
    params = [fecha_inicio, fecha_fin]
    
    if objetivo_id:
        query += " AND p.objetivo_id = ?"
        params.append(objetivo_id)
    
    query += " ORDER BY p.fecha DESC, p.hora DESC"
    
    return gestor_db.ejecutar(query, tuple(params))


def obtener_estado_cobertura_dia(fecha: str) -> dict:
    query = """
        SELECT 
            o.id,
            o.nombre,
            COALESCE(SUM(CASE WHEN p.turno = 'diurno' THEN 1 ELSE 0 END), 0) as pasadas_diurno,
            COALESCE(SUM(CASE WHEN p.turno = 'nocturno' THEN 1 ELSE 0 END), 0) as pasadas_nocturno,
            COUNT(DISTINCT p.supervisor_id) as supervisores
        FROM objetivos o
        LEFT JOIN pasadas p ON o.id = p.objetivo_id AND p.fecha = ?
        WHERE o.fecha_fin IS NULL OR o.fecha_fin >= ?
        GROUP BY o.id, o.nombre
        ORDER BY o.nombre
    """
    
    resultados = gestor_db.ejecutar(query, (fecha, fecha))
    
    return {
        'fecha': fecha,
        'objetivos': [
            {
                'id': r['id'],
                'nombre': r['nombre'],
                'pasadas_diurno': r['pasadas_diurno'],
                'pasadas_nocturno': r['pasadas_nocturno'],
                'supervisores': r['supervisores'],
                'completo': r['pasadas_diurno'] > 0 and r['pasadas_nocturno'] > 0
            }
            for r in resultados
        ]
    }


def batch_contar_pasadas(fecha: str, objetivo_ids: list[int]) -> dict:
    if not objetivo_ids:
        return {}
    
    placeholders = ','.join(['?'] * len(objetivo_ids))
    query = f"""
        SELECT objetivo_id, COUNT(*) as total
        FROM pasadas
        WHERE fecha = ? AND objetivo_id IN ({placeholders})
        GROUP BY objetivo_id
    """
    
    params = [fecha] + objetivo_ids
    resultados = gestor_db.ejecutar(query, tuple(params))
    
    return {r['objetivo_id']: r['total'] for r in resultados}


def obtener_resumen_diario(fecha: str) -> dict:
    query = """
        SELECT 
            COUNT(*) as total_pasadas,
            COUNT(DISTINCT objetivo_id) as objetivos_controlados,
            COUNT(DISTINCT supervisor_id) as supervisores_activos,
            COUNT(CASE WHEN turno = 'diurno' THEN 1 END) as pasadas_diurno,
            COUNT(CASE WHEN turno = 'nocturno' THEN 1 END) as pasadas_nocturno
        FROM pasadas
        WHERE fecha = ?
    """
    
    resultados = gestor_db.ejecutar(query, (fecha,))
    
    if resultados:
        r = resultados[0]
        return {
            'fecha': fecha,
            'total_pasadas': r['total_pasadas'],
            'objetivos_controlados': r['objetivos_controlados'],
            'supervisores_activos': r['supervisores_activos'],
            'pasadas_diurno': r['pasadas_diurno'] or 0,
            'pasadas_nocturno': r['pasadas_nocturno'] or 0
        }
    
    return {
        'fecha': fecha,
        'total_pasadas': 0,
        'objetivos_controlados': 0,
        'supervisores_activos': 0,
        'pasadas_diurno': 0,
        'pasadas_nocturno': 0
    }