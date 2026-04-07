# Sistema de Control de Objetivos
### V.E.S.P Organizations – Seguridad Privada

![Logo](assets/vesp.png)

---

## ¿De qué trata el sistema?

Sistema de escritorio desarrollado para reemplazar el control manual en Excel de objetivos de seguridad privada.

Permite registrar y visualizar en tiempo real qué objetivos fueron controlados durante el día, qué supervisores estaban de turno, cuántas pasadas se realizaron por turno y generar reportes mensuales de cumplimiento.

**Versión actual: 1.0.0** - Con API REST avanzada y sincronización en tiempo real.

---

## 🚀 Novedades en v2.0

- ✅ **API REST completa** con autenticación JWT y documentación OpenAPI
- ✅ **Sincronización en tiempo real** entre módulos con notificaciones SSE
- ✅ **Sistema de auditoría avanzado** con logs detallados y respaldo automático
- ✅ **Validaciones exhaustivas** de datos con reglas de negocio
- ✅ **Caché inteligente** para optimización de rendimiento
- ✅ **Indexación óptima** de base de datos para consultas rápidas
- ✅ **Interfaz mejorada** con actualizaciones automáticas en tiempo real

---

## 📦 Instalación

### Opción 1: Instalador (Recomendado)

1. Descargá el instalador desde la sección **Releases** del repositorio
2. Ejecutá `VESP_Control_Instalador.exe`
3. Seguí los pasos de instalación
4. Se creará un acceso directo en el escritorio

### Opción 2: Desde código fuente

```bash
# Clonar repositorio
git clone https://github.com/Taiuuu/sistema-control-objetivos.git
cd sistema-control-objetivos

# Instalar dependencias
pip install -r requirements.txt

# Ejecutar aplicación
python main.py
```

### Credenciales por defecto
```
Usuario: admin
Contraseña: 0000
```

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

## 🔌 API REST Avanzada

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
