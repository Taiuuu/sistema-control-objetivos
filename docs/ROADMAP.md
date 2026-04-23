# 🗺️ Roadmap de Desarrollo
## V.E.S.P Organizations – Control de Objetivos

**Versión actual:** 1.0.0  
**Última actualización:** Abril 2026  
**Próxima versión:** 2.0.0 (Q2-Q3 2026)

---

## 🎯 Visión General

Transformar el sistema de una **aplicación de escritorio monolítica** a una **solución empresarial distribuida** que soporte:
- Múltiples usuarios simultáneos en la oficina
- Trabajo en campo con tablets Android
- Acceso remoto desde web
- Sincronización automática offline/online
- Escalabilidad futura hacia nube

---

## 📊 Fases de Desarrollo

### 🟢 Fase 1.0 - ACTUAL (Hecho ✅)
**Periodo:** Marzo - Abril 2026  
**Estado:** En producción

**Logros:**
- ✅ Aplicación PyQt6 funcional
- ✅ Sistema de usuarios con roles
- ✅ Registro y reportes de pasadas
- ✅ Lógica de turnos nocturnos
- ✅ API REST básica
- ✅ Auditoría y validaciones
- ✅ Backup automático
- ✅ Importación parcial

**Código:**
```
main.py → desktop/main.py (se moverá)
ui/      → desktop/ui/
services/ → compartidos luego
```

---

### 🟡 Fase 2.0 - MULTI-CLIENTE (Q2-Q3 2026)
**Periodo estimado:** Mayo - Agosto 2026  
**Duración:** 3-4 meses

#### 2.1 Refactoring a Arquitectura Modular (3 semanas)

**Objetivo:** Separar lógica compartida de UI específica

**Tareas:**
```
✅ Crear estructura:
   ├── desktop/         (código PyQt6 existente)
   ├── mobile/android/  (app Kivy nueva)
   ├── shared/          (servicios reutilizables)
   └── backend/         (preparado para futuro)

✅ Extraer a shared/services/:
   ├── data_provider.py    (abstracción de datos)
   ├── sync_manager.py     (sincronización)
   ├── gestor_turnos.py    (lógica de turnos)
   └── importador_universal.py (Excel/JSON/tablets)

✅ Crear shared/models/:
   ├── usuario.py
   ├── objetivo.py
   ├── pasada.py
   └── supervisor.py

✅ Actualizar desktop/ui/ para usar shared/
```

**Salida:** Código modular, sin duplicación

#### 2.2 App Móvil Android (4-5 semanas)

**Objetivo:** Supervisores registren pasadas desde tablets en campo

**Herramienta:** Kivy (multiplataforma)

**Features:**
```
✅ Login con usuario/contraseña
✅ Pantalla principal con formulario
✅ Selector de objetivos
✅ Selector de turno (diurno/nocturno)
✅ Registro de pasadas
✅ Notas/observaciones
✅ Lista de pasadas del día
✅ Sincronización automática con PC

📋 Próximas versiones:
  - GPS tracking
  - Cámara (fotos adjuntas)
  - Notificaciones push
  - Maps de recorrido
```

**Compilar APK:**
```bash
# Instalar herramientas
pip install kivy buildozer cython

# En mobile/android/
buildozer android debug  # Generar APK

# Instalar en tablet
adb install bin/*.apk
```

**Instalación en Tablet:**
1. Habilitar "Fuentes desconocidas" en Android
2. Transferir APK
3. Instalar
4. Usar

#### 2.3 Sistema de Sincronización Avanzado (3-4 semanas)

**Objetivo:** Trabajo offline con sincronización automática

**Implementación:**
```python
# Ya existe: SyncManager en services/sync_manager.py
# Mejoras necesarias:

✅ Persistencia de cambios en archivo JSON
✅ Monitor de conexión (check cada 30s)
✅ Reintento automático de envios fallidos
✅ Detección de duplicados mejorada
✅ Resolución de conflictos
✅ Sincronización bidireccional

# Uso:
sync_mgr = get_sync_manager()
sync_mgr.crear_pasada_offline(...)  # Automático
sync_mgr.obtener_estado_sincronizacion()
```

#### 2.4 Importación Universal Mejorada (2-3 semanas)

**Objetivo:** Importar desde Excel, tablets, servidores

**Ya existe:** `services/importador_universal.py`

**Mejoras:**
```
✅ Validación exhaustiva
✅ Detección de duplicados con ±5 min tolerancia
✅ Conversión de formatos JSON→Excel
✅ Soporte para datos de tablets
✅ Reporte detallado de errores
✅ Opción de reintentar/ignorar/fusionar

Formatos soportados:
├── Excel (.xlsx) - directamente
├── JSON (tablets) - desde app móvil
├── CSV (futuro)
└── API REST (futuro)
```

**Salida:** Importador robusto listo para producción

#### 2.5 Base de Datos Mejorada (2 semanas)

**Objetivo:** Preparar para escalabilidad

**Cambios:**
```
✅ Esquema compatible con PostgreSQL
✅ Migraciones con Alembic
✅ Índices optimizados
✅ Relaciones normalizadas
✅ Backup incremental
✅ Script de migración SQLite → PostgreSQL

# Generar migración:
alembic init migrations
alembic revision --autogenerate -m "v2.0"
```

**Requisitos:**
```
pip install alembic sqlalchemy psycopg2-binary
```

---

### 🔵 Fase 3.0 - DISTRIBUIDA CON SERVIDOR (Q4 2026 - Q1 2027)
**Periodo estimado:** Septiembre 2026 - Marzo 2027  
**Duración:** 5-6 meses

#### 3.1 Backend Centralizado (6-8 semanas)

**Objetivo:** Servidor central con API REST

**Stack:**
- Backend: Flask + SQLAlchemy
- BD: PostgreSQL
- Cache: Redis
- WebSocket: Flask-SocketIO
- Auth: JWT + OAuth2 (futuro)

**Estructura:**
```
backend/
├── app.py                # Punto de entrada
├── config.py             # Configuración
├── api/                  # Endpoints REST
├── services/             # Lógica centralizada
├── models/               # ORM SQLAlchemy
├── database/             # Migraciones
├── authentication/       # JWT, OAuth
└── tests/               # Tests
```

**Endpoints REST:**
```
POST   /api/auth/login
POST   /api/auth/logout
POST   /api/auth/refresh

GET/POST   /api/v1/pasadas
GET/PUT/DELETE /api/v1/pasadas/{id}

GET/POST   /api/v1/objetivos
GET/POST   /api/v1/supervisores
GET/POST   /api/v1/usuarios

GET    /api/v1/reportes/mensual/{año}/{mes}
GET    /api/v1/reportes/diario/{fecha}

GET    /api/v1/sincronizacion/estado
POST   /api/v1/sincronizacion/forzar

WS     /ws/notifications  # WebSocket
```

**Requisitos:**
```
flask>=2.0
flask-sqlalchemy>=2.5
flask-cors>=3.0
flask-socketio>=5.0
python-dotenv>=0.19
psycopg2-binary>=2.9
redis>=4.0
```

#### 3.2 Cliente Web (5-6 semanas)

**Objetivo:** Acceso remoto desde navegador

**Tech Stack:**
- Frontend: React + TypeScript
- State Management: Redux
- UI: Material-UI o Ant Design
- Charts: Recharts o Chart.js

**Features:**
```
✅ Dashboard en tiempo real
✅ Reportes interactivos
✅ Gestión de usuarios (admin)
✅ Exportación PDF/Excel
✅ Gráficos de cobertura
✅ Auditoría visual
```

#### 3.3 App iOS (Flutter) (6-8 semanas)

**Objetivo:** Supervisores con iPhones

**Tech Stack:**
- Frontend: Flutter
- State Management: Provider o Riverpod
- HTTP Client: Dio

**Features:**
```
✅ Interfaz nativa iOS
✅ Trabajo offline
✅ Sincronización automática
✅ Push notifications
✅ GPS tracking (opcional)
✅ Fotos adjuntas
```

#### 3.4 Análisis Avanzado (3-4 semanas)

**Objetivo:** KPIs y predicciones

**Features:**
```
✅ Dashboard ejecutivo
✅ Gráficos de tendencias
✅ Análisis de rendimiento por supervisor
✅ Predicciones de cobertura
✅ Alertas automáticas
✅ Reportes programados por email
```

#### 3.5 DevOps y Deployment (2-3 semanas)

**Objetivo:** Desplegar en producción

**Tareas:**
```
✅ CI/CD con GitHub Actions
✅ Docker para backend
✅ Deploy en VPS/AWS
✅ SSL/TLS automático
✅ Monitoring (Prometheus)
✅ Logs centralizados (ELK)
```

---

## 📋 Checklist Actual (v1.0 → v2.0)

### 🚀 Ya Implementado
- ✅ Estructura de carpetas creada
- ✅ Documentación (ARQUITECTURA.md, ESTRUCTURA_PROYECTO.md)
- ✅ data_provider.py (abstracción de datos)
- ✅ sync_manager.py (sincronización)
- ✅ importador_universal.py (importación)
- ✅ mobile_app.py (app Kivy básica)
- ✅ Test de nuevas funcionalidades

### ⏳ Próximas Semanas
- 📋 Refactoring desktop/ para usar shared/
- 📋 Mejorar mobile/android/app.py
- 📋 Documentación: TECH_SPEC_COMPLETO.md
- 📋 Documentación: GUIA_INSTALACION.md
- 📋 Documentación: API_REFERENCE.md
- 📋 Compilar y distribuir APK
- 📋 Testing exhaustivo

---

## 🎯 Objetivos por Trimestre

### 🔶 Q2 2026 (Abril-Junio)
- Terminar v2.0 (arquitectura modular)
- App Android funcional
- Sincronización offline/online

### 🔷 Q3 2026 (Julio-Septiembre)
- Refinamiento y testing
- Feedback de usuarios
- Optimizaciones de performance

### 🟦 Q4 2026 (Octubre-Diciembre)
- Iniciar v3.0 (backend)
- Cliente web básico
- iOS (Flutter inicial)

### 🟩 Q1 2027 (Enero-Marzo)
- v3.0 en producción
- Análisis avanzado
- Mantenimiento y soporte

---

## 💰 Estimación de Esfuerzo

| Fase | Duración | Complejidad | Dependencias |
|------|----------|-------------|--------------|
| 2.0 (Módulos) | 3-4 meses | Media | v1.0 ✅ |
| 2.0 (Android) | 4-5 semanas | Media-Alta | Módulos |
| 2.0 (Sync) | 3-4 semanas | Media | Módulos |
| 2.0 (Importación) | 2-3 semanas | Media | Módulos |
| 3.0 (Backend) | 6-8 semanas | Alta | v2.0 ✅ |
| 3.0 (Web) | 5-6 semanas | Alta | Backend |
| 3.0 (iOS) | 6-8 semanas | Alta | Backend |
| 3.0 (Análisis) | 3-4 semanas | Media | Backend |

**Total acumulado:** ~13-16 meses desde hoy

---

## 🚨 Riesgos y Mitigación

| Riesgo | Probabilidad | Impacto | Mitigación |
|--------|-------------|--------|-----------|
| Cambios de requisitos | Media | Alto | Feedback temprano del usuario |
| Problemas de sincronización | Media | Alto | Tests exhaustivos offline |
| Performance degradada | Media | Medio | Benchmarking regular |
| Compatibilidad Android | Baja | Medio | Testing en múltiples dispositivos |
| Costos de servidor | Baja | Medio | Alternativas open-source |

---

## 📞 Contacto y Soporte

- **Repositorio:** https://github.com/Taiuuu/sistema-control-objetivos
- **Issues:** GitHub Issues
- **Email:** soporte@vesp.com.ar (futuro)
- **Equipo:** Desarrollo VESP

---

**Estado del documento:** Aprobado  
**Responsable:** Equipo de desarrollo  
**Próxima revisión:** Julio 2026
