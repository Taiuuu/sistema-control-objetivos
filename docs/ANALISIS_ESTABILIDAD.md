# Análisis de Estabilidad - VESP Control de Objetivos

**Fecha**: 2025-01-XX  
**Status**: 🔴 CRÍTICO - Problemas identificados  
**Prioridad**: ALTA  

## 📋 Resumen Ejecutivo

Sistema compila sin errores pero tiene **deficiencias críticas en error handling** que pueden causar crashes en producción. Identificados 12 problemas de estabilidad, de los cuales 5 son **críticos**.

---

## 🔴 PROBLEMAS CRÍTICOS (Deben Solucionarse Inmediatamente)

### 1. **scripts/main.py - Sin Error Handling en Inicialización**
**Severidad**: 🔴 CRÍTICA  
**Ubicación**: `iniciar_app()` líneas 115-142  
**Problema**:
```python
def iniciar_app():
    crear_base_datos()        # ❌ Si falla, app crashea
    migrar_supervisor3()      # ❌ Si falla, app crashea
    migrar_supervisores_alta_baja()  # ❌ Si falla, app crashea
    hacer_backup()            # ❌ Si falla, app crashea
    iniciar_api_rest()        # ❌ Si falla, app crashea
    app = QApplication(...)   # ❌ Si algo falló, app nunca llega aquí
```
**Impacto**: Si cualquier inicialización falla, la app no arranca en absoluto.  
**Solución**: Wrappear en try-except con logging y fallback graceful.

### 2. **ui/login.py - Vulnerability en bcrypt**
**Severidad**: 🔴 CRÍTICA  
**Ubicación**: `verificar_login()` líneas 27-46  
**Problema**:
```python
try:
    if bcrypt.checkpw(password.encode(), resultado[3].encode()):
        return (resultado[0], resultado[1], resultado[2])
except Exception:
    pass  # ❌ Silencia CUALQUIER error - posible intrusión
return None
```
**Impacto**: 
- Errores de validación bcrypt quedan ocultos
- Un atacante podría explotar esto
- No se loguean intentos de ataque

**Solución**: Diferenciar entre errores legítimos y de seguridad. Loguear intentos fallidos.

### 3. **ui/login.py - Race Condition en _login_post_cambio()**
**Severidad**: 🔴 CRÍTICA  
**Ubicación**: `_login_post_cambio()` líneas 186-192  
**Problema**:
```python
def _login_post_cambio(self, usuario_id: int) -> None:
    conexion = sqlite3.connect(DB_PATH)
    cursor = conexion.cursor()
    cursor.execute("SELECT rol FROM usuarios WHERE id = ?", (usuario_id,))
    rol = cursor.fetchone()[0]  # ❌ Podría ser None si usuario fue eliminado
    conexion.close()
    self.on_login_exitoso(usuario_id, rol)
    self.close()
```
**Impacto**: Si el usuario es eliminado entre cambio de password y este llamado, app crashea con `TypeError: 'NoneType' object is not subscriptable`.

**Solución**: Validar que `fetchone()` retorna algo.

### 4. **services/sesion.py - Sin Validación de Estado**
**Severidad**: 🔴 CRÍTICA  
**Ubicación**: `get_usuario_id()`, `get_rol()` - líneas 105-119  
**Problema**: Funciones retornan valores sin validar si sesión está iniciada correctamente.

**Impacto**: Código cliente puede usar valores None sin saber que sesión está inválida.

**Solución**: Agregar función de validación central.

### 5. **ui/ventana_principal.py - Cargar tabla sin error handling**
**Severidad**: 🔴 CRÍTICA  
**Ubicación**: Método `cargar_tabla()` no revisado aún  
**Problema**: Método presumiblemente carga datos sin try-except.

**Impacto**: Si BD está corrupta o hay conexión fallida, UI se congela.

**Solución**: Wrappear en try-except, mostrar error al usuario.

---

## 🟠 PROBLEMAS ALTOS (Deben Solucionarse Pronto)

### 6. **database/db.py - Sin Rollback en Migraciones**
**Severidad**: 🟠 ALTA  
**Ubicación**: `migrar_supervisor3()`, `migrar_supervisores_alta_baja()` - líneas 144-168  
**Problema**:
```python
def migrar_supervisor3():
    conexion = conectar()
    cursor = conexion.cursor()
    try:
        cursor.execute(...)
        conexion.commit()  # ✅ Bien
    except sqlite3.OperationalError:
        pass  # ❌ No hace rollback explícito
    conexion.close()
```
**Impacto**: Si migración falla parcialmente, BD queda en estado inconsistente.

**Solución**: Agregar rollback explícito y logging.

### 7. **ui/login.py - Sin Validación de Entrada**
**Severidad**: 🟠 ALTA  
**Ubicación**: `intentar_login()` línea 175  
**Problema**:
```python
username = self.input_usuario.text().strip()
password = self.input_password.text()
if not username or not password:
    QMessageBox.warning(...)
    return
# ❌ No valida largos máximos, caracteres especiales, SQL injection
```
**Impacto**: Aunque parametrizado (bien), no hay validación de integridad.

**Solución**: Agregar validación de entrada.

### 8. **services/permisos.py - Decoradores sin Validación de Función**
**Severidad**: 🟠 ALTA  
**Ubicación**: Decoradores `@requiere_permiso`, etc. - no revisado aún  
**Problema**: Si decorador falla, función nunca ejecuta pero tampoco hay feedback claro.

**Solución**: Agregar error handling en decoradores.

---

## 🟡 PROBLEMAS MEDIOS (Mejoras de Usabilidad)

### 9. **ui/ventana_principal.py - Método actualizar_tema() Incompleto**
**Severidad**: 🟡 MEDIO  
**Problema**: BotonMenu tiene método `actualizar_tema()` pero no se sabe si se propaga a toda la UI.

**Solución**: Validar que theme switch funciona completamente.

### 10. **services/logger.py - Logging sin Límite de Tamaño**
**Severidad**: 🟡 MEDIO  
**Problema**: Logs podrían crecer sin límite en pruebas largas.

**Solución**: Implementar log rotation.

### 11. **ui/widgets/ - Builder Pattern Incompleto**
**Severidad**: 🟡 MEDIO  
**Problema**: Builders existen pero no se usan en ventana_principal.py.

**Solución**: Refactorizar ventana_principal para usar builders.

### 12. **database/db.py - Índices sin Análisis EXPLAIN**
**Severidad**: 🟡 MEDIO  
**Problema**: Muchos índices pero no sabemos cuáles se usan realmente.

**Solución**: Hacer análisis de consultas lentas.

---

## 📊 Plan de Remediación

### Fase 1: Crítica (Hoy)
- [ ] Agregar error handling en `scripts/main.py::iniciar_app()`
- [ ] Arreglar bcrypt exception en `ui/login.py::verificar_login()`
- [ ] Arreglar None validation en `ui/login.py::_login_post_cambio()`
- [ ] Validación de sesión en `services/sesion.py`
- [ ] Error handling en `ui/ventana_principal.py::cargar_tabla()`

### Fase 2: Alta (Esta semana)
- [ ] Agregar rollback en migraciones
- [ ] Validación de entrada en login
- [ ] Error handling en decoradores de permisos
- [ ] Testeo de theme switching

### Fase 3: Media (Próximas semanas)
- [ ] Completar refactorización con builders
- [ ] Log rotation
- [ ] Análisis de índices

---

## 🎯 Recomendaciones Inmediatas

1. **NO usar la app en producción** hasta arreglar problemas críticos
2. **Crear suite de tests básicos** para casos de error
3. **Agregar logging comprehensivo** en todas las funciones críticas
4. **Validar manualmente** los 5 casos críticos identificados

---

## 📝 Nota del Revisor

El código es funcional y bien estructurado, pero **carece de robustez ante errores**. En un ambiente de producción con datos sensibles (seguridad privada), esto es un riesgo.

La refactorización de arquitectura es excelente (builders, decoradores, RBAC), pero debe complementarse con error handling profesional.

