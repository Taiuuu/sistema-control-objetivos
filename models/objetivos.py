import sqlite3

def agregar_objetivo(nombre, fecha_inicio, fecha_fin, dias_semana):
    conexion = sqlite3.connect('seguridad.db')
    cursor = conexion.cursor()

    cursor.execute('''
        INSERT INTO objetivos (nombre, fecha_inicio, fecha_fin, dias_semana)
        VALUES (?, ?, ?, ?)
    ''', (nombre, fecha_inicio, fecha_fin, dias_semana))

    conexion.commit()
    conexion.close()
    print(f"Objetivo '{nombre}' agregado correctamente.")

def listar_objetivos():
    conexion = sqlite3.connect('seguridad.db')
    cursor = conexion.cursor()

    cursor.execute('SELECT * FROM objetivos')
    objetivos = cursor.fetchall()

    conexion.close()

    if not objetivos:
        print("No hay objetivos cargados.")
    else:
        for o in objetivos:
            print(f"{o[0]} - {o[1]} | Inicio: {o[2]} | Fin: {o[3]} | Días: {o[4]}")

def dar_de_baja_objetivo(objetivo_id, fecha_fin):
    conexion = sqlite3.connect('seguridad.db')
    cursor = conexion.cursor()

    cursor.execute('''
        UPDATE objetivos SET fecha_fin = ? WHERE id = ?
    ''', (fecha_fin, objetivo_id))

    conexion.commit()
    conexion.close()
    print(f"Objetivo dado de baja correctamente.")