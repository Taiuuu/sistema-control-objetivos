# 🏗️ Arquitectura del Sistema
## V.E.S.P Organizations – Control de Objetivos

**Versión:** 2.0.0  
**Última actualización:** Abril 2026  
**Estado:** Versión 1.0 en producción, versión 2.0 en desarrollo

---

## 📊 Evolución de la Arquitectura

### Versión 1.0 - ACTUAL (Monolítica Local)

```
┌──────────────────────────────────────┐
│       Computadora de Escritorio      │
│  (Una sola máquina, una sola persona)│
├──────────────────────────────────────┤
│                                      │
│  ┌────────────────────────────────┐  │
│  │  UI (PyQt6)                    │  │
│  │  - Ventana Principal           │  │
│  │  - Dashboards                  │  │
│  │  - Reportes                    │  │
│  └────────────────────────────────┘  │
│             ↓                         │
│  ┌────────────────────────────────┐  │
│  │  Servicios (Lógica)            │  │
│  │  - Gestión de pasadas          │  │
│  │  - Reportes                    │  │
│  │  - Validaciones                │  │
│  │  - Auditoría                   │  │
│  └────────────────────────────────┘  │
│             ↓                         │
│  ┌────────────────────────────────┐  │
│  │  SQLite Local                  │  │
│  │  (Un archivo .db en PC)        │  │
│  └────────────────────────────────┘  │
│                                      │
└──────────────────────────────────────┘

✅ Ventajas:
- Fácil de implementar
- Sin dependencias de red
- Rápido en máquina local
- Backup local automático

❌ Limitaciones:
- Un solo usuario por vez
- No hay sincronización en tiempo real
- Datos no compartidos con otros
- Difícil de escalar
```

---

### Versión 2.0 - PRÓXIMA (Multi-cliente Local)

```
┌─────────────────────────────────────────────────────────────────┐
│               Red Local (Oficina)                               │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │  PC 1        │  │  PC 2        │  │  Tablet      │          │
│  │  Operador A  │  │  Supervisor  │  │  (Android)   │          │
│  ├──────────────┤  ├──────────────┤  ├──────────────┤          │
│  │ PyQt6        │  │ PyQt6        │  │ Kivy         │          │
│  │ Desktop      │  │ Desktop      │  │ Mobile       │          │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘          │
│         │                 │                 │                  │
│         └─────────────────┼─────────────────┘                  │
│                           │                                     │
│                    ┌──────▼───────────┐                        │
│                    │ Sincronización   │                        │
│                    │ (SyncManager)    │                        │
│                    └──────┬───────────┘                        │
│                           │                                     │
│                    ┌──────▼───────────────────┐                │
│                    │ PostgreSQL / SQLite      │                │
│                    │ Compartida (o servidor)  │                │
│                    └──────────────────────────┘                │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘

✅ Ventajas nuevas:
- Múltiples usuarios simultáneos
- Datos compartidos y sincronizados
- Trabajo offline con sync posterior
- Escalable a servidor

❌ Desafíos:
- Manejo de conflictos de edición
- Control de concurrencia
- Persistencia de cambios offline
```

---

### Versión 3.0 - FUTURO (Completamente Distribuida)

```
                    ☁️ NUBE / VPS
        ┌───────────────────────────────────────┐
        │       Backend Central                 │
        ├───────────────────────────────────────┤
        │                                       │
        │  ┌─────────────────────────────────┐ │
        │  │  API REST (Flask)               │ │
        │  │  - Autenticación JWT            │ │
        │  │  - Endpoints CRUD               │ │
        │  │  - Sincronización WebSocket     │ │
        │  └─────────────────────────────────┘ │
        │                                       │
        │  ┌─────────────────────────────────┐ │
        │  │  PostgreSQL Centralizado        │ │
        │  │  - Replicación                  │ │
        │  │  - Backup automático            │ │
        │  │  - Concurrencia nativa          │ │
        │  └─────────────────────────────────┘ │
        │                                       │
        │  ┌─────────────────────────────────┐ │
        │  │  Redis Cache                    │ │
        │  │  - Sesiones                     │ │
        │  │  - Caché distribuido            │ │
        │  └─────────────────────────────────┘ │
        │                                       │
        └───────────────────────────────────────┘
                         ↕️
              WebSocket / HTTP REST
                         ↕️
        ┌─────────────────────────────────────┐
        │      Aplicaciones Cliente           │
        ├─────────────────────────────────────┤
        │                                     │
        │ ┌────────┐ ┌────────┐ ┌────────┐  │
        │ │Desktop │ │Tablet  │ │Web     │  │
        │ │PyQt6   │ │Kivy    │ │React   │  │
        │ └────────┘ └────────┘ └────────┘  │
        │                                     │
        │ ┌────────────────────────────────┐ │
        │ │ SQLite Local (Cache)           │ │
        │ │ - Trabajo offline              │ │
        │ │ - Datos cacheados              │ │
        │ └────────────────────────────────┘ │
        │                                     │
        └─────────────────────────────────────┘

✅ Ventajas finales:
- Acceso desde cualquier lugar
- Múltiples plataformas
- Sincronización automática en tiempo real
- Escalabilidad ilimitada
- Seguridad centralizada

✅ Capacidades:
- Trabajo offline/online automático
- Notificaciones en tiempo real
- Reportes en la nube
- Análisis de datos
- Auditoría centralizada
```

---

## 🔄 Capas de Arquitectura (Valida para todas las versiones)

```
┌──────────────────────────────────────────────┐
│        PRESENTACIÓN (UI Layer)               │
│  - PyQt6 (Desktop)                           │
│  - Kivy (Tablet Android)                     │
│  - Flutter (iPhone)                          │
│  - React (Web - futuro)                      │
├──────────────────────────────────────────────┤
│      SINCRONIZACIÓN (Sync Layer)             │
│  - SyncManager (offline/online)              │
│  - WebSocket (v3.0)                          │
│  - Gestión de conflictos                     │
├──────────────────────────────────────────────┤
│   SERVICIOS (Business Logic Layer)           │
│  - Lógica de turnos nocturnos                │
│  - Validaciones de datos                     │
│  - Generación de reportes                    │
│  - Importación universal                     │
├──────────────────────────────────────────────┤
│      API REST (Datos Access Layer)           │
│  - Endpoints REST (v3.0)                     │
│  - Autenticación JWT (v3.0)                  │
│  - Control de acceso                         │
├──────────────────────────────────────────────┤
│         PERSISTENCIA (Data Layer)            │
│  - SQLite (v1.0 / v2.0 local)                │
│  - PostgreSQL (v2.0 compartido / v3.0)       │
│  - Redis Cache (v3.0)                        │
└──────────────────────────────────────────────┘
```

---

## 🔌 Componentes Principales

### 1. **shared/services/** (Compartido en todas las versiones)

#### `data_provider.py`
Abstracción de datos que permite cambiar de fuente sin afectar UI:
```
DataProvider (Interface)
├─ SQLiteDataProvider (Local)
└─ RemoteDataProvider (Servidor - v3.0)
```

#### `sync_manager.py`
Maneja sincronización offline/online:
- Cola de cambios pendientes
- Monitor de conexión
- Persistencia de cambios

#### `gestor_turnos.py`
Lógica crítica de turnos nocturnos:
- Cálculo de fecha operativa
- Validación de horarios

#### `importador_universal.py`
Importación desde múltiples fuentes:
- Excel (.xlsx)
- JSON (tablets)
- API REST (futuro)

---

### 2. **Específicos por Versión**

#### Versión 1.0 (Actual - desktop/)
```
desktop/
├── main.py              # PyQt6 UI
├── ui/                  # Componentes de UI
├── services/            # Lógica local (heredada)
└── SQLite              # BD local
```

#### Versión 2.0 (Multi-cliente - desktop/ + mobile/android/)
```
desktop/
├── main.py
├── ui/
└── shared/services/    # Usa abstracción

mobile/android/
├── app.py              # Kivy UI
└── shared/services/    # Mismos servicios

Datos: SQLite compartida o servidor básico
```

#### Versión 3.0 (Distribuida - con backend/)
```
backend/
├── app.py              # API REST
├── services/           # Lógica centralizada
└── PostgreSQL         # BD principal

Clientes usan:
├── shared/services/    # Con RemoteDataProvider
└── SyncManager        # Para offline
```

---

## 📡 Flujo de Datos

### Operación: Registrar una Pasada

#### V1.0 (Local - Hoy)
```
1. Usuario clic "Registrar pasada"
        ↓
2. UI valida datos
        ↓
3. Llama SyncManager.crear_pasada_offline()
        ↓
4. SyncManager valida con reglas de turnos
        ↓
5. DataProvider (SQLite) guarda
        ↓
6. ✅ Pasada registrada
```

#### V2.0 (Multi-cliente)
```
1-5. (igual a V1.0)
        ↓
6. SyncManager agrega a cola de sincronización
        ↓
7. Monitor detecta servidor disponible
        ↓
8. Envía cambio a servidor
        ↓
9. Servidor valida y guarda
        ↓
10. Notifica a otros clientes vía WebSocket
        ↓
11. Otros clientes sincronizan automáticamente
        ↓
12. ✅ Todos ven el cambio en tiempo real
```

#### V3.0 (Distribuida - Futuro)
```
1-8. (igual a V2.0, pero con API REST)
        ↓
9. Servidor procesa con PostgreSQL
        ↓
10. Redis cachea resultado
        ↓
11. Emite evento vía WebSocket
        ↓
12. Web/Mobile/Desktop reciben en tiempo real
        ↓
13. ✅ Todo sincronizado automáticamente
```

---

## 🔐 Seguridad por Versión

| V | Autenticación | Autorización | Encriptación | Auditoría |
|---|---|---|---|---|
| 1.0 | Login local | Sistema de roles | ✅ | ✅ Logs locales |
| 2.0 | JWT (v2.1) | Control de permisos | ✅ | ✅ Logs centralizados |
| 3.0 | JWT + OAuth | Granular por recurso | ✅ SSL/TLS | ✅ Auditoría completa |

---

## 🚀 Roadmap de Migración

```
HOY (Abril 2026)
└─ v1.0: Monolítica local ✅

Q2-Q3 2026
└─ v2.0: Multi-cliente con sincronización
   - Refactoring a módulos compartidos
   - App Android (Kivy)
   - Sistema de sincronización offline

Q4 2026 - Q1 2027
└─ v3.0: Completamente distribuida
   - Backend con PostgreSQL
   - Cliente web con React
   - iOS con Flutter
   - Análisis avanzado
```

---

## 📚 Referencias

- Ver `ESTRUCTURA_PROYECTO.md` para detalles de carpetas
- Ver `TECH_SPEC.md` para especificaciones técnicas
- Ver `ROADMAP.md` para plan detallado
- Ver `GUIA_DESARROLLO.md` para instrucciones

---

**Estado:** En evolución constante  
**Responsable:** Equipo de desarrollo VESP
