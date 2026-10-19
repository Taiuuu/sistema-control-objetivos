Última actualización: 2026-10-19

Propósito: explicar creación, verificación, retención y recuperación de copias SQLite.
Los errores de copia/restauración deben propagarse y conservar trazabilidad en el log.

Archivos clave:
- `services/backups/backup.py` — `crear_backup`, `hacer_backup`, `listar_backups`, `restaurar_backup`, `limpiar_backups`.
- `core/configuracion.py` — DB y directorios `data/backups`, `data/logs`, `data/exports_seguridad`.
- `scripts/main.py` — comprueba/crea backup diario al iniciar.
- `database/db.py` — respalda antes de migrar/archivar duplicados.
- `services/importador/importacion.py` — backup previo a importar.
- `services/operaciones_seguras.py` — backup previo al borrado mensual.
- `ui/configuracion.py` — creación manual, selección de carpeta externa y restauración.
- `scripts/restaurar_backup.py` — restauración de emergencia sin Qt.

Flujo: motivo permitido → SQLite `Connection.backup` → comprobar integridad y claves foráneas + conteos base → copiar local → intentar copia externa → retención. Restauración valida la fuente, crea copia previa cuando la base actual es íntegra, reemplaza mediante temporal y conserva recuperación ante error.

Motivos observados: diario, pre_importacion, pre_migracion, pre_borrado_mes, pre_restauracion y manual. Una copia externa se configura por interfaz o `VESP_BACKUP_EXTERNAL_PATH`; es secundaria y su fallo se registra como warning, no invalida la copia local.

Retención: preserva hasta 14 backups diarios verificados; pre_importacion/pre_migracion/pre_borrado_mes/manual por 90 días; pre_restauracion por 30 días. Nunca elimina la última copia verificada. Copias externas se copian, pero no se limpian mediante esta política.

Restauración: la interfaz exige selección verificada, confirmación y escribir `RESTAURAR`; el script lista copias y también exige confirmación, y bloquea si otra instancia tiene la base. Reabrir la aplicación después de restaurar desde la UI.

Invariantes: backup previo obligatorio para importar, migrar y borrar mes; backup verificado antes de aceptar/restaurar; no sobrescribir la base activa sin cerrar conexiones; no tratar la copia externa como único respaldo.

Trampas conocidas: el backup diario se garantiza al ejecutar el arranque, no por un daemon; verificar no significa almacenar credenciales; `crear_backup` requiere motivo reconocido y espacio disponible.

Dependencias: `DB_PATH` determina los directorios; restauración coordina `database.db` y `GestorDB`; logging central en `core/logging_config.py`.

Cómo actualizar este archivo: verificar llamadas, motivos y edades exactas en `backup.py` y los puntos de operación antes de cambiar políticas.
