# UI/UX Improvements v2.0

Mejoras de interfaz y experiencia de usuario implementadas en v2.0.

---

## 🎨 Sistema de Temas

### Tema Oscuro (Default)

- Fondo: `#1a1a1a` (casi negro)
- Texto: `#ffffff` (blanco puro)
- Primario: `#1f9e49` (verde VESP)
- Acentos: Grises `#2d2d2d` a `#3d3d3d`

**Mejor para:**
- ✅ Ambientes con poca luz
- ✅ Largas sesiones de trabajo
- ✅ Reducir fatiga ocular
- ✅ Uso nocturno

### Tema Claro

- Fondo: `#f5f5f5` (gris muy claro)
- Texto: `#212121` (gris oscuro)
- Primario: `#1f9e49` (verde VESP)
- Acentos: Grises `#efefef` a `#ffffff`

**Mejor para:**
- ✅ Ambientes bien iluminados
- ✅ Presentaciones
- ✅ Imprimir
- ✅ Usuarios con sensibilidad a luz azul

### Cambiar Tema

**Ubicación:** Menú Settings → Tema

```
[🌙 Tema Oscuro]  [☀️ Tema Claro]
```

La preferencia se guarda automáticamente en `~/.VESP Control/tema.json`

---

## 📱 Responsive Design

### Breakpoints

| Pantalla | Min Width | Ajustes |
|----------|-----------|---------|
| Mobile | < 768px | - (no soportado aún) |
| Tablet | 768px - 1024px | Columnas reducidas |
| Desktop | > 1024px | Layout completo |

### Tablas Adaptables

- Scroll horizontal en pantallas pequeñas
- Filas expandibles para más detalles
- Ocultar columnas secundarias automáticamente

### Ventanas Redimensionables

Todas las ventanas principales ahora:
- ✅ Se adaptan al tamaño de la pantalla
- ✅ Guardan su tamaño en preferencias
- ✅ Tienen tamaño mínimo recomendado

---

## ✨ Animaciones y Transiciones

### Transiciones de UI

| Elemento | Transición | Duración |
|----------|-----------|----------|
| Botones | Fade + Scale | 150ms |
| Color de fondo | Fade | 200ms |
| Cambio de tab | Slide | 300ms |
| Aparición de diálogos | Fade + Scale | 250ms |

### Estados de Botones

```
[Estado Normal]  →  [Hover]  →  [Pressed]  →  [Disabled]
```

Transiciones suaves con opacidad y escala.

### Cargando

- Spinner animado
- Barra de progreso con animación
- Pulso de entrada

---

## ♿ Accesibilidad (WCAG 2.1)

### Contraste

| Elemento | Contraste | Estándar |
|----------|-----------|----------|
| Texto normal | 4.5:1 | AA ✅ |
| Texto grande | 3:1 | AA ✅ |
| Elementos UI | 3:1 | AA ✅ |

### Navegación por Teclado

- ✅ Tab para navegar
- ✅ Enter/Space para activar
- ✅ ESC para cerrar diálogos
- ✅ Atajos configurables
- ✅ Indicador de foco visible

### Lectores de Pantalla

- ✅ ARIA labels en todos los inputs
- ✅ Role hints para elementos custom
- ✅ Descripciones de errores claras
- ✅ Anuncios de cambios dinámicos

### Reducir Movimiento

Cuando `prefers-reduced-motion` está activo:
- Las animaciones se desactivan
- Las transiciones son instantáneas
- Los gifs se reemplazan con imágenes estáticas

---

## 🚀 Performance

### Loading Optimizado

- ✅ Lazy loading de componentes
- ✅ Imágenes optimizadas (WebP con fallback)
- ✅ Bundling de CSS/JS
- ✅ Caché local de preferencias

### Renderizado Eficiente

- ✅ Virtual scrolling en grandes tablas
- ✅ Debouncing de búsquedas
- ✅ Throttling de eventos de scroll
- ✅ Re-renders minimizados

### Memoria

- ✅ Cleanup de listeners
- ✅ Caché con expiración
- ✅ Pool de componentes reutilizables

---

## 📐 Grid y Layout

### Sistema de Grid

Base 12 columnas:

```
[Full Width]
[1/2] [1/2]
[1/3] [1/3] [1/3]
[1/4] [1/4] [1/4] [1/4]
```

### Espaciado

```
xs: 4px
sm: 8px
md: 16px
lg: 24px
xl: 32px
```

### Breakpoints

```css
@media (max-width: 768px)   /* Tab */
@media (min-width: 1024px)  /* Desktop */
```

---

## 🎯 Componentes Mejorados

### Input Fields

```
[Label]
[╔═══════════════╗]  ← Focus ring verde
[ Placeholder    ]
[✓ Error message] ← Rojo si hay error
```

Características:
- Validación en tiempo real
- Iconos de estado
- Ayuda contextual
- Sugerencias autocompletadas

### Selects

```
[▼ Selecciona una opción]
┌─────────────────────┐
│ Opción 1            │
│ Opción 2      (✓)   │
│ Opción 3            │
└─────────────────────┘
```

- Búsqueda de opciones
- Iconos personalizados
- Agrupamiento opcional

### Tablas

```
┌────── Objetivo ──────┬──── % ────┬─── Estado ───┐
│ Objetivo A           │  95.5%    │  ✓ Cumple   │
├──────────────────────┼───────────┼─────────────┤
│ Objetivo B           │  62.3%    │  ✗ No cumple│
└──────────────────────┴───────────┴─────────────┘

Acciones en hover:
─ Editar ✎
─ Eliminar 🗑
─ Ver detalles →
```

### Modales

```
┌─────────────────────────────┐
│ ✕  Título del Modal         │
├─────────────────────────────┤
│                             │
│   Contenido del modal       │
│                             │
├─────────────────────────────┤
│                   [Cancelar] [Guardar]
└─────────────────────────────┘
```

- Animación de entrada suave
- Backdrop oscurecido
- ESC para cerrar
- Scroll atrapado

---

## 🌐 Paleta de Colores

### Colores Principales

```
Verde VESP:     #1f9e49 (Success)
Verde hover:    #2bb86a
Azul acceso:    #0088cc (Info)
Rojo error:     #ff4444 (Error)
Amarillo alerta:#ffaa00 (Warning)
```

### Escala de Grises

**Oscuro:**
```
#1a1a1a (Fondo principal)
#2d2d2d (Fondo secundario)
#3d3d3d (Fondo tercero)
#404040 (Borde)
#b0b0b0 (Texto secundario)
#ffffff (Texto principal)
```

**Claro:**
```
#f5f5f5 (Fondo principal)
#ffffff (Fondo secundario)
#efefef (Fondo tercero)
#dddddd (Borde)
#666666 (Texto secundario)
#212121 (Texto principal)
```

---

## 📱 Componentes Específicos

### Dashboard

- **Cards**: Resumen ejecutivo con métricas
- **Gráficos**: Líneas, barras, pie charts
- **Gauge**: Indicador de cumplimiento
- **Mini tabla**: Últimas pasadas

### Reporte Mensual

- Tabla con sorting/filtering
- Exportación a PDF/Excel
- Vista previa de gráfico
- Descarga directa

### Gestión de Usuarios

- Tabla expandible
- Inline editing
- Confirmación antes de eliminar
- Búsqueda en tiempo real

---

## 🔄 Estados de Carga

### Skeleton Loading

```
┌───────────────────┐
│ ░░░░ Objetivo ░░░░│
│ ░░░░░░░░░░░░░░░░░│
│ ░░░░░░░░░░░░░░░░░│
└───────────────────┘
```

Mejor experiencia que screens en blanco.

### Spinner

```
    ⠏ Cargando...
```

Mensaje descriptivo abajo.

### Progreso

```
[████████░░░░░░░░░░] 40%
```

Para operaciones largas.

---

## 🎴 Iconografía

### Set de Iconos

- ✅ Check
- ✕ Close/Cancel
- ⚠ Warning
- ℹ Info
- 🔐 Lock
- 👤 User
- ⚙ Settings
- 🔄 Sync/Reload
- 💾 Save
- 🗑 Delete
- ✎ Edit
- + Add
- ← Back
- → Next

**Fuente:** Material Design Icons compatible

---

## 📚 Componentes Reutilizables

Localización: `ui/components/`

- `Button` - Botón base
- `Input` - Campo de entrada
- `Select` - Selector dropdown
- `Modal` - Diálogo modal
- `Table` - Tabla de datos
- `Card` - Tarjeta contenedor
- `Badge` - Insignia/marca
- `Progress` - Barra de progreso
- `Tooltip` - Ayuda flotante
- `Alert` - Alerta/mensaje

---

## 🧪 Testing de UI

### Visual Regression

```bash
pytest --visual-regression
```

Compara screenshots contra baseline.

### Accesibilidad

```bash
pytest --a11y
```

Valida WCAG compliance.

### Performance

```bash
pytest --performance
```

Mide tiempos de renderizado.

---

## 📖 Guía de Estilos

Ver [`STYLE_GUIDE.md`](STYLE_GUIDE.md) para:
- Colores exactos y valores hexadecimales
- Tipografía y tamaños de fuente
- Espaciado y márgenes
- Radios de borde
- Ejemplos de componentes

---

## ✨ Próximas Mejoras

- [ ] Dark mode automático basado en hora
- [ ] Temas personalizados
- [ ] Modo de alto contraste
- [ ] Visualizaciones en tiempo real
- [ ] Animaciones más fluidas (Framer Motion)
- [ ] PWA - Modo offline
