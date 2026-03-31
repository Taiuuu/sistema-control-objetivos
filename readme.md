# Sistema de Control de Objetivos
### V.E.S.P Organizations – Seguridad Privada

![Logo](assets/vesp_logo.png)

---

## ¿De qué trata el sistema?

Sistema de escritorio desarrollado para reemplazar el control manual en Excel de objetivos de seguridad privada.

Permite registrar y visualizar en tiempo real qué objetivos fueron controlados durante el día, qué supervisores estaban de turno, cuántas pasadas se realizaron por turno y generar reportes mensuales de cumplimiento.

---

## Instalación

1. Descargá el instalador desde la sección **Releases** del repositorio
2. Ejecutá `VESP_Control_Instalador.exe`
3. Seguí los pasos de instalación
4. Se creará un acceso directo en el escritorio

### Credenciales por defecto
```
Usuario: admin
Contraseña: 0000
```

---

## Funcionalidades

- Control diario de objetivos con estado por turno (día/noche)
- Registro de equipos de turno (dos supervisores por turno)
- Registro de pasadas con filtro automático por equipo de turno
- Tabla principal con colores de estado en tiempo real
- Filtros por turno, supervisor y estado
- Buscador de objetivos en tiempo real
- Notas y observaciones diarias
- Reporte mensual de cumplimiento por objetivo
- Exportación de reportes a Excel y PDF con logo corporativo
- Sistema de usuarios con roles (admin/operador)
- Historial de acciones (logs de auditoría)
- Backup automático diario de la base de datos
- Cierre de sesión automático por inactividad con backup previo
- Auto-actualización desde GitHub
- Atajos de teclado para operaciones frecuentes

---

## Atajos de teclado

| Atajo | Acción |
|-------|--------|
| Ctrl + P | Registrar pasada |
| Ctrl + O | Agregar objetivo |
| Ctrl + S | Agregar supervisor |
| Ctrl + T | Registrar turno |
| Ctrl + N | Notas del día |
| Ctrl + R | Reporte mensual |
| Ctrl + B | Actualizar tabla |
| Ctrl + H | Ayuda |

---

## Reset de fábrica

Para borrar todos los datos y dejar el sistema como nuevo ejecutá desde la carpeta del proyecto:
```bash
python reset_fabrica.py
```

---

## Seguridad

- Contraseñas encriptadas con bcrypt
- Sistema de roles (admin/operador)
- Historial completo de acciones
- Backup automático diario
- Cierre de sesión por inactividad

---

## Tecnologías utilizadas

- Python 3
- PyQt6
- SQLite
- bcrypt
- openpyxl
- reportlab
- requests

---

*Desarrollado para V.E.S.P Organizations – Seguridad Privada*

```
