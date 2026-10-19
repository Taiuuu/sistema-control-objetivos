
# 📖 MANUAL DE USUARIO - VESP Organizations

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

- Ingresá con las credenciales que te asignó la administración.
- La ventana es fija y se centra en la pantalla. Presioná **Entrar** o la tecla `Enter`.
- Si la aplicación solicita cambiar la contraseña, completá el formulario para continuar.

Después de iniciar sesión se abre **Inicio**, con accesos a las secciones disponibles para
tu rol.

---

## 📋 FUNCIONES PRINCIPALES

### Inicio y menú lateral

**Inicio** es la pantalla de entrada después del login. Sus tarjetas muestran accesos según
tu rol y las funciones visibles que tengas seleccionadas. El menú lateral agrupa las
secciones de operación diaria, objetivos y supervisores, reportes, importación y datos, y
administración. **Configuración** es una única opción al pie del menú.

### Control diario

- **Ubicación**: **Inicio** o menú lateral → "Control diario"
- **Qué ves**: Resumen de objetivos, equipos, supervisores
- **Para qué**: Vista general del estado del sistema
- **Filtros**: fecha y búsqueda están visibles. Supervisor, turno y estado están en
  **Más filtros**, que indica cuántos filtros adicionales están activos; usá el botón
  **Limpiar filtros** para restablecerlos.

### Objetivos

- **Crear**: "Agregar objetivo" en la pantalla **Ver objetivos** o el acceso correspondiente en **Inicio**
- **Listar**: menú lateral → "Ver objetivos"
- **Consultar**: las pestañas **Objetivos actuales**, **Objetivos finalizados** y **Todos** filtran la tabla; **Objetivos actuales** se abre por defecto
- **Editar**: seleccioná el objetivo en la tabla y elegí la acción de edición
- **Dar de baja**: abrí el menú contextual del objetivo y elegí **Dar de baja**; confirmá la acción en el diálogo que muestra el nombre del objetivo

### Equipos y Supervisores

- **Crear supervisor**: menú lateral → "Agregar supervisor"
- **Listar**: menú lateral → "Ver supervisores"
- Las opciones disponibles dependen del rol. Los equipos se administran desde las pantallas y permisos que tenga habilitados tu cuenta.

### Registros históricos incompletos

- Los registros marcados **Incompleto** conservan el ID usado por pasadas históricas, pero su ficha original no pudo recuperarse.
- No se ofrecen para nuevas pasadas. Editalos solo cuando puedas confirmar sus datos reales; al guardar una ficha corregida vuelve a estar disponible.
- No se pueden eliminar objetivos o supervisores que tengan historial asociado. Para retirarlos del uso, dales de baja.

### Reportes

- **Mensual**: Menú → "Reporte Mensual"
- **Por objetivo**: Menú → "Reporte Objetivo"
- **Detalle diario**: Menú → "Lista de pasadas", seleccioná el día
- **Exportar**: en cualquiera de esas pantallas, usá **Exportar**; abre el mismo diálogo y
  toma los filtros ya aplicados

#### Elegir y generar un informe

1. Abrí **Reporte Mensual**, **Reporte Objetivo** o **Lista de pasadas** y establecé los
   filtros de la pantalla. En Lista de pasadas elegí la fecha que querés incluir.
2. Presioná **Exportar**. En el diálogo **Exportar**, ajustá el
   período: mes, rango de fechas o día. El resumen mensual exige el mes calendario completo;
   el reporte por objetivo exige un mes completo y un solo objetivo.
3. Elegí todos los objetivos o una selección (podés buscarlos), todos o algunos
   supervisores, equipo y turnos Día/Noche. Los valores iniciales reflejan los filtros
   vigentes en la pantalla.
4. Marcá las columnas que querés incluir y usá **Subir**/**Bajar** para cambiar el orden.
   Elegí resumen, detalle o ambos; indicá si querés totales y notas diarias; seleccioná una
   agrupación si corresponde.
5. Elegí Excel, PDF o ambos y presioná **Actualizar vista previa**. Se muestra una muestra
   de hasta 100 filas y el total. Si cambiás opciones después, volvé a actualizarla antes
   de continuar. Sin datos no se genera un archivo.
6. Presioná **Continuar**, elegí la ubicación y esperá la generación. No se sobrescribe un
   archivo existente. Si el archivo está abierto en Excel o un visor, cerralo o elegí otro
   nombre. Al finalizar podés seleccionar **Abrir archivo** o **Abrir carpeta**.

#### Plantillas y contenido de los archivos

- Para reutilizar opciones, escribí un nombre en **Nombre de plantilla** y presioná
  **Guardar plantilla**. Luego seleccionala y elegí **Usar plantilla**. Las plantillas se
  guardan en la configuración local de la aplicación.
- En Excel, **Resumen** contiene las filas principales y su total; **Detalle** aparece
  cuando se pidió el detalle; **Parámetros** enumera filtros, criterio de conteo, fecha de
  generación, usuario y versión de aplicación.
- En PDF, el encabezado identifica empresa, informe, período y filtros; las tablas repiten
  sus encabezados al paginar, incluyen totales/subtotales elegidos y el pie muestra número
  de página y fecha/hora de generación. Se usa A4 vertical u horizontal según las columnas.
- La lista de pasadas exporta detalle diario. No hay una pantalla separada de reporte diario.
- La exportación registra usuario, filtros, informe y archivo en auditoría. No altera las
  pasadas ni otros datos de negocio; el registro de auditoría sí se agrega intencionalmente.

### Configuración

- Abrí la única opción **Configuración** en la parte inferior del menú lateral.
- **Temas**: elegí Claro, Verde, Negro o Grafito. El cambio se aplica sin reiniciar y cada
  tema muestra el logo correspondiente. En esta pestaña también podés ajustar el tamaño de
  letra y activar **Reducir animaciones**.
- **Funciones visibles**: elegí qué accesos mostrar en el menú. Solo se oculta el acceso;
  no cambian los permisos, los datos ni el registro de auditoría. Las opciones disponibles
  respetan tu rol.
- **Backups y datos**: creá o restaurá copias verificadas y configurá, si corresponde, una
  ubicación externa.
- **Cuenta**: cambiá la contraseña de tu usuario.
- **Acerca de**: muestra el nombre y propósito de la aplicación.
- **Atajos de teclado**: abrí el botón de ayuda en **Funciones visibles** o presioná `F1`.

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

| Campo      | Ejemplo válido     | Ejemplo no válido                           |
| ------     | --------------     | -----------------                           |
| Usuario    | `usuario_123`      | `usuario@email.com` (caracteres especiales) |
| Contraseña | `MiPassword2024`   |  `123` (muy corta)                          |

### Roles y Permisos

| Rol            | Permisos                                                      |
| -------------- | ------------------------------------------------------------- |
| **Admin**      | Control total, gestión de usuarios y backups.                 |
| **Supervisor** | Crear y editar objetivos, equipos y pasadas.                  |
| **Operador**   | Ver y registrar pasadas básicas.                              |
| **Auditor**    | Acceso de solo lectura a toda la información.                 |
| **Gerente**    | Vista ejecutiva y acceso a reportes.                          |

---

## 🎨 PERSONALIZACIÓN

### Cambiar Tema

- En **Configuración** → **Temas**, elegí Claro, Verde, Negro o Grafito.
- El tema elegido se guarda y se aplica inmediatamente en la aplicación.
- No hay un interruptor separado de modo oscuro/claro.

### Validar Índices y Caché

- Menú → "Administración" → "Optimización de BD" (solo admin)
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

La lista completa está en **Configuración** → **Funciones visibles** → **Atajos de teclado**;
podés abrirla desde cualquier pantalla con `F1` o `Ctrl+H`.

| Tecla         | Acción                            |
| ------------- | --------------------------------  |
| `Ctrl+F` | Enfocar el buscador de la pantalla actual, cuando exista. |
| `Ctrl+E` | Abrir las opciones de exportación en pantallas compatibles. |
| `Ctrl+N` | Crear un registro en pantallas que admiten altas, como pasadas y objetivos. |
| `F5` | Actualizar la pantalla actual; en reportes vuelve a generarlos. |
| `Esc` | Limpiar la búsqueda si contiene texto; si no, cerrar la ventana actual. |
| `Ctrl+1` a `Ctrl+9` | Abrir una de las primeras nueve opciones visibles del menú. |
| `F1` o `Ctrl+H` | Abrir la ayuda y la tabla completa de atajos. |
| `Ctrl+P` | Registrar una pasada desde la ventana principal. |
| `Ctrl+O` | Agregar un objetivo desde la ventana principal. |
| `Ctrl+S` | Agregar un supervisor desde la ventana principal. |
| `Ctrl+T` | Registrar un turno desde la ventana principal. |
| `Ctrl+R` | Abrir el reporte mensual desde la ventana principal. |
| `Ctrl+B` | Volver al control diario y actualizarlo. |
| `Ctrl+Enter` | Generar el reporte mensual o por objetivo. |
| `Ctrl+=` / `Ctrl+-` | Aumentar o reducir el tamaño de letra. |
| `Ctrl+←` / `Ctrl+→` | Ir al día anterior o siguiente en el control diario. |
| `Ctrl+\` | Contraer o expandir el menú lateral. |

Los atajos de acción se ignoran mientras el foco está en un campo de texto para no
interrumpir la escritura. Los atajos contextuales se aplican solo a las pantallas que
ofrecen la acción; los tooltips indican los atajos disponibles.

---

## 🔧 CONFIGURACIÓN

- **Inicio**: muestra accesos grandes a las secciones permitidas para tu rol.
- **Funciones visibles**: elegí qué accesos aparecen en el menú; ocultar una opción no
  cambia permisos ni desactiva registros de auditoría.
- **Objetivos**: usá las pestañas actuales/finalizados/todos para elegir qué objetivos ver.
- **Configuración**: concentra Temas, Funciones visibles, Backups y datos, Cuenta y Acerca de.
- **Atajos**: consultá la tabla en Configuración o presioná `F1`.

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
- [ ] Elegí un tema desde Configuración
- [ ] Hice un backup manual

---
