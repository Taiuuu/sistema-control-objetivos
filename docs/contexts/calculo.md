Última actualización: 2026-10-19

Propósito: ubicar la regla compartida de fecha de turno y selección mensual.
Para definiciones completas y casos límite, consultar [docs/reglas_de_calculo.md](../reglas_de_calculo.md).

Archivos clave:
- `services/pasadas/calculo_pasadas.py` — módulo único: `fecha_de_turno`, `mes_de_pasada`, rangos y conteos.
- `services/logica_turnos.py` — adaptador de turno/fecha para consumidores existentes.
- `services/reportes.py` — reportes diarios/mensuales y rango mensual común.
- `services/exportar_mes.py`, `services/exportacion_extendida.py` — filtran/exportan meses usando el módulo común.
- `ui/reportes/reporte_mensual.py`, `ui/reportes/reporte_objetivo.py` — pantallas y consultas de reporte.
- `ui/widgets/tabla_cobertura.py` — cobertura DIA/NOCHE por fecha.
- `services/estadisticas.py`, `services/data_provider.py`, `services/api_rest.py` — estadísticas, datos y conteo.
- `tests/test_calculo_pasadas.py`, `tests/test_golden_pasadas.py` — reglas y regresión de datos dorados.

Flujo: fecha/hora calendario local + turno declarado → `fecha_de_turno` → mes de fecha operativa → filtros, conteos y reportes.

Ejemplos: 14/10 03:00 NOCHE → 13/10, mes octubre; 01/11 02:00 NOCHE → 31/10, mes octubre; 14/10 07:40 NOCHE → 13/10 pero DIA → 14/10; el turno declarado resuelve los solapamientos 07–08 y 19–20. Para mes nocturno, `rango_datetime_de_mes` usa inicio día 1 a las 08:00 inclusive y día 1 siguiente a las 08:00 exclusive.

Invariantes: hora local sin UTC; NOCHE antes de 08:00 pertenece al día anterior; mes deriva de fecha de turno; jamás inferir turno solo por hora en zonas de solapamiento; módulo puro central es la única fuente para la regla.

Trampas conocidas: la hora 07:40 puede ser DIA o NOCHE; no desplazar una segunda vez fechas con `fecha_operativa` ya persistida; el rango mensual no sustituye validar el turno de cada fila.

Dependencias: reglas en `docs/reglas_de_calculo.md`; identidad natural del importador en `docs/contexts/importador.md`; consumidores en servicios de reportes/exportación, API y UI.

Cómo actualizar este archivo: contrastar ejemplos y consumidores con el módulo y sus pruebas al cambiar la regla de fecha/mes.
