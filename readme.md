# 🏢 VESP Control de Objetivos
### Sistema de gestión de seguridad privada - V.E.S.P Organizations

![VESP Logo](assets/vesp.png)

---

## 📌 ¿Qué es VESP?

**VESP** es un sistema profesional diseñado para mejorar la gestión de **objetivos de seguridad privada**.

Permite registrar, monitorear y reportar el cumplimiento de supervisiones en tiempo real desde múltiples dispositivos (PC, tablets, móviles), con sincronización automática y reportes detallados.

### Caso de Uso Principal
```
Oficina: PC con PyQt6
Supervisores en campo: Tablets Android (Kivy)
Jefes: Acceso web para reportes
Integración: APIs REST para sistemas externos
```

**Versión actual: 1.0.0** - Sistema de escritorio completo con API REST

---

## ✨ Características Principales

### ✅ Versión Actual (v1.0) - Funcionando

**Aplicación de Escritorio**
- 📊 Dashboard con estado de cobertura en tiempo real
- 📝 Registro de pasadas por turno (diurno/nocturno)
- 👥 Gestión de supervisores y objetivos
- 📈 Reportes mensuales detallados
- 📊 Gráficos de cumplimiento
- 🔐 Sistema de usuarios con roles (admin/operador/supervisor/auditor/gerente)

**Base de Datos**
- 🗄️ SQLite local con backup automático
- 🔒 Auditoría completa de acciones
- 📋 Validaciones exhaustivas de datos
- 🔐 Encriptación de datos sensibles

**Seguridad**
- 🔐 Contraseñas encriptadas con bcrypt
- 👤 Sistema de roles y permisos
- 📋 Log de auditoría completo
- 🔒 Cierre de sesión por inactividad

**API REST**
- ✅ Autenticación JWT
- ✅ Endpoints documentados
- ✅ Sincronización en tiempo real con SSE
- ✅ Importación/exportación de datos

### 🚀 Próximas Versiones

**v2.0 - Q2-Q3 2026** 🟡
- 📱 App móvil Android para supervisores
- 🔄 Sincronización automática offline/online
- 🖥️ Múltiples PCs trabajando simultáneamente
- 📊 Importación universal (Excel/JSON/Tablets)

**v3.0 - Q4 2026** 🔵
- ☁️ Backend centralizado en servidor
- 🌐 Cliente web para acceso remoto
- 📱 App iOS nativa (Flutter)
- 📡 WebSocket para sync en tiempo real
- 📈 Análisis avanzado y predicciones

---

## � Instalación Rápida

### Opción 1: Instalador (Recomendado)
```bash
1. Descargar desde: GitHub Releases
2. Ejecutar: VESP_Control_Instalador.exe
3. Seguir asistente de instalación
4. Se crea acceso directo en escritorio
```

### Opción 2: Desde código fuente

**Requisitos previos:**
- Python 3.8+
- pip (gestor de paquetes Python)

**Instalación:**
```bash
# Clonar repositorio
git clone https://github.com/Taiuuu/sistema-control-objetivos.git
cd sistema-control-objetivos

# Crear entorno virtual
python -m venv venv
.\venv\Scripts\activate  # Windows
# o en Linux/Mac: source venv/bin/activate

# Instalar dependencias
pip install -r requirements.txt

# Ejecutar
python main.py
```

**Primera vez:**
- Usuario: `admin`
- Contraseña: `0000`
- ⚠️ Se te pedirá cambiar la contraseña
- Se creará base de datos automáticamente

---

## 📱 Instalación de App Móvil (Android)

### Requisitos:
- Tablet Android 5.0+
- 50 MB de espacio libre
- Conexión WiFi (para sincronización)

### Instalación:
1. **Descargar APK** desde GitHub Releases
2. En la tablet: Settings → Security → Enable "Unknown sources"
3. Transferir APK a tablet (por USB o email)
4. Tocar archivo → Install
5. Abrir app → Login con mismo usuario que en PC

---

## 🎯 Funcionalidades Principales

### Control Diario
- Control diario de objetivos con estado por turno (día/noche)
- Registro de equipos de turno (dos supervisores por turno)
- Registro de pasadas con filtro automático por equipo de turno
- Tabla principal con colores de estado en tiempo real
- Filtros por turno, supervisor y estado
- Buscador de objetivos en tiempo real

### Gestión de Datos
- Gestión completa de objetivos (alta, baja, modificación)
- Gestión de supervisores con asignación a turnos
- Notas y observaciones diarias
- Historial completo de todas las operaciones

### Seguridad Avanzada
- Sistema de roles granulares (Admin, Supervisor, Operador) con permisos específicos
- Encriptación AES-256 para datos sensibles
- Validación de contraseñas fuertes con políticas de seguridad
- Sesiones con expiración automática (8 horas) y tokens seguros
- Control de acceso basado en permisos para todas las operaciones

#### Roles y Permisos

**Administrador (Admin):**
- Control total del sistema
- Gestión de usuarios y permisos
- Todas las operaciones CRUD
- Configuración del sistema
- Auditoría completa

**Supervisor:**
- Gestión de operaciones diarias
- Control de objetivos y supervisores
- Reportes y análisis
- Notas y observaciones

**Operador:**
- Operaciones básicas de registro
- Visualización de datos asignados
- Funciones limitadas de consulta

### Reportes y Exportación
- Reporte mensual de cumplimiento por objetivo
- Reporte diario detallado
- Exportación de reportes a Excel y PDF con logo corporativo
- Gráficos de cumplimiento y estadísticas

### Sistema de Usuarios
- Sistema de usuarios con roles (admin/operador)
- Gestión de usuarios y permisos
- Cierre de sesión automático por inactividad con backup previo

### Auditoría y Seguridad
- Historial de acciones completo (logs de auditoría)
- Backup automático diario de la base de datos
- Sistema de validaciones exhaustivas
- Encriptación de datos sensibles
- Rate limiting en API

### Rendimiento
- Caché inteligente para consultas frecuentes
- Indexación óptima de base de datos
- Sincronización en tiempo real entre módulos
- Actualizaciones automáticas de interfaz

---

## � Funcionalidades Preparadas para Multi-usuario

### Arquitectura Modular
- **Proveedores de datos intercambiables**: Fácil cambio entre SQLite local y bases de datos remotas
- **Sistema de sincronización**: Trabajo offline/online con cola de cambios pendientes
- **API preparada**: Estructura lista para comunicación cliente-servidor

### App Móvil para Supervisores
```bash
# Ejecutar app móvil (requiere Kivy)
python mobile_app.py
```

**Características:**
- ✅ **Offline-first**: Funciona sin conexión a internet
- ✅ **Sincronización automática**: Envía datos cuando hay conexión
- ✅ **Interfaz intuitiva**: Diseño optimizado para móviles
- ✅ **GPS opcional**: Registro de ubicación (preparado)
- ✅ **Fotos adjuntas**: Para evidencia visual (preparado)

### Importación Universal
- ✅ **Excel**: Archivos `.xlsx` con formato estandarizado
- ✅ **Tablets**: Archivos JSON desde dispositivos móviles
- ✅ **API**: Recepción de datos desde sistemas externos
- ✅ **Validación automática**: Detección de duplicados y errores

### Base de Datos Centralizada
**Preparado para migración a PostgreSQL/MySQL:**
- ✅ Esquema compatible con PostgreSQL
- ✅ Consultas optimizadas para concurrencia
- ✅ Sistema de backups preparado para la nube
- ✅ Pool de conexiones para múltiples usuarios

---

## �🔌 API REST Avanzada

El sistema incluye una API REST completa para integración con otros sistemas:

### Endpoints principales
- `POST /api/auth/login` - Autenticación JWT
- `GET/POST/PUT/DELETE /api/objetivos` - Gestión de objetivos
- `GET/POST/PUT/DELETE /api/supervisores` - Gestión de supervisores
- `POST /api/pasadas` - Registro de pasadas
- `GET /api/reportes/mensual/<anio>/<mes>` - Reportes mensuales
- `GET /api/sse/events` - Notificaciones en tiempo real

### Inicio de la API
```bash
python -m api.app
```

Accede a `http://127.0.0.1:5000/api/docs` para documentación completa.

---

## 🏗️ Arquitectura del Sistema

### Tecnologías
- **Frontend**: PyQt6 con interfaz moderna y responsiva
- **Backend**: SQLite3 con índices optimizados
- **API**: Flask con JWT y documentación OpenAPI
- **Sincronización**: Señales PyQt con notificaciones SSE

### Módulos principales
- `models/` - Capa de acceso a datos
- `services/` - Lógica de negocio y utilidades
- `ui/` - Interfaces de usuario
- `api/` - API REST
- `database/` - Configuración de BD

### Características técnicas
- Sincronización en tiempo real entre módulos
- Caché inteligente con invalidación automática
- Validaciones exhaustivas con reglas de negocio
- Sistema de auditoría completo
- Backup automático con compresión

---

## 📋 Requisitos del Sistema

- **SO**: Windows 10/11
- **Python**: 3.8+ (para instalación desde código)
- **Espacio**: 50MB mínimo
- **RAM**: 512MB mínimo
- **Base de datos**: SQLite3 (incluida)

---

## 🔧 Desarrollo

### Configuración del entorno
```bash
# Crear entorno virtual
python -m venv venv
venv\Scripts\activate

# Instalar dependencias
pip install -r requirements.txt

# Ejecutar en modo desarrollo
python main.py
```

### Estructura del proyecto
```
sistema-control-objetivos/
├── main.py                 # Punto de entrada principal
├── api/                    # API REST
├── models/                 # Modelos de datos
├── services/               # Servicios y utilidades
├── ui/                     # Interfaces de usuario
├── database/               # Configuración BD
├── assets/                 # Recursos gráficos
├── build/                  # Archivos de compilación
├── instalador/             # Scripts de instalación
└── docs/                   # Documentación
```

---

## � Licencia y Uso

Este software es propiedad privada de V.E.S.P Organizations y fue desarrollado por Taiel Clot. El uso, modificación o distribución está estrictamente prohibido sin autorización expresa del propietario.

---

**Desarrollado por Taiel Clot para V.E.S.P Organizations**

## Atajos de teclado

| Atajo | Acción |
|-------|--------|
| Ctrl + P | Registrar pasada |
| Ctrl + O | Agregar objetivo |
| Ctrl + S | Agregar supervisor |
| Ctrl + T | Registrar turno |
| Ctrl + N | Notas del día |
| Ctrl + R | Reporte mensual |
| Ctrl + B | Actualizar tabla |
| Ctrl + H | Ayuda |

---

## Reset de fábrica

Para borrar todos los datos y dejar el sistema como nuevo ejecutá desde la carpeta del proyecto:
```bash
python reset_fabrica.py
```

---

## Seguridad

- Contraseñas encriptadas con bcrypt
- Sistema de roles (admin/operador)
- Historial completo de acciones
- Backup automático diario
- Cierre de sesión por inactividad

---

## Tecnologías utilizadas

- Python 3
- PyQt6
- SQLite
- bcrypt
- openpyxl
- reportlab
- requests

---

*Desarrollado para V.E.S.P Organizations – Seguridad Privada*

```
