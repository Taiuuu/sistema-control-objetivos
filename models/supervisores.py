from database.db import crear_base_datos
import sqlite3

def agregar_supervisor(nombre):
    conexion = sqlite3.connect('seguridad.db')
    cursor = conexion.cursor()

    cursor.execute('''
        INSERT INTO supervisores (nombre)
        VALUES (?)
    ''', (nombre,))

    conexion.commit()
    conexion.close()
    print(f"Supervisor '{nombre}' agregado correctamente.")

def listar_supervisores():
    conexion = sqlite3.connect('seguridad.db')
    cursor = conexion.cursor()

    cursor.execute('SELECT * FROM supervisores')
    supervisores = cursor.fetchall()

    conexion.close()

    if not supervisores:
        print("No hay supervisores cargados.")
    else:
        for s in supervisores:
            print(f"{s[0]} - {s[1]}")