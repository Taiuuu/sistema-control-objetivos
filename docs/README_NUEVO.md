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

**Lógica de Negocios**
- 🕐 Cálculo inteligente de turnos nocturnos (cruza medianoche)
- 📅 Determinación automática de fecha operativa
- ✅ Validaciones de horarios por turno
- 🎯 Detección de objetivos sin cobertura

**Importación de Datos**
- 📊 Importar pasadas desde Excel
- 📱 Conversión JSON para tablets
- 🔄 Detección automática de duplicados
- 📝 Reportes de errores con soluciones

**Seguridad**
- 🔐 Contraseñas encriptadas con bcrypt
- 👤 Sistema de roles y permisos
- 📋 Log de auditoría completo
- 🔒 Cierre de sesión por inactividad

---

### 🚀 Próximas Versiones (Roadmap)

**v2.0 - Q2-Q3 2026** 🟡
- 📱 App móvil Android para supervisores
- 🔄 Sincronización automática offline/online
- 🖥️ Múltiples PCs trabajando simultáneamente
- 📊 Importación universal (Excel/JSON/Tablets)

**v3.0 - Q4 2026** 🔵
- ☁️ Backend centralizado en servidor
- 🌐 Cliente web para acceso remoto
- 📱 App iOS nativa
- 📡 WebSocket para sync en tiempo real
- 📈 Análisis avanzado y predicciones

---

## 🚀 Instalación Rápida

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

**Uso en campo:**
```
✅ Registra pasadas sin internet
✅ Sincroniza automáticamente cuando hay WiFi
✅ Funciona offline completamente
✅ Notas con observaciones
```

---

## 🏗️ Estructura del Proyecto

```
sistema-control-objetivos/
│
├── 📋 docs/                    # Documentación completa
│   ├── ARQUITECTURA.md         # Estructura técnica
│   ├── ROADMAP.md              # Plan de desarrollo
│   ├── ESTRUCTURA_PROYECTO.md  # Guía de carpetas
│   ├── TECH_SPEC.md            # Especificaciones técnicas
│   └── ...
│
├── 🖥️ desktop/                 # Aplicación de escritorio
│   ├── main.py                 # Punto de entrada
│   ├── ui/                     # Interfaz gráfica
│   └── requirements.txt
│
├── 📱 mobile/                  # Apps móviles
│   ├── android/                # Kivy (Android)
│   ├── ios/                    # Flutter (iPhone - futuro)
│   └── shared/                 # Código compartido
│
├── 🔗 shared/                  # Código reutilizable
│   ├── services/               # Lógica compartida
│   └── models/                 # Modelos de datos
│
├── ⚙️ backend/                 # API (futuro)
│   ├── app.py
│   └── requirements.txt
│
└── 📦 assets/                  # Logos y recursos
```

**Ver más detalles:** `docs/ESTRUCTURA_PROYECTO.md`

---

## 🔧 Uso Básico

### En Escritorio (PyQt6)

#### Primer acceso:
1. Abrir aplicación
2. Ingresar usuario/contraseña
3. Cambiar contraseña si es primera vez
4. ✅ Listo para usar

#### Flujo principal:
```
1. Ver Dashboard → estado de cobertura
2. Registrar Pasada → Ctrl+P
3. Crear Objetivo → Ctrl+O
4. Ver Reportes → Ctrl+R
5. Descargar PDF/Excel
```

#### Atajos útiles:
- `Ctrl+P` - Registrar pasada
- `Ctrl+O` - Agregar objetivo
- `Ctrl+S` - Agregar supervisor
- `Ctrl+T` - Registrar turno
- `Ctrl+R` - Reporte mensual
- `Ctrl+H` - Ayuda y FAQ
- `Ctrl++` - Aumentar zoom
- `Ctrl+-` - Reducir zoom

### En Tablet (Android)

```
1. Abrir app
2. Ingresar usuario/contraseña (mismo que PC)
3. Ver lista de objetivos asignados
4. Tocar "Registrar pasada"
5. Seleccionar objetivo
6. Seleccionar turno (diurno/nocturno)
7. Agregar notas si es necesario
8. Confirmar
9. ✅ Pasada registrada localmente
10. Se sincroniza cuando hay WiFi
```

---

## 📊 Reportes

### Disponibles Ahora:

**Reporte Mensual**
- Cumplimiento por objetivo
- Cobertura por turno
- Gráficos de tendencias
- Exportar a PDF/Excel

**Reporte Diario**
- Estado actual de cobertura
- Equipos por turno
- Observaciones

**Exportación**
- 📄 PDF con logo
- 📊 Excel con datos crudos
- 📅 Filtrable por fecha/supervisor

---

## 👥 Roles y Permisos

| Rol | Crear | Editar | Eliminar | Reportes | Auditoría |
|-----|-------|--------|----------|----------|-----------|
| 👑 Admin | ✅ | ✅ | ✅ | ✅ | ✅ |
| 👷 Supervisor | ✅ | ✅ | ⚠️ | ✅ | ⚠️ |
| 🔧 Operador | ✅ | ⚠️ | ❌ | ⚠️ | ❌ |
| 👁️ Auditor | ❌ | ❌ | ❌ | ✅ | ✅ |
| 📊 Gerente | ❌ | ❌ | ❌ | ✅ | ❌ |

**Admin:** Control total del sistema + gestión de usuarios  
**Supervisor:** Gestión de operaciones del día  
**Operador:** Solo registro de pasadas  
**Auditor:** Solo lectura + exportación  
**Gerente:** Reportes ejecutivos  

---

## 🔐 Seguridad

✅ **Contraseñas:** Encriptadas con bcrypt (no se pueden recuperar)  
✅ **Auditoría:** Todos los cambios se registran  
✅ **Backup:** Automático cada hora  
✅ **Datos:** Validados antes de guardar  
✅ **Encriptación:** Datos sensibles protegidos  
✅ **Sesiones:** Cierre automático por inactividad (2 horas)  

---

## ⚙️ Configuración

### Archivos de configuración:

**`.env`** (crear en raíz si no existe)
```env
DATABASE_PATH=seguridad.db
API_HOST=127.0.0.1
API_PORT=5000
LOG_LEVEL=INFO
BACKUP_INTERVAL=3600  # segundos
SESSION_TIMEOUT=7200  # 2 horas
```

**`version.txt`**
- Versión actual del sistema
- Se actualiza automáticamente

### Base de datos:
- Ubicación: `seguridad.db` (SQLite)
- Backup: `seguridad.db.backup`
- Se crea automáticamente en primer uso

---

## 🧪 Testing

### Ejecutar tests:
```bash
# Instalar dependencias de test
pip install -r requirements-dev.txt

# Correr todos los tests
pytest

# Con cobertura
pytest --cov=services
```

### Casos de prueba disponibles:
- ✅ Lógica de turnos nocturnos
- ✅ Validaciones de datos
- ✅ Importación de Excel
- ✅ Cálculo de reportes
- ✅ Gestión de usuarios

---

## 📚 Documentación Completa

Todos los documentos están en `docs/`:

1. **ARQUITECTURA.md** - Estructura técnica del sistema
2. **ROADMAP.md** - Plan de desarrollo futuro
3. **ESTRUCTURA_PROYECTO.md** - Organización de carpetas
4. **TECH_SPEC.md** - Especificaciones técnicas detalladas
5. **API_REFERENCE.md** - API REST (próximamente)
6. **GUIA_INSTALACION.md** - Instrucciones paso a paso
7. **GUIA_DESARROLLO.md** - Para desarrolladores

---

## 🐛 Reportar Bugs

Si encuentras un problema:

1. Abre un issue en GitHub
2. Describe el problema claramente
3. Incluye:
   - Versión del sistema (`version.txt`)
   - Pasos para reproducir
   - Logs relevantes (`logs/`)
   - Screenshots si aplica

---

## 💡 Sugerencias

¿Tienes ideas para mejorar?

1. Abre una Discussion en GitHub
2. Describe la idea
3. Indica la prioridad
4. Se revisará en el siguiente ciclo

---

## 📄 Licencia

Código proprietary de V.E.S.P Organizations  
Todos los derechos reservados © 2026

---

## 👥 Equipo

- **Desarrollador Principal:** Taiel Clot
- **Diseño UI/UX:** Taiel Clot
- **QA/Testing:** Equipo de operaciones
- **Soporte:** Equipo de soporte

---

## 🚀 Comenzar Ahora

```bash
# Opción 1: Instalador
Descargar desde GitHub → Ejecutar .exe → Listo

# Opción 2: Código fuente
git clone https://github.com/Taiuuu/sistema-control-objetivos.git
cd sistema-control-objetivos
python main.py

# Opción 3: Tablet Android
Descargar APK → Instalar → Abrir → Login
```

---

## ❓ Preguntas Frecuentes

**P: ¿Puedo usar desde múltiples PCs?**  
R: En v1.0 cada PC es independiente. En v2.0 (Q2-Q3 2026) habrá sincronización automática.

**P: ¿Funciona sin internet?**  
R: Sí. En v1.0 completamente offline. En v2.0 con sincronización cuando hay conexión.

**P: ¿Se pueden importar datos de Excel?**  
R: Sí, formato estandarizado. Ver documentación.

**P: ¿Cómo hago backup?**  
R: Automático cada hora. También manual en Archivo → Backup.

**P: ¿Puedo acceder desde mi celular?**  
R: En v1.0 no. En v2.0 desde Android, en v3.0 desde iPhone.

**Para más preguntas:** Ver `docs/FAQ.md` (próximamente)

---

## 📞 Soporte

- 📧 Email: soporte@vesp.com.ar (próximamente)
- 💬 GitHub Issues: github.com/Taiuuu/sistema-control-objetivos/issues
- 📱 WhatsApp: (próximamente)

---

## 🎉 Agradecimientos

- PyQt6 - Framework de UI
- SQLAlchemy - ORM
- Kivy - Framework móvil
- Flask - Web framework
- PostgreSQL - Base de datos

---

**Versión:** 1.0.0  
**Última actualización:** Abril 2026  
**Próxima versión:** 2.0.0 (Q2-Q3 2026)

[⬆️ Volver al inicio](#-vesp-control-de-objetivos)
