# Comparación del cálculo anterior y el centralizado

## Método y límites

El cálculo anterior de reportes agrupaba por `COALESCE(fecha_operativa, fecha)`. En el importador de Excel, `fecha_operativa` se asignaba desde la fecha de la hoja, y la hoja N/D identifica el día de turno. Se comparó ese día atribuido por la lógica anterior con `fecha_de_turno` aplicado a la hora calendario inferida desde la fecha de la hoja y el turno.

Esta comparación usa los registros válidos detectados en las hojas mensuales y compara días objetivo/turno con al menos una pasada, que es la medida de cobertura del reporte mensual. No certifica conteos persistidos históricos: `seguridad.db` disponible en este entorno no contiene pasadas ni objetivos.

Al comparar las fechas completas del importador, la fecha calendario inferida difiere para filas NOCHE entre las 08:00 y las 11:59: la heuristica anterior usaba 12:00 y movia esas horas al dia calendario siguiente; el ciclo operativo confirmado usa como madrugada solo las horas anteriores a las 08:00. La fecha operativa de la hoja y las combinaciones objetivo/fecha/turno de cobertura no cambian en los libros analizados.

## Resumen por libro/mes

| Mes | Pasadas con hora normalizada | Combinaciones objetivo-fecha-turno anterior | Combinaciones objetivo-fecha-turno nuevo | Diferencias | Clasificación |
|---|---:|---:|---:|---:|---|
| 2026-09 | 1.567 | 1.512 | 1.512 | 0 | Sin diferencia en la atribución a partir de fecha de hoja; la fila `5-9 (N)`, 15, tiene turno de celda contradictorio y debe revisarse. |
| 2026-10 | 729 | 710 | 710 | 0 | Sin diferencia en la atribución a partir de fecha de hoja. |

La tabla de diferencias por objetivo está vacía: no se encontró ningún objetivo/mes con distinta cantidad de días cubiertos al aplicar la regla central a la fecha/turno de hoja. Por lo tanto no hay una diferencia específica que pueda clasificarse como corrección histórica o regresión. Las filas contradictorias de horario anotadas en el análisis son anomalías de fuente y no una diferencia matemática entre ambos métodos.

| Objetivo | Mes | Valor anterior | Valor nuevo | Causa probable |
|---|---|---:|---:|---|
| — | — | — | — | No se detectaron diferencias por objetivo en los dos libros. |

## Comparación con datos persistidos

No se pudo comparar el informe viejo y el nuevo sobre un mes cargado en la base real: la base `seguridad.db` del entorno tiene cero filas en `pasadas` y `objetivos`, y no hay otra copia de base mensual disponible en el repositorio. La tabla anterior compara los libros contra la regla de atribución que el importador anterior persistía, no un informe histórico ya emitido.

No se debe marcar como verificado el caso dorado solo porque el test reproduce el mismo Excel. `tests/golden/2026-10.json` queda intencionalmente marcado **SIN VERIFICAR** hasta cotejar manualmente cifras contra las hojas.
