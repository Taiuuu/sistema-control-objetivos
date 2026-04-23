# 📱 VESP Control - Android Edition
## App móvil para supervisores en tablets Android

**Versión:** 1.0.0  
**Tecnología:** Kivy (Python)  
**Plataforma:** Android 5.0+  
**Estado:** En desarrollo

---

## 📋 Requisitos

### Tablet
- Android 5.0 (API 21) o superior
- 100 MB de almacenamiento libre
- WiFi para sincronización (opcional)
- Pantalla de 5" mínimo (recomendado 7"+)

### Compilación (Para desarrolladores)
- Python 3.7+
- Java JDK
- Android SDK
- Kivy + Buildozer

---

## 📥 Instalación para Usuarios

### Paso 1: Descargar APK
Ir a GitHub Releases y descargar:
- `VESP_Control_Android_v1.0.apk`

### Paso 2: Preparar tablet
1. Settings → Security
2. Habilitar "Unknown sources"

### Paso 3: Instalar
1. Abrir archivo (descarga o desde USB)
2. Tocar "Install"
3. Esperar

### Paso 4: Usar
1. Abrir app
2. Login con usuario de oficina
3. Registrar pasadas

---

## 🎯 Características

### ✅ Versión Actual (v1.0)
- ✅ Login seguro
- ✅ Registro de pasadas
- ✅ Selección de objetivos
- ✅ Selector de turno (diurno/nocturno)
- ✅ Notas/observaciones
- ✅ Lista de pasadas del día
- ✅ Offline-first (guarda localmente)

### 🟡 Próximas Versiones
- 📋 Sincronización automática
- 📋 GPS tracking
- 📋 Fotos adjuntas
- 📋 Notificaciones push
- 📋 Mapas de recorrido
- 📋 Reportes en app

---

## 🔧 Compilar APK (Desarrolladores)

### Instalación de herramientas

```bash
# 1. Instalar Kivy y buildozer
pip install kivy buildozer cython

# 2. Instalar Java
# Windows: Descargar desde oracle.com
# Mac: brew install java
# Linux: sudo apt-get install default-jdk
```

### Compilar

```bash
cd mobile/android

# Debug APK (para testing)
buildozer android debug

# Release APK (para distribuir)
buildozer android release

# APK generado en: bin/VESP_Control*.apk
```

**Primera compilación:** 10-15 minutos (descarga Android SDK)

### Configurar buildozer.spec

Archivo: `mobile/android/buildozer.spec`

```ini
[app]
title = VESP Control
package.name = vespeontrol
package.domain = org.vesp

[buildozer]
log_level = 2
warn_on_root = 1
```

---

## 📱 Uso en Campo

### Registrar Pasada

1. **Abrir app**
   - Tocar icono en launcher
   - Ingresar credenciales

2. **Pantalla principal**
   ```
   [Objetivo: Seleccionar ▼]
   [Turno: Seleccionar ▼]
   [Notas: Escribir aquí]
   [REGISTRAR PASADA]
   
   --- Pasadas de Hoy ---
   08:30 - Centro Comercial A (diurno)
   14:15 - Banco Central (diurno)
   ```

3. **Seleccionar objetivo**
   - Tocar dropdown "Objetivo"
   - Seleccionar de la lista

4. **Seleccionar turno**
   - Tocar dropdown "Turno"
   - Elegir "diurno" o "nocturno"

5. **Agregar notas (opcional)**
   - Escribir observaciones
   - Máx 500 caracteres

6. **Confirmar**
   - Tocar botón "REGISTRAR PASADA"
   - ✅ "Pasada registrada correctamente"

### Sincronización

**Estado:**
- Tocar botón "Sync" en header
- Ver estado de conexión y cambios pendientes

**Manual:**
- Si hay WiFi y cambios pendientes
- Se sincroniza automáticamente
- O tocar "Sync Now"

**Indicadores:**
- 🟢 Conectado: Sincroniza en tiempo real
- 🔴 Offline: Los datos se guardan localmente
- ⚠️ Pendientes: X cambios esperando

---

## 🔄 Flujo de Sincronización

```
1. Tablet sin WiFi
   └─ Registra pasada localmente
      └─ Se guarda en base de datos local

2. WiFi disponible
   └─ App detecta conexión
      └─ Envía cambios pendientes al servidor
         └─ Servidor confirma recepción
            └─ Actualizaciones en tiempo real a otras PCs

3. Múltiples tablets
   └─ Cada una trabaja offline
      └─ Se sincronizan cuando hay WiFi
         └─ Datos consolidados en servidor
            └─ Reportes con toda la información
```

---

## ⚙️ Configuración

### En la app

1. **Settings** (icono ⚙️)
   - Usuario conectado
   - Cambiar contraseña
   - Estado de sincronización
   - Limpiar datos locales

2. **Forzar sincronización**
   - Tocar "Sync Now"
   - Esperar confirmación

3. **Desconectar**
   - Tocar "Logout"
   - Volver a pantalla de login

---

## 🐛 Troubleshooting

### No puedo instalar
**Error:** "App not installed"

**Soluciones:**
1. Verificar que "Unknown sources" está habilitado
2. Revisar espacio libre (100+ MB)
3. Reintentar descarga del APK
4. Si persiste, reinstalar (desinstalar primero)

### La app se cierra
**Causa:** Compatibilidad Android

**Soluciones:**
1. Actualizar Android de tablet
2. Reiniciar tablet
3. Desinstalar y reinstalar app
4. Limpiar caché: Settings → Apps → VESP Control → Clear Cache

### No sincroniza
**Causas posibles:**
- WiFi no conectado
- Servidor no disponible
- Usuario/contraseña incorrectos

**Verificar:**
1. Conectar a WiFi
2. Verificar credenciales en Settings
3. Probar desde una PC
4. Forzar sincronización: Tocar "Sync Now"

### Lento o congelado
**Soluciones:**
1. Reiniciar tablet
2. Limpiar caché
3. Desinstalar y reinstalar
4. Verificar espacio libre

---

## 🔐 Seguridad

✅ **Contraseña:** Encriptada, nunca se almacena en texto plano  
✅ **Datos locales:** Encriptados en la tablet  
✅ **Sincronización:** HTTPS (cuando esté en servidor)  
✅ **Sesión:** Cierre automático por inactividad  
✅ **Logs:** Auditoría de todas las acciones  

**No compartir tablet entre usuarios diferentes**

---

## 📊 Datos Almacenados Localmente

La app guarda en tablet:
- Pasadas registradas
- Usuarios (si aplica)
- Configuración de app
- Caché de objetivos/supervisores

**Datos:** Solo necesarios, sin información privada

---

## 🆘 Soporte

**Problema común:**
- App lenta → Reiniciar tablet
- No sincroniza → Verificar WiFi
- Error de login → Verificar credenciales
- APK no instala → Habilitar "Unknown sources"

**Contactar soporte:**
- GitHub Issues
- Email de soporte (próximamente)
- WhatsApp (próximamente)

---

## 🔄 Actualizar App

**Nueva versión disponible?**

1. Descargar nuevo APK desde GitHub
2. Instalar (actualizará automáticamente)
3. Datos locales se mantienen
4. Listo para usar

---

## 📝 Nota para Desarrolladores

El código está en: `mobile/android/`

**Estructura:**
```
mobile/android/
├── app.py              # Código Kivy
├── buildozer.spec      # Config compilación
├── requirements.txt    # Dependencias
└── README_ANDROID.md   # Este archivo
```

**Para modificar:**
1. Editar `app.py`
2. Recompilar: `buildozer android debug`
3. Probar en tablet

---

**Versión:** 1.0.0  
**Última actualización:** Abril 2026  
**Próxima versión:** 1.5.0 (Q3 2026)
