import sqlite3
import datetime


def registrar_accion(usuario_id, accion):
    conexion = sqlite3.connect('seguridad.db')
    cursor = conexion.cursor()

    ahora = datetime.datetime.now()
    fecha = ahora.strftime("%Y-%m-%d")
    hora = ahora.strftime("%H:%M:%S")

    cursor.execute('''
        INSERT INTO logs (fecha, hora, usuario_id, accion)
        VALUES (?, ?, ?, ?)
    ''', (fecha, hora, usuario_id, accion))

    conexion.commit()
    conexion.close()