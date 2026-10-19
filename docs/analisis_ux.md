# Auditoría visual y de usabilidad

Fecha de auditoría: 2026-10-19. Alcance: inspección estática de `ui/`, arranque y documentación de contexto; no se modificó código de producto en esta fase.

## Inventario de ventanas, pantallas y diálogos

La ventana de trabajo se compone actualmente de `LoginWindow` y `VentanaPrincipal`. La segunda tiene una landing inicial y una vista interna de control diario; no hay una clase de ventana Dashboard separada. También se detectaron las siguientes pantallas, formularios y diálogos:

| Grupo | Componentes |
|---|---|
| Inicio y navegación | `LoginWindow`; landing y control diario dentro de `VentanaPrincipal`; `Ayuda`; `ConfiguracionDialog`; diálogos de `CambiarPassword` |
| Operación y catálogos | `FormPasada`, `FormTurno`, `TablaDiaria`, `ListaPasadas` y `DialogoEditarPasada`; `ListaObjetivos` y `DialogoEditarObjetivo`; `ListaSupervisores` y `DialogoEditarSupervisor`; `FormObjetivo`, `FormSupervisor`, `NotasDiarias`, `VistaFeriados` |
| Importación y reportes | `ImportarExcel`, `DialogoResolverCoincidencias`, `ReporteMensual`, `ReporteObjetivo`, `DialogoExportar` |
| Administración | `GestionarUsuarios`, `VistaLogs`, `VistaAuditoria`, `VistaIndexacion`, `VistaSincronizacion`, `TransferirDatos` |
| Componentes de ventana reutilizables | `DialogoMensaje`, `OverlayProgreso`, `SidebarWidget`, `TablaCoberturaWidget`, `ModuleCard`, `Sparkline` |

Fuentes: clases de `ui/` y subdirectorios; listado de módulos en [docs/contexts/ui.md](./contexts/ui.md).

## Menú y sidebar actual

El orden de `VentanaPrincipal._construir_botones_menu` ([ui/ventana_principal.py](../ui/ventana_principal.py), líneas 382-495) es:

1. **Operación diaria**: Control diario, Registrar pasada, Registrar turno, Notas del día.
2. **Consultas y reportes**: Ver pasadas, Feriados, Reporte mensual, Reporte objetivo, Transferir datos, Importar Excel, Ayuda.
3. **Gestión**: Agregar objetivo, Ver objetivos, Agregar supervisor, Ver supervisores.
4. **Administración**: Gestionar usuarios, Historial, Optimización de BD, Auditoría detallada, Sincronización.
5. **Pie del sidebar**: Configuración y Cerrar sesión.

Los accesos se filtran mediante permisos y la preferencia guardada del menú. La app inicia en una landing con tarjetas principales; no es necesario añadirla desde cero, pero debe armonizarse con los roles y orden nuevos.

## Hallazgos ordenados por gravedad

### Bloquea el uso

No se confirmó un defecto que bloquee universalmente la navegación en la inspección estática. El resultado base de pytest sí quedó bloqueado en recolección por el entorno, no por fallos de la aplicación: cuatro módulos de pruebas PyQt no se pudieron importar porque falta `libGL.so.1` (ver sección de validación).

### Molesta

1. **Estilos paralelos y posible divergencia entre temas — resuelto en Fase 2.** La inspección inicial encontró dos QSS sin consumidores (`ui/tema_claro.qss`, `ui/tema_oscuro.qss`) y un acento distinto al institucional. Se retiraron los QSS obsoletos y el acento del tema Claro ahora usa `#0E7F09`; el test de temas impide reintroducir colores hex/rgb en `ui/` fuera de `ui/theme/tokens.py`.
2. **Sistema legacy de colores y responsabilidades duplicadas.** `VentanaPrincipal` mezcla tokens con `ui/widgets/estilos.py` (`obtener_color`), por ejemplo `ui/ventana_principal.py:105-124` y `:352-376`; el contexto identifica además `services/tema.py` como paleta legacy. Esta duplicidad hace que un cambio de tema pueda dejar partes desactualizadas.
3. **Configuración dispersa e incompleta.** `ui/configuracion.py:165-409` reúne navegación, backups y apariencia/tamaño de fuente, pero no presenta secciones internas para Cuenta, Acerca de, funciones visibles o atajos. El pie agrega Configuración aparte del menú por categorías (`ui/ventana_principal.py:508-558`).
4. **Acciones principales y filtros aún ocupan espacio fijo.** `ListaPasadas` tiene fecha y búsqueda en la fila principal, filtros avanzados desplegables, exportaciones, acciones de borrado y una fila administrativa de mes (`ui/lista_pasadas.py:395-510`). Es un avance parcial, pero falta rango/mes para consulta, recuento de filtros activos y limpiar filtros; en anchos pequeños hay muchas acciones concurrentes.
5. **Carga de datos y construcción de tablas síncronas en algunas vistas.** `VistaLogs._cargar_tabla` consulta y llena todos los elementos directamente (`ui/vista_logs.py:22-35, 88-98`); `VistaAuditoria._cargar_usuarios` y `_cargar_datos` realizan consultas/carga directa (`ui/vista_auditoria.py:160-220`); `ListaObjetivos._cargar_tabla` carga y reconstruye las tres tablas (`ui/lista_objetivos.py:455-500`). Pueden bloquear al crecer los datos. Las consultas de `ListaPasadas` también se ejecutan al cambiar filtros (`ui/lista_pasadas.py:477-506`); en contraste, exportación (`ui/reportes/acciones_exportacion.py:107-127`) y generación de ambos reportes usan `run_background_task`.
6. **Tablas sin estrategia uniforme para volumen o texto largo.** Varias pantallas usan `QTableWidget` y crean ítems por fila; `ListaObjetivos` rellena las tres pestañas en cada carga (`ui/lista_objetivos.py:455-499`). No se observa una política global de elipsis/tooltip para celdas largas o carga por lotes. En logs se ejecuta `fetchall()` sin límite (`ui/vista_logs.py:22-35`).
7. **Tamaños mínimos y fijos no uniformes.** Hay mínimos de 560×360 en objetivos, pasadas, auditoría e indexación (`ui/lista_objetivos.py:279`, `ui/lista_pasadas.py:402`, `ui/vista_auditoria.py:45`, `ui/vista_indexacion.py:28`) y un diálogo de pasada fijo 360×300 (`ui/lista_pasadas.py:243`). Hay que validar contenido y escalado a 1024×600/125%-150%; `VentanaPrincipal` fija mínimo 720×440 (`ui/ventana_principal.py:220-225`).
8. **Calidad visual y contraste no verificados en ejecución.** Hay QSS inline en múltiples componentes y pantallas (por ejemplo `ui/components/base.py:60-84`, `ui/configuracion.py:183-238`, `ui/lista_objetivos.py:339-454`); el resultado depende de que cada widget se conecte/reaplique al tema. Los calendarios cuentan con `configure_calendar_theme` y stylesheet global (`ui/components/calendar.py`, `ui/theme/stylesheet.py`), por lo que no se afirma aquí que estén negros, pero falta una prueba de tema para ventanas emergentes, cuadros estándar, menús y diálogos del sistema.
9. **Atajos parcialmente solapados y documentación incompleta.** `VentanaPrincipal` registra Ctrl+N para Notas y Ctrl+F global (`ui/ventana_principal.py:1425-1443`); la ayuda lista atajos por separado (`ui/ayuda.py`). `docs/contexts/ui.md` advierte que los rótulos y shortcuts no coinciden en todos los casos. Faltan F5, navegación Ctrl+1..9, escape contextual y revisión de foco en campos de edición.
10. **Rastros incompatibles con el diseño objetivo.** La búsqueda inicial no encontró en `ui/` menciones literales a `V.E.S.P`, “En vivo”, “Deshacer importación” o “modo rendimiento”, ni un interruptor oscuro/claro. En Fase 2 se eliminaron los QSS legacy que conservaban `DashboardTitle` y se quitó la opacidad de `GlassCard`, por lo que las cards son opacas. Continúan nombres internos legacy `GlassCard`/`wrap_content_in_glass_card` y `_mostrar_dashboard` (la acción visible se llama “Control diario”); su renombre técnico queda pendiente, sin efecto de vidrio/transparencia en la interfaz.

### Cosmético

- Los tokens son homogéneos por construcción: las cuatro paletas pasan por `_palette` (`ui/theme/tokens.py:4-79`), con el mismo conjunto actual de claves. No incluyen todavía un token explícito de selección, hover genérico o foco; esos estados se componen en QSS con acento/superficie.
- `ThemeLogo` resuelve un logo por tema (`ui/theme/tokens.py:105,132,159,192`). Los cuatro archivos referenciados existen: `assets/vespLogoDarkGreen.svg`, `assets/vespLogoLight.svg`, `assets/logo_vesp_transparente.png` y `assets/logo_vesp_fondo_oscuro_transparente.png`; no se detectó ausencia que requiera fallback.
- Las capturas en `docs/capturas_antes/` no existen en el árbol inspeccionado.
- `LoginWindow` ya impide maximizar/redimensionar con flags y tamaño fijo adaptado a la pantalla (`ui/login.py:241-268`), aunque el título de ventana es la marca correcta y no hay un rótulo visible “VESP Organizations” en el contenido del formulario.
- `ListaObjetivos` ya tiene las pestañas “Objetivos actuales”, “Objetivos finalizados” y “Todos” (`ui/lista_objetivos.py:315-323`), indicador “Pendiente de revisión” y operación para marcar revisado (`:485-490, 552-559`), y baja desde el menú ⋯ con confirmación que incluye el nombre (`:525-529, 570-588`). La selección depende de `Objetivo.es_activo()`; la regla y su ubicación se revisan en la fase correspondiente.
- La landing ya presenta tarjetas y las actualiza según visibilidad del menú (`ui/ventana_principal.py:690-739`). El sidebar colapsa por ancho en `:1504-1511`; no se verificaron capturas que acrediten la legibilidad efectiva en todos los tamaños.

## Registro de los 10 problemas y estado

Este archivo es la línea base de la Fase 1. En Fase 2 se resolvieron el hallazgo 1, la opacidad de cards del 10 y se cubrieron tokens de estado/selección/hover/deshabilitado en el stylesheet global. Los demás hallazgos continúan pendientes de las fases de navegación, responsive y fluidez; las funciones ya existentes listadas como avances se deben preservar.

## Validación base

- `python -m pytest`: **falló en colección**; 234 pruebas detectadas, 4 errores de importación en `test_configuracion_theme.py`, `test_pasadas_ui.py`, `test_theme_components.py` y `test_theme_system.py`, todos causados por `ImportError: libGL.so.1: cannot open shared object file`. No se ejecutaron las pruebas de esos módulos.
- `python -m compileall .`: pendiente de la validación de cierre de esta fase.

## Mediciones de apertura

No se tomaron tiempos de apertura en esta auditoría. La medición comparativa antes/después corresponde a la fase de fluidez; cualquier valor debe obtenerse ejecutando la aplicación con una base de prueba y un mismo perfil de datos.
