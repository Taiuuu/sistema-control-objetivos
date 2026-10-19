Última actualización: 2026-10-19

Propósito: localizar pantallas principales, servicios consumidos y atajos.
La UI está organizada por función, pero conserva algunas consultas SQLite y acoplamientos legacy.

Archivos clave:
- `scripts/main.py` — arranque PyQt, logging, login y apertura de ventana principal.
- `ui/ventana_principal.py` — dashboard/tablas, navegación, sesión, tema y atajos generales.
- `ui/form_pasada.py`, `ui/form_de_turno.py`, `ui/lista_pasadas.py`, `ui/tabla_diaria.py` — operación diaria; usan modelos, validaciones, consultas y/o SQLite.
- `ui/lista_objetivos.py`, `ui/form_objetivo.py`, `ui/lista_supervisores.py`, `ui/form_supervisor.py` — catálogos; modelos, permisos/sync y acceso legacy.
- `ui/importador/importar_excel.py` — vista previa/resoluciones del servicio importador.
- `ui/reportes/reporte_mensual.py`, `ui/reportes/reporte_objetivo.py`, `ui/reportes/dialogo_exportar.py`, `ui/widgets/tabla_cobertura.py` — reportes y selección de exportación.
- `ui/feriados.py`, `ui/notas_diarias.py` — calendario/feriados y notas.
- `ui/login.py`, `ui/cambiar_password.py`, `ui/gestionar_usuarios.py` — identidad, contraseña y cuentas.
- `ui/configuracion.py`, `ui/vista_auditoria.py`, `ui/vista_logs.py`, `ui/vista_indexacion.py`, `ui/vista_sincronizacion.py` — preferencias/backups, auditoría, logs, BD y sincronización.
- `ui/theme/` — temas globales; `ui/components/` y `ui/widgets/` — componentes visuales.
- `ui/ayuda.py` — tabla de atajos y FAQ.

Flujo: `scripts/main.py` → login → `VentanaPrincipal` → pantallas/diálogos → servicios y modelos; la interfaz recibe señales para refrescar tema y tareas asíncronas.

Tema: `ui/theme/tokens.py` define Claro, Verde, Negro y Grafito; `theme_manager.py` aplica paleta/stylesheet a QApplication y emite cambios; `stylesheet.py` y componentes enlazan tokens. Ver [ui-theme.md](./ui-theme.md), no duplicar tokens acá.

Sidebar actual: Operación diaria → Objetivos y supervisores → Reportes y consultas → Importación y datos → Administración; Configuración y Cerrar sesión permanecen en el pie. La landing inicial se llama “Inicio” y filtra tarjetas por permisos/preferencias. Configuración contiene pestañas Temas, Funciones visibles, Backups y datos, Cuenta y Acerca de.

Vigencia de objetivos: las pestañas y la API usan `services/estado_objetivos.py`; no se debe volver a clasificar por fecha directamente en la pantalla. Ver el criterio de fin de hoy en [reglas_de_calculo.md](../reglas_de_calculo.md).

Atajos globales registrados en ventana principal: Ctrl+P pasada, O objetivo, S supervisor, T turno, N notas, R reporte mensual, B recargar, F buscar, H ayuda, =/- zoom, flechas izquierda/derecha cambiar fecha, Ctrl+\\ sidebar. Esc cierra diálogos/ventanas que registran ese shortcut. Reportes: Ctrl+Enter genera y Ctrl+E exporta Excel. La ayuda omite algunos atajos registrados; modificarla junto a los shortcuts.

Invariantes: pantallas nuevas deben consumir servicios cuando exista contrato adecuado; UI no debe importar `database` ni SQL directo según arquitectura objetivo; actualizar temas en diálogos/widgets relevantes.

Trampas conocidas: excepciones UI→SQLite figuran en `tests/test_arquitectura.py`; algunos textos del menú muestran Ctrl+Ñ pero no está en la lista de shortcuts registrados; el tema global no elimina estilos locales hardcodeados automáticamente.

Dependencias: tema detallado en [ui-theme.md](./ui-theme.md), capas en `docs/estructura.md`, permisos en `seguridad_y_usuarios.md`, cálculos en `calculo.md`.

Cómo actualizar este archivo: verificar imports, atajos registrados y pantallas en la ventana principal al modificarlos.
