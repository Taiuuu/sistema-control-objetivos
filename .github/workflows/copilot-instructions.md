# Instrucciones para Copilot — Proyecto VESP Control de Objetivos

## Formato de respuesta (prioridad máxima)
- Respondé SOLO con código: el diff o el fragmento modificado. Nada de explicaciones, resúmenes, ni "esto es lo que hice" antes o después.
- No repitas código que no cambió. Si edito una función de 50 líneas y cambian 3, mostrame solo esas 3 (o el bloque mínimo necesario con contexto de 1-2 líneas arriba/abajo para ubicarlo).
- No agregues comentarios nuevos explicando el cambio salvo que lo pida explícitamente.
- Si algo es ambiguo, hacé UNA pregunta corta en vez de asumir y generar código de más. No expliques por qué preguntás.
- Nunca repitas el prompt ni parafrasees lo que pedí.
- Nunca agregues disclaimers, advertencias genéricas ni "tené en cuenta que...". Si hay un riesgo real y concreto (ej: rompe una función que se usa en otro lado), una línea, no un párrafo.

## Alcance de lectura
- No releas ni escanees el proyecto entero salvo que se pida explícitamente. Trabajá solo sobre el/los archivo(s) y fragmento(s) que te paso en el prompt.
- Si necesitás contexto de otro archivo para resolver algo, pedímelo puntualmente en vez de asumir o inventar la estructura.
- Preferí `CONTEXT.md` (si está en el repo) como fuente de verdad sobre la arquitectura general, en vez de inferir leyendo todo.

## Estilo de código
- Python 3, tipado con type hints donde ya se usa en el archivo.
- Seguí el estilo existente del archivo (nombres en español para dominio del negocio: `pasadas`, `turno`, `objetivo`, `supervisor`, `fecha_operativa`, etc. — no traduzcas a inglés).
- No reformatees código que no toqué (no cambies comillas, imports ya ordenados, etc. "de paso").
- No agregues logging/prints extra salvo que lo pida o que el archivo ya tenga ese patrón y sea consistente hacerlo.
- No agregues manejo de errores genérico (try/except amplios) salvo que se pida. Si agregás uno, que sea específico.
- No introduzcas dependencias nuevas sin avisar primero (una línea: "esto requiere instalar X").

## Reglas de dominio del proyecto (importante, no las cuestiones ni las expliques, solo aplicalas)
- El turno de una pasada lo define la hoja/sheet de origen (CONTROL_RECORRIDOS), no el horario. Un turno "nocturno" puede tener horarios variables (19-07, 20-08) y sigue siendo nocturno aunque la hora puntual esté fuera de rango.
- La fecha operativa de una pasada nocturna en horario de madrugada (00:00-06:59) corresponde al día anterior (el turno arrancó la noche previa).
- Nunca perder registros por descartarlos silenciosamente (`continue` sin loguear) cuando hay una discrepancia de datos — preferí forzar la regla de negocio correcta y loguear la discrepancia, no tirar el dato.

## Qué NO hacer nunca
- No reescribas archivos completos si el cambio es puntual.
- No sugieras refactors grandes no pedidos ("ya que estamos, también podríamos...").
- No agregues tests salvo que se pidan.
- No cambies nombres de funciones/variables existentes salvo que sea el pedido explícito.