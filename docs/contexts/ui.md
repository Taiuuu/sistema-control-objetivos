Última actualización: 2026-10-19

Propósito: localizar pantallas principales, servicios consumidos y atajos.
La UI está organizada por función, pero conserva algunas consultas SQLite y acoplamientos legacy.

Archivos clave:
- `scripts/main.py` — arranque PyQt, logging, login y apertura de ventana principal.
- `ui/ventana_principal.py` — landing, control diario, navegación, sesión, tema y atajos generales.
- `ui/form_pasada.py`, `ui/form_de_turno.py`, `ui/lista_pasadas.py`, `ui/tabla_diaria.py` — operación diaria; usan modelos, validaciones, consultas y/o SQLite.
- `ui/lista_objetivos.py`, `ui/form_objetivo.py`, `ui/lista_supervisores.py`, `ui/form_supervisor.py` — catálogos; modelos, permisos/sync y acceso legacy.
- `ui/importador/importar_excel.py` — vista previa/resoluciones del servicio importador.
- `ui/reportes/reporte_mensual.py`, `ui/reportes/reporte_objetivo.py`, `ui/reportes/dialogo_exportar.py`, `ui/widgets/tabla_cobertura.py` — reportes y selección de exportación.
- `ui/feriados.py`, `ui/notas_diarias.py` — calendario/feriados y notas.
- `ui/login.py`, `ui/cambiar_password.py`, `ui/gestionar_usuarios.py` — identidad, contraseña y cuentas.
- `ui/configuracion.py`, `ui/vista_auditoria.py`, `ui/vista_logs.py`, `ui/vista_indexacion.py`, `ui/vista_sincronizacion.py` — preferencias/backups, auditoría, logs, BD y sincronización.
- `ui/theme/` — temas globales; `ui/components/` y `ui/widgets/` — componentes visuales.
- `ui/tabla_lotes.py` — renderizado progresivo de filas de `QTableWidget` para no monopolizar el bucle de eventos.
- `ui/feedback.py` — mensajes de error simples en español; conserva detalles técnicos en el log.
- `ui/ayuda.py` — tabla de atajos y FAQ.

Flujo: `scripts/main.py` → login → `VentanaPrincipal` → pantallas/diálogos → servicios y modelos; la interfaz recibe señales para refrescar tema y tareas asíncronas.

Tema: `ui/theme/tokens.py` define Claro, Verde, Negro y Grafito; `theme_manager.py` aplica paleta/stylesheet a QApplication y emite cambios; `stylesheet.py` y componentes enlazan tokens. Ver [ui-theme.md](./ui-theme.md), no duplicar tokens acá.

Sidebar actual: Operación diaria → Objetivos y supervisores → Reportes y consultas → Importación y datos → Administración; Configuración y Cerrar sesión permanecen en el pie. La landing inicial se llama “Inicio” y filtra tarjetas por permisos/preferencias. Configuración contiene pestañas Temas, Funciones visibles, Backups y datos, Cuenta y Acerca de.

Vigencia de objetivos: las pestañas y la API usan `services/estado_objetivos.py`; no se debe volver a clasificar por fecha directamente en la pantalla. Ver el criterio de fin de hoy en [reglas_de_calculo.md](../reglas_de_calculo.md).

Atajos: `ui/atajos.py` es el catálogo único; la ayuda lo muestra y el manual lo documenta. La ventana principal registra Ctrl+P/O/S/T/R/B, Ctrl+N para alta, Ctrl+F, F1/Ctrl+H, F5, Ctrl+1…9, zoom, fecha y sidebar. Las pantallas que admiten altas, búsqueda, actualización o exportación registran Ctrl+N, Ctrl+F, F5 o Ctrl+E localmente. Los reportes también usan Ctrl+Enter. Esc limpia un buscador reconocido o cierra la ventana. Los atajos de acción se protegen cuando un campo de texto tiene el foco.

Responsive: la ventana principal usa un mínimo de 720×440, colapsa el sidebar por debajo de 980 px y lo vuelve a expandir sobre 1120 px; Ctrl+\\ y el botón permiten cambiarlo manualmente. Guarda/restaura su geometría con QSettings en `VESP Organizations/Interfaz`, clave `ventana_principal/geometria`. La prueba `tests/test_responsive_ui.py` recorre 23 pantallas en 1920×1080, 1366×768 y 1024×600 con los cuatro temas; `VESP_GENERAR_CAPTURAS_UI=1` guarda capturas en `docs/capturas_despues/`, excluido de Git.

DPI: Qt 6 aplica escalado de alta densidad; `scripts/main.py` usa la política PassThrough antes de crear QApplication para conservar factores fraccionarios.

Fluidez: las listas de pasadas, objetivos, logs y auditoría consultan mediante `services.background_task.run_background_task`; actualizaciones obsoletas se descartan con identificadores de solicitud y la interfaz muestra estado de carga. El renderizado de filas se distribuye en lotes con `ui/tabla_lotes.py`. La preferencia “Reducir animaciones” se guarda en QSettings y evita los efectos de entrada.

Accesibilidad: las acciones solo con icono deben tener tooltip y nombre accesible; los botones y controles muestran foco visible mediante el token `focus`. Las tablas vacías deben acompañarse de un estado claro. Los errores técnicos se registran y la pantalla muestra una instrucción breve, no la excepción.

Invariantes: pantallas nuevas deben consumir servicios cuando exista contrato adecuado; UI no debe importar `database` ni SQL directo según arquitectura objetivo; actualizar temas en diálogos/widgets relevantes.

Trampas conocidas: excepciones UI→SQLite figuran en `tests/test_arquitectura.py`; algunos textos del menú muestran Ctrl+Ñ pero no está en la lista de shortcuts registrados; el tema global no elimina estilos locales hardcodeados automáticamente.

Dependencias: tema detallado en [ui-theme.md](./ui-theme.md), capas en `docs/estructura.md`, permisos en `seguridad_y_usuarios.md`, cálculos en `calculo.md`.

Cómo actualizar este archivo: verificar imports, atajos registrados y pantallas en la ventana principal al modificarlos.
