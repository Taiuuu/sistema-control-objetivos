Última actualización: 2026-10-19

Propósito: encontrar servicios de negocio y sus consumidores principales.
La lista describe módulos existentes; no todos aplican la arquitectura objetivo sin excepciones.

Archivos clave:
- `services/cache.py` — `CacheManager` thread-safe, caché RAM con TTL, patrones e invalidación explícita.
- `services/data_provider.py` — proveedor abstracto y SQLite para usuarios/objetivos/supervisores/pasadas; usado por `sync_manager.py`.
- `services/estadisticas.py` — métricas cacheadas; consume consultas y cálculo común, usada por vistas/reportes.
- `services/pasadas/calculo_pasadas.py` — fecha operativa, mes, filtros y conteo; importador, reportes, API y UI.
- `services/estado_objetivos.py` — vigencia efectiva por fecha de fin, compartida por UI y API.
- `services/reportes_unificados/` — modelos dataclass y adaptadores del mismo objeto de datos para las salidas de reportes.
- `services/reportes.py` — reportes diarios/mensuales y objetivos del día; UI y API.
- `services/exportar.py`, `services/exportar_mes.py`, `services/exportacion_extendida.py` — exportación XLSX/PDF/mes y CSV extendido; pantallas de reportes.
- `services/backups/backup.py` — backups y restauración; arranque, configuración, scripts y operaciones.
- `services/importador/*.py` — pipeline Excel; pantalla `ui/importador/importar_excel.py` (detalle en `importador.md`).
- `services/actualizaciones/actualizador.py` — consulta de versión y apertura de releases; `scripts/main.py`.
- `services/api_rest.py` — API HTTP local threaded; `scripts/main.py`.
- `services/auditoria.py` — auditoría estructurada, consultas, integridad y CSV; pantallas de auditoría/indexación/sincronización.
- `services/logger.py` — acciones en tabla `logs`; login, formularios y pantallas.
- `services/usuarios.py`, `services/permisos.py`, `services/sesion.py` — identidad, autorización y sesión; UI, modelos/API según módulo.
- `services/encriptacion.py` — cifrado reversible de token de sesión y validación/creación de contraseñas; sesión/usuarios.
- `services/validaciones.py`, `services/validador_horas_limite.py` — validación de entidades/pasadas y compatibilidad horaria; formularios.
- `services/gestor_turnos.py`, `services/logica_turnos.py` — operaciones y compatibilidad de fecha/turno; modelos, sync y UI.
- `services/feriados.py` — persistencia y consulta de feriados; `ui/feriados.py` y reportes.
- `services/queries_tabla.py` — datos para tablas; ventana principal y reportes.
- `services/operaciones_seguras.py` — operaciones protegidas, incluido borrado mensual con backup; pantallas de pasadas.
- `services/background_task.py` — trabajos/señales Qt; pantallas que ejecutan consultas/reportes en segundo plano.
- `services/sincronizacion.py`, `services/sync_manager.py`, `services/config_app.py` — notificaciones, cola y preferencia de sync; UI, modelos y arranque.
- `services/notificaciones.py` — notificaciones de escritorio; consumidor de UI/operaciones.
- `services/menu_config.py` — configuración de módulos/menú; ventana principal y sidebar.
- `services/tema.py` — paletas legacy; `ui/widgets/estilos.py` (tema global actual está en `ui/theme/`).
- `services/assets.py` — resolución de recursos; tema, UI y actualizador.
- `services/db_analyzer.py` — diagnóstico/índices SQLite; `ui/vista_indexacion.py`.
- `services/exceptions.py` — jerarquía de errores de servicio; consumidores de servicios.
- `services/__init__.py` — paquete; sin API funcional asumida.

Caché: guarda objetos/resultados en memoria con TTL; `data_provider.py` cachea catálogos 120 s y pasadas por fecha 60 s; `estadisticas.py` define TTL por función; `obtener_supervisores_cache` dura 60 s. `invalidar_objetivos`, `invalidar_supervisores`, `invalidar_pasadas` eliminan por substring. CRUD de `models/objetivos.py`, `models/supervisores.py`, `models/turnos.py` y `models/equipos.py` invalida claves relacionadas; escrituras SQL directas pueden saltarse esa invalidación.

Invariantes: agregar un servicio no habilita dependencias arbitrarias; los servicios ordinarios no deben importar UI/Qt salvo excepciones explícitas del test; invalidar al mutar datos cacheados.

Trampas conocidas: hay imports legacy cruzados, servicios que acceden a SQLite y excepciones PyQt declaradas en `tests/test_arquitectura.py`; el gestor SQL también admite caché opcional por query.

Dependencias: reglas y excepciones en `docs/estructura.md`/`tests/test_arquitectura.py`; datos SQLite en `database/`; interfaces y consumidores en `ui/` y `api/`.

Cómo actualizar este archivo: al agregar/mover servicio, verificar sus imports y consumidores con el código y actualizar esta lista.
