Última actualización: 2026-10-19

Propósito: orientar a Copilot hacia el contexto del área antes de editar código.
Este índice resume límites observados; los archivos enlazados son la referencia detallada.

Archivos clave:
- [docs/contexts/](.) — Contextos funcionales mantenidos junto al código.

| Si la tarea trata de... | Leé este archivo |
|---|---|
| Importar Excel, conciliar, corregir o auditar filas | [importador.md](./importador.md) |
| Fecha operativa, turno, mes, conteos o reportes | [calculo.md](./calculo.md) y [reglas_de_calculo.md](../reglas_de_calculo.md) |
| Copias, verificación, retención o restauración | [backups.md](./backups.md) |
| Servicios, caché o proveedor de datos | [services.md](./services.md) |
| Esquema SQLite, conexión o migración | [database.md](./database.md) |
| Ventanas, pantallas, atajos o temas | [ui.md](./ui.md) y [ui-theme.md](./ui-theme.md) |
| API Flask, JWT, rate limit o SSE | [api.md](./api.md) |
| Usuarios, roles, permisos, sesiones o auditoría | [seguridad_y_usuarios.md](./seguridad_y_usuarios.md) |
| Reportes, selección de datos o exportación Excel/PDF | [reportes.md](./reportes.md), [calculo.md](./calculo.md) y [reglas_de_calculo.md](../reglas_de_calculo.md) |
| Convenciones, dependencias entre capas o pruebas | [convenciones.md](./convenciones.md) y [estructura.md](../estructura.md) |

Flujo: tarea → leer este índice → abrir el contexto específico → comprobar el código citado.

Invariantes: la documentación no sustituye el comportamiento real; no asumir funciones, rutas ni garantías ausentes del código.

Trampas conocidas: quedan excepciones arquitectónicas listadas en `tests/test_arquitectura.py`; ver `convenciones.md`.

Dependencias: los contextos apuntan a servicios, UI, API, base, pruebas y documentación de desarrollo.

Cómo actualizar este archivo: al agregar o renombrar un contexto, actualizar la tabla y la fecha.
