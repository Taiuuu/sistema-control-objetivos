# 🚀 ROADMAP DE ESTABILIZACIÓN - VESP Control Objetivos
## Versión Estable v1.1.0

**Objetivo**: Convertir el sistema de "funcional pero frágil" a "producción-ready"  
**Tiempo Estimado**: 3-4 horas de desarrollo  
**Commits Estimados**: 5-7 commits atómicos  

---

## 📊 RESUMEN DE TAREAS

| # | Tarea | Severidad | Status | Esfuerzo |
|---|-------|-----------|--------|----------|
| 1 | ✅ Validación de entrada login | 🔴 CRÍTICA | DONE | 1 hora |
| 2 | Error handling decoradores permisos | 🔴 CRÍTICA | ⏳ PRÓXIMO | 1 hora |
| 3 | Theme switching completo | 🟠 ALTA | ⏳ PRÓXIMO | 45 min |
| 4 | Tests básicos de estabilidad | 🟠 ALTA | ⏳ PRÓXIMO | 1 hora |
| 5 | Documentación de uso y troubleshooting | 🟡 MEDIA | ⏳ PRÓXIMO | 30 min |
| **TOTAL** | | | | **4-4.5 horas** |

---

## 🎯 TAREAS DETALLADAS

### ✅ TAREA 1: Validación de Entrada Login [COMPLETADA]
**Status**: ✅ YA HECHO  
**Archivo**: `ui/login.py`  
**Cambios**:
- ✅ Nueva función `_validar_entrada_login()` con 7 validaciones
- ✅ Integración en método `intentar_login()`
- ✅ Mensajes de error específicos para cada caso

**Resultado**: Login ahora rechaza entradas malformadas antes de conectarse a BD

---

### 2️⃣ TAREA 2: Error Handling en Decoradores de Permisos [PRÓXIMO]
**Status**: ⏳ EN PROGRESO  
**Archivo**: `services/permisos.py`  
**Cambios a Hacer**:
- [ ] Mejorar `@requiere_permiso()` decorator con try-except
- [ ] Agregar logging de intentos fallidos
- [ ] Manejo de sesión expirada en decoradores
- [ ] Tests básicos de decoradores

**Impacto**: Auditoría completa de accesos, mejor debugging

---

### 3️⃣ TAREA 3: Theme Switching Completo [PRÓXIMO]
**Status**: ⏳ PENDIENTE  
**Archivos**: `ui/ventana_principal.py`, `scripts/main.py`  
**Cambios a Hacer**:
- [ ] Método `alternar_tema_global()` en VentanaPrincipal
- [ ] Propagación de cambio a todos los widgets
- [ ] Persistencia del tema elegido
- [ ] Validación visual (ejecutar y cambiar tema)

**Impacto**: UX consistente en cambios de tema

---

### 4️⃣ TAREA 4: Tests Básicos de Estabilidad [PRÓXIMO]
**Status**: ⏳ PENDIENTE  
**Archivos**: `tests/test_estabilidad.py` [NEW]  
**Tests a Implementar**:
- [ ] Test: Validación de entrada login (campos vacíos, largos, caracteres)
- [ ] Test: Decorador de permisos (usuarios sin permisos, sesión expirada)
- [ ] Test: Theme switching (cambios persistentes)
- [ ] Test: Manejo de BD no disponible (graceful degradation)
- [ ] Test: Sesión expirada (timeout de 8 horas)

**Impacto**: Confianza en estabilidad, prevención de regresos

---

### 5️⃣ TAREA 5: Documentación de Uso [PRÓXIMO]
**Status**: ⏳ PENDIENTE  
**Archivos**: `MANUAL_USUARIO.md`, `TROUBLESHOOTING.md` [NEW]  
**Contenido**:
- Guía de inicio rápido (5 minutos)
- Resolución de problemas comunes
- Mejores prácticas de uso
- Contacto de soporte

**Impacto**: Reduce tickets de soporte, mejora experiencia usuario

---

## 📋 ESTÁNDARES DE CÓDIGO PARA CADA FIX

```python
# ESTÁNDAR 1: Siempre incluir docstring Google-style
def mi_funcion(parametro: str) -> bool:
    """
    Descripción breve de qué hace.
    
    Descripción larga si es necesario.
    
    Args:
        parametro: Descripción del parámetro
        
    Returns:
        Descripción de qué retorna
        
    Raises:
        Excepción: Cuándo se lanza
        
    Example:
        >>> resultado = mi_funcion("test")
        >>> print(resultado)
        True
    """
    pass

# ESTÁNDAR 2: Siempre usar type hints
def procesar_datos(usuario_id: int, datos: list[str]) -> dict | None:
    """Procesa datos con type hints."""
    pass

# ESTÁNDAR 3: Loguear acciones críticas
import logging
logger = logging.getLogger(__name__)

def accion_importante():
    try:
        logger.info("Iniciando acción importante")
        # ... código ...
        logger.info("✅ Acción completada exitosamente")
    except Exception as e:
        logger.error(f"❌ Error en acción importante: {e}", exc_info=True)
        raise

# ESTÁNDAR 4: Manejo de excepciones específicas
def conectar_bd():
    try:
        # ... código ...
    except sqlite3.DatabaseError as e:
        logger.error(f"Error BD: {e}")
        # Mostrar error amigable al usuario
    except Exception as e:
        logger.error(f"Error inesperado: {e}", exc_info=True)
        raise

# ESTÁNDAR 5: Validación de entrada
def procesar_usuario(username: str) -> bool:
    # Validación antes de procesar
    if not (3 <= len(username) <= 50):
        raise ValueError("Username debe tener 3-50 caracteres")
    
    if not all(c.isalnum() or c == '_' for c in username):
        raise ValueError("Username solo alfanuméricos y _")
    
    # Procesar...
    return True
```

---

## 🔄 FLUJO DE TRABAJO PARA CADA TAREA

1. **Análisis**: Revisar código existente
2. **Implementación**: Aplicar cambios con estándares
3. **Validación**: Verificar que compila sin errores
4. **Testing**: Probar manualmente si es posible
5. **Commit**: Hacer commit atómico con mensaje claro

---

## 💾 TEMPLATE DE COMMITS

```bash
# Para fixes de bugs
git commit -m "fix(nombre_archivo): Descripción breve

- Cambio específico 1
- Cambio específico 2
- Resultado: qué mejora"

# Para nuevas funcionalidades
git commit -m "feat(nombre_archivo): Descripción breve

- Feature nueva 1
- Feature nueva 2
- Impacto: qué beneficio trae"

# Para refactoring
git commit -m "refactor(nombre_archivo): Descripción breve

- Mejora 1
- Mejora 2
- Beneficio: mantenibilidad, performance, etc"
```

---

## ✅ CHECKLIST FINAL

Después de cada tarea:
- [ ] Código compila sin errores (`python -m py_compile`)
- [ ] Imports funcionan correctamente
- [ ] Docstrings completos (Google-style)
- [ ] Type hints en funciones públicas
- [ ] Logging en rutas críticas
- [ ] Manejo de excepciones específicas
- [ ] Commit con mensaje descriptivo

---

## 🎯 DEFINICIÓN DE "COMPLETADO"

El proyecto estará **ESTABLE Y LISTO PARA PRODUCCIÓN** cuando:

✅ Todas las 5 tareas estén completadas  
✅ 100% de sintaxis validada  
✅ Error handling en todos los puntos críticos  
✅ Logging completo (auditoría + debugging)  
✅ Tests básicos pasando  
✅ Documentación actualizada  
✅ Sin warnings o errores no resueltos  

---

## 📌 PROMPT PARA USAR CONMIGO

Aquí te proporciono el **PROMPT ESTÁNDAR** que puedes copiar y pegar cuando quieras que trabaje en las tareas:

---

### 🚀 PROMPT PARA COPIAR Y PEGAR:

```
Estoy trabajando en estabilizar VESP Control Objetivos siguiendo este ROADMAP:

📊 ROADMAP DE ESTABILIZACIÓN:
- Tarea 1: ✅ Validación entrada login (COMPLETADA)
- Tarea 2: Error handling decoradores permisos
- Tarea 3: Theme switching completo
- Tarea 4: Tests básicos de estabilidad
- Tarea 5: Documentación de uso

ESTÁNDARES DE CÓDIGO:
✅ Docstrings Google-style
✅ Type hints en todas las funciones
✅ Logging en acciones críticas
✅ Excepciones específicas (no genéricas)
✅ Validación de entrada
✅ Mensajes de error amigables al usuario

FLUJO DE TRABAJO:
1. Analizar código existente
2. Implementar cambios con estándares
3. Validar que compila (python -m py_compile)
4. Hacer commit atómico con mensaje descriptivo

ESTOY EN LA TAREA #[número] - [nombre tarea]

Por favor:
1. Implementa los cambios necesarios
2. Valida que todo compila sin errores
3. Haz commit con mensaje descriptivo
4. Pasa a la siguiente tarea
5. Reporta cuando termines

Gracias.
```

---

## 🎓 CÓMO USAR ESTE ROADMAP

1. **Ahora**: Lee este documento y entiende el plan
2. **Pregunta**: Yo te preguntaré "¿Empiezo?"
3. **Responde**: Tú dices "Sí" o "Sí, adelante"
4. **Trabajo**: Yo ejecuto todas las tareas en orden
5. **Reportes**: Yo te actualizo el progreso después de cada tarea
6. **Final**: Cuando terminen las 5 tareas, tendrás versión estable

---

