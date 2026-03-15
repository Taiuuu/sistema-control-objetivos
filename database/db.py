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
    #Tabla para guardar qué dos supervisores estaban de turno cada día
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS equipos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        fecha TEXT,
        turno TEXT,
        supervisor1_id INTEGER,
        supervisor2_id INTEGER,
        FOREIGN KEY (supervisor1_id) REFERENCES supervisores(id),
        FOREIGN KEY (supervisor2_id) REFERENCES supervisores(id)
        )
    ''')
    #Tabla para notas
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS notas (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        fecha TEXT,
        nota TEXT
        )
    ''')
    #Tabla de Usuarios
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS usuarios (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT NOT NULL UNIQUE,
        password TEXT NOT NULL,
        rol TEXT NOT NULL DEFAULT 'operador',
        debe_cambiar_password INTEGER DEFAULT 1
        )
    ''')

    # Crear usuario admin por defecto si no existe
    cursor.execute("SELECT COUNT(*) FROM usuarios")
    if cursor.fetchone()[0] == 0:
        import hashlib
        password_hash = hashlib.sha256("0000".encode()).hexdigest()
        cursor.execute('''
            INSERT INTO usuarios (username, password, rol, debe_cambiar_password)
            VALUES (?, ?, ?, ?)
        ''', ("admin", password_hash, "admin", 1))
    
    conexion.commit()
    conexion.close()

    print("Base de datos creada exitosamente.")