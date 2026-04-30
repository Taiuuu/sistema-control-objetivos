# 🔧 TROUBLESHOOTING - Problemas Comunes y Soluciones
## VESP Control Objetivos

**Versión**: 1.1.0  
**Última actualización**: Abril 2026  

---

## ❌ "La aplicación no inicia"

### Posibles Causas y Soluciones

#### 1. Error: `ModuleNotFoundError: No module named 'PyQt6'`
**Solución**:
```bash
pip install PyQt6
pip install PyQt6-sip
```

#### 2. Error: `No such file or directory: seguridad.db`
**Solución**: La carpeta VESP Control no existe
```bash
# Se creará automáticamente al iniciar
# Si no, crea la carpeta manualmente:
mkdir "C:\Users\[Tu usuario]\VESP Control"
```

#### 3. Error: Python no encontrado
**Solución**:
```bash
# Verifica que Python está instalado
python --version

# Si no funciona, usa:
python3 --version

# O agranda la ruta:
C:\Users\Microsoft\AppData\Local\Programs\Python\Python314\python.exe scripts/main.py
```

#### 4. Error en inicialización de migraciones
**Solución**: La base de datos está corrupta
```bash
# Haz backup de tu BD actual
cp "C:\Users\[Tu usuario]\VESP Control\seguridad.db" seguridad.db.backup

# Elimina la BD corrupta (se recreará)
del "C:\Users\[Tu usuario]\VESP Control\seguridad.db"

# Vuelve a iniciar
python scripts/main.py
```

---

## 🔐 "No puedo iniciar sesión"

### "Usuario o contraseña incorrectos"

**Causa**: Credenciales mal introducidas

**Solución**:
1. Verifica que escribiste correctamente (sin espacios antes/después)
2. Contraseña es case-sensitive (mayúsculas importan)
3. Si es tu primer acceso, usa: `admin` / `0000`
4. Contacta al admin si olvidaste tu contraseña

### "Sesión no válida" después de cambiar password

**Causa**: Sesión expirada durante el cambio

**Solución**:
1. Cierra la aplicación completamente
2. Vuelve a abrir e inicia sesión normalmente
3. Tu nueva contraseña ya está activa

---

## 🖥️ "Interfaz congelada / No responde"

### Aplicación lenta o freezeada

**Causa**: Operación de BD larga o threads bloqueados

**Solución 1**: Espera 30 segundos (puede estar cargando datos grandes)

**Solución 2**: Si persiste, cierra desde el administrador de tareas
```bash
# En PowerShell (como administrador)
taskkill /F /IM python.exe
```

**Solución 3**: Limpia el caché
1. Menú → Configuración → Ver Caché
2. Haz clic en "Limpiar Caché"
3. Reinicia la aplicación

---

## 🎨 "El tema no se aplica correctamente"

### Cambio de tema no funciona

**Causa**: Archivos de tema corrupto o CSS no valida

**Solución**:
1. Menú → Configuración → "Restaurar Tema Default"
2. Si eso no existe, cierra y reabre la app
3. Intenta cambiar tema nuevamente

### Algunos elementos ven mal en tema claro/oscuro

**Causa**: Algunos componentes no actualizan estilo

**Solución**:
1. Cierra la ventana del componente problemático
2. Vuelve a abrirla desde el menú
3. El tema se aplicará correctamente

---

## 💾 "Error al guardar datos"

### "Error al guardar objetivo"

**Causa 1**: Campos obligatorios vacíos
- Todos los campos con * son obligatorios
- Solución: Completa todos antes de guardar

**Causa 2**: Nombres duplicados
- Algunos campos requieren ser únicos
- Solución: Cambia el nombre

**Causa 3**: Base de datos bloqueada
- Otro proceso está usando la BD
- Solución:
  ```bash
  # Cierra todas las instancias de la app
  taskkill /F /IM python.exe
  # Espera 2 segundos
  # Vuelve a abrir
  ```

### "Permiso denegado"

**Causa**: Tu rol no tiene permiso para esta acción

**Solución**:
1. Verifica tu rol (Menú → Gestionar Usuarios)
2. Contacta al admin para aumentar permisos
3. Cada rol tiene permisos específicos:
   - **Admin**: Todo
   - **Supervisor**: Crear/editar objetivos y equipos
   - **Operador**: Solo registrar pasadas
   - **Auditor**: Solo lectura
   - **Gerente**: Vista ejecutiva

---

## 📊 "Los reportes no se generan"

### "Error al generar reporte"

**Causa 1**: Sin datos en el período
- Solución: Asegúrate de tener pasadas en el mes/año seleccionado

**Causa 2**: Fechas inválidas
- Solución: Verificar que fecha inicio < fecha fin

**Causa 3**: Acceso denegado
- Solución: Tu rol no permite ver reportes
- Contacta al admin

### "Exportación lenta"

**Causa**: Mucho volumen de datos

**Solución**:
1. Intenta un período más pequeño (una semana en lugar de un mes)
2. O espera más tiempo (puede tomar 1-2 minutos)

---

## 📁 "Backup no funciona"

### "No puedo hacer backup"

**Causa 1**: Carpeta sin permisos
```bash
# Verifica permisos en C:\Users\[Tu usuario]\VESP Control\
# Debe ser completamente accesible
```

**Causa 2**: Disco lleno
- Solución: Libera espacio en disco

**Causa 3**: Permiso denegado (solo admin)
- Solución: Solo administradores pueden hacer backups
- Contacta al admin

### Encontrar backups realizados
- **Ubicación**: `C:\Users\[Tu usuario]\VESP Control\`
- **Formato**: `seguridad_2026-04-30_14-25.db` (con fecha y hora)

---

## 🔍 "Datos desaparecidos o corruptos"

### "Mis datos se borraron"

**Solución**: Restaura desde backup
```bash
# 1. Cierra la aplicación completamente
# 2. En C:\Users\[Tu usuario]\VESP Control\
# 3. Renombra seguridad.db a seguridad.db.corrupto
# 4. Copia el backup que quieres restaurar
# 5. Renómbralo a seguridad.db
# 6. Abre la aplicación
```

### "Base de datos corrupta"

**Síntomas**:
- Errores frecuentes al guardar
- Datos inconsistentes
- Aplicación inestable

**Solución**:
1. Haz backup de la BD actual
2. Usa una BD de backup anterior (si existe)
3. Si no hay backup, contacta al admin para recuperación

---

## 🌐 "API REST no funciona"

### "La sincronización está deshabilitada"

**Causa**: API REST no se inició correctamente

**Solución**:
1. Esto es no-crítico, la app sigue funcionando sin API
2. Verifica en los logs: Menú → Configuración → Ver Logs
3. Busca líneas con "API" o "REST"

### "No puedo sincronizar datos"

**Causa**: API no disponible

**Solución**:
1. Esto es opcional, la app funciona offline también
2. Si necesitas sincronización, contacta al admin

---

## 📝 "Problemas con logs"

### "Logs muy grandes"

**Causa**: Logs acumulados sin límite

**Solución**:
1. Menú → Configuración → Ver Logs
2. Haz clic en "Limpiar Logs Antiguos"
3. O espera a que se limpien automáticamente

### "No veo mis acciones en logs"

**Causa**: Logging deshabilitado o nivel bajo

**Solución**:
1. Menú → Configuración → Ver Logs
2. Haz clic en "Aumentar Nivel de Logging"
3. Vuelve a hacer la acción

---

## 🆘 "Error que no está aquí"

### Pasos para debugging

1. **Anota el error exacto** que ves en pantalla
2. **Revisa los logs**: Menú → Configuración → Ver Logs
3. **Copia el traceback** completo del error
4. **Contacta al admin** con:
   - Error exacto
   - Qué estabas haciendo
   - Tu rol
   - Logs relevantes

### Información útil para reportar bugs

```
- Versión de la app: (Ver en login)
- Tu rol: (Ver en Gestionar Usuarios)
- Qué hiciste antes del error: (paso a paso)
- Mensaje de error exacto: (copia completo)
- Logs: (de Menú → Configuración → Ver Logs)
- Screenshot: (si aplica)
```

---

## ✅ CHECKLIST ANTES DE CONTACTAR SOPORTE

- [ ] Reintenté cerrar y abrir la aplicación
- [ ] Revisé que tengo los permisos necesarios
- [ ] Chequeé los logs para más detalles
- [ ] Limpié el caché (Menú → Configuración → Limpiar Caché)
- [ ] Verifiqué que la BD no está corrupta
- [ ] Tengo un backup reciente

---

