# 📥 Guía de Instalación
## V.E.S.P Control de Objetivos

---

## 🖥️ Instalación en PC (Escritorio)

### Requisitos Mínimos

- **SO:** Windows 7+, macOS 10.12+, Linux (Ubuntu 18.04+)
- **Python:** 3.8 o superior
- **RAM:** 2 GB mínimo
- **Almacenamiento:** 500 MB libres
- **Conexión:** No requerida (funciona offline)

### Opción 1: Instalador Ejecutable (Windows)

**Pasos:**
1. Descargar `VESP_Control_v1.0_Setup.exe` desde GitHub Releases
2. Hacer doble clic en el archivo
3. Aceptar términos de licencia
4. Seleccionar carpeta de instalación (default: `C:\Program Files\VESP Control\`)
5. Completar instalación
6. Se creará acceso directo en:
   - Escritorio
   - Menú Inicio → VESP Control

**Desinstalar:**
- Control Panel → Programas → Desinstalar programa
- O ejecutar `uninstall.exe` en carpeta de instalación

---

### Opción 2: Desde Código Fuente (Recomendado para desarrollo)

#### 2.1 Descargar código

```bash
# Opción A: Git (recomendado)
git clone https://github.com/Taiuuu/sistema-control-objetivos.git
cd sistema-control-objetivos

# Opción B: Descargar ZIP
# - Ir a GitHub
# - Code → Download ZIP
# - Extraer archivo
```

#### 2.2 Crear entorno virtual

```bash
# Windows
python -m venv venv
.\venv\Scripts\activate

# macOS / Linux
python3 -m venv venv
source venv/bin/activate
```

Deberías ver `(venv)` al inicio de tu terminal.

#### 2.3 Instalar dependencias

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

**Dependencias principales:**
- PyQt6 >= 6.0
- SQLAlchemy >= 1.4
- openpyxl >= 3.8 (para Excel)
- python-dotenv >= 0.19

#### 2.4 Ejecutar aplicación

```bash
python main.py
```

**Primera ejecución:**
- Se crea `seguridad.db` (base de datos)
- Se crea usuario admin con contraseña `0000`
- Se te pedirá cambiar la contraseña inmediatamente

---

### Opción 3: Conda (Alternativa)

```bash
# Crear ambiente
conda create -n vesp python=3.9
conda activate vesp

# Instalar dependencias
pip install -r requirements.txt

# Ejecutar
python main.py
```

---

## 📱 Instalación en Tablets Android

### Requisitos

- **Versión Android:** 5.0 (API 21) o superior
- **Almacenamiento:** 100 MB libres
- **Conexión:** WiFi (para sincronización)
- **Pantalla:** Mínimo 5" (recomendado 7"+)

### Instalación de APK

#### Paso 1: Preparar tablet

1. Ir a **Settings** (Configuración)
2. **Security** (Seguridad)
3. Buscar **Unknown sources** o **Install unknown apps**
4. Habilitarlo

**⚠️ Advertencia:** Esto es seguro si descargas APK de fuente confiable.

#### Paso 2: Descargar APK

- Ir a GitHub Releases
- Descargar `VESP_Control_v1.0.apk`
- Guardar en tablet (por USB, email, Drive, etc.)

#### Paso 3: Instalar

**Opción A: Desde el gestor de archivos**
1. Abrir archivo manager (Files, Archivos, etc.)
2. Navegar a carpeta con APK
3. Tocar archivo `VESP_Control_v1.0.apk`
4. Tocar "Install"
5. Esperar completación

**Opción B: Desde USB**
```bash
# En PC
adb install VESP_Control_v1.0.apk

# Requiere:
# - Android Debug Bridge (ADB) instalado
# - Tablet conectada por USB
# - USB Debug habilitado en tablet
```

#### Paso 4: Primera ejecución

1. Abrir app desde launcher
2. Ingresar usuario (mismo de PC)
3. Contraseña (mismo de PC)
4. ✅ Listo

---

## 🔧 Compilar APK desde Código Fuente

**Para desarrolladores**

### Requisitos

```bash
pip install kivy buildozer cython
sudo apt-get install -y default-jdk  # Linux
# macOS: instalar Java desde Oracle
```

### Compilar

```bash
cd mobile/android

# Debug APK (para testing)
buildozer android debug

# Release APK (para distribuir)
buildozer android release

# APK estará en: bin/VESP_Control*.apk
```

### Primeras dos compilaciones tardan ~10-15 min (descarga Android SDK)

---

## 🍎 Instalación en iPhone (Futuro - v3.0)

**Estado:** Planificado para Q4 2026

**Tecnología:** Flutter

**Requisitos anticipados:**
- iPhone 6S+ (iOS 11+)
- Xcode (para compilación en Mac)
- App Store o distribución empresarial

**Se documentará cuando esté disponible.**

---

## ⚙️ Configuración Inicial

### 1. Base de Datos

**Primera ejecución:**
- Se crea `seguridad.db` automáticamente
- Se genera usuario `admin / 0000`
- Se crea carpeta `backups/`

### 2. Usuario Inicial

Al ejecutar por primera vez:

```
Usuario: admin
Contraseña: 0000
```

**IMPORTANTE:** Cambiar contraseña en primer login

```
Archivo → Cambiar contraseña
O: Ctrl+Shift+P
```

### 3. Datos Iniciales

Crear datos base:

1. **Supervisores:**
   - Menú → Agregar supervisor
   - O: Ctrl+S
   - Rellenar datos

2. **Objetivos:**
   - Menú → Agregar objetivo
   - O: Ctrl+O
   - Rellenar datos (fecha inicio/fin opcional)

3. **Usuarios:**
   - Menú → Gestionar usuarios (solo admin)
   - Crear nuevos usuarios
   - Asignar roles

### 4. Archivo `.env` (Opcional)

Crear en raíz del proyecto:

```env
# Base de datos
DATABASE_PATH=seguridad.db

# API
API_HOST=127.0.0.1
API_PORT=5000

# Logging
LOG_LEVEL=INFO
LOG_FILE=logs/app.log

# Sesión
SESSION_TIMEOUT=7200  # 2 horas

# Backup
BACKUP_INTERVAL=3600  # cada hora
BACKUP_DIR=backups/

# Sincronización (futuro v2.0)
SYNC_ENABLED=False
SYNC_SERVER=http://localhost:5000
```

---

## 🔌 Actualizar Aplicación

### Desde código fuente

```bash
# Descargar últimos cambios
git pull origin main

# Actualizar dependencias (si cambiaron)
pip install -r requirements.txt --upgrade

# Ejecutar
python main.py
```

### Desde instalador

1. Desinstalar versión actual
2. Descargar nuevo instalador
3. Instalar (sobre la misma carpeta si lo deseas)

---

## 🐛 Troubleshooting

### Problema: "ModuleNotFoundError: No module named 'PyQt6'"

**Solución:**
```bash
# Asegúrate que el entorno virtual está activado
# En Windows:
.\venv\Scripts\activate

# Luego instala:
pip install PyQt6
```

### Problema: "SQLite database is locked"

**Causa:** Otro proceso usa la base de datos

**Soluciones:**
```bash
# 1. Cerrar todas las instancias de VESP
# 2. Esperar 30 segundos
# 3. Reiniciar

# O eliminar lock file (si existe):
rm seguridad.db-wal
rm seguridad.db-shm
```

### Problema: Error al importar Excel

**Posibles causas:**
- Archivo no es .xlsx (debe ser Excel 2010+)
- Columnas mal nombradas
- Datos con formato incorrecto

**Verificar:**
- Archivo tiene columnas: Fecha, Supervisor, Objetivo, Hora, Turno
- Fechas en formato dd/mm/yyyy o similar
- Horas en formato HH:MM
- Supervisores y objetivos existen en sistema

### Problema: App móvil no sincroniza

**Causas:**
- WiFi no conectado
- Servidor no disponible
- Usuario/contraseña incorrectos

**Soluciones:**
1. Verificar WiFi está conectado
2. Verificar usuario/contraseña en PC
3. Verificar logs: Settings → Sync Status
4. Forzar sincronización: Settings → Sync Now

### Problema: Performance lenta

**Soluciones:**
```bash
# Optimizar base de datos
python scripts/optimize_db.py

# Limpiar caché
Archivo → Limpiar caché

# Reiniciar aplicación
```

### Problema: No puedo cambiar contraseña

**Debe ser admin o usuario que desea cambiar:**
```bash
# Como admin:
1. Menú → Gestionar usuarios
2. Seleccionar usuario
3. Botón "Resetear"
4. Contraseña se resetea a: 0000
5. Usuario debe cambiar en próximo login
```

---

## 📊 Verificar Instalación

Ejecutar tests para verificar que todo funciona:

```bash
# Instalar dependencias de test
pip install -r requirements-dev.txt

# Correr tests
pytest -v

# Si todo está ✅, la instalación es correcta
```

---

## 📚 Siguientes Pasos

1. **Leer documentación:**
   - `docs/ARQUITECTURA.md` - Entender la estructura
   - `docs/ESTRUCTURA_PROYECTO.md` - Organización de archivos

2. **Configurar datos iniciales:**
   - Crear supervisores
   - Crear objetivos
   - Crear usuarios

3. **Pruebas:**
   - Registrar pasadas
   - Generar reportes
   - Importar Excel

4. **Backup:**
   - Hacer backup inicial
   - Configurar backup automático

---

## ✅ Checklist de Instalación

- ☐ Python 3.8+ instalado
- ☐ Proyecto clonado o descargado
- ☐ Entorno virtual creado y activado
- ☐ Dependencias instaladas (`pip install -r requirements.txt`)
- ☐ Aplicación ejecutada sin errores (`python main.py`)
- ☐ Base de datos creada (`seguridad.db` existe)
- ☐ Usuario admin creado
- ☐ Contraseña inicial cambiada
- ☐ Datos iniciales cargados (supervisores, objetivos)
- ☐ Tests ejecutados sin errores

---

**Necesitas ayuda?**
- GitHub Issues: github.com/Taiuuu/sistema-control-objetivos/issues
- Revisar FAQ: `docs/FAQ.md`

---

**Última actualización:** Abril 2026
