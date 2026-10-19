# Investigación del cálculo de pasadas

## Archivos de ejemplo encontrados

Libros completos analizados:

- `tests/fixtures/CONTROL RECORRIDOS - SEPTIEMBRE - 2026.xlsx`: septiembre de 2026.
- `tests/fixtures/CONTROL RECORRIDOS - OCTUBRE - 2026.xlsx`: octubre de 2026.

El directorio `tests/fixtures/` contiene además `CONTROL RECORRIDOS - OCTUBRE - 2026.xlsx` y fixtures de parser (`ambiguedad.xlsx`, `columnas_faltantes.xlsx`, `formatos_hora.xlsx`, `hora_corrupta.xlsx`, `objetivos_misma_hora.xlsx`, `orden_cronologico.xlsx`, `reimportacion.xlsx`, `supervisor_distinto.xlsx` y `vacio.xlsx`). Los otros fixtures sirven para probar entradas; no representan meses completos.

## Estructura real de los libros completos

Los libros tienen hojas de listado y hojas diarias. Las hojas de datos se llaman, por ejemplo, `19-9 (D)`, `19-9 (N)`, `6-9(D)` y `6-9(N)`. El primer número es día, el segundo mes, `D` identifica DIA y `N` identifica NOCHE; se observó variación en el espacio antes del paréntesis. El año no está en el nombre de la hoja.

Las tablas de datos repiten horizontalmente hasta tres bloques de seis columnas: `NO`, `OBJETIVO`, `TURNO`, `MOVIL`, `HORA`, `SUPERVISOR`. Por ejemplo, en `1-10 (D)`, fila 2 están los encabezados y fila 3 aparece `BARRIO CORTIJO RUTA 202`, turno `DIA`, móvil `L-200`, hora `08;26` y supervisor `PRIETO, HECTOR ADRIAN`. El texto de TURNO puede estar vacío en filas normales; la hoja aporta entonces el turno de la cuadrilla. Las horas tienen formatos mixtos: `datetime.time`, texto `HH;MM` y números como `2121`, que el importador interpreta como 21:21.

En los libros analizados, las pasadas NOCHE de madrugada aparecen en hojas `N` del turno al que pertenecen, no en hojas DIA. Ejemplos: libro de octubre, `1-10 (N)`, fila 15, `CENTRO INTEGRAL DE LA MUJER`, NOCHE, 00:01; libro de septiembre, `16-9 (N)`, fila 3, `BARRIO CORTIJO RUTA 202`, NOCHE, 00:00. Esta convención de hojas respalda que el nombre de hoja identifica la fecha de turno, pero no resuelve por sí sola qué fecha calendario real se debe asignar a cada celda.

## Rango horario observado y límites de la evidencia

Las cifras siguientes se obtuvieron recorriendo las filas con un bloque NO/OBJETIVO/TURNO/MOVIL/HORA/SUPERVISOR y normalizando las horas con `services.importador.normalizador.normalizar_hora`. Los extremos son rangos de horas anotadas, no una prueba de que los horarios extremos sean válidos.

| Libro | Turno de hoja | Cantidad | Hora mínima (hoja, fila) | Hora máxima (hoja, fila) |
|---|---:|---:|---|---|
| Septiembre 2026 | DIA | 764 | 07:13 (`21-9 (D)`, fila 22) | 19:36 (`16-9 (D)`, fila 21) |
| Septiembre 2026 | NOCHE | 803 | 00:00 (`16-9 (N)`, fila 3) | 23:59 (`5-9 (N)`, fila 24) |
| Octubre 2026 | DIA | 362 | 06:33 (`2-10 (D)`, fila 22) | 19:23 (`10-10 (D)`, fila 46) |
| Octubre 2026 | NOCHE | 367 | 00:01 (`1-10 (N)`, fila 15) | 23:59 (`1-10 (N)`, fila 8) |

Hay horas solapadas/atípicas incompatibles con inferir una frontera exacta solo de los libros:

- Septiembre: NOCHE aparece a las 07:00 (`2-9 (N)`, fila 16) y a las 07:12 (`8-9 (N)`, fila 24); DIA llega a 19:36.
- Octubre: DIA aparece a las 06:33 (`2-10 (D)`, fila 22) y NOCHE a las 07:15 (`7-10 (N)`, fila 37). También hay DIA posterior a las 19:00, hasta 19:23.
- Septiembre: `5-9 (N)`, fila 15, tiene `TURNO=DIA` a las 05:36. El parser prioriza el turno de la hoja y reportaría una discrepancia; la celda no es evidencia limpia de un turno DIA a esa hora.

**Conclusion operativa:** hay dos ciclos coordinados, DIA 07:00-19:00 con NOCHE 19:00-07:00, o DIA 08:00-20:00 con NOCHE 20:00-08:00. El usuario confirmo esta regla. El modulo central usa las 08:00 como limite para atribuir la madrugada NOCHE al dia de turno anterior; el turno declarado resuelve las horas superpuestas. Una pasada NOCHE a las 07:40 pertenece al turno operativo del dia anterior en el ciclo 20-08.

## Lógica de fecha, turno y mes encontrada antes de centralizar

- `services/importador/parser.py::parsear_nombre_hoja` interpreta día/mes y D/N del título de la hoja.
- `services/importador/normalizador.py::determinar_fecha_operativa_y_calendario` asigna como fecha operativa la fecha de la hoja para ambos turnos; para N decide si la fecha calendario es el mismo día o el siguiente usando 12:00. `normalizar_turno` y `resolver_turno_con_prioridad` usan la hoja como autoridad frente a una celda contradictoria.
- `services/logica_turnos.py::calcular_turno_y_fecha_operativa` define DIA de 07:00 a 18:59, y NOCHE desde 19:00 o antes de 07:00; la madrugada se atribuye al día anterior.
- `services/gestor_turnos.py::GestorTurnos.calcular_fecha_operativa` y el modulo central aceptan DIA 07:00-20:00 o NOCHE 19:00-08:00; son las ventanas combinadas de ambos ciclos y se superponen en 07:00-08:00 y 19:00-20:00. Sin turno declarado no se infiere automaticamente.
- `services/importador/importacion.py` persiste `fecha` (fecha calendario derivada de hoja/hora) y `fecha_operativa` (fecha de turno calculada desde hoja); consultas de duplicados e importación de seguridad leen esa fecha operativa.
- `services/sync_manager.py` calcula `fecha_operativa` con `GestorTurnos`; ante errores conserva la fecha original, lo que puede crear registros con una regla distinta.
- `database/db.py::migrar_pasadas_campos` rellena `fecha_operativa` faltante con `fecha` cruda; no recalcula filas históricas desde hora y turno. No se encontró una migración histórica de turnos versionada: sí se crea `schema_version`, sin que eso garantice una fecha operativa correcta en las filas antiguas.
- `services/reportes.py::generar_reporte_mensual` filtra `COALESCE(fecha_operativa, fecha)` entre el primer y último día del mes; agrupa por objetivo y fecha y convierte cualquier cantidad de pasadas de ese día en un solo día con pasada. No separa el número de pasadas por turno.
- `ui/reportes/reporte_objetivo.py::calcular_reporte_objetivo` también filtra por fecha operativa y mes calendario, separa las pasadas en los turnos almacenados y cuenta presencia (no el número de pasadas). Usa otra consulta/cálculo independiente.
- `services/estadisticas.py` mezcla `fecha_operativa` con `fecha` cruda: el promedio anual agrupa con `strftime` sobre `fecha`, distribución mensual y top de supervisores filtran `fecha`, mientras otras estadísticas usan `COALESCE(fecha_operativa, fecha)`.
- `services/exportar_mes.py::exportar_mes_json` filtra las pasadas por `p.fecha` cruda, no por fecha operativa; puede excluir/incluir una pasada en el mes incorrecto cuando la fecha calendario difiere de la fecha de turno. Sus equipos/notas son registros por fecha y no pasadas.
- `services/importador/importacion.py::_exportar_pasadas_seguridad` exporta por `COALESCE(fecha_operativa, fecha)`; se deduce el mes de esa fecha, que sí es de turno cuando está correctamente persistida.
- `services/data_provider.py`, `ui/tabla_diaria.py`, `ui/lista_pasadas.py`, `ui/widgets/tabla_cobertura.py` y `ui/ventana_principal.py` consultan fecha cruda, fecha operativa o ambas según pantalla. La lista individual muestra `fecha` y las consultas diarias no son uniformes.
- `api/routes/reportes.py` delega en `services.reportes`; no implementa un cálculo mensual independiente.

Las rutas mensuales que usan `fecha_operativa` dependen de que ese campo esté poblado y represente la fecha de turno. El fallback histórico `COALESCE(fecha_operativa, fecha)` puede trasladar pasadas al mes calendario incorrecto. Las consultas de mes por `p.fecha`, el `strftime` sobre la fecha cruda y los filtros de primer/último día no incorporan automáticamente la madrugada del último turno noche del mes.

## Resolución aplicada en esta etapa

- `services/pasadas/calculo_pasadas.py` concentra la atribución de fecha de turno, mes, rangos mensuales y conteo natural de pasadas.
- El importador usa el modulo central para inferir fecha calendario a partir de la fecha de hoja; NOCHE antes de las 08:00 cae en el dia calendario siguiente, conservando la fecha operativa de la hoja.
- Reportes mensual/por objetivo, estadísticas mensuales, exportaciones, API y pantallas consultan `fecha_operativa` (con fallback histórico cuando falta) y reutilizan las funciones centrales para indexar o contar. La tabla de cobertura también deduplica con la clave natural central.
- La sincronización conserva la validación opcional del horario, pero calcula la fecha de turno centralmente incluso cuando se desactiva esa validación.
- No se agregó otra fecha persistida: `fecha_operativa` ya existe. No se rellenaron automáticamente valores históricos incompletos porque no se puede determinar si cada `fecha` antigua es calendario o fecha de turno.

## Alcance pendiente de decisión/evidencia

Los libros no permiten resolver horarios fuera de ambos ciclos ni filas con TURNO contrario a la hoja. El usuario confirmo los ciclos 07-19/19-07 y 08-20/20-08. Tampoco contienen un estado inequivoco de pasada anulada, reglas para objetivos dados de baja/historicos ni definicion completa de cuantas pasadas se esperan por turno. La base `seguridad.db` disponible tiene cero pasadas y objetivos.
