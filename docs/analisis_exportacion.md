# Análisis de exportación (situación previa a la etapa 4)

## Alcance y entorno de inspección

Se revisaron los exportadores de reportes, pantallas, servicios y endpoints visibles en el código, además de las dependencias declaradas. No se modificó código de ejecución en esta fase. `requirements.txt` ya contiene `openpyxl==3.1.5` y `reportlab==4.4.10`; pandas también figura, aunque no participa en los exportadores de reportes revisados.

La suite base exacta (`python -m pytest`) no pudo iniciar porque `pytest.ini` configura opciones de `pytest-cov` y el complemento no está instalado. Al ejecutar `python -m pytest -o addopts= --tb=short`, pytest recolectó 217 pruebas pero falló la colección de cuatro módulos de UI por falta del sistema `libGL.so.1`. Por esa dependencia no fue posible ejecutar desde este entorno las pruebas de pantallas ni importar el módulo UI de reporte por objetivo.

Se probaron los servicios de Excel/PDF existentes con filas y nombres de ejemplo en un directorio temporal (incluidas tildes, eñe, comillas y texto muy largo). Los cuatro formatos produjeron archivos; el mensual vacío también produjo un XLSX de 108181 bytes sin advertir que no había filas. No había una herramienta de extracción de texto PDF disponible (`pypdf` no instalado y `pdftotext` ausente), por lo que la comparación de texto PDF queda pendiente para la etapa de pruebas. No se probó contra la base real para evitar modificarla.

Las fixtures `tests/fixtures/*.xlsx` son archivos de entrada del importador (mesas con formatos, horas y errores); no se encontró un ejemplo de Excel/PDF de salida ni una plantilla de informe en `docs/`.

## Exportadores de informes de pasadas

| Pantalla/servicio | Salida y columnas | Origen de datos y filtros | Fechas, horas y errores |
|---|---|---|---|
| `ui/lista_pasadas.py` → `services/exportar.py::exportar_pasadas_excel` | Hoja `Pasadas`; columnas Hora, Turno, Objetivo, Supervisor. Encabezado con fecha, supervisor, turno y búsqueda. | La pantalla consulta `pasadas` con objetivos/supervisores, filtra por fecha operativa, supervisor, turno y texto, y pasa las filas ya filtradas. El exportador copia los campos `datos[1:5]`; no consulta ni recalcula. | La fecha se conserva como texto de filtro `AAAA-MM-DD`; hora se toma de `p.hora` sin normalización. No hay captura de errores en el servicio; la pantalla muestra el error de la tarea. No hay autofiltro, panel congelado, ajuste de texto ni anchos calculados. |
| `ui/lista_pasadas.py` → `services/exportar.py::exportar_pasadas_pdf` | Tabla con las mismas cuatro columnas y los filtros en un párrafo. | Recibe la misma consulta/filtrado de la pantalla; no consulta la base. | Hora tal cual está guardada. El PDF usa anchos fijos y cadenas sin párrafos de celda; texto largo no se ajusta. No repite la fila de cabecera al paginar ni añade numeración/pie. |
| `ui/reportes/reporte_mensual.py` → `services/exportar.py::exportar_excel` | Hoja llamada con mes/año; Objetivo, Días con pasada, Días sin pasada, Cumplimiento, Estado. | `_obtener_datos_reporte` mapea el dict de `services.reportes.generar_reporte_mensual`; el botón pasa el reporte visible, si existe. Sin reporte precalculado, el exportador genera otro sin los filtros de supervisor/turno/estado de la pantalla. El filtro se imprime como texto, pero no se aplica de nuevo. | Período `MM/AAAA`, generación `DD/MM/AAAA HH:MM`; no se exportan fechas/horas de pasadas. Los conteos son números, el porcentaje se convierte a texto con `%`. El mes se indexa antes de validar; un mes inválido puede causar `IndexError`. Las excepciones suben a la tarea y la pantalla las muestra. |
| `ui/reportes/reporte_mensual.py` → `services/exportar.py::exportar_pdf` | Mismas cinco columnas, filtro y una frase de resumen. No hay fila de total tabular. | Mismo origen del reporte mensual que Excel; ambos generan su propia representación, no comparten un objeto de exportación tipado. | Período y generación `MM/AAAA`, `DD/MM/AAAA HH:MM`. Conteos y porcentaje se convierten a cadenas. Anchos fijos, sin `repeatRows` ni ajuste de textos de celda; el logo se omite con aviso de logging ante los errores capturados, otros errores se propagan. |
| `ui/reportes/reporte_objetivo.py` → `_exportar_excel_objetivo` local | Hoja `Reporte`; Fecha, Día, Diurno, Nocturno, Estado, seguida de renglones de resumen con días esperados, coberturas y cumplimiento. | Datos calculados por `calcular_reporte_objetivo` en la propia pantalla, con SQL, fechas iteradas localmente y filtros supervisor/turno/estado. No usa el generador mensual como fuente. | Fecha `DD/MM/AAAA`; no exporta la hora. Conteos numéricos; porcentaje en texto. El nombre se inserta en el título/nombre de archivo sin sanitización (solo espacios a `_`). No hay manejo local de errores, anchos fijos ni wrap/filtro/congelado. |
| `ui/reportes/reporte_objetivo.py` → `_exportar_pdf_objetivo` local | Tabla diaria con Fecha, Día, Diurno, Nocturno, Estado y resumen de cumplimiento. | Mismo cálculo local anterior. Es un exportador distinto al servicio mensual y al exportador PDF mensual. | Fecha `DD/MM/AAAA`; no exporta la hora. Anchos fijos y valores de celda sin envoltura; no repite encabezados ni incluye pie/número de página. Usa `✔`/`✘` con la fuente Helvetica incorporada por defecto: el glifo puede no estar disponible aunque el texto español básico sí. Errores de generación se muestran por la tarea. |

No se encontró una pantalla PyQt independiente de “Reporte diario”. El servicio `services.reportes::generar_reporte_diario` entrega pasadas de una fecha operativa y conteo a la API; la pantalla `lista_pasadas.py` exporta el listado diario, no un modelo de reporte diario con objetivos, notas y totales.

## Otras salidas encontradas (no son exportadores de reportes operativos)

| Pantalla/servicio | Salida |
|---|---|
| `ui/importador/importar_excel.py` → `services/importador/reporte.py::generar_reporte_detallado` | XLSX temporal en memoria con hojas Análisis, Problemas y Horas normalizadas. Lo guarda la pantalla como `informe_importacion.xlsx`; informa errores con un mensaje genérico. No debe unificarse con informes de pasadas: explica problemas del archivo de entrada. |
| `services/exportacion_extendida.py` | CSV mensual de pasadas, CSV mensual de supervisor, JSON de reporte mensual y JSON parcial de base. Funciones de servicio sin llamadas desde las pantallas buscadas. Los CSV consultan SQL de forma propia; el mensual usa el rango común pero filtra `COALESCE(fecha_operativa, fecha)` como fecha; el JSON de reporte consume `services.reportes` y `services.estadisticas`. Abren rutas directamente y propagan errores. |
| `services/exportar_mes.py::exportar_mes_json` | Archivo JSON de intercambio mensual con objetivos, supervisores, pasadas, equipos y notas. Usa `rango_datetime_de_mes` y `mes_de_pasada`; forma parte del flujo de importar/exportar mes y puede crear backup al importar, no es un reporte para gerencia. |
| `services/auditoria.py::exportar_auditoria_csv` | CSV de auditoría: fecha, hora, usuario, operación, tabla, registro, detalles y estado. Consulta la tabla de auditoría; devuelve `False` y usa `print` en caso de error. |
| `ui/vista_indexacion.py::exportar_reporte` | Texto diagnóstico de índices/BD con fecha en el nombre. No es un informe de pasadas; escribe una ruta relativa fija y muestra un error con diálogo. |
| `services/importador/importacion.py::_exportar_pasadas_seguridad` | CSV de seguridad generado automáticamente durante importación; no es una exportación de reportes y no debe mezclarse con `data/exports_seguridad/` ni modificarse en esta etapa. |

La vista de auditoría importa `QFileDialog`, pero la búsqueda de usos no encontró un flujo activo que conecte esa pantalla con `exportar_auditoria_csv`; la función de servicio sí existe. Los CSV/JSON auxiliares no tienen consumidor UI encontrado en el código revisado.

## Fuentes de conteos y reglas detectadas

- El único módulo puro compartido de atribución es `services/pasadas/calculo_pasadas.py`: normaliza turno, calcula fecha/mes de turno y proporciona el rango semiabierto mensual e indexación de pasadas.
- El resumen mensual de `services/reportes.py` usa `rango_datetime_de_mes`, reconstruye fecha/hora con el módulo y agrupa mediante `indexar_pasadas_por_objetivo`. Cuenta días de cobertura como presencia por objetivo/día, no pasadas brutas; itera los días elegibles para calcular expectativa y cumplimiento. Respeta filtros de supervisor/turno en el índice y aplica estado después.
- El reporte por objetivo calcula por separado en `ui/reportes/reporte_objetivo.py`: consulta SQL, itera días del mes y cuenta expectativa/estado allí. Aunque consulta `rango_datetime_de_mes`, `fecha_hora_desde_fecha_turno`, `indexar_pasadas_por_objetivo` y `fecha_de_turno`, esta lógica de reporte está duplicada y vuelve a atribuir la fecha reconstruida. Debe moverse a la capa común sin cambiar la regla de cumplimiento.
- El reporte diario de `services/reportes.py` filtra por `COALESCE(fecha_operativa, fecha)`, cuenta filas con `len` y calcula cobertura de objetivos por nombre. No llama al módulo de pasadas en esa función. La fecha almacenada puede ser operativa o calendario en datos históricos, por lo que el filtro merece revisión al integrarse.
- Los CSV mensuales de `services/exportacion_extendida.py` consultan directamente SQL y usan `COALESCE(fecha_operativa, fecha)` más límites mensuales; no llaman a `mes_de_pasada` ni reconstruyen/validan el turno registro por registro.
- `services/exportar.py` no recalcula fechas, turnos ni conteos cuando recibe filas/reporte. El cálculo de reporte mensual ocurre en `services.reportes`; el exportador por objetivo llama al cálculo local de UI si no recibe un objeto precalculado.

### Errores observados y riesgos confirmados

1. En las pruebas temporales, el mes sin datos generó un libro válido con cabeceras y sin filas, sin mensaje ni prevención de un archivo vacío engañoso.
2. Los textos muy largos se guardan y generan en los cuatro servicios probados, pero el Excel no activa ajuste de texto y los PDF usan celdas sin `Paragraph`; por lo tanto no hay garantía de lectura completa ni ajuste en página.
3. El nombre de archivo del reporte por objetivo conserva caracteres del objetivo (excepto reemplazo de espacio); caracteres como `:`, `/`, `\\`, `?`, `*`, comillas o `< > |` pueden invalidar o alterar la ruta en Windows.
4. Ningún exportador de reportes protege `wb.save`/`doc.build` frente a `PermissionError`; una ruta abierta/bloqueada llega como error de tarea sin una acción específica para guardar con otro nombre. Tampoco hay generador común que detecte archivos existentes y gestione sobrescritura.
5. El PDF objetivo emite marcas de verificación/cruz con Helvetica estándar; el soporte de esos símbolos no está garantizado. El entorno impidió importar esa pantalla por falta de `libGL.so.1`, así que el caso exacto no se ejecutó.
6. Los exportadores no auditan por informe/usuario/ruta, no recuerdan carpeta, no ofrecen abrir archivo/carpeta y no comprueban permiso `reportes.exportar` antes de crear el archivo.
7. El tratamiento de tildes y eñes en los servicios mensual y listado se probó al generar archivos, pero no pudo verificarse por extracción PDF porque faltan `pypdf`/`pdftotext`. Los nombres y filtros se interpolan en `Paragraph` sin escapar caracteres XML; valores con `&`, `<` o `>` son candidatos a error o texto alterado.
8. La exportación mensual por objetivo agrega el nombre sin sanitizar al nombre predeterminado y la pantalla permite exportar antes de tener un reporte recién generado; en ese caso puede recalcularse sin los filtros actuales.

## Conclusión de fase

Hay dos flujos de exportación activos para el mismo dominio en `lista_pasadas.py` y `reporte_mensual.py`, más un tercer par independiente dentro de `reporte_objetivo.py`. No existe un exportador de reporte diario de UI ni una salida de reporte diario PDF/XLSX. La API expone reportes JSON con los servicios actuales, no archivos.

La implementación unificada debe tener una sola capa de datos tipada y reproducible, mantener separada la función de intercambio mensual y los informes de importación/diagnóstico, y producir ambos formatos desde la misma instancia. Las dudas de expectativa por turno y vigencia histórica están descriptas en `docs/reglas_de_calculo.md`; no se infiere que cada objetivo requiera una pasada por DIA y otra por NOCHE.

## Resultado de las fases de implementación

- Las tres pantallas con exportación se conectaron a `ui/reportes/acciones_exportacion.py` y `DialogoExportar`; conservan los filtros de fecha/supervisor/turno/búsqueda/estado aplicables. No se encontró una pantalla diaria separada. `Lista de pasadas` es el punto de entrada al detalle diario.
- `services/reportes_unificados/` concentra metadatos, catálogo de columnas, filas, totales, notas y subtotales. Los servicios existentes de cumplimiento y el módulo puro `services/pasadas/calculo_pasadas.py` siguen determinando los cálculos; los escritores Excel/PDF reciben el mismo `ReporteDatos`.
- `ReporteObjetivo` delega el cálculo a services y usa los mismos escritores y el diálogo. La API mensual ahora adapta el modelo común conservando el JSON histórico; la API diaria adapta el resultado del servicio diario para conservar su contrato.
- La exportación bloquea informes vacíos, sanitiza el nombre, rechaza sobrescrituras, traduce errores de archivo, registra errores técnicos, recuerda carpeta y ofrece abrir archivo/carpeta. Cada archivo generado añade una fila a auditoría; no se modifican datos operativos.
- Las plantillas se guardan en `QSettings`, por lo que no hizo falta migración. No se añadió dependencia. Los exportadores de compatibilidad en `services/exportar.py` se mantienen porque pruebas y posibles consumidores externos aún los usan; las pantallas migradas ya no los llaman.
- Agrupar ordena filas de detalle y el modelo calcula subtotales, que el PDF imprime. La barra de progreso es indeterminada; no hay indicador porcentual. La vista previa visualiza hasta 100 filas.
- El resumen mensual exige el mes completo; el reporte por objetivo requiere un objetivo y el mes completo. No se amplió a informes mensuales parciales porque el servicio define expectativa por mes calendario. La lista de objetivos de la pantalla objetivo limita el origen de selección al objetivo mensual disponible.
- El entorno no permite ejecutar las pantallas Qt: falta la biblioteca del sistema `libGL.so.1`. `compileall` y las pruebas de servicio/API/arquitectura sí se ejecutan.

## Comparación de cifras anterior/nueva (prueba sintética)

No había exportaciones de salida en fixtures/docs ni se usó la base real. La fixture dorada de octubre está marcada **SIN VERIFICAR**, por lo que no se presenta como verdad de negocio. Se comparó el exportador mensual anterior de `services/exportar.py` contra el nuevo Excel usando una base temporal de pytest, un objetivo laborable y una pasada DIA el miércoles 28/10/2026. El cálculo mensual del commit previo se conserva en el servicio; los campos comunes coinciden:

| Objetivo | Turno/métrica | Valor anterior | Valor nuevo | Causa probable / clasificación |
|---|---|---:|---:|---|
| Objetivo Test | Días esperados | 22 | 22 | Sin diferencia; misma expectativa mensual. |
| Objetivo Test | Días con pasada | 1 | 1 | Sin diferencia; misma fecha operativa. |
| Objetivo Test | Días sin pasada | 21 | 21 | Sin diferencia; misma regla de cobertura diaria. |
| Objetivo Test | Cumplimiento | 4,5 % | 4,5 % | Sin diferencia; porcentaje ponderado preservado. |
| Objetivo Test | Pasadas DIA (conteo bruto) | No expuesto | 1 | Métrica añadida en la nueva exportación, no una regresión comparable. |
| Objetivo Test | Pasadas NOCHE (conteo bruto) | No expuesto | 0 | Métrica añadida; no implica expectativa por turno. |

La comparación automatizada está en `test_exportador_anterior_y_unificado_coinciden_en_resumen_mensual`. No demuestra que el conteo de producción sea correcto: compara una entrada de prueba conocida y clasifica como **sin evidencia de regresión** únicamente las métricas compartidas. No se comparó un archivo viejo real ni se decidió la validez de filas del Excel de octubre.
