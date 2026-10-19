# Instrucciones de Copilot

- Antes de modificar código, leer `docs/contexts/00-indice.md` y el contexto específico relacionado.
- Respetar las capas: UI → services → database; services no dependen de UI; database no depende de services/UI; models se mantiene independiente.
- No inventar rutas, funciones, columnas ni comportamientos: verificarlos en el código y reutilizar APIs existentes.
- La arquitectura conserva excepciones legacy documentadas en `tests/test_arquitectura.py`; no ampliarlas sin necesidad y justificación.
- Mantener cambios quirúrgicos y actualizar pruebas cuando cambie el comportamiento.
- Al terminar un cambio estructural, actualizar el contexto correspondiente y su fecha.
- No incluir secretos, credenciales ni valores sensibles en documentación, ejemplos o código.
- Ejecutar las pruebas pertinentes antes de dar el cambio por terminado; usar `python -m pytest` para la suite completa.
