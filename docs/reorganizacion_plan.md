# Plan de reorganización

Los movimientos confirmados se aplican con `git mv`; cada lote se actualiza, valida y confirma antes de avanzar. Los cambios que rompen compatibilidad externa o dependen de archivos locales no versionados quedan pendientes de decisión.

| Ruta actual | Ruta nueva | Motivo | Referencias a actualizar / estado |
|---|---|---|---|
| `services/actualizador.py` | `services/actualizaciones/actualizador.py` | Módulo hoja sin imports internos del proyecto; agrupar la funcionalidad de actualización. | `scripts/main.py`; mantener el acceso runtime a `version.txt` y la URL pública sin cambios. |
| `CONTROL RECORRIDOS - SEPTIEMBRE - 2026.xlsx` | `tests/fixtures/CONTROL RECORRIDOS - SEPTIEMBRE - 2026.xlsx` | Fixture dorado del importador; ya está versionado y contiene datos reales. | `tests/test_importador_integridad.py`, documentación que lo sitúa en raíz; confirmar la prueba del importador. |
| `scripts/instalador.iss` | `instalador.iss` | El `.iss` es archivo de empaquetado permitido en raíz; el workflow ya espera esa ubicación. | `GUIA_INSTALADOR_INNO_SETUP.txt`, referencias textuales; confirmar `release.yml`. |
| `database/__pycache__/*.pyc`, `models/__pycache__/*.pyc`, `ui/__pycache__/*.pyc` | Eliminados del índice (archivos generados) | Bytecode no debe versionarse y `.gitignore` ya lo excluye. | Verificar que no queden `.pyc` versionados; no borrar fuentes. |
| `seguridad.db` | `data/seguridad.db` | Base local en la raíz, fuera de la estructura permitida. | Verificar rutas de base; mantener el contenido existente y no incluir datos nuevos en commits. |
| `sync_queue.json` | `data/sync_queue.json` | Estado runtime en la raíz, fuera de la estructura permitida. | Actualizar `services/sync_manager.py` y comprobar `ruta_sync_queue()`. |
| `version.txt` | Pendiente de decisión | Es consumido por actualizaciones ya instaladas a través de una URL pública en raíz y por `services.actualizador`; moverlo rompe compatibilidad de versiones anteriores. | Mantener la ruta hasta definir compatibilidad de URL, CI y empaquetado. |
| `CONTROL RECORRIDOS - OCTUBRE - 2026.xlsx` (raíz, no versionado) | Pendiente de decisión | Archivo local fuera del índice y existe una fixture de octubre aparte; no alterar datos locales sin verificar identidad y uso. | Comparar contenido y referencias antes de decidir. |
| Módulos planos de `services/` | Subpaquetes funcionales (`pasadas/`, `reportes/`, `backups/`, `usuarios_seguridad/`, `sincronizacion/`) | La mayoría tiene múltiples imports directos desde UI, API, scripts y tests. | Pendiente de decisión por alto acoplamiento y por la imposibilidad actual de ejecutar el verificador Qt. No cambiar lógica. |
| Pantallas planas de `ui/` | Subpaquetes por funcionalidad (`pasadas/`, `objetivos/`, `importador/`, `reportes/`, `usuarios/`, `configuracion/`, `comunes/`) | Los imports entre pantallas y desde `VentanaPrincipal` son numerosos; varios acceden directamente a SQLite. | Pendiente de decisión; requiere lote integral de imports/rutas y pruebas con Qt disponible. |
| `database/db.py`, `database/gestor_db.py` | Subcarpetas de conexión/repositorios | Importadas directamente desde modelos, servicios, UI, API y scripts. | Pendiente de decisión: modificarlo exige cambios de compatibilidad amplios. |
| `models/*.py` | Se mantienen en `models/` | No se recomienda mover antes de resolver la dependencia actual `models -> database`. | Registrar la violación en `tests/test_arquitectura.py`; no reescribir lógica en esta tarea. |
| `api/` y `api/routes/` | Sin movimiento | Ya conserva `python -m api.app` y separa rutas en blueprints. | Mantener el punto de entrada. |
| `scripts/main.py` | Sin movimiento | Punto de entrada desktop establecido. | Mantener `python scripts/main.py`. |

## Archivos grandes

No se dividen archivos ni se altera lógica. Se recomienda evaluar en otra tarea los módulos de más de 25 KB, especialmente `ui/ventana_principal.py`, `services/importador/importacion.py`, `ui/importar_excel.py`, `database/db.py`, `ui/lista_objetivos.py`, `ui/reporte_objetivo.py`, `ui/lista_pasadas.py` y `ui/widgets/tabla_cobertura.py`.