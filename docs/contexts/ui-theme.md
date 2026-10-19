Última actualización: 2026-10-19

Propósito: reglas de implementación de los cuatro temas y componentes visuales.

Archivos clave:
- `ui/theme/tokens.py`: paletas y contrato común de tokens.
- `ui/theme/theme_manager.py`: preferencia local, paleta Qt, stylesheet y señal `theme_changed`.
- `ui/theme/stylesheet.py`: controles globales, calendario, tablas, diálogos y estados.
- `ui/theme/colors.py`: conversión de colores a `QColor`.
- `ui/components/base.py`, `ui/components/indicators.py`: cards, KPI, badges y logos.
- `ui/configuracion.py`: selector y preferencia de tamaño de fuente.

Flujo: selector → `ThemeManager.set_theme` → `~/VESP Control/tema.json` → `QApplication` palette/stylesheet → `theme_changed` → componentes propios reaplican estilos dependientes del tema.

Temas: nombres canónicos: Claro, Verde, Negro y Grafito. Cada paleta se construye con `_palette` y comparte las mismas claves:
- Superficies: `bg_gradient_start`, `bg_gradient_end`, `surface`, `surface_alt`, `card_contrast`, `border`.
- Texto/estados: `text_primary`, `text_secondary`, `text_disabled`, `success`, `success_text`, `warning`, `warning_text`, `danger`, `danger_text`.
- Interacción: `accent`, `accent_text`, `accent_hover`, `accent_hover_text`, `focus`, `hover_bg`, `hover_text`, `selection_bg`, `selection_text`, `disabled_bg`.
- Componentes y marca: botones de peligro, sidebar, sombra, logo, radios, espaciado, tipografía y dimensiones.

Para agregar un tema: definir una paleta completa con `_palette`, asignarla a `THEMES`, agregar su logo en `assets/` y actualizar las pruebas de temas/logos. No agregues colores locales en pantallas; consumí tokens. La prueba de contraste es la referencia automatizada para los estados.

Responsive: usar layouts y políticas de tamaño; no fijar anchuras de contenido. Los calendarios se inicializan con `configure_calendar_theme`; el stylesheet global cubre calendario, tablas, encabezados, combos, tooltips, menús, cuadros de mensaje y diálogos de archivo. La app fuerza diálogos de archivo Qt no nativos para que el tema sea aplicable.

Verificación visual: `tests/test_responsive_ui.py` comprueba widgets visibles en 23 pantallas, tres tamaños y los cuatro temas. Para guardar imágenes con `QWidget.grab()`, ejecutá `VESP_GENERAR_CAPTURAS_UI=1 python -m pytest tests/test_responsive_ui.py`; los archivos van a `docs/capturas_despues/` y no se versionan.

DPI y ventana principal: el arranque configura `PassThrough` antes de crear QApplication; Qt 6 realiza el escalado de alta densidad. La ventana principal guarda y restaura su geometría, limitada por su mínimo de 720×440. Las ventanas secundarias deben usar layouts y mínimos que permitan 1024×600.

Invariantes: un nombre de tema no reconocido produce `ValueError`; tamaño de fuente entre 9 y 20; el tema por defecto es Grafito; los logos por tema se resuelven en `tokens.py`. Los fondos de cards son opacos: no usar transparencias ni efectos de vidrio.

Atajos: se registran desde navegación y pantallas; mantener sus nombres y tooltips sincronizados con [ui.md](./ui.md) y la ayuda de la app.

Accesibilidad: usar el token `focus` para el borde visible de los controles; conservar contraste de texto, tooltips y nombres accesibles para botones solo con icono.

Animaciones: breves y no bloqueantes; leer la preferencia de reducir animaciones cuando esté disponible.

Dependencias: assets vía `services/assets.py`; contexto de pantallas y navegación en [ui.md](./ui.md).
