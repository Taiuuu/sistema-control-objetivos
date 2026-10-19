Última actualización: 2026-10-19

Propósito: describir el análisis Excel sin escritura y su confirmación transaccional.
Usalo junto a las pruebas del importador antes de cambiar formatos, conciliación o persistencia.

Archivos clave:
- `services/importador/__init__.py` — API pública: `analizar_excel`, `previsualizar_importacion`, `confirmar_importacion`.
- `services/importador/parser.py` — Excel → `PasadaCruda`, hojas, bloques, fecha y turno de hoja.
- `services/importador/normalizador.py` — valores crudos → hora/turno y fechas operativa/calendario.
- `services/importador/matcher.py` — nombres → registros existentes, sugerencias o no reconocidos.
- `services/importador/duplicados.py` — clave natural → clasificación y detección de duplicados.
- `services/importador/validador.py` — pasadas normalizadas → problemas de calidad/horario.
- `services/importador/modelos.py` — `PasadaCruda`, `PasadaNormalizada`, `Problema`, `ResultadoAnalisis`.
- `services/importador/reporte.py` — coordina dry-run, resumen y reporte descargable XLSX.
- `services/importador/resolucion.py` — decisiones de revisión → registros preparados para auditoría.
- `services/importador/importacion.py` — aplica altas, correcciones, pasadas, auditoría y CSV tras confirmar.
- `services/importador/notificacion.py` — resultado de importación → mensaje/notificación.
- `services/importador/import_history.py` — guarda y consulta historial local de importaciones.
- `ui/importador/importar_excel.py` — pantalla de selección, vista previa, resolución y confirmación.

Flujo: XLSX → `parser` → `normalizador` → `matcher` → `duplicados` → `validador` → `ResultadoAnalisis` → UI/resoluciones → confirmación → SQLite/auditoría.

Contratos módulo por módulo:
- `parser`: ruta/hoja XLSX → nombres de hojas y lista de `PasadaCruda` con coordenadas; parsea fecha/turno desde nombre de hoja.
- `modelos`: datos de entrada/salida tipados del pipeline; no lee Excel ni accede a SQLite.
- `normalizador`: valor de celda y fecha/turno de hoja → hora validada, turno resuelto, fechas operativa/calendario y advertencias.
- `matcher`: nombres del libro + catálogos SQLite → coincidencia exacta, sugerencias, ambiguo o no reconocido.
- `duplicados`: pasadas normalizadas + conexión → marca acción nueva/actualizar/omitir y cuenta duplicados.
- `validador`: pasadas normalizadas + contexto horario opcional → lista de `Problema`.
- `reporte`: archivo, año y conexión → `ResultadoAnalisis`; resumen → texto y detalle → bytes XLSX.
- `resolucion`: usuario + decisiones de UI → `EstadoResolucion` con registros listos para auditar, sin escribir.
- `importacion`: análisis + resoluciones + usuario + conexión → resumen dict y escrituras atómicas.
- `notificacion`: resumen + callback de UI → mensaje y `ResultadoNotificacion`; no persiste.
- `import_history`: evento → historial JSON local de hasta 50 importaciones; no es la auditoría SQLite.

Funciones públicas: `analizar_excel(path, anio, conexion_bd, forzar_sobrescritura=False)` y `previsualizar_importacion(...)` entregan análisis sin escribir; `confirmar_importacion(analisis, resoluciones, usuario, conexion_bd, ...)` entrega resumen; `generar_reporte_detallado(resultado)` entrega bytes XLSX.

Transacción: confirmar valida estado y conexión inactiva, crea primero backup `pre_importacion`, abre una transacción única, aplica resoluciones, reclasifica duplicados, persiste, exige conciliación `leídas = insertadas/actualizadas + duplicadas + rechazadas`, audita y confirma. Una excepción revierte la transacción; el fallo se audita aparte si es posible.

Invariantes: identidad única = objetivo + fecha_operativa + minuto + supervisor; el turno de la hoja manda; la vista previa no escribe; nunca perder filas sin problema trazable; el original Excel no se guarda. Un fallo del backup previo cancela la confirmación.

Trampas conocidas: hora inválida/ausente y errores críticos de hoja bloquean; advertencias no bloquean; coincidencias ambiguas requieren elección explícita; éxito SQL y CSV de seguridad son etapas separadas (un error CSV se informa tras commit).

Dependencias: `services/pasadas/calculo_pasadas.py` aporta atribución de fecha; `services/backups/backup.py` respalda; UI proporciona `EstadoResolucion`; SQLite y auditoría se manejan en `importacion.py`.

Cómo actualizar este archivo: verificar contratos y pruebas de cada etapa al cambiar el pipeline, la clave natural o su conciliación.
