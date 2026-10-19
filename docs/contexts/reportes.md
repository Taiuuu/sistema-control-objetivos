Última actualización: 2026-10-19

Propósito: describir el flujo compartido para preparar y exportar reportes.
La atribución de fecha/turno no se implementa aquí; consultar [reglas_de_calculo.md](../reglas_de_calculo.md).

Archivos clave:
- `services/reportes_unificados/modelos.py` — `ReporteDatos`, metadatos y catálogo de columnas.
- `services/reportes_unificados/datos.py` — adaptadores, filtros y totales.
- `services/reportes_unificados/consultas.py` — selección del diálogo a instantánea común.
- `services/reportes_unificados/objetivo.py` — cálculo por objetivo en services.
- `services/reportes_unificados/excel.py`, `pdf.py` — escritores que reciben el mismo objeto.
- `services/reportes_unificados/archivos.py` — nombres, escritura exclusiva, mensajes y auditoría.
- `ui/reportes/dialogo_exportar.py`, `acciones_exportacion.py` — selección, vista previa, plantillas y flujo asíncrono.
- `ui/reportes/reporte_mensual.py`, `reporte_objetivo.py`, `ui/lista_pasadas.py` — puntos de entrada.
- `api/routes/reportes.py` — contratos JSON históricos adaptados al modelo compartido.
- `tests/test_reportes_unificados.py`, `tests/test_api.py` — contrato, exportadores e integración API.

Flujo: filtros de pantalla → diálogo y plantilla opcional → proveedor de datos → `ReporteDatos` inmutable → Excel/PDF → registro de auditoría.

Invariantes:
- Los cálculos de cobertura mensual siguen en `services.reportes`; la atribución usa `services/pasadas/calculo_pasadas.py`.
- Excel y PDF reciben la misma instantánea; los escritores no consultan DB ni calculan conteos.
- Los totales/subtotales se preparan en services; sin filas útiles no se escribe archivo.
- `reportes.exportar` se valida antes de mostrar el diálogo y al guardar; cada archivo generado se audita.
- Las plantillas y la última carpeta se conservan en `QSettings`, no en SQLite.
- `data/exports_seguridad/` es independiente y no participa en informes.

Formatos: Excel ofrece Resumen, Detalle opcional y Parámetros, con tipos numéricos, impresión ajustada y títulos repetidos. PDF usa A4, fuentes Vera de ReportLab, tablas paginadas y subtotales de agrupación. La vista previa muestra hasta 100 filas y el total de filas.

Filtros: el mes mensual debe ser calendario completo; detalle admite día o rango. El reporte por objetivo exige un único objetivo y mes completo. “Todos los supervisores” no restringe registros históricos; una selección explícita sí. La agrupación ordena el detalle y calcula subtotales.

Errores: nombres se sanitizan, archivos existentes no se reemplazan, `PermissionError` se traduce a mensaje accionable, y errores técnicos se registran en `data/logs/vesp.log`. El registro de auditoría es la única escritura intencional a la base durante una exportación.

Limitaciones verificadas: no hay pantalla autónoma de reporte diario; `Lista de pasadas` ofrece detalle diario. La API diaria toma filas y total del modelo común, pero conserva el porcentaje del servicio legacy para no redefinir su indicador. La barra de progreso es indeterminada. Los escritores legacy en `services/exportar.py` permanecen por compatibilidad, pero las pantallas de reportes ya no los invocan.

Pruebas: `python -m pytest -o addopts= tests/test_reportes_unificados.py tests/test_api.py tests/test_arquitectura.py`; la suite completa también se valida con `python -m pytest` cuando el sistema Qt dispone de `libGL.so.1`.

Dependencias: `openpyxl` y `reportlab` ya están en `requirements.txt`; no se añadió dependencia ni migración.

Cómo actualizar este archivo: mantener sincronizados los puntos de entrada, el esquema de selección, los límites reales y las pruebas al cambiar el contrato.
