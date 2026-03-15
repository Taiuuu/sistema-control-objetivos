import sqlite3

def registrar_turno(fecha, hora, turno, objetivo_id, supervisor_id):
    conexion = sqlite3.connect('seguridad.db')
    cursor = conexion.cursor()

    cursor.execute('''
        INSERT INTO pasadas (fecha, hora, turno, objetivo_id, supervisor_id)
        VALUES (?, ?, ?, ?, ?)
    ''', (fecha, hora, turno, objetivo_id, supervisor_id))

    conexion.commit()
    conexion.close()
    print(f"Turno registrado correctamente.")

def listar_turnos_del_dia(fecha):
    conexion = sqlite3.connect('seguridad.db')
    cursor = conexion.cursor()

    cursor.execute('''
        SELECT p.id, p.hora, p.turno, o.nombre, s.nombre
        FROM pasadas p
        JOIN objetivos o ON p.objetivo_id = o.id
        JOIN supervisores s ON p.supervisor_id = s.id
        WHERE p.fecha = ?
    ''', (fecha,))

    turnos = cursor.fetchall()
    conexion.close()

    if not turnos:
        print(f"No hay turnos registrados para {fecha}.")
    else:
        for t in turnos:
            print(f"{t[0]} | {t[1]} | {t[2]} | Objetivo: {t[3]} | Supervisor: {t[4]}")