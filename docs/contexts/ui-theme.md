Estoy trabajando en VESP Organizations, una app de escritorio en Python 3.11+ con PyQt6 y SQLite (carpetas: ui/, services/, database/, models/, api/). Quiero rediseñar la apariencia visual por ETAPAS, sin romper nada de la lógica ni de las funciones existentes.

ESTILO VISUAL:
- Superficies opacas con bordes redondeados (16-20px), borde fino y sombra suave.
- Fondo con degradado suave según el tema.
- Sidebar a la izquierda sobre una card translúcida; ítem activo como "pill" resaltada; inactivos con ícono + texto en gris suave.
- Título grande de pantalla arriba a la izquierda, usuario/menú arriba a la derecha.
- Fila de KPIs en una card: ícono en círculo + etiqueta chica + número grande.
- Tablas limpias, sin grillas pesadas, filas con aire, barras de progreso finas.
- Una card de contraste para info destacada (ej. alertas pendientes).
- Tipografía sans-serif limpia, jerarquía clara por tamaño y peso.

IDENTIDAD DE MARCA (VESP Organizations, Seguridad Privada). Colores institucionales exactos:
- Verde institucional #0E7F09
- Verde claro #60BA5A
- Negro #000000
- Grafito #231F20
- Blanco #FFFFFF
NO usar naranja ni otros acentos fuera de esta paleta (salvo colores semánticos de estado: advertencia/peligro, que deben convivir bien con la paleta).

CUATRO TEMAS seleccionables (cada uno corresponde a una variante del logo):
1. "Claro": fondo blanco / gris muy suave, acento #0E7F09, texto #231F20.
2. "Verde": fondo #0E7F09 con degradé a un verde más oscuro, acento blanco y #60BA5A, texto blanco.
3. "Negro": fondo #000000, acento blanco con detalles #60BA5A, texto blanco.
4. "Grafito": fondo #231F20, acento #60BA5A, texto blanco.
Regla de contraste: en temas oscuros, texto y acentos usan #60BA5A (NO #0E7F09, que no alcanza contraste sobre negro/grafito); #0E7F09 solo para superficies, bordes o botones con texto blanco.

REGLAS NO NEGOCIABLES:
1. Los 4 temas deben tener el mismo estilo de superficies opacas y cambiarse en caliente, aplicándose a TODA la app, incluidos diálogos y ventanas secundarias.
2. Cero textos ilegibles: contraste mínimo WCAG AA en los 4 temas.
3. Prohibido hardcodear colores en widgets. Todo color sale del archivo de tokens de tema.
4. No cambiar lógica de negocio, base de datos, servicios ni API. Solo capa visual.
5. Performance: la app no puede sentirse lenta. Prohibido QGraphicsDropShadowEffect en muchos widgets chicos o celdas de tablas; usarlo solo en cards grandes (máx. ~6 por pantalla).
6. Cambios chicos y revisables: tocar solo los archivos de la etapa actual, y al terminar decirme qué archivos modificaste y cómo probar que no se rompió nada.
7. La ventana conserva un fondo de degradado opaco; no usar translucidez de ventana ni efectos Acrylic/Mica/DWM.
8. El token logo_path selecciona el logo por tema: Claro usa assets/vespLogoDarkGreen.svg, Verde usa assets/vespLogoLight.svg, Negro usa assets/logo_vesp_transparente.png y Grafito usa assets/logo_vesp_fondo_oscuro_transparente.png.