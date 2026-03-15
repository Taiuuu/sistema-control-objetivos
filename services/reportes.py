import sqlite3
import datetime

def obtener_objetivos_del_dia(fecha):
    conexion = sqlite3.connect('seguridad.db')
    cursor = conexion.cursor()

    # Traer todos los objetivos activos en esa fecha
    cursor.execute('''
        SELECT id, nombre, dias_semana
        FROM objetivos
        WHERE fecha_inicio <= ? AND (fecha_fin >= ? OR fecha_fin IS NULL)
    ''', (fecha, fecha))

    objetivos = cursor.fetchall()
    conexion.close()

    # Detectar qué día de la semana es la fecha
    fecha_dt = datetime.datetime.strptime(fecha, "%Y-%m-%d")
    dia_semana = fecha_dt.isoweekday()  # 1=lunes, 7=domingo

    # Filtrar solo los que corresponden ese día
    objetivos_del_dia = []
    for o in objetivos:
        dias_lista = [int(d) for d in o[2].split(",")]
        if dia_semana in dias_lista:
            objetivos_del_dia.append(o)

    return objetivos_del_dia


def reporte_diario(fecha):
    conexion = sqlite3.connect('seguridad.db')
    cursor = conexion.cursor()

    objetivos = obtener_objetivos_del_dia(fecha)

    if not objetivos:
        print(f"No hay objetivos para {fecha}.")
        return

    print(f"\n=== REPORTE DEL DÍA {fecha} ===\n")
    print(f"{'Objetivo':<20} {'Pasadas':<10} {'Estado'}")
    print("-" * 40)

    for o in objetivos:
        cursor.execute('''
            SELECT COUNT(*) FROM pasadas
            WHERE fecha = ? AND objetivo_id = ?
        ''', (fecha, o[0]))

        pasadas = cursor.fetchone()[0]
        estado = "OK" if pasadas > 0 else "FALTA"
        print(f"{o[1]:<20} {pasadas:<10} {estado}")

    conexion.close()

def reporte_mensual(anio, mes):
    conexion = sqlite3.connect('seguridad.db')
    cursor = conexion.cursor()

    cursor.execute('SELECT id, nombre, fecha_inicio, fecha_fin, dias_semana FROM objetivos')
    objetivos = cursor.fetchall()

    print(f"\n=== REPORTE MENSUAL {mes}/{anio} ===\n")
    print(f"{'Objetivo':<20} {'Días esperados':<16} {'Días cumplidos':<16} {'Cumplimiento'}")
    print("-" * 70)

    for o in objetivos:
        obj_id = o[0]
        nombre = o[1]
        inicio = o[2]
        fin = o[3]
        dias_semana = [int(d) for d in o[4].split(",")]

        # Contar dias del mes que corresponden al objetivo
        dias_esperados = 0
        dias_cumplidos = 0

        import calendar
        total_dias = calendar.monthrange(anio, mes)[1]

        for dia in range(1, total_dias + 1):
            fecha = f"{anio}-{mes:02d}-{dia:02d}"
            fecha_dt = datetime.datetime.strptime(fecha, "%Y-%m-%d")

            # Verificar si el objetivo estaba activo ese dia
            if fecha < inicio:
                continue
            if fin and fecha > fin:
                continue

            # Verificar si corresponde ese dia de la semana
            if fecha_dt.isoweekday() not in dias_semana:
                continue

            dias_esperados += 1

            # Verificar si hubo al menos una pasada ese dia
            cursor.execute('''
                SELECT COUNT(*) FROM pasadas
                WHERE fecha = ? AND objetivo_id = ?
            ''', (fecha, obj_id))
            pasadas = cursor.fetchone()[0]
            if pasadas > 0:
                dias_cumplidos += 1

        if dias_esperados > 0:
            porcentaje = (dias_cumplidos / dias_esperados) * 100
        else:
            porcentaje = 0

        print(f"{nombre:<20} {dias_esperados:<16} {dias_cumplidos:<16} {porcentaje:.1f}%")

    conexion.close()