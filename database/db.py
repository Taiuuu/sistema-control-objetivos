import sqlite3

def crear_base_datos():
    conexion = sqlite3.connect('seguridad.db')
    cursor = conexion.cursor()

    # Tabla de Objetivos
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS objetivos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL,
            fecha_inicio TEXT,
            fecha_fin TEXT,
            dias_semana TEXT
        )
    ''')

    # Tabla de Supervisores
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS supervisores (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL
        )
    ''')

    # Tabla de Pasadas
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS pasadas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            fecha TEXT,
            hora TEXT,
            turno TEXT,
            objetivo_id INTEGER,
            supervisor_id INTEGER,
            FOREIGN KEY (objetivo_id) REFERENCES objetivos(id),
            FOREIGN KEY (supervisor_id) REFERENCES supervisores(id)
        )
    ''')

    conexion.commit()
    conexion.close()

    print("Base de datos creada exitosamente.")