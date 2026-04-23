# 📋 TECH SPEC - Especificación Técnica
## V.E.S.P Control de Objetivos - v1.0

**Versión:** 1.0.0  
**Última actualización:** Abril 2026  
**Autor:** Taiel Clot  
**Estado:** ✅ Producción

---

## 🎯 Visión General

Sistema de gestión de objetivos de seguridad privada que permite registrar, monitorear y reportar el cumplimiento de supervisiones en tiempo real. Diseñado para escalar desde monolítico local (v1.0) a multi-usuario con sincronización (v2.0) y finalmente distribuido con servidor central (v3.0).

---

## 🏗️ Arquitectura del Sistema

### Capas de Aplicación

```
┌─────────────────────────────────────────┐
│         PRESENTACIÓN (UI)               │
│     PyQt6 Desktop + Kivy Mobile         │
└──────────────┬──────────────────────────┘
               │
┌──────────────▼──────────────────────────┐
│      SERVICIOS (Business Logic)         │
│  - Gestión de turnos                    │
│  - Importación de datos                 │
│  - Validaciones exhaustivas             │
│  - Sincronización                       │
└──────────────┬──────────────────────────┘
               │
┌──────────────▼──────────────────────────┐
│      ACCESO A DATOS (Data Layer)        │
│  - DataProvider (abstracción)           │
│  - SQLite (local)                       │
│  - PostgreSQL (futuro)                  │
└──────────────┬──────────────────────────┘
               │
┌──────────────▼──────────────────────────┐
│      PERSISTENCIA                       │
│  - Base de datos                        │
│  - Sistema de caché                     │
│  - Backups automáticos                  │
└─────────────────────────────────────────┘
```

### Stack Tecnológico

| Componente | Tecnología | Versión | Propósito |
|-----------|-----------|---------|----------|
| **Desktop UI** | PyQt6 | 6.0+ | Interfaz gráfica principal |
| **Mobile (Android)** | Kivy | 2.1+ | App para tablets |
| **Mobile (iOS)** | Flutter | 2.0+ | App nativa iPhone (futuro) |
| **Base de Datos** | SQLite | 3.35+ | Almacenamiento local |
| **ORM** | SQLAlchemy | 1.4+ | Mapeo de datos |
| **API REST** | Flask | 2.0+ | Backend HTTP |
| **Autenticación** | PyJWT | 2.0+ | Tokens JWT |
| **Encriptación** | cryptography | 3.4+ | Datos sensibles |
| **Hash de contraseñas** | bcrypt | 3.2+ | Seguridad |
| **Excel** | openpyxl | 3.8+ | Importación |
| **PDF** | ReportLab | 3.6+ | Generación reportes |

---

## 📊 Modelo de Datos

### Entidades Principales

#### 1. Usuario
```python
@dataclass
class Usuario:
    id: int
    nombre_usuario: str  # Único
    nombre_completo: str
    email: str
    password_hash: str  # Encriptado con bcrypt
    rol: str  # admin, supervisor, operador, auditor, gerente
    estado: str  # activo, inactivo, suspendido
    fecha_creacion: datetime
    ultimo_acceso: datetime
```

**Validaciones:**
- Nombre único (no duplicados)
- Email válido (RFC 5322)
- Contraseña >= 8 caracteres con complejidad
- Rol debe estar en ROLES_DISPONIBLES

#### 2. Objetivo
```python
@dataclass
class Objetivo:
    id: int
    nombre: str
    descripcion: str
    direccion: str
    ciudad: str
    responsable: str
    telefono: str
    email: str
    tipo: str  # comercial, residencial, industrial
    fecha_inicio: datetime
    fecha_fin: datetime  # NULL si activo indefinido
    estado: str  # activo, suspendido, cerrado
    fecha_creacion: datetime
```

**Validaciones:**
- Nombre no vacío (max 255 caracteres)
- Dirección válida (mínimo 5 caracteres)
- Fecha fin > fecha inicio (si se especifica)
- Teléfono formato válido

#### 3. Supervisor
```python
@dataclass
class Supervisor:
    id: int
    nombre: str
    apellido: str
    dni: str  # Único
    telefono: str
    email: str
    fecha_ingreso: datetime
    estado: str  # activo, inactivo, licencia
    especialidad: str
```

**Validaciones:**
- DNI único, formato válido (8 números)
- Teléfono número válido
- Email válido

#### 4. Pasada
```python
@dataclass
class Pasada:
    id: int
    objetivo_id: int  # FK
    supervisor_id: int  # FK
    turno: str  # "diurno" o "nocturno"
    fecha_operativa: datetime  # Fecha cuando se realizó
    hora_llegada: time
    hora_salida: time
    observaciones: str
    estado: str  # registrado, verificado, revisado
    fecha_creacion: datetime
    creado_por: int  # Usuario que registró
```

**Validaciones:**
- Objetivo debe existir
- Supervisor debe existir
- Hora salida > hora llegada
- Fecha máximo hoy (no futuro)
- Duración entre 5 min y 12 horas

#### 5. Turno
```python
@dataclass
class Turno:
    id: int
    objetivo_id: int  # FK
    fecha: datetime
    turno: str  # "diurno" o "nocturno"
    supervisor1_id: int  # FK (primero)
    supervisor2_id: int  # FK (segundo)
    estado: str  # asignado, cubierto, vencido
    notas: str
```

**Validaciones:**
- Dos supervisores diferentes
- No mismas fechas/turnos duplicados
- Supervisores debe estar activos

---

## 🔐 Seguridad

### Autenticación

**Sistema JWT:**
```python
# Login
POST /api/auth/login
{
  "usuario": "admin",
  "password": "xxxx"
}
Respuesta: {
  "token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "expires_in": 7200,  # 2 horas
  "usuario": {...}
}

# Uso en requests posteriores
Authorization: Bearer <token>
```

**Expiración de sesión:**
- Token válido: 2 horas
- Refresco automático: 30 minutos antes de expirar
- Cierre forzado: Logout manual

### Autorización (Roles)

Matriz de permisos:

| Permiso | Admin | Supervisor | Operador | Auditor | Gerente |
|---------|-------|-----------|----------|---------|---------|
| usuarios.ver | ✅ | ✅ | ❌ | ✅ | ❌ |
| usuarios.crear | ✅ | ❌ | ❌ | ❌ | ❌ |
| usuarios.editar | ✅ | ❌ | ❌ | ❌ | ❌ |
| usuarios.cambiar_rol | ✅ | ❌ | ❌ | ❌ | ❌ |
| objetivos.ver | ✅ | ✅ | ✅ | ✅ | ✅ |
| objetivos.crear | ✅ | ✅ | ❌ | ❌ | ❌ |
| objetivos.editar | ✅ | ✅ | ❌ | ❌ | ❌ |
| pasadas.crear | ✅ | ✅ | ✅ | ❌ | ❌ |
| reportes.ver | ✅ | ✅ | ⚠️ | ✅ | ✅ |
| auditoria.ver | ✅ | ❌ | ❌ | ✅ | ❌ |

### Encriptación

**Datos en reposo:**
- Contraseñas: bcrypt con salt (2^12 rounds)
- Datos sensibles: AES-256-CBC
- Backups: Comprimidos + AES-256

**Datos en tránsito:**
- HTTPS/TLS 1.2+ (futuro v2.0)
- Firma de requests con HMAC-SHA256

### Validación de Datos

Todas las entradas validadas:
```python
# Ejemplo: Validar pasada
def validar_pasada(pasada: Pasada) -> List[str]:
    errores = []
    
    # Validar referencias
    if not existe_objetivo(pasada.objetivo_id):
        errores.append("Objetivo no existe")
    
    # Validar tiempos
    if pasada.hora_salida <= pasada.hora_llegada:
        errores.append("Hora de salida debe ser posterior a llegada")
    
    # Validar duración
    duracion = (pasada.hora_salida - pasada.hora_llegada).total_seconds() / 60
    if duracion < 5 or duracion > 720:
        errores.append("Duración debe estar entre 5 minutos y 12 horas")
    
    # Validar fecha
    if pasada.fecha_operativa > datetime.now().date():
        errores.append("No se pueden registrar pasadas futuras")
    
    return errores
```

---

## 🔄 Lógica de Negocio

### Cálculo de Turnos Nocturnos

Los turnos nocturnos cruzan la medianoche (00:00).

```python
def calcular_fecha_operativa(fecha: date, turno: str, hora: time) -> date:
    """
    Determina la fecha operativa de una pasada.
    
    Regla: Si es turno nocturno y hora < 12:00, fecha_operativa es día anterior
    
    Ejemplos:
    - Turno diurno, 10:00 → fecha es hoy
    - Turno diurno, 18:00 → fecha es hoy
    - Turno nocturno, 22:00 → fecha es hoy
    - Turno nocturno, 08:00 → fecha es hoy - 1 día
    """
    if turno == "nocturno" and hora < time(12, 0):
        return fecha - timedelta(days=1)
    return fecha
```

### Detección de Duplicados

```python
def detectar_duplicado(pasada: Pasada) -> Optional[Pasada]:
    """
    Detecta si una pasada es duplicado.
    
    Regla: Mismo objetivo, supervisor y turno en fecha_operativa ±5 minutos
    """
    umbral_minutos = 5
    
    existentes = db.query(Pasada).filter(
        Pasada.objetivo_id == pasada.objetivo_id,
        Pasada.supervisor_id == pasada.supervisor_id,
        Pasada.turno == pasada.turno,
        Pasada.fecha_operativa == pasada.fecha_operativa,
        abs(extract('epoch', Pasada.hora_llegada - pasada.hora_llegada)) < umbral_minutos * 60
    ).first()
    
    return existentes
```

### Reportes

#### Reporte Mensual
```
Generar informe para mes/año:
1. Agrupar pasadas por objetivo
2. Calcular cobertura (pasadas / días turno esperado)
3. Generar gráficos de tendencias
4. Exportar a PDF/Excel
```

#### Reporte Diario
```
Estado actual de cobertura:
1. Listar todos los objetivos
2. Mostrar si fue cubierto hoy (turno diurno/nocturno)
3. Último supervisor que registró pasada
4. Observaciones relevantes
```

---

## 📊 Base de Datos

### Schema (SQLite/PostgreSQL compatible)

```sql
-- Usuarios
CREATE TABLE usuarios (
    id INTEGER PRIMARY KEY,
    nombre_usuario VARCHAR(100) UNIQUE NOT NULL,
    nombre_completo VARCHAR(255) NOT NULL,
    email VARCHAR(255) UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    rol VARCHAR(50) NOT NULL,
    estado VARCHAR(50) DEFAULT 'activo',
    fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    ultimo_acceso TIMESTAMP
);

-- Objetivos
CREATE TABLE objetivos (
    id INTEGER PRIMARY KEY,
    nombre VARCHAR(255) NOT NULL,
    descripcion TEXT,
    direccion VARCHAR(500),
    ciudad VARCHAR(100),
    responsable VARCHAR(255),
    telefono VARCHAR(20),
    email VARCHAR(255),
    tipo VARCHAR(50),
    fecha_inicio DATE,
    fecha_fin DATE,
    estado VARCHAR(50) DEFAULT 'activo',
    fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Supervisores
CREATE TABLE supervisores (
    id INTEGER PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL,
    apellido VARCHAR(100) NOT NULL,
    dni VARCHAR(20) UNIQUE NOT NULL,
    telefono VARCHAR(20),
    email VARCHAR(255),
    fecha_ingreso DATE NOT NULL,
    estado VARCHAR(50) DEFAULT 'activo',
    especialidad VARCHAR(255)
);

-- Pasadas
CREATE TABLE pasadas (
    id INTEGER PRIMARY KEY,
    objetivo_id INTEGER NOT NULL,
    supervisor_id INTEGER NOT NULL,
    turno VARCHAR(50) NOT NULL,
    fecha_operativa DATE NOT NULL,
    hora_llegada TIME NOT NULL,
    hora_salida TIME NOT NULL,
    observaciones TEXT,
    estado VARCHAR(50) DEFAULT 'registrado',
    fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    creado_por INTEGER NOT NULL,
    FOREIGN KEY (objetivo_id) REFERENCES objetivos(id),
    FOREIGN KEY (supervisor_id) REFERENCES supervisores(id),
    FOREIGN KEY (creado_por) REFERENCES usuarios(id)
);

-- Índices para performance
CREATE INDEX idx_pasadas_objetivo ON pasadas(objetivo_id);
CREATE INDEX idx_pasadas_supervisor ON pasadas(supervisor_id);
CREATE INDEX idx_pasadas_fecha ON pasadas(fecha_operativa);
CREATE INDEX idx_objetivos_estado ON objetivos(estado);
CREATE INDEX idx_usuarios_nombre ON usuarios(nombre_usuario);
```

### Backups

- **Automático:** Cada hora a carpeta `backups/`
- **Retención:** Últimos 30 días
- **Compresión:** ZIP
- **Encriptación:** Opcional AES-256

```bash
# Manual
python -m services.backup --full
```

---

## 🔄 Sincronización

### Sistema de Sync (v2.0 preparado)

```python
# v1.0: Sin sincronización
# v2.0: Sincronización offline/online

class CambioPendiente:
    id: str
    tipo: str  # "crear", "actualizar", "eliminar"
    entidad: str  # "pasada", "objetivo", etc
    datos: dict
    timestamp: datetime
    intentos: int = 0
    ultima_tentativa: datetime

# SyncManager persiste en sync_queue.json
```

### Monitor de Conexión

- Check cada 30 segundos
- Detecta WiFi disponible
- Sincroniza cambios automáticamente
- Reintenta fallos con backoff exponencial

---

## 🧪 Testing

### Cobertura Requerida

- `services/`: 80%+ (lógica crítica)
- `api/`: 70%+ (endpoints)
- `models/`: 90%+ (validaciones)
- `ui/`: Manual (GUI compleja)

### Ejecución

```bash
# Todos los tests
pytest

# Con cobertura
pytest --cov=services --cov-report=html

# Tests específicos
pytest tests/test_turnos.py -v
```

---

## 📈 Performance

### Optimizaciones

| Aspecto | Meta | Medio |
|--------|------|--------|
| Carga inicial UI | < 2s | Lazy loading |
| Reportes | < 5s | Caché + índices |
| Búsqueda | < 100ms | Full-text search |
| API endpoint | < 200ms | Caching |

### Caché

```python
@cache.cached(timeout=3600)  # 1 hora
def obtener_objetivos_activos():
    return db.query(Objetivo).filter(
        Objetivo.estado == 'activo'
    ).all()
```

---

## 📱 Sincronización Móvil (v2.0)

### Flujo Offline-First

```
Tablet Android (Kivy)
├─ Registra pasada → Base de datos local
├─ Detecta WiFi → Sincroniza con PC
└─ PC recibe → Consolida en BD principal
```

### Formato JSON (Tablets)
```json
{
  "version": "1.0",
  "dispositivo": "tablet-001",
  "timestamp": "2026-04-15T14:30:00Z",
  "cambios": [
    {
      "tipo": "crear",
      "entidad": "pasada",
      "datos": {
        "objetivo_id": 5,
        "supervisor_id": 3,
        "turno": "diurno",
        "fecha_operativa": "2026-04-15",
        "hora_llegada": "10:30",
        "hora_salida": "11:15"
      }
    }
  ]
}
```

---

## 🚀 Deployment

### Requisitos del servidor

- **SO:** Linux (Ubuntu 20.04+) o Windows Server 2019+
- **Python:** 3.8+
- **RAM:** 2GB mínimo
- **Almacenamiento:** 10GB mínimo
- **Conexión:** Mínimo 10 Mbps

### Setup

```bash
# Clonar y configurar
git clone <repo>
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Crear base de datos
python -m database.init

# Iniciar
python main.py
```

---

## 🔄 Versionado

- **v1.0.x:** Bugfixes y parches menores
- **v2.0.0:** Multi-usuario, sincronización, mobile
- **v3.0.0:** Backend distribuido, web, iOS

---

**Documento:** TECH_SPEC  
**Estado:** ✅ Aprobado  
**Última revisión:** Abril 2026
