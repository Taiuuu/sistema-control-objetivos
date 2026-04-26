# Arquitectura Multi-usuario - Sistema de Control de Objetivos
## V.E.S.P Organizations – Seguridad Privada

---

## 1. Visión General de la Arquitectura

### 1.1 Evolución del sistema

```
V1.0 - ACTUAL (Monolítica Local)
┌─────────────────────────────┐
│        PC/Escritorio        │
├─────────────────────────────┤
│   UI PyQt6                  │
│   Services (lógica)         │
│   SQLite Local              │
└─────────────────────────────┘
  ❌ Una sola PC
  ❌ Datos locales
  ❌ Sin sincronización

                    ↓

V3.0 - FUTURO (Distribuida con servidor central)
┌──────────────┐  ┌──────────────┐  ┌──────────────┐
│    PC 1      │  │    PC 2      │  │  Tablet      │
│  Operador A  │  │  Supervisor  │  │  Campo       │
└──────┬───────┘  └──────┬───────┘  └──────┬───────┘
       │                 │                 │
       └─────────────────┼─────────────────┘
                         │
                    ┌────▼─────────────┐
                    │  API REST        │
                    │  (Flask)         │
                    │  WebSocket       │
                    │  JWT Auth        │
                    └────┬─────────────┘
                         │
          ┌──────────────┴──────────────┐
          │                             │
       ┌──▼──────┐            ┌──────▼──┐
       │PostgreSQL            │  Redis  │
       │Centralizada          │  Cache  │
       │ + Replicación        │ (Sesiones)
       └──────────┘            └─────────┘

✅ Múltiples usuarios simultáneos
✅ Datos compartidos
✅ Sincronización en tiempo real
✅ Escalable
```

---

## 2. Componentes de la Arquitectura

### 2.1 Capas

```
┌─────────────────────────────────────────────────────────┐
│                 PRESENTACIÓN (UI)                       │
│              PyQt6 / Interfaz Web                       │
├─────────────────────────────────────────────────────────┤
│                   SINCRONIZACIÓN                        │
│          WebSocket / Event Bus / Notificaciones         │
├─────────────────────────────────────────────────────────┤
│                    SERVICIOS                            │
│  Lógica de negocio, validaciones, autenticación        │
├─────────────────────────────────────────────────────────┤
│                  API REST (Flask)                       │
│    Endpoints CRUD, autenticación, autorización         │
├─────────────────────────────────────────────────────────┤
│                     DATOS                               │
│         PostgreSQL (ORM) / Redis (Caché)               │
└─────────────────────────────────────────────────────────┘
```

### 2.2 Flujo de datos

```
Usuario interactúa con UI
         ↓
Event capturado en UI
         ↓
Llama servicio local
         ↓
Servicio valida datos
         ↓
Servicio llama API REST
         ↓
API autentica (JWT)
         ↓
API autoriza (permisos)
         ↓
API procesa en servicio backend
         ↓
Servicio actualiza BD (PostgreSQL)
         ↓
API emite evento WebSocket
         ↓
WebSocket notifica a otros clientes
         ↓
Otros clientes reciben evento
         ↓
Actualizan su UI
         ↓
Usuario ve cambio en tiempo real
```

---

## 3. Base de Datos - PostgreSQL

### 3.1 Schema completo

```sql
-- Usuarios y Autenticación
CREATE TABLE usuarios (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    rol_id INTEGER NOT NULL,
    esta_activo BOOLEAN DEFAULT TRUE,
    ultimo_acceso TIMESTAMP,
    fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (rol_id) REFERENCES roles(id)
);

-- Roles y Permisos
CREATE TABLE roles (
    id SERIAL PRIMARY KEY,
    nombre VARCHAR(50) UNIQUE NOT NULL,
    descripcion TEXT
);

CREATE TABLE permisos (
    id SERIAL PRIMARY KEY,
    nombre VARCHAR(100) UNIQUE NOT NULL,
    descripcion TEXT
);

CREATE TABLE rol_permisos (
    rol_id INTEGER NOT NULL,
    permiso_id INTEGER NOT NULL,
    PRIMARY KEY (rol_id, permiso_id),
    FOREIGN KEY (rol_id) REFERENCES roles(id),
    FOREIGN KEY (permiso_id) REFERENCES permisos(id)
);

-- Sesiones
CREATE TABLE sesiones (
    id SERIAL PRIMARY KEY,
    usuario_id INTEGER NOT NULL,
    token JWT VARCHAR(500) NOT NULL UNIQUE,
    ip_origen VARCHAR(50),
    dispositivo VARCHAR(255),
    fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    fecha_expiracion TIMESTAMP NOT NULL,
    esta_activa BOOLEAN DEFAULT TRUE,
    
    FOREIGN KEY (usuario_id) REFERENCES usuarios(id)
);

-- Datos operacionales
CREATE TABLE objetivos (
    id SERIAL PRIMARY KEY,
    nombre VARCHAR(255) NOT NULL,
    descripcion TEXT,
    fecha_inicio DATE,
    fecha_fin DATE,
    dias_semana VARCHAR(7),  -- "1,2,3,4,5,6,7"
    esta_activo BOOLEAN DEFAULT TRUE,
    fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(nombre)
);

CREATE TABLE supervisores (
    id SERIAL PRIMARY KEY,
    nombre VARCHAR(255) NOT NULL,
    email VARCHAR(100),
    fecha_alta DATE,
    fecha_baja DATE,
    esta_activo BOOLEAN DEFAULT TRUE,
    fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(nombre)
);

CREATE TABLE pasadas (
    id SERIAL PRIMARY KEY,
    fecha DATE NOT NULL,
    fecha_operativa DATE NOT NULL,  -- Corregida por lógica de turno nocturno
    hora TIME NOT NULL,
    turno VARCHAR(20),  -- 'diurno' o 'nocturno'
    objetivo_id INTEGER NOT NULL,
    supervisor_id INTEGER NOT NULL,
    usuario_registrador_id INTEGER NOT NULL,  -- Quién registró
    notas TEXT,
    timestamp_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (objetivo_id) REFERENCES objetivos(id),
    FOREIGN KEY (supervisor_id) REFERENCES supervisores(id),
    FOREIGN KEY (usuario_registrador_id) REFERENCES usuarios(id)
);

-- Auditoría
CREATE TABLE auditoria (
    id SERIAL PRIMARY KEY,
    usuario_id INTEGER NOT NULL,
    accion VARCHAR(100) NOT NULL,  -- 'CREAR', 'ACTUALIZAR', 'ELIMINAR', etc.
    tabla_afectada VARCHAR(50),
    registro_id INTEGER,
    cambios_antes JSONB,  -- Snapshot antes
    cambios_despues JSONB,  -- Snapshot después
    ip_origen VARCHAR(50),
    dispositivo VARCHAR(255),
    motivo TEXT,  -- Por qué se hizo la acción
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (usuario_id) REFERENCES usuarios(id)
);

-- Sincronización de eventos
CREATE TABLE eventos_sincronizacion (
    id SERIAL PRIMARY KEY,
    tipo VARCHAR(100),  -- 'pasada_creada', 'objetivo_actualizado', etc.
    usuario_id INTEGER,
    datos JSONB,
    procesado BOOLEAN DEFAULT FALSE,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (usuario_id) REFERENCES usuarios(id)
);

-- Índices críticos para rendimiento
CREATE INDEX idx_pasadas_fecha ON pasadas(fecha);
CREATE INDEX idx_pasadas_fecha_operativa ON pasadas(fecha_operativa);
CREATE INDEX idx_pasadas_objetivo_id ON pasadas(objetivo_id);
CREATE INDEX idx_pasadas_supervisor_id ON pasadas(supervisor_id);
CREATE INDEX idx_usuarios_username ON usuarios(username);
CREATE INDEX idx_sesiones_token ON sesiones(token);
CREATE INDEX idx_sesiones_usuario_id ON sesiones(usuario_id);
CREATE INDEX idx_auditoria_usuario_id ON auditoria(usuario_id);
CREATE INDEX idx_auditoria_timestamp ON auditoria(timestamp);
```

### 3.2 Migrations (Alembic)

```bash
# Inicializar migraciones
alembic init alembic

# Crear versión inicial
alembic revision --autogenerate -m "Initial schema"

# Aplicar migraciones
alembic upgrade head
```

---

## 4. API REST con Autenticación JWT

### 4.1 Endpoints principales

```python
# api/routes/auth.py
POST /api/v3/auth/login          # Autenticación
POST /api/v3/auth/logout         # Cierre de sesión
POST /api/v3/auth/refresh        # Refrescar token
GET  /api/v3/auth/me             # Datos usuario actual

# api/routes/objetivos.py
GET    /api/v3/objetivos                  # Listar con permisos
GET    /api/v3/objetivos/{id}
POST   /api/v3/objetivos          # Solo admin/supervisor
PUT    /api/v3/objetivos/{id}
DELETE /api/v3/objetivos/{id}

# api/routes/pasadas.py
GET    /api/v3/pasadas
GET    /api/v3/pasadas/{id}
POST   /api/v3/pasadas            # Registrar nueva
PUT    /api/v3/pasadas/{id}       # Editar
DELETE /api/v3/pasadas/{id}
DELETE /api/v3/pasadas/dia/{fecha}        # Masivo por día
DELETE /api/v3/pasadas/mes/{anio}/{mes}   # Masivo por mes

# api/routes/importacion.py
POST   /api/v3/importacion/cargar      # Cargar archivo Excel
POST   /api/v3/importacion/validar     # Validar estructura
POST   /api/v3/importacion/vista-previa # Generar preview
POST   /api/v3/importacion/confirmar   # Confirmar importación

# api/routes/auditoria.py
GET    /api/v3/auditoria
GET    /api/v3/auditoria/{usuario_id}

# api/routes/usuarios.py
GET    /api/v3/usuarios            # Solo admin
POST   /api/v3/usuarios            # Solo admin
PUT    /api/v3/usuarios/{id}       # Solo admin/self
DELETE /api/v3/usuarios/{id}       # Solo admin
```

### 4.2 Estructura de autenticación

```python
# api/auth.py
from flask_jwt_extended import create_access_token

@app.route('/api/v3/auth/login', methods=['POST'])
def login():
    """
    Endpoint de autenticación.
    
    Payload:
    {
        "username": "juan",
        "password": "contraseña123"
    }
    
    Response (200):
    {
        "access_token": "eyJhbGc...",
        "refresh_token": "eyJhbGc...",
        "usuario": {
            "id": 1,
            "username": "juan",
            "rol": "supervisor",
            "permisos": ["crear_pasada", "ver_reportes"]
        },
        "expires_in": 3600
    }
    """
    username = request.json.get('username')
    password = request.json.get('password')
    
    usuario = Usuario.query.filter_by(username=username).first()
    
    if not usuario or not usuario.verificar_password(password):
        return {'error': 'Credenciales inválidas'}, 401
    
    # Generar tokens
    access_token = create_access_token(
        identity=usuario.id,
        additional_claims={'rol': usuario.rol.nombre}
    )
    
    # Registrar sesión
    sesion = Sesion(
        usuario_id=usuario.id,
        token=access_token,
        ip_origen=request.remote_addr
    )
    db.session.add(sesion)
    db.session.commit()
    
    # Registrar en auditoría
    registrar_auditoria(
        usuario_id=usuario.id,
        accion='LOGIN',
        ip_origen=request.remote_addr
    )
    
    return {
        'access_token': access_token,
        'usuario': usuario.to_dict(),
        'expires_in': 3600
    }, 200
```

### 4.3 Protección de endpoints

```python
from flask_jwt_extended import jwt_required, get_jwt_identity
from functools import wraps

def require_permission(permiso):
    """Decorador para verificar permisos."""
    def decorator(fn):
        @wraps(fn)
        @jwt_required()
        def wrapper(*args, **kwargs):
            usuario_id = get_jwt_identity()
            usuario = Usuario.query.get(usuario_id)
            
            if not usuario:
                return {'error': 'Usuario no encontrado'}, 401
            
            if not usuario.tiene_permiso(permiso):
                registrar_auditoria(
                    usuario_id=usuario_id,
                    accion='ACCESO_DENEGADO',
                    tabla_afectada='N/A',
                    motivo=f'Falta permiso: {permiso}'
                )
                return {'error': f'Permiso requerido: {permiso}'}, 403
            
            return fn(*args, **kwargs)
        return wrapper
    return decorator

# Uso
@app.route('/api/v3/pasadas/dia/<fecha>', methods=['DELETE'])
@require_permission('ELIMINAR_MASIVO')
def eliminar_pasadas_dia(fecha):
    # Implementación
    pass
```

---

## 5. WebSocket y Sincronización en Tiempo Real

### 5.1 Servidor WebSocket

```python
# api/websocket.py
from flask import Flask
from flask_socketio import SocketIO, emit, join_room, leave_room
import json

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")

# Almacenar conexiones activas
conexiones_activas = {}

@socketio.on('connect')
def handle_connect(auth):
    """Cliente se conecta."""
    usuario_id = auth.get('usuario_id')
    token = auth.get('token')
    
    # Validar token
    if not validar_token_jwt(token):
        return False
    
    conexiones_activas[usuario_id] = {
        'sid': request.sid,
        'connected_at': datetime.now(),
        'ip': request.remote_addr
    }
    
    print(f'Usuario {usuario_id} conectado')
    emit('conectado', {'usuarios_en_linea': len(conexiones_activas)})

@socketio.on('disconnect')
def handle_disconnect():
    """Cliente se desconecta."""
    # Limpiar conexión
    print('Cliente desconectado')

@socketio.on('pasada_creada')
def handle_pasada_creada(data):
    """Evento: nueva pasada creada."""
    # Emitir a todos los clientes
    emit('pasada_creada', data, broadcast=True)
    
    # Guardar en eventos_sincronizacion
    evento = EventoSincronizacion(
        tipo='pasada_creada',
        usuario_id=data['usuario_id'],
        datos=json.dumps(data)
    )
    db.session.add(evento)
    db.session.commit()

@socketio.on('solicitar_sincronizacion')
def handle_solicitar_sincronizacion(data):
    """Cliente pide resincronización."""
    usuario_id = data.get('usuario_id')
    ultima_sincronizacion = data.get('ultima_sincronizacion')
    
    # Obtener eventos desde última sincronización
    eventos = EventoSincronizacion.query.filter(
        EventoSincronizacion.timestamp > ultima_sincronizacion
    ).all()
    
    emit('eventos_pendientes', {
        'eventos': [e.to_dict() for e in eventos]
    })
```

### 5.2 Cliente WebSocket (PyQt)

```python
# ui/websocket_client.py
import socketio
from datetime import datetime

class ClienteWebSocket:
    def __init__(self, url='http://localhost:5000'):
        self.sio = socketio.Client()
        self.url = url
        self.usuario_id = None
        self.token = None
        self.ultima_sincronizacion = None
        
        # Registrar event handlers
        self.sio.on('pasada_creada', self._on_pasada_creada)
        self.sio.on('pasada_eliminada', self._on_pasada_eliminada)
        self.sio.on('objetivo_actualizado', self._on_objetivo_actualizado)
        self.sio.on('conectado', self._on_conectado)
    
    def conectar(self, usuario_id, token):
        """Conectar a WebSocket con autenticación."""
        self.usuario_id = usuario_id
        self.token = token
        
        try:
            self.sio.connect(
                self.url,
                auth={'usuario_id': usuario_id, 'token': token}
            )
            print(f'Conectado a WebSocket como usuario {usuario_id}')
        except Exception as e:
            print(f'Error conectando a WebSocket: {e}')
    
    def _on_pasada_creada(self, data):
        """Manejador: nueva pasada creada."""
        print(f'Nueva pasada: {data}')
        # Emitir signal PyQt para actualizar UI
        signals.pasada_creada.emit(data)
    
    def _on_pasada_eliminada(self, data):
        """Manejador: pasada eliminada."""
        signals.pasada_eliminada.emit(data)
    
    def _on_objetivo_actualizado(self, data):
        """Manejador: objetivo actualizado."""
        signals.objetivo_actualizado.emit(data)
    
    def _on_conectado(self, data):
        """Manejador: confirmación de conexión."""
        self.ultima_sincronizacion = datetime.now()
        print(f'Usuarios en línea: {data["usuarios_en_linea"]}')
    
    def emitir_pasada_creada(self, pasada_dict):
        """Emitir evento cuando se crea pasada."""
        self.sio.emit('pasada_creada', pasada_dict)
    
    def solicitar_sincronizacion(self):
        """Pedir resincronización de cambios."""
        self.sio.emit('solicitar_sincronizacion', {
            'usuario_id': self.usuario_id,
            'ultima_sincronizacion': self.ultima_sincronizacion.isoformat()
        })
```

### 5.3 Eventos de sincronización

```python
EVENTOS_SINCRONIZACION = {
    'pasada_creada': {
        'datos': ['id', 'fecha', 'supervisor_id', 'objetivo_id', 'turno'],
        'broadcast': True,
        'guardar_evento': True
    },
    'pasada_eliminada': {
        'datos': ['id', 'fecha'],
        'broadcast': True,
        'guardar_evento': True
    },
    'pasada_actualizada': {
        'datos': ['id', 'cambios'],
        'broadcast': True,
        'guardar_evento': True
    },
    'objetivo_creado': {
        'datos': ['id', 'nombre'],
        'broadcast': True,
        'guardar_evento': True
    },
    'objetivo_actualizado': {
        'datos': ['id', 'cambios'],
        'broadcast': True,
        'guardar_evento': True
    },
    'importacion_completada': {
        'datos': ['total_registros', 'duplicados', 'usuarios_afectados'],
        'broadcast': True,
        'guardar_evento': True
    },
    'usuario_conectado': {
        'datos': ['usuario_id', 'nombre'],
        'broadcast': True,
        'guardar_evento': False
    },
    'usuario_desconectado': {
        'datos': ['usuario_id'],
        'broadcast': True,
        'guardar_evento': False
    }
}
```

---

## 6. Caché Distribuido (Redis)

### 6.1 Uso de caché

```python
# services/cache_service.py
import redis
from datetime import timedelta

class ServicioCache:
    def __init__(self):
        self.redis = redis.Redis(host='localhost', port=6379, db=0)
        self.TTL_DEFAULT = timedelta(minutes=5)
    
    def obtener_usuario(self, usuario_id):
        """Obtener usuario del caché."""
        key = f'usuario:{usuario_id}'
        datos = self.redis.get(key)
        
        if datos:
            return json.loads(datos)
        
        # Si no está en caché, obtener de BD
        usuario = Usuario.query.get(usuario_id)
        if usuario:
            self.guardar_usuario(usuario)
            return usuario.to_dict()
        
        return None
    
    def guardar_usuario(self, usuario):
        """Guardar usuario en caché."""
        key = f'usuario:{usuario.id}'
        self.redis.setex(
            key,
            self.TTL_DEFAULT,
            json.dumps(usuario.to_dict())
        )
    
    def invalidar_usuario(self, usuario_id):
        """Invalidar caché de usuario."""
        key = f'usuario:{usuario_id}'
        self.redis.delete(key)
    
    def guardar_sesion(self, usuario_id, sesion_data):
        """Guardar sesión en caché."""
        key = f'sesion:{usuario_id}'
        self.redis.setex(
            key,
            timedelta(hours=8),  # Duración de sesión
            json.dumps(sesion_data)
        )
    
    def obtener_permisos_usuario(self, usuario_id):
        """Obtener permisos cacheados."""
        key = f'permisos:{usuario_id}'
        permisos = self.redis.get(key)
        
        if permisos:
            return json.loads(permisos)
        
        # Obtener de BD
        usuario = Usuario.query.get(usuario_id)
        permisos_lista = [p.nombre for p in usuario.rol.permisos]
        
        self.redis.setex(
            key,
            timedelta(hours=1),
            json.dumps(permisos_lista)
        )
        
        return permisos_lista
```

### 6.2 Invalidación de caché

```python
# En cada operación de modificación
def crear_pasada(datos):
    pasada = Pasada(**datos)
    db.session.add(pasada)
    db.session.commit()
    
    # Invalidar caches relacionados
    cache.invalidar_pasadas_dia(pasada.fecha_operativa)
    cache.invalidar_reportes_mes(pasada.fecha_operativa.year, pasada.fecha_operativa.month)
    cache.invalidar_usuario(datos['usuario_id'])
    
    return pasada
```

---

## 7. Consideraciones de Seguridad

### 7.1 Autenticación
- JWT con expiración de 1 hora
- Refresh token con expiración de 7 días
- Múltiples sesiones simultáneas por usuario (configurables)
- Rate limiting en endpoints de login

### 7.2 Autorización
- RBAC (Role-Based Access Control)
- Verificación de permisos en cada endpoint
- Validación a nivel de BD con Row-Level Security (PostgreSQL)

### 7.3 Encriptación
- Contraseñas con bcrypt (10 rounds)
- Datos sensibles encriptados en tránsito (HTTPS)
- Tokens JWT firmados con secret key

### 7.4 Auditoría
- Cada acción registrada en `auditoria`
- Snapshots antes/después de cambios
- IP origen, dispositivo, motivo

---

## 8. Escalabilidad

### 8.1 Load balancing
```
                ┌─────────────┐
                │   Nginx     │
                │ Load Balancer
                └────────┬────┘
         ┌──────────┬────┴────┬──────────┐
         │          │         │          │
      ┌──▼──┐  ┌───▼──┐ ┌───▼──┐  ┌──▼──┐
      │API 1│  │API 2 │ │API 3 │  │API 4│
      └──┬──┘  └───┬──┘ └───┬──┘  └──┬──┘
         └──────────┼────────┼────────┘
                    │        │
            ┌───────▼────────▼───────┐
            │   PostgreSQL Master    │
            │  (Replicación)         │
            └───────┬────────────────┘
                    │
         ┌──────────┴─────────────┐
         │                        │
      ┌──▼──────┐          ┌─────▼───┐
      │Replica 1│          │Replica 2│
      └─────────┘          └─────────┘
```

### 8.2 Monitoreo
- Prometheus para métricas
- Grafana para dashboards
- ELK Stack para logs centralizados

---

## 9. Roadmap de implementación

**Q3 2026**: Migración a PostgreSQL + API REST  
**Q4 2026**: WebSocket + Caché Redis  
**Q1 2027**: Multi-usuario con sincronización  
**Q2 2027**: Importación Excel + Tablets  
**Q3 2027**: Auditoría avanzada + Load balancing  

---

*Documento de arquitectura v1.0 - Abril 2026*
