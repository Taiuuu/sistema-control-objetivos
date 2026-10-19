Última actualización: 2026-10-19

Propósito: resumir esquema y acceso a SQLite para cambios de persistencia.
DDL y migraciones viven en `database/db.py`; confirmar allí el esquema exacto antes de alterar datos.

Archivos clave:
- `core/configuracion.py` — `DB_PATH` configurable; por defecto bajo `~/VESP Control/seguridad.db`.
- `database/db.py` — apertura, pragmas, integridad, creación de tablas/migraciones; `SCHEMA_VERSION = 2`.
- `database/gestor_db.py` — singleton `GestorDB`, conexión por hilo, ejecución y transacciones.
- `tests/test_backup_seguridad.py`, `tests/test_importador_integridad.py`, `tests/test_arquitectura.py` — protecciones relacionadas.

Tablas: `objetivos` (nombre, descripción, vigencia, días, activo, placeholder/revisión); `objetivos_aliases` (alias único normalizado → objetivo); `objetivo_periodos` (vigencias por objetivo); `feriados` (fecha única); `supervisores` (nombre, alta/baja, placeholder); `pasadas` (fecha, hora, turno, objetivo, supervisor, notas, fecha_operativa); `equipos` (fecha/turno y hasta tres supervisores); `notas` (fecha/texto); `usuarios` (username único, hash, rol, flags); `logs` (fecha/hora/usuario/acción); `preferencias_usuario` (usuario+clave); `auditoria` (operación, usuario, registro, valores, detalle y estado); `schema_version`; `pasadas_duplicados_migracion` (archivo histórico previo a unicidad).

Relaciones: pasadas → objetivos/supervisores; equipos → hasta tres supervisores; logs/auditoria/preferencias → usuarios; aliases y periodos → objetivos. Triggers impiden eliminar objetivo/supervisor con historial, pasadas con fichas placeholder y conservan integridad referencial.

Índices relevantes: pasadas por fecha, objetivo, fecha+objetivo, supervisor y turno; índice único parcial `idx_pasadas_clave_natural` por objetivo + fecha_operativa + hora a minuto + supervisor (`NULL` normalizado a -1); auditoría por fecha/usuario/tabla+registro; objetivo_periodos por objetivo+vigencia; feriados por fecha única; tablas auxiliares tienen índices por fechas/relaciones.

Migraciones: `crear_base_datos()` crea tablas, añade campos de objetivos/pasadas, archiva duplicados naturales y crea índice/triggers. Antes de archivar duplicados se crea `pre_migracion`; se conserva el ID menor y los demás quedan en `pasadas_duplicados_migracion`. Migraciones adicionales cubren placeholder, feriados, supervisor3, alta/baja, usuario activo y columnas heredadas. `schema_version` registra versión 2; confirmar cambios de versión ahí y en migración al ampliar esquema.

Convenciones: IDs `INTEGER PRIMARY KEY AUTOINCREMENT`; fechas ISO `YYYY-MM-DD`, hora texto y fecha_operativa como día del turno; flags enteros 0/1; turno persistido en formas legibles como diurno/nocturno; `username` único y contraseña hasheada.

Acceso/hilos: `conectar()` abre SQLite directo con foreign_keys, WAL, synchronous=NORMAL y busy_timeout; el módulo envuelve `sqlite3.connect` para configurar/seguir conexiones. `GestorDB` conserva conexión local por hilo (`threading.local`), usa row factory y expone `transaction()` con commit/rollback. No compartir operaciones concurrentes sin transacción/gestión de conexión apropiada.

Invariantes: activar claves foráneas; nunca eludir el índice natural ni borrar entidades con historial; ejecutar backup previo a migraciones destructivas; actualizar `SCHEMA_VERSION`/tests al cambiar esquema.

Trampas conocidas: UI/modelos aún acceden a SQLite directamente en excepciones declaradas; no interpretar todos los campos `fecha` antiguos como calendario; `fecha_operativa` es autoridad mensual para pasadas.

Dependencias: política de capas en `docs/estructura.md`; backup previo en `docs/contexts/backups.md`; fecha de turno en `docs/contexts/calculo.md`.

Cómo actualizar este archivo: cotejar columnas, índices y versión con DDL/migraciones después de cada cambio de esquema.
