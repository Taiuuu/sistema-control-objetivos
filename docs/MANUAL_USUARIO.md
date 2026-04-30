# 📖 MANUAL DE USUARIO - VESP Control Objetivos
## Guía de Inicio Rápido

**Versión**: 1.1.0  
**Última actualización**: Abril 2026  

---

## 🚀 INICIO RÁPIDO (5 MINUTOS)

### 1. Iniciar la Aplicación
```bash
cd "c:\Vesp taiu\sistema-control-objetivos"
python scripts/main.py
```

### 2. Pantalla de Login
- **Usuario**: `admin` (usuario por defecto)
- **Contraseña**: `0000` (contraseña por defecto)
- **Botón**: Haz clic en "Entrar" o presiona Enter

```
Advertencia: Debes cambiar la contraseña del admin en la primera sesión
```

### 3. Cambiar Contraseña (Primera Vez)
Después del login, se abrirá la pantalla de cambio de contraseña obligatorio:
1. Ingresa nueva contraseña (mínimo 4 caracteres)
2. Confirma la contraseña
3. Haz clic en "Cambiar"

---

## 📋 FUNCIONES PRINCIPALES

### Dashboard
- **Ubicación**: Menú principal (botón "Dashboard")
- **Qué ves**: Resumen de objetivos, equipos, supervisores
- **Para qué**: Vista general del estado del sistema

### Objetivos
- **Crear**: Menú → "Nuevo Objetivo"
- **Editar**: Tabla → Selecciona objetivo → "Editar"
- **Listar**: Menú → "Objetivos"

### Equipos y Supervisores
- **Crear equipo**: Menú → "Nuevo Equipo"
- **Crear supervisor**: Menú → "Nuevo Supervisor"
- **Listar**: Menú → "Equipos" o "Supervisores"

### Reportes
- **Mensual**: Menú → "Reporte Mensual"
- **Por objetivo**: Menú → "Reporte Objetivo"
- **Exportar**: En el reporte → "Exportar a Excel/PDF"

### Configuración
- **Tema**: Botón "☀ Modo claro" / "🌙 Modo oscuro" (arriba derecha)
- **Usuarios**: Menú → "Gestionar Usuarios" (solo admin)
- **Backup**: Menú → "Configuración" → "Hacer Backup"

---

## 🎯 TAREAS COMUNES

### Crear un Objetivo
1. Haz clic en "Nuevo Objetivo"
2. Completa:
   - Nombre del objetivo
   - Fecha de inicio
   - Fecha de fin
   - Días de la semana
3. Haz clic en "Guardar"

### Agregar una Pasada
1. En la tabla, selecciona la fecha
2. Haz clic en "Nueva Pasada"
3. Completa:
   - Hora de pasada
   - Objetivo (dropdown)
   - Supervisor (dropdown)
   - Estado (cumplida/no cumplida)
4. Guarda

### Ver Reporte Mensual
1. Menú → "Reporte Mensual"
2. Selecciona mes y año
3. Haz clic en "Generar Reporte"
4. Para exportar: "Exportar a Excel" o "Exportar a PDF"

### Cambiar Contraseña
1. Menú → "Gestionar Usuarios" → Tu usuario
2. Haz clic en "Cambiar Contraseña"
3. Ingresa contraseña actual
4. Ingresa nueva contraseña (2 veces)
5. Guarda

---

## 🔐 SEGURIDAD

### Reglas de Entrada
- **Usuario**: 3-50 caracteres, solo letras, números y guiones bajos (_)
- **Contraseña**: Mínimo 4 caracteres, máximo 100
- Los espacios en usuario no se permiten

### Ejemplo Válido
```
Usuario: usuario_123 ✅
Contraseña: MiPassword2024 ✅

Usuario: usuario@email.com ❌ (caracteres especiales)
Contraseña: 123 ❌ (muy corta)
```

### Roles y Permisos
| Rol | Permisos |
|-----|----------|
| **Admin** | Control total, gestión de usuarios, backups |
| **Supervisor** | Crear/editar objetivos, equipos, pasadas |
| **Operador** | Ver y registrar pasadas básicas |
| **Auditor** | Solo lectura de todo |
| **Gerente** | Vista ejecutiva y reportes |

---

## 🎨 PERSONALIZACIÓN

### Cambiar Tema
- Botón arriba derecha: "☀ Modo claro" / "🌙 Modo oscuro"
- El tema elegido se guarda automáticamente

### Validar Índices y Caché
- Menú → "Configuración" → "Ver Índices" o "Ver Caché"
- Estos son herramientas avanzadas

---

## 💾 DATOS

### Dónde se Guardan
- **Base de datos**: `C:\Users\[Tu usuario]\VESP Control\seguridad.db`
- **Backups automáticos**: Misma carpeta, nombrados por fecha

### Hacer Backup Manual
1. Menú → "Configuración" → "Hacer Backup"
2. Se crea un archivo con la fecha actual
3. Se guarda en `C:\Users\[Tu usuario]\VESP Control\`

---

## ⌨️ ATAJOS DE TECLADO

| Tecla | Acción |
|-------|--------|
| `Enter` | Completar login / Guardar cambios |
| `Esc` | Cerrar diálogo |
| `Ctrl+E` | Exportar (en reportes) |
| `Ctrl+Q` | Cerrar aplicación |

---

## 🔧 CONFIGURACIÓN RECOMENDADA

- **Temá**: Oscuro (menos cansado para sesiones largas)
- **Frecuencia de backup**: Diaria
- **Sincronización**: Automática (si está habilitada)

---

## 📞 CONTACTO Y SOPORTE

Si tienes problemas:

1. **Revisa TROUBLESHOOTING.md** - Soluciones a problemas comunes
2. **Mira los logs**: Menú → "Configuración" → "Ver Logs"
3. **Contacta al administrador** para problemas de permisos

---

## ✅ CHECKLIST DE PRIMERA SESIÓN

- [ ] Inicie sesión con admin/0000
- [ ] Cambié la contraseña del admin
- [ ] Creé mi usuario o fui agregado por admin
- [ ] Probé crear un objetivo
- [ ] Probé registrar una pasada
- [ ] Vi un reporte
- [ ] Cambié entre tema claro y oscuro
- [ ] Hice un backup manual

---

