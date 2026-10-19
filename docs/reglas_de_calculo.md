# Reglas de cálculo de pasadas

> **Regla operativa confirmada:** existen dos ciclos completos: DIA 07:00–19:00 con NOCHE 19:00–07:00, o DIA 08:00–20:00 con NOCHE 20:00–08:00. Cada supervisor pertenece a un solo turno. Las horas de solapamiento se interpretan según el turno informado, nunca solo por la hora.

## Definiciones

- **Pasada:** registro persistido que representa una visita de un supervisor a un objetivo. Para poder asignarle fecha de turno debe tener fecha y hora calendario y un turno reconocible.
- **Turno DIA:** turno cuya fecha de turno coincide con la fecha calendario de la pasada. Puede pertenecer al ciclo 07:00–19:00 o al 08:00–20:00.
- **Turno NOCHE:** turno que atraviesa medianoche. Según el ciclo termina a las 07:00 o a las 08:00; las pasadas de madrugada anteriores a las 08:00 pertenecen a la fecha de turno anterior.
- **Fecha de turno:** día al que se atribuye la pasada, según fecha/hora calendario y turno. No es necesariamente `fecha` calendario.
- **Mes de la pasada:** año y mes de la fecha de turno, no los de la hora calendario.

Las fechas/horas se tratan como hora local de Argentina (America/Argentina/Buenos_Aires): son valores de pared sin conversión a UTC. Una conversión UTC podría desplazar la fecha y no debe participar en la atribución.

## Corte y respaldo

La fecha limite comun para atribuir pasadas NOCHE es **08:00**: 07:59:59 se atribuye al dia anterior y 08:00:00 o posterior a la fecha calendario. Esto cubre los dos ciclos admitidos. El turno declarado distingue DIA a las 07:40 (ciclo 07-19) de NOCHE a las 07:40 (ciclo 20-08); entre 19:00 y 20:00 tampoco se infiere turno solo por la hora.

El ciclo 07-19/19-07 o 08-20/20-08 fue aclarado por el usuario. Los libros contienen NOCHE a las 07:12 y 07:15, compatibles con el ciclo 20-08, y valores que deben revisarse contra el turno indicado, como DIA a las 06:33. El corte de las 08:00 en la funcion compartida conserva las pasadas de madrugada de ambos ciclos.

Las celdas NOCHE de madrugada aparecen en hojas N que identifican el turno, por ejemplo `1-10 (N)`, fila 15, 00:01, octubre. Esto respalda la fecha de turno de la hoja, pero no prueba qué fecha calendario corresponde cuando la fuente solo conserva el nombre de hoja.

## Ejemplos con los ciclos operativos

Se asume que la columna de fecha/hora representa la fecha calendario real y que el turno ya está identificado correctamente.

| Fecha y hora calendario | Turno | Fecha de turno | Mes de la pasada |
|---|---|---|---|
| 13/10/2026 09:00 | DIA | 13/10/2026 | octubre 2026 |
| 14/10/2026 03:00 | NOCHE | 13/10/2026 | octubre 2026 |
| 14/10/2026 06:59:59 | NOCHE | 13/10/2026 | octubre 2026 |
| 14/10/2026 07:40:00 | NOCHE (ciclo 20-08) | 13/10/2026 | octubre 2026 |
| 14/10/2026 07:40:00 | DIA (ciclo 07-19) | 14/10/2026 | octubre 2026 |
| 14/10/2026 08:00:00 | NOCHE | 14/10/2026 | octubre 2026 |
| 14/10/2026 08:30:00 | DIA (ciclo 08-20) | 14/10/2026 | octubre 2026 |
| 14/10/2026 19:30:00 | DIA o NOCHE, segun turno declarado | 14/10/2026 | octubre 2026 |
| 31/10/2026 23:00 | NOCHE | 31/10/2026 | octubre 2026 |
| 01/11/2026 02:00 | NOCHE | 31/10/2026 | octubre 2026 |
| 01/11/2026 09:00 | DIA | 01/11/2026 | noviembre 2026 |
| 31/12/2026 23:30 | NOCHE | 31/12/2026 | diciembre 2026 |
| 01/01/2027 02:00 | NOCHE | 31/12/2026 | diciembre 2026 |
| 01/02/2024 02:00 (año bisiesto) | NOCHE | 31/01/2024 | enero 2024 |
| 29/02/2024 02:00 (año bisiesto) | NOCHE | 28/02/2024 | febrero 2024 |
| 01/03/2024 02:00 (año bisiesto) | NOCHE | 29/02/2024 | febrero 2024 |
| 01/03/2025 02:00 | NOCHE | 28/02/2025 | febrero 2025 |

En un filtro mensual por fecha/hora calendario, el rango compartido cubre desde el primer dia del mes a las 08:00 inclusive hasta el primer dia del mes siguiente a las 08:00 exclusive. Incluye hasta las 07:59 del ultimo turno NOCHE del mes y excluye la madrugada del primer dia del propio mes, que pertenece al mes anterior. Siempre se respeta el turno declarado.

## Qué cuenta como pasada

La importación existente omite duplicados reconocidos por su clave natural de objetivo, fecha operativa, hora y supervisor. Para contar pasadas deben usarse registros persistidos después de esa protección, sin colapsar pasadas distintas de un objetivo solo por ocurrir el mismo día. Los reportes de cumplimiento actuales sí convierten la presencia de una o más pasadas en un indicador de día cubierto; eso no equivale al número bruto de pasadas.

No hay evidencia suficiente para decidir de forma segura:

- cómo tratar una pasada anulada o corregida que siga en la base;
- si una fila incompleta, sin supervisor, hora u objetivo puede ser válida;
- si debe contar un objetivo dado de baja en la actualidad pero activo cuando ocurrió;
- qué vigencia histórica prevalece si hay `fecha_inicio/fecha_fin` y `objetivo_periodos`;
- si una pasada en un día sin servicio configurado debe excluirse o conservarse como pasada real anómala;
- cómo resolver horas fuera de rango, TURNOS contradictorios entre hoja y celda, ni las filas que contradigan el ciclo indicado por su turno.

Los registros que contradicen el horario no deben reasignarse de forma silenciosa: deben quedar señalados para revisión. La condición “objetivo esperado ese día” se obtiene de la vigencia aplicable y de `dias_semana`, pero la semántica de vigencias históricas debe validarse.

## “Pasó por todos los objetivos”

El código mensual actual calcula expectativa por objetivo y día calendario elegible: un objetivo cuenta como “con pasada” si existe al menos una pasada de ese objetivo en su fecha operativa; las pasadas duplicadas no aumentan días cubiertos. El reporte por objetivo presenta por separado si hubo DIA y/o NOCHE, pero no calcula el cumplimiento contra una expectativa configurable por turno. `dias_semana` representa los días de servicio y no se encontró un campo inequívoco de expectativa por turno.

Por lo tanto, no se debe interpretar todavía “todos” como una pasada por cada turno: no se puede deducir si cada objetivo requiere una o dos pasadas al día, si NOCHE se exige siempre que esté habilitado el día, ni si la expectativa cambia según objetivo. Esa decisión queda pendiente.

## Casos dudosos que requieren validación humana

1. Revisar filas cuyo horario contradice el turno escrito, en particular DIA antes de las 07:00 o NOCHE desde las 08:00; no se cambia el turno silenciosamente.
2. Confirmar si el nombre de la hoja indica siempre fecha de inicio del turno, incluyendo las filas de madrugada, o si algunas filas se cargan bajo fecha calendario.
3. Determinar validez y conteo de anulaciones, datos incompletos, registros fuera de horario y objetivos fuera de vigencia o sin servicio ese día.
4. Determinar cuántas pasadas se esperan por objetivo y por turno; hoy el esquema solo aporta días de servicio, no turnos requeridos.
5. Revisar los registros marcados en el análisis, en especial septiembre `5-9 (N)`, fila 15 (TURNO DIA a las 05:36), octubre `2-10 (D)`, fila 22 (DIA a las 06:33), septiembre `2-9 (N)`, fila 16 (NOCHE a las 07:00) y octubre `7-10 (N)`, fila 37 (NOCHE a las 07:15).

Para los informes, mantener separados el número bruto de pasadas registradas por turno y los días cubiertos por objetivo. Un día con varias pasadas sigue siendo un solo día cubierto; los conteos DIA/NOCHE son descriptivos y no representan cumplimiento esperado por turno hasta validar la regla del punto 4.
