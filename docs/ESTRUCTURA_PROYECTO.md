# 📁 Estructura del Proyecto
## V.E.S.P Organizations – Control de Objetivos

---

## Organización de Carpetas

```
sistema-control-objetivos/
│
├── 📋 docs/                          # Documentación completa
│   ├── ESTRUCTURA_PROYECTO.md        # Este archivo
│   ├── ARQUITECTURA.md               # Arquitectura general del sistema
│   ├── ROADMAP.md                    # Plan de desarrollo
│   ├── TECH_SPEC.md                  # Especificación técnica completa
│   ├── GUIA_INSTALACION.md           # Instrucciones de instalación
│   ├── GUIA_DESARROLLO.md            # Para desarrolladores
│   ├── API_REFERENCE.md              # Referencia de API
│   └── FAQ.md                        # Preguntas frecuentes
│
├── 🖥️ desktop/                       # Aplicación de escritorio (PyQt6)
│   ├── main.py                       # Punto de entrada
│   ├── requirements.txt              # Dependencias específicas
│   ├── ui/                           # Interfaz gráfica
│   │   ├── ventana_principal.py
│   │   ├── dashboard.py
│   │   ├── reporte_*.py
│   │   └── ...
│   ├── tests/                        # Tests específicos del desktop
│   └── assets/                       # Recursos de UI (local)
│
├── 📱 mobile/                        # Aplicaciones móviles
│   │
│   ├── android/                      # Android (Kivy)
│   │   ├── app.py                    # Aplicación Android
│   │   ├── requirements.txt
│   │   ├── buildozer.spec            # Config para compilar APK
│   │   └── README_ANDROID.md         # Instrucciones Android
│   │
│   ├── ios/                          # iOS (Flutter - futuro)
│   │   ├── pubspec.yaml              # Dependencias Flutter
│   │   ├── lib/
│   │   └── README_iOS.md             # Instrucciones iOS
│   │
│   └── shared/                       # Código compartido entre móviles
│       ├── models.py
│       └── utils.py
│
├── ⚙️ backend/                       # Backend/API (futuro con servidor)
│   ├── app.py                        # Punto de entrada de API
│   ├── config.py                     # Configuración
│   ├── requirements.txt              # Dependencias backend
│   ├── api/                          # Endpoints REST
│   ├── services/                     # Lógica de negocio
│   ├── database/                     # Acceso a datos
│   ├── models/                       # Modelos ORM
│   ├── migrations/                   # Migraciones BD
│   └── tests/                        # Tests del backend
│
├── 🔗 shared/                        # Código compartido entre apps
│   ├── models/
│   │   ├── usuario.py
│   │   ├── objetivo.py
│   │   ├── pasada.py
│   │   └── __init__.py
│   ├── services/
│   │   ├── data_provider.py          # Abstracción de datos
│   │   ├── sync_manager.py           # Sincronización
│   │   ├── gestor_turnos.py          # Lógica de turnos
│   │   └── __init__.py
│   └── constants.py                  # Constantes globales
│
├── 🧪 tests/                         # Tests integrados
│   ├── conftest.py
│   ├── test_turnos.py
│   ├── test_importacion.py
│   └── test_api.py
│
├── 📦 assets/                        # Recursos globales
│   ├── vesp.png
│   ├── icono.ico
│   └── README.md
│
├── 🔧 scripts/                       # Scripts utilitarios
│   ├── setup.py                      # Instalación inicial
│   ├── migrate.py                    # Migración de datos
│   ├── backup.py                     # Backup de BD
│   └── requirements.txt              # Dependencias de scripts
│
├── 🔐 .github/workflows/             # CI/CD automatizado
│   ├── test.yml
│   ├── build.yml
│   └── deploy.yml
│
├── 📝 README.md                      # Descripción general
├── 📝 CHANGELOG.md                   # Historial de cambios
├── 📝 LICENSE                        # Licencia del proyecto
├── 📝 .gitignore                     # Archivos ignorados
├── 📝 requirements-dev.txt           # Dependencias de desarrollo
└── 📝 version.txt                    # Versión actual
```

---

## Capa de Aplicación

### Desktop (PyQt6)
```
desktop/main.py
    ↓
    └─ Servicios compartidos (shared/services/)
    └─ Modelos compartidos (shared/models/)
    └─ Base de datos local (SQLite)
```

### Mobile Android (Kivy)
```
mobile/android/app.py
    ↓
    └─ Servicios compartidos (shared/services/)
    └─ Modelos compartidos (shared/models/)
    └─ Base de datos local (SQLite)
    └─ Sincronización con servidor (cuando exista)
```

### Mobile iOS (Flutter)
```
mobile/ios/lib/main.dart
    ↓
    └─ API REST (backend)
    └─ Sincronización automática
```

### Backend (API)
```
backend/app.py
    ↓
    ├─ API REST (Flask)
    ├─ Autenticación JWT
    ├─ Servicios de negocio
    └─ Base de datos centralizada (PostgreSQL)
```

---

## Módulos Clave

### `shared/services/`
Servicios reutilizables entre todas las aplicaciones:
- `data_provider.py`: Abstracción de datos (local/remoto)
- `sync_manager.py`: Sincronización offline/online
- `gestor_turnos.py`: Lógica de turnos nocturnos
- `importador_universal.py`: Importación Excel/JSON/Tablets

### `shared/models/`
Modelos de datos compartidos:
- `usuario.py`: Estructura de usuario
- `objetivo.py`: Estructura de objetivo
- `pasada.py`: Estructura de pasada
- `supervisor.py`: Estructura de supervisor

---

## Flujo de Datos por Versión

### Versión 1.0 - ACTUAL (Local Monolítica)
```
Desktop (PyQt6)
    └─ Servicios locales
        └─ SQLite local
```

### Versión 2.0 - PRÓXIMA (Multi-escritorio)
```
Desktop (PyQt6) ─┐
Tablet (Kivy)   ├─ Sincronización ─ SQLite compartido/PostgreSQL
Mobile (Kivy)  ─┘
```

### Versión 3.0 - FUTURO (Completa distribuida)
```
Desktop (PyQt6) ─┐
Tablet (Kivy)   ├─ API REST ─ PostgreSQL centralizado
Mobile (Flutter)─┐           ─ Redis Cache
Web (React)     ─┘           ─ WebSocket (sync real-time)
```

---

## Configuración por Carpeta

### desktop/requirements.txt
```
PyQt6>=6.0
PyQt6-WebEngine>=6.0
... (específico de UI)
```

### mobile/android/requirements.txt
```
kivy>=2.1
kivy-garden
... (específico de Kivy)
```

### backend/requirements.txt
```
Flask>=2.0
SQLAlchemy>=1.4
psycopg2-binary  # PostgreSQL
... (específico de API)
```

### shared/ (sin requirements.txt)
Solo código Python puro, sin dependencias externas

---

## Importante: Rutas Relativas

Cuando importes desde `shared/`:
```python
# Desktop
import sys
sys.path.insert(0, '../..')
from shared.services import get_data_provider

# Mobile
import sys
sys.path.insert(0, '../../..')
from shared.services import get_data_provider

# Backend
import sys
sys.path.insert(0, '../..')
from shared.services import get_data_provider
```

---

## Estado del Proyecto

| Carpeta | Estado | Observaciones |
|---------|--------|---------------|
| `desktop/` | ✅ Funcional | Aplicación completa, código en raíz |
| `mobile/android/` | 🔨 En progreso | Básico, necesita refinamiento |
| `mobile/ios/` | 📋 Planificado | Usar Flutter en futuro |
| `backend/` | 📋 Planificado | Cuando exista servidor |
| `shared/` | 🆕 Nuevo | Abstracción de lógica |
| `docs/` | 🔨 En progreso | Documentación centralizada |

---

**Última actualización:** Abril 2026  
**Responsable:** Equipo de desarrollo VESP
