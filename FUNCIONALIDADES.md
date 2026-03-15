# VESP Organizations
## Sistema de Control de Objetivos
### Versión 0.9.0

---

### Acceso y seguridad
- Pantalla de login con logo corporativo
- Contraseñas encriptadas con bcrypt
- Validación de contraseña fuerte con indicadores visuales en tiempo real
- Sistema de roles: admin y operador
- Cambio de contraseña obligatorio al primer inicio para usuarios nuevos
- Cierre de sesión automático por inactividad con backup previo
- Reset de contraseña por parte del admin
- Versión del sistema visible en pantalla de login

### Gestión de datos
- Alta de objetivos con nombre, fecha de inicio y días de cobertura semanal
- Baja de objetivos con fecha registrada
- Alta y eliminación de supervisores
- Registro de equipos de turno (dos supervisores por turno por día)
- Registro de pasadas con fecha, hora, turno, objetivo y supervisor
- Filtro automático de supervisores por equipo al registrar una pasada
- Edición de pasadas ya registradas
- Eliminación de pasadas registradas por error

### Control diario
- Tabla principal con objetivos del día según fecha y cobertura configurada
- Estado por turno: Pasaron los dos / No pasó día / No pasó noche / No pasó nadie
- Colores en tiempo real: verde / amarillo / rojo
- Equipos de turno visibles directamente en la tabla
- Filtros por turno, supervisor y estado
- Buscador de objetivos en tiempo real

### Notas
- Registro de notas y observaciones por día
- Eliminación de notas

### Reportes
- Reporte mensual de cumplimiento por objetivo
- Días controlados, días sin control y porcentaje
- Porcentaje calculado solo sobre los días de cobertura configurados
- Exportación a Excel con logo corporativo y colores
- Exportación a PDF con logo corporativo y colores

### Usuarios
- Gestión de usuarios: crear, eliminar y resetear contraseña (solo admin)
- Usuario admin protegido contra eliminación
- Nuevos usuarios creados con contraseña 0000 y cambio obligatorio

### Historial y auditoría
- Log de todas las acciones del sistema con usuario, fecha y hora
- Registro de inicios de sesión, pasadas, objetivos, bajas, eliminaciones y ediciones
- Pantalla de historial filtrable por fecha (solo admin)

### Backup
- Backup automático diario al iniciar el programa
- Retención de backups por 30 días con limpieza automática
- Backup automático antes del cierre por inactividad

### Interfaz
- Tema oscuro corporativo
- Menú lateral con todas las funciones organizadas por sección
- Atajos de teclado para operaciones frecuentes
- Pantalla de ayuda con listado de atajos
- Confirmación al cerrar el programa
- Formularios que no se pueden abrir dos veces
- Ícono corporativo en la barra de tareas

### Sistema
- Base de datos SQLite local en un solo archivo
- Script de reset de fábrica
- Notificación automática de nuevas versiones desde GitHub
- Instalador generado con PyInstaller
- Control de versiones con Git y GitHub