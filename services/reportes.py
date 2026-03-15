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