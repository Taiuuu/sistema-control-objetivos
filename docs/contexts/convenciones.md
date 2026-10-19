Última actualización: 2026-10-19

Propósito: conservar reglas de trabajo verificadas para cambios pequeños y seguros.
Las expectativas arquitectónicas están automatizadas parcialmente en `tests/test_arquitectura.py`.

Archivos clave:
- `docs/estructura.md` — límites y excepciones actuales entre paquetes.
- `tests/test_arquitectura.py` — inspección AST y allowlists de dependencias.
- `pytest.ini`, `docs/requirements-dev.txt` — descubrimiento y dependencias de pruebas.
- `services/exceptions.py` — excepciones de dominio/servicio.
- `.github/copilot-instructions.md` — instrucciones breves al agente.

Flujo: UI → services → database; API puede usar services/models; models debería aislarse; database y models no deben depender de UI. `tests/test_arquitectura.py` conserva allowlists explícitas para deuda actual.

Estilo observado: Python, nombres de dominio en español en UI/servicios y nombres técnicos cuando ya existen; reutilizar funciones públicas y servicios existentes; no duplicar reglas de fecha, esquema o matching. Cambios localizados con el formateo existente del archivo.

Errores: validar en la capa que tiene contexto, usar excepciones específicas existentes y propagar errores con registro/notificación cuando corresponde; no convertir fallos de persistencia en éxito aparente ni descartar filas del importador sin problema trazable.

No hacer: no inventar rutas, servicios, APIs ni columnas; no importar UI desde services; no sumar accesos SQLite en UI ni nuevos ciclos entre paquetes; no duplicar la regla de pasadas; no cambiar formato de datos existente sin migración/compatibilidad.

Pruebas: `python -m pytest` ejecuta suite; seleccionar `tests/test_arquitectura.py`, `tests/test_calculo_pasadas.py`, `tests/test_importador_integridad.py`, `tests/test_backup_seguridad.py`, `tests/test_api.py` según cambio. La validación completa puede necesitar dependencias de `docs/requirements-dev.txt` y entorno Qt.

Invariantes: nuevos módulos deben satisfacer arquitectura o añadirse como excepción justificada; cambios de estructura requieren actualizar contexto; aplicar cambios de esquema con migración y backup previo.

Trampas conocidas: allowlists arquitectónicas reflejan infracciones existentes, no permiso para extenderlas sin justificar; `models/` todavía importa servicios/database en módulos listados.

Dependencias: índice central en [00-indice.md](./00-indice.md); reglas arquitectónicas en [estructura.md](../estructura.md).

Cómo actualizar este archivo: ajustar reglas solo cuando test, tooling o convención mantenida cambie y comprobar el comando real.
