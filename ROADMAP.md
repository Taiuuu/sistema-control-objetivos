# Roadmap de Desarrollo - Sistema de Control de Objetivos
## V.E.S.P Organizations – Seguridad Privada

**Versión actual**: 1.0.0  
**Última actualización**: Abril 2026  
**Estado**: En planificación de v3.0 (Multi-usuario con sincronización en tiempo real)

---

## 📋 Visión Futura

Transformar el sistema de escritorio en una solución empresarial escalable y modular que permita:
- Operación simultánea desde múltiples equipos
- Sincronización en tiempo real de datos
- Importación automática desde tablets en campo
- Gestión avanzada de datos
- Base sólida para crecimiento empresarial

---

## 🚀 Fase 3.0 - Multi-usuario en Red (Q3-Q4 2026)

### 3.1 Arquitectura Multi-usuario
**Objetivo**: Permitir que múltiples usuarios trabajen simultáneamente desde diferentes PC.

#### Requisitos técnicos
- **Backend centralizado**: Migrar de SQLite local a servidor PostgreSQL/MySQL compartido
- **Autenticación mejorada**: Implementar sistema JWT con sesiones persistentes
- **Sincronización en tiempo real**: WebSockets para notificaciones de cambios
- **Gestión de conexiones**: Pool de conexiones DB, manejo de offline/online

#### Cambios en arquitectura
```
Sistema Actual (Local):
┌─────────────────────────┐
│  PC 1: Aplicación      │
│  ├── SQLite Local       │
│  ├── UI (PyQt6)        │
│  └── Services          │
└─────────────────────────┘

Sistema Futuro (Red):
┌──────────────┐  ┌──────────────┐  ┌──────────────┐
│  PC 1        │  │  PC 2        │  │  PC 3        │
│ Aplicación   │  │ Aplicación   │  │ Aplicación   │
└──────┬───────┘  └──────┬───────┘  └──────┬───────┘
       │                 │                 │
       └─────────┬───────┴────────────────┬┘
                 │                         │
         ┌───────▼─────────┐      ┌───────▼─────────┐
         │  WebSocket      │      │ PostgreSQL      │
         │  Server (Flask) │      │ Central DB      │
         └─────────────────┘      └─────────────────┘
         
         │ Sincronización │       │ Almacenamiento │
         │ Notificaciones │       │ Compartido     │
```

#### Implementación
1. **Migrar SQLite → PostgreSQL**
   - Script de migración de datos
   - Actualizar modelo de conexión
   - Implementar migraciones con Alembic

2. **WebSocket Server (Flask)**
   ```python
   # Nueva arquitectura
   - api/websocket.py        # Servidor WebSocket
   - api/sync_manager.py      # Gestor de sincronización
   - services/db_sync.py      # Sincronización de BD
   ```

3. **Cliente con caché local**
   - Cache local con sincronización periódica
   - Detectar cambios remotos
   - Resolver conflictos automáticamente

---

### 3.2 Control de Acceso Avanzado
**Objetivo**: Roles y permisos granulares para entorno multiusuario.

#### Nuevos roles
- **Administrador**: Control total, gestión de usuarios, auditoría
- **Supervisor de Operaciones**: Gestión de pasadas, reportes
- **Operador**: Solo registro de pasadas asignadas
- **Auditor**: Lectura de auditoría y reportes
- **Gerente**: Reportes ejecutivos, análisis de datos

#### Permisos por rol
```python
PERMISOS = {
    'CREAR_OBJETIVO': ['admin', 'supervisor'],
    'ELIMINAR_PASADA': ['admin', 'supervisor'],
    'ELIMINAR_MASIVO': ['admin'],
    'VER_AUDITORIA': ['admin', 'auditor'],
    'EXPORTAR_REPORTES': ['admin', 'supervisor', 'gerente'],
    'GESTIONAR_USUARIOS': ['admin'],
    'SINCRONIZAR_DATOS': ['admin', 'supervisor']
}
```

#### Implementación
- Tabla `user_roles` en BD
- Tabla `role_permissions` con matriz de permisos
- Decorador `@require_permission('accion')` en servicios
- Validación en cada operación CRUD

---

### 3.3 Sincronización en Tiempo Real
**Objetivo**: Cambios de un usuario reflejados automáticamente en otros.

#### Tecnología
- **WebSockets** (socket.io o raw WebSocket)
- **Event bus** local para cambios
- **Caché compartido** con TTL

#### Flujo de sincronización
```
Usuario A modifica dato
    ↓
Evento capturado en services/
    ↓
WebSocket emite a WebSocket Server
    ↓
Server actualiza PostgreSQL
    ↓
Server notifica a Usuarios B, C, D
    ↓
UI actualiza automáticamente
    ↓
Cache local invalidado
```

#### Eventos a sincronizar
- `pasada_creada`
- `pasada_eliminada`
- `objetivo_modificado`
- `supervisor_actualizado`
- `usuario_conectado`
- `usuario_desconectado`
- `operacion_masiva` (importación, eliminación bulk)

---

## 🔄 Fase 3.1 - Importación desde Excel (Q2-Q3 2026)

### 3.1.1 Estructura del archivo Excel
**Nombre**: `pasadas_yyyy-mm-dd.xlsx` o configurable

**Columnas requeridas**:
| Columna | Tipo | Validación | Ejemplo |
|---------|------|-----------|---------|
| Fecha | DATE | dd/mm/yyyy | 21/04/2026 |
| Supervisor | TEXT | Debe existir en BD | Juan García |
| Objetivo | TEXT | Debe existir en BD | Centro Comercial A |
| Hora | TIME | HH:MM format | 14:30 |
| Turno | TEXT | "diurno" o "nocturno" | diurno |
| Notas | TEXT | Opcional | Revisión perimetral |

**Ejemplo de archivo**:
```
Fecha       | Supervisor    | Objetivo           | Hora  | Turno    | Notas
21/04/2026  | Juan García   | Centro Comercial A | 14:30 | diurno   | Control rutinario
21/04/2026  | María López   | Banco Central      | 22:15 | nocturno | Revisión entrada
22/04/2026  | Juan García   | Centro Comercial A | 03:00 | nocturno | Cierre nocturno
```

---

### 3.1.2 Lógica de Turnos Nocturnos
**Requerimiento crítico**: Turnos que cruzan medianoche deben contabilizarse en el día operativo correcto.

#### Algoritmo de mapeo de turnos nocturnos
```python
def calcular_fecha_operativa(fecha: date, hora: time, turno: str) -> date:
    """
    Calcula la fecha operativa considerando turnos nocturnos.
    
    Turno diurno: 07:00 - 19:00 → Usa fecha tal cual
    Turno nocturno: 19:00 - 07:00 → 
        - Si hora >= 19:00 → fecha actual (ej: 21/04 23:00 = 21/04)
        - Si hora < 07:00 → fecha anterior (ej: 22/04 03:00 = 21/04)
    """
    if turno == 'diurno':
        return fecha
    
    elif turno == 'nocturno':
        if hora >= time(19, 0):  # 19:00 - 23:59
            return fecha
        elif hora < time(7, 0):  # 00:00 - 06:59
            return fecha - timedelta(days=1)
        else:
            raise ValueError(f"Hora {hora} fuera del rango de turno nocturno")
    
    else:
        raise ValueError(f"Turno inválido: {turno}")

# Ejemplos:
# Pasada el 21/04 a las 22:00 turno nocturno → se registra como 21/04 ✓
# Pasada el 22/04 a las 03:00 turno nocturno → se registra como 21/04 ✓
# Pasada el 21/04 a las 14:30 turno diurno → se registra como 21/04 ✓
```

#### Validaciones de turno
- Turno diurno: hora entre 07:00 y 19:00
- Turno nocturno: hora entre 19:00 y 23:59, o 00:00 y 07:00
- Faltan horas: 19:00 - 07:00 próximo día

---

### 3.1.3 Flujo de Importación
**Ubicación**: `ui/importador_excel.py`

#### Pasos

**1. Selección de archivo**
```
┌─────────────────────────────────┐
│ Seleccionar archivo Excel       │
│ [Buscar archivo...]             │
└─────────────────────────────────┘
```

**2. Validación automática**
- Verificar estructura (columnas requeridas)
- Validar fechas (formato dd/mm/yyyy)
- Validar supervisores (existen en BD)
- Validar objetivos (existen en BD)
- Verificar duplicados contra DB existente
- Aplicar lógica de turnos nocturnos

**3. Detección de duplicados**
```python
def detectar_duplicados(pasadas_nuevas: list, fecha_operativa: date) -> dict:
    """
    Compara pasadas nuevas con registros existentes para el día.
    
    Considera duplicado si coinciden:
    - fecha_operativa
    - supervisor_id
    - objetivo_id
    - hora (±5 minutos de tolerancia)
    """
    pasadas_existentes = DB.query_pasadas(fecha_operativa)
    
    duplicados = []
    nuevas = []
    
    for pasada_nueva in pasadas_nuevas:
        encontrado = False
        for pasada_existe in pasadas_existentes:
            if (pasada_nueva.supervisor_id == pasada_existe.supervisor_id and
                pasada_nueva.objetivo_id == pasada_existe.objetivo_id and
                abs(pasada_nueva.hora - pasada_existe.hora) <= timedelta(minutes=5)):
                duplicados.append({
                    'existente': pasada_existe,
                    'nueva': pasada_nueva,
                    'accion': 'skip'  # Por defecto saltar
                })
                encontrado = True
                break
        
        if not encontrado:
            nuevas.append(pasada_nueva)
    
    return {
        'nuevas': nuevas,
        'duplicados': duplicados,
        'total_importar': len(nuevas),
        'total_duplicados': len(duplicados)
    }
```

**4. Vista previa**
```
┌────────────────────────────────────────────┐
│ Vista Previa - 45 registros a importar     │
├────────────────────────────────────────────┤
│ ✓ 40 registros nuevos                      │
│ ⚠️ 5 registros duplicados (acción: skip)   │
│ ✗ 0 registros con error                    │
│                                            │
│ Supervisor: Juan García (10 registros)     │
│ Supervisor: María López (8 registros)      │
│ Objetivo: Centro Comercial A (12 registros)│
│ Objetivo: Banco Central (15 registros)     │
│                                            │
│ [Importar]  [Ver duplicados]  [Cancelar]  │
└────────────────────────────────────────────┘
```

**5. Confirmación**
- Opción: "Reemplazar duplicados" o "Saltar"
- Opción: "Combinar datos" (mantener ambos si son de distinta hora)
- Confirmación de seguridad con contraseña para cambios masivos

**6. Auditoría**
```python
registrar_auditoria(
    usuario_id=usuario.id,
    accion='IMPORTAR_EXCEL',
    detalles={
        'archivo': 'pasadas_2026-04-21.xlsx',
        'total_registros': 45,
        'registros_nuevos': 40,
        'duplicados_saltados': 5,
        'fecha_inicio': '2026-04-21',
        'fecha_fin': '2026-04-22'
    },
    timestamp=datetime.now()
)
```

---

### 3.1.4 Importador desde Tablets
**Concepto**: App móvil o web que sincroniza con Excel local.

**Flujo tablet → Excel → Sistema**:
```
1. Supervisor en tablet:
   - Selecciona Objetivo
   - Ingresa su nombre (o se carga automático)
   - Registra hora
   - Selecciona turno

2. Se guarda en Excel local:
   - Sincroniza cuando hay conexión
   - Almacena localmente si está offline

3. Excel se importa a Sistema Central:
   - Usuario carga el archivo
   - Sistema valida y detecta duplicados
   - Confirma importación

4. Datos se sincronizan a todas las PC:
   - WebSocket notifica cambios
   - Usuarios ven datos actualizados
```

#### Estructura de datos en tablet (Excel)
```json
{
  "sesion_id": "tablet_001_2026-04-21",
  "dispositivo": "Tablet Samsung",
  "supervisor": "Juan García",
  "pasadas": [
    {
      "timestamp": "2026-04-21T14:35:00",
      "objetivo": "Centro Comercial A",
      "turno": "diurno",
      "notas": "Control entrada norte"
    },
    {
      "timestamp": "2026-04-21T22:15:00",
      "objetivo": "Banco Central",
      "turno": "nocturno",
      "notas": "Cierre seguro"
    }
  ]
}
```

---

## 🗑️ Fase 3.2 - Gestión Masiva de Datos (Q3 2026)

### 3.2.1 Funcionalidad de Eliminación Masiva
**Ubicación**: `ui/gestor_datos.py` (nuevo)

#### Opciones de eliminación
```
┌─────────────────────────────────────┐
│ Gestor de Datos - Eliminar          │
├─────────────────────────────────────┤
│                                     │
│ ☐ Eliminar pasadas de un día       │
│   Fecha: [21/04/2026]              │
│   Total a eliminar: 12 registros   │
│                                     │
│ ☐ Eliminar pasadas de un mes       │
│   Mes: [Abril 2026]                │
│   Total a eliminar: 287 registros  │
│                                     │
│ ☐ Eliminar por objetivo            │
│   Objetivo: [Centro Comercial A]   │
│   Rango fechas: [21/04] - [30/04]  │
│   Total a eliminar: 45 registros   │
│                                     │
│ ☐ Eliminar por supervisor          │
│   Supervisor: [Juan García]        │
│   Rango fechas: [21/04] - [30/04]  │
│   Total a eliminar: 23 registros   │
│                                     │
│ [Eliminar]  [Cancelar]             │
└─────────────────────────────────────┘
```

#### Confirmación de seguridad
```
⚠️ CONFIRMACIÓN DE SEGURIDAD

Está a punto de eliminar 12 registros de pasadas
del día 21/04/2026

Esta acción NO PUEDE DESHACERSE.

Se creará registro de auditoría.

Usuario: Juan García (Admin)
Motivo: [Archivo duplicado importado]

Ingresa tu contraseña para confirmar:
[●●●●●●●●]

[CONFIRMAR ELIMINACIÓN]  [CANCELAR]
```

#### Auditoría de eliminación
```python
registrar_auditoria(
    usuario_id=usuario.id,
    accion='ELIMINAR_PASADAS_MASIVO',
    detalles={
        'tipo': 'por_dia',
        'fecha': '2026-04-21',
        'total_eliminadas': 12,
        'motivo': 'Archivo duplicado importado',
        'supervisor_afectados': ['Juan García', 'María López'],
        'objetivos_afectados': ['Centro Comercial A']
    },
    timestamp=datetime.now(),
    ip_origen='192.168.1.100'
)
```

---

### 3.2.2 Prevención de Duplicados en Importación
**Ubicación**: `services/importador_excel.py`

#### Estrategias
1. **Detección por hash**
   - Crear hash de (supervisor, objetivo, fecha_operativa, hora)
   - Comparar con hashes existentes
   - Marca como duplicado si coincide

2. **Ventana de tolerancia**
   - Pasadas con ±5 min de diferencia = duplicadas
   - Configurable por usuario

3. **Merge inteligente**
   - Si hay duplicados parciales, ofrecer combinar
   - Ej: misma pasada con notas diferentes = tomar notas más recientes

---

## 🔐 Fase 3.3 - Seguridad Avanzada (Q4 2026)

### 3.3.1 Auditoría completa
Debe registrarse:
- **Quién**: usuario_id
- **Qué**: acción (crear, editar, eliminar, importar, etc.)
- **Cuándo**: timestamp exacto
- **Dónde**: ip_origen, dispositivo
- **Por qué**: motivo (opcional pero recomendado)
- **Antes y después**: snapshot de datos modificados

### 3.3.2 Respaldo automático
- Backup diario con timestamp
- Replicación en servidor secundario
- Punto de restauración por día

---

## 📊 Estimación de Esfuerzo

| Fase | Feature | Horas | Complejidad |
|------|---------|-------|------------|
| 3.0 | Arquitectura PostgreSQL | 40 | Alta |
| 3.0 | WebSocket Server | 30 | Alta |
| 3.0 | Sincronización cliente | 35 | Alta |
| 3.0 | Control de acceso | 25 | Media |
| 3.1 | Importador Excel | 30 | Media |
| 3.1 | Validación de turnos | 15 | Media |
| 3.1 | Detección duplicados | 20 | Media |
| 3.1 | Integración tablet | 50 | Alta |
| 3.2 | Gestión masiva | 20 | Baja |
| 3.3 | Auditoría avanzada | 25 | Media |
| **Total** | | **290** | - |

**Estimación total**: ~7-8 meses de desarrollo (con equipo de 2 personas)

---

## 🎯 Prioridades Recomendadas

### 🔴 Crítica (Bloquea otras features)
1. Migración a PostgreSQL
2. WebSocket Server
3. Control de acceso

### 🟠 Alta (Valor empresarial)
4. Importación desde Excel
5. Sincronización en tiempo real
6. Lógica de turnos nocturnos

### 🟡 Media (Mejora UX)
7. Gestión masiva de datos
8. Integración tablet
9. Auditoría avanzada

### 🟢 Baja (Polish)
10. Detección automática de duplicados en UI
11. Vista previa mejorada
12. Reportes de importación

---

## 📝 Notas técnicas

### Consideraciones de rendimiento
- Sincronización: batching de eventos cada 500ms
- Caché: TTL de 5 minutos para consultas frecuentes
- Índices: agregar índices en fecha, usuario, objetivo
- Conexiones: pool de 20 conexiones concurrentes

### Compatibilidad backward
- Sistema actual seguirá funcionando localmente
- Migración gradual a PostgreSQL
- API REST compatible

### Testing
- Unit tests para lógica de turnos nocturnos (crítico)
- Integration tests para importación Excel
- Load tests para sincronización
- Cobertura mínima: 80%

---

**Documento actualizado**: Abril 22, 2026  
**Próxima revisión**: Junio 2026  
**Responsable**: Equipo de desarrollo
