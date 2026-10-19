Última actualización: 2026-10-19

Propósito: documentar el sistema real de temas y componentes visuales de VESP.
Describe el código actual; no implica que todas las pantallas cumplan contraste o usen tokens.

Archivos clave:
- `ui/theme/tokens.py` — paletas Claro, Verde, Negro, Grafito y tokens semánticos.
- `ui/theme/theme_manager.py` — singleton, preferencia local, señales y aplicación a QApplication.
- `ui/theme/stylesheet.py` — stylesheet global construido desde tokens.
- `ui/theme/colors.py` — colores auxiliares.
- `ui/components/base.py`, `ui/components/indicators.py` — GlassCard, KPI, badge y logo.
- `ui/configuracion.py` — selector de tema y tamaño de fuente.
- `ui/widgets/estilos.py` — paletas legacy independientes.

Flujo: selector → `ThemeManager.set_theme` → preferencia `~/VESP Control/tema.json` → paleta/stylesheet global → `theme_changed` → componentes conectados reaplican tokens.

Tokens: la paleta define fondos, superficies, texto, acento, estados, logo, radios, espacios y tamaños. Los nombres canónicos son Claro, Verde, Negro y Grafito; `available_themes()` y `tokens()` son contratos públicos del gestor.

Invariantes: solicitar tema no reconocido produce `ValueError`; cambio de fuente acepta enteros entre 9 y 20; el tema por defecto al no hallar preferencia es Grafito; logo por tema se resuelve en `tokens.py`.

Trampas conocidas: hay colores específicos con valores distintos a la paleta institucional solicitada (incluido acento de Claro) y estilos inline/locales en pantallas; no asegurar WCAG AA ni ausencia total de colores hardcodeados sin auditoría visual. `services/tema.py` es un sistema legacy aparte.

Dependencias: la UI y los componentes consumen el manager/tokens; assets se resuelven con `services/assets.py`; [ui.md](./ui.md) cubre pantallas y atajos.

Cómo actualizar este archivo: cotejar tokens, persistencia, señal y consumidores después de cambiar tema o estilos compartidos.
