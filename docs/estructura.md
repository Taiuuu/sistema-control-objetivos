# Estructura del proyecto

```text
.
├── _archivo/                         Datos versionados archivados sin uso runtime
│   ├── seguridad.db                  Copia SQLite antigua preservada
│   └── sync_queue.json               Cola antigua preservada
├── api/                              Aplicación Flask (`python -m api.app`)
│   └── routes/                       Blueprints de la API
├── assets/                           Imágenes, iconos y recursos compartidos
├── core/                             Configuración y utilidades de instancia/logging
├── database/                         Conexión SQLite y gestor de persistencia
├── docs/                             Manuales, análisis, planes e inventarios
│   └── contexts/                     Contextos de diseño y producto
├── models/                           Entidades, tipos y validadores de dominio
├── scripts/                          Entrada desktop y utilidades operativas
│   └── main.py                       Entrada principal PyQt6
├── services/                         Servicios de aplicación y lógica de negocio
│   ├── actualizaciones/              Actualización de la aplicación
│   ├── backups/                      Copias de seguridad y restauración
│   ├── importador/                   Pipeline y estado de importación Excel
│   ├── pasadas/                      Reglas puras de atribución y conteo
│   └── reportes_unificados/          Modelo, consultas, escritores y archivos de reportes
│       ├── modelos.py, datos.py, consultas.py, objetivo.py
│       ├── excel.py, pdf.py, archivos.py
├── tests/                            Suite automatizada
│   ├── fixtures/                     Libros dorados completos y archivos de entrada
│   ├── golden/                       Resultados y cargadores de pruebas doradas
│   ├── test_arquitectura.py          Reglas de dependencias inspeccionadas con AST
│   └── test_sin_rutas_viejas.py      Detección de referencias a rutas migradas
└── ui/                               Interfaz PyQt6
    ├── components/                   Componentes visuales reutilizables
    ├── importador/                   Importación desde Excel
    ├── reportes/                     Reportes, diálogo y flujo de exportación compartido
    ├── theme/                        Tokens, colores y estilos
    └── widgets/                      Widgets reutilizables
```

## Reglas de dependencia

- `ui` puede depender de `services`; las pantallas deberían evitar importar `database` o ejecutar SQL directamente.
- `services` puede depender de `database` y `models`, pero no debería depender de PyQt6.
- `database` no debería depender de `services` ni de `ui`.
- `models` debería contener dominio independiente de `database`, `services` y `ui`.
- `api` conserva su punto de entrada Flask y registra sus blueprints en `api/routes/`.
- `services/reportes_unificados/` prepara datos y metadatos sin depender de PyQt6; `services/reportes.py` se conserva como API histórica de cálculo.
- `ui/reportes/acciones_exportacion.py` conecta el diálogo reutilizable con proveedores de datos y persistencia en segundo plano.
- `scripts/main.py` conserva la entrada desktop.

## Deuda conocida

`tests/test_arquitectura.py` enumera excepciones existentes: los modelos consultan SQLite y servicios; la capa database usa servicios de backup/caché; cuatro servicios usan Qt para tareas, actualización o notificaciones; varias pantallas ejecutan consultas o importan directamente database. El test AST falla cuando aparecen módulos nuevos fuera de esas listas. También documenta los ciclos actuales `database`/`services`, `database`/`services`/`models` y `services`/`models`.

Quedan módulos funcionales planos en `services/` y `ui/`; su traslado requiere actualizar numerosos imports. Se dejaron pendientes para evitar una migración masiva sin poder ejecutar Qt en este contenedor.

## Tamaño y archivos de raíz pendientes

Se recomienda evaluar en otra tarea la división de `ui/ventana_principal.py`, `services/importador/importacion.py`, `ui/importador/importar_excel.py`, `database/db.py`, `ui/lista_objetivos.py`, `ui/reportes/reporte_objetivo.py`, `ui/lista_pasadas.py` y `ui/widgets/tabla_cobertura.py`. No se partieron en esta reorganización.

`pytest.ini` permanece en raíz para el descubrimiento estándar de pytest; `version.txt` permanece por la URL pública y compatibilidad del actualizador. La fixture simplificada de octubre y el libro completo del conteo dorado son archivos distintos; ambos se conservan en `tests/fixtures/`.