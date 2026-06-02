# 🔄 Mapeo Automático de Supervisores en Importación

## ✨ Nueva Funcionalidad

Se agregó el mapeo automático de supervisores durante la importación de archivos Excel, igual que funciona con los objetivos. Ahora puedes:

1. **Detectar automáticamente** todos los supervisores que aparecen en tu archivo
2. **Clasificarlos** en "encontrados" (que existen en la BD) y "nuevos" (que necesitan ser creados)
3. **Resolver supervisores faltantes** mediante un diálogo intuitivo
4. **Mapear automáticamente** todos los supervisores durante la importación

---

## 🎯 Cómo Funciona

### Paso 1: Seleccionar Archivo
- Abre "📥 Importar Excel" en el menú principal
- Selecciona tu archivo Excel
- Se detectan automáticamente todas las hojas y registros

### Paso 2: Previsualización
El sistema ahora detecta y muestra:
- **Objetivos detectados**: Los objetivos que aparecen en el archivo
- **Supervisores detectados**: Los supervisores que aparecen en el archivo

Ejemplo:
```
Objetivos detectados: 5
  - RECORRIDO_NORTE
  - RECORRIDO_SUR
  - MANTENIMIENTO
  - LIMPIEZA
  - INSTALACION

Supervisores detectados: 3
  - JUAN PEREZ
  - MARIA GARCIA
  - CARLOS LOPEZ
```

### Paso 3: Resolver Supervisores (Igual que Objetivos)
Si aparecen supervisores que no existen en tu BD:

1. El botón "Resolver supervisores" se muestra en rojo
2. Haz click en "🔧 Resolver supervisores"
3. Se abre un diálogo donde puedes:
   - **Mapear a supervisor existente**: Selecciona de la lista de supervisores en tu BD
   - **Crear nuevo supervisor**: Selecciona "-- Crear nuevo --" y escribe el nombre
   - **Búsqueda rápida**: Escribe para buscar supervisores (autocomplete)

Ejemplo del diálogo:
```
Supervisor en archivo          | Acción
JUAN PEREZ                     | ✓ JUAN PEREZ (existe)
MARIA GARCIA                   | ✓ MARIA GARCIA (existe)
CARLOS LOPEZ                   | ✓ CARLOS LOPEZ (existe)
```

### Paso 4: Importar
- Una vez resueltos todos los supervisores y objetivos
- El botón "Importar datos" se habilita
- Haz click para importar
- El sistema usa los mapeos automáticamente

---

## 📋 Flujo Completo

```
Seleccionar Excel
    ↓
Detectar objetivos y supervisores
    ↓
¿Hay objetivos no encontrados?
├─ SI → Resolver objetivos → ¿Resueltos?
│                                ├─ NO → Esperar
│                                └─ SI → Continuar
└─ NO → Continuar
    ↓
¿Hay supervisores no encontrados?
├─ SI → Resolver supervisores → ¿Resueltos?
│                                  ├─ NO → Esperar
│                                  └─ SI → Continuar
└─ NO → Continuar
    ↓
✓ Botón "Importar" habilitado
    ↓
Importar con mapeos automáticos
```

---

## 🔍 Detección Automática

El sistema detecta supervisores de:
- **Columna "SUPERVISOR"** en los bloques de CONTROL_RECORRIDOS
- Busca en todos los registros del archivo
- Elimina duplicados automáticamente
- Normaliza nombres para buscar coincidencias

---

## 📝 Ejemplo Práctico

### Escenario: Importar archivo con supervisores nuevos

**Archivo contiene**:
- JUAN PEREZ (existe)
- MARIA GARCIA (existe)
- LUIS TORRES (nuevo - no existe)

**Proceso**:
1. Abro "Importar Excel"
2. Selecciono archivo
3. Se detectan 3 supervisores
4. El sistema identifica que "LUIS TORRES" no existe
5. Botón "Resolver supervisores" se habilita (en rojo)
6. Hago click en "Resolver supervisores"
7. Se abre diálogo:
   ```
   JUAN PEREZ     → JUAN PEREZ (existe)
   MARIA GARCIA   → MARIA GARCIA (existe)
   LUIS TORRES    → [-- Crear nuevo --] (escribo "LUIS TORRES")
   ```
8. Confirmo el diálogo
9. Se crea "LUIS TORRES" en la BD automáticamente
10. Ahora puedo importar los datos
11. Todas las pasadas se asignan correctamente

---

## 🎨 Interfaz de Usuario

### Panel de Estado de Supervisores
Se agregó una nueva sección en la pantalla de importación:

```
┌─────────────────────────────────────────┐
│ Supervisores detectados: 3              │  [🔧 Resolver supervisores]
└─────────────────────────────────────────┘
```

El estado cambia según el estado de resolución:

- **Gris** (`color: #d0d0d0`): Todos resueltos
  ```
  Supervisores detectados: 3
  ```

- **Amarillo** (`color: #ffb74d`): Hay pendientes
  ```
  Supervisores pendientes de resolución: 1
  ```

- **Verde** (`color: #8affc1`): Todos resueltos (después de resolver)
  ```
  Todos los supervisores pendientes fueron resueltos.
  ```

- **Rojo** (`color: #ff8a80`): Error al resolver
  ```
  Faltan 1 supervisores por resolver.
  ```

### Lista de Supervisores No Resueltos
Como con los objetivos, se muestra una lista de supervisores que aún no se han resuelto:

```
┌────────────────────────────────────┐
│ Supervisores no encontrados en BD: │
├────────────────────────────────────┤
│ • LUIS TORRES                      │
│ • PEDRO SANCHEZ                    │
└────────────────────────────────────┘
```

---

## 🔐 Validaciones

El diálogo de resolver supervisores valida:

✓ **Nombre requerido**: Si seleccionas "Crear nuevo", debe completar el nombre  
✓ **Supervisores existentes**: Los datos se buscan en tu BD  
✓ **Autocomplete**: Sugiere supervisores mientras escribes  
✓ **Mapeo completo**: Todos los supervisores deben tener un mapeo antes de importar

---

## 🔗 Relación con Objetivos

El sistema de supervisores **funciona exactamente igual** que el de objetivos:

| Aspecto | Objetivos | Supervisores |
|---------|-----------|--------------|
| Detección | ✓ | ✓ |
| Listado de no resueltos | ✓ | ✓ |
| Diálogo de mapeo | ✓ | ✓ |
| Crear nuevos | ✓ | ✓ |
| Auto-búsqueda | ✓ | ✓ |
| Importación automática | ✓ | ✓ |

---

## ⚙️ Cambios Técnicos

### Archivos Modificados

**ui/importar_excel.py**:
- ✅ Agregada clase `DialogoResolverSupervisores`
- ✅ Agregadas variables: `_detected_supervisores`, `supervisor_mapeo`, `unresolved_supervisores`
- ✅ Agregado botón "Resolver supervisores"
- ✅ Agregado método `_resolver_supervisores()`
- ✅ Agregado método `_actualizar_supervisores_no_resueltos()`
- ✅ Actualizado manejo de preview para detectar supervisores
- ✅ Actualizado ImportWorker para pasar `supervisor_mapeo`
- ✅ Importada función `listar_supervisores` y `agregar_supervisor`

**services/importador_universal.py**:
- ✅ Ya soporta `supervisor_mapeo` como parámetro
- ✅ Detecta automáticamente supervisores en preview
- ✅ Usa el mapeo durante la importación

---

## ✅ Validación

- ✓ Sin errores de sintaxis Python
- ✓ Interfaz completa y funcional
- ✓ Diálogos intuitivos
- ✓ Flujo consistente con objetivos
- ✓ Importación de supervisores integrada

---

**Versión**: 1.5.2+ - Mapeo Automático de Supervisores  
**Estado**: ✅ Listo para Usar  
**Compatibilidad**: 100% con importador universal existente
