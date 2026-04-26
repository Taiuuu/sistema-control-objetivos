# Nuevas Funcionalidades v2.0

Guía de uso de las nuevas funcionalidades agregadas en v2.0.

---

## 📊 Estadísticas y Gráficos

Módulo: `services/estadisticas.py`

### Funciones Disponibles

#### `obtener_estadisticas_semana()`

Estadísticas de cumplimiento de la semana actual.

```python
from services.estadisticas import obtener_estadisticas_semana

stats = obtener_estadisticas_semana()
# {
#   'fecha_inicio': '2025-01-06',
#   'fecha_fin': '2025-01-12',
#   'dias_semana': [
#     {
#       'fecha': '2025-01-06',
#       'dia_nombre': 'Lun',
#       'diurno': 5,
#       'nocturno': 3,
#       'objetivos_controlados': 8
#     },
#     ...
#   ]
# }
```

#### `obtener_cumplimiento_por_objetivo(anio, mes)`

Cumplimiento de cada objetivo en el mes.

```python
datos = obtener_cumplimiento_por_objetivo(2025, 1)
# [
#   {'nombre': 'Objetivo A', 'cumplimiento': 95.0, 'cumple': True},
#   {'nombre': 'Objetivo B', 'cumplimiento': 65.0, 'cumple': False},
# ]
```

#### `obtener_promedio_cumplimiento_mensual(anio)`

Promedio anual de cumplimiento.

```python
datos = obtener_promedio_cumplimiento_mensual(2025)
# [
#   {'mes': 1, 'mes_nombre': 'Enero', 'promedio': 85.5},
#   ...
# ]
```

#### `obtener_top_supervisores(anio, mes, limite=10)`

Supervisores más activos del mes.

```python
top = obtener_top_supervisores(2025, 1, limite=5)
# [
#   {'nombre': 'Juan', 'pasadas': 45},
#   {'nombre': 'María', 'pasadas': 42},
#   ...
# ]
```

---

## 📁 Exportación Extendida

Módulo: `services/exportacion_extendida.py`

### CSV

#### `exportar_pasadas_csv(anio, mes, ruta)`

Exporta todas las pasadas del mes a CSV.

```python
from services.exportacion_extendida import exportar_pasadas_csv

exportar_pasadas_csv(2025, 1, "pasadas_enero.csv")
```

Output:
```csv
Fecha;Hora;Turno;Objetivo;Supervisor
2025-01-06;10:30;diurno;Objetivo A;Juan
2025-01-06;14:45;diurno;Objetivo B;María
...
```

#### `exportar_supervisor_mes_csv(supervisor_id, anio, mes, ruta)`

Exporta pasadas de un supervisor específico.

```python
exportar_supervisor_mes_csv(1, 2025, 1, "juan_enero.csv")
```

### JSON

#### `exportar_reporte_json(anio, mes, ruta)`

Exporta reporte completo con estadísticas.

```python
exportar_reporte_json(2025, 1, "reporte_enero.json")
```

Output:
```json
{
  "fecha_generacion": "2025-01-15T10:30:00",
  "periodo": "2025-01",
  "resumen": {
    "total_objetivos": 5,
    "objetivos_cumplen": 4,
    "cumplimiento_promedio": 88.5,
    "distribucion_turnos": {"diurno": 150, "nocturno": 120}
  },
  "objetivos": [...],
  "top_supervisores": [...]
}
```

#### `exportar_base_completa_json(ruta)`

Exporta toda la BD en JSON (para backups/migración).

```python
exportar_base_completa_json("backup_completo.json")
```

---

## 🔔 Notificaciones Desktop

Módulo: `services/notificaciones.py`

### NotificadorDesktop

```python
from PyQt6.QtWidgets import QApplication
from services.notificaciones import NotificadorDesktop

app = QApplication([])
notificador = NotificadorDesktop(app)

# Notificación simple
notificador.mostrar_notificacion("Pasada registrada", "Objetivo A - Juan (diurno)")

# Notificación de error
notificador.notificar_error("Error", "No se pudo guardar")

# Notificación de advertencia
notificador.notificar_advertencia("Cuidado", "Sesión por expirar")

# Notificación de pasada
notificador.notificar_pasada_registrada("Objetivo A", "Juan", "diurno")
```

### MonitorNotificaciones

Monitorea eventos y emite notificaciones automáticamente.

```python
from services.notificaciones import MonitorNotificaciones

monitor = MonitorNotificaciones(notificador)
monitor.iniciar(intervalo_ms=30000)  # Chequear cada 30s

# Callbacks
monitor.on_pasada_registrada("Objetivo A", "Juan", "diurno")
monitor.on_error_sincronizacion()
monitor.on_backup_completado()

monitor.detener()
```

---

## 🎨 Temas Claro/Oscuro

Módulo: `services/tema.py`

### TemaManager

```python
from services.tema import obtener_tema_manager

manager = obtener_tema_manager()

# Obtener tema actual
tema = manager.obtener_tema()
# {'nombre': 'oscuro', 'background': '#1a1a1a', ...}

# Cambiar tema
manager.cambiar_tema('claro')

# Verificar
if manager.es_tema_oscuro():
    print("Tema oscuro activo")

# Obtener color específico
color_primario = manager.obtener_color('primario')
```

### Cambiar Tema en la App

```python
from PyQt6.QtWidgets import QMainWindow
from services.tema import cambiar_tema_aplicacion

window = QMainWindow()
cambiar_tema_aplicacion(window, 'claro')
```

### Agregar Botón de Tema

```python
from PyQt6.QtWidgets import QPushButton
from services.tema import obtener_tema_manager, cambiar_tema_aplicacion

def toggle_tema(window):
    manager = obtener_tema_manager()
    nuevo_tema = 'claro' if manager.es_tema_oscuro() else 'oscuro'
    cambiar_tema_aplicacion(window, nuevo_tema)

boton = QPushButton("🌙 Alternar Tema")
boton.clicked.connect(lambda: toggle_tema(window))
```

### Personalizar Colores

```python
theme = manager.obtener_tema()
bg = theme['background_principal']
text = theme['texto_principal']
primary = theme['primario']

# Usar en UI
widget.setStyleSheet(f"""
    QWidget {{
        background-color: {bg};
        color: {text};
    }}
""")
```

---

## 🔌 API REST - Nuevos Endpoints

### Estadísticas

```bash
# Estadísticas semana
curl -H "Authorization: Bearer <token>" \
  http://localhost:5000/api/estadisticas/semana

# Cumplimiento por objetivo
curl -H "Authorization: Bearer <token>" \
  http://localhost:5000/api/estadisticas/cumplimiento/2025/1

# Promedio mensual
curl -H "Authorization: Bearer <token>" \
  http://localhost:5000/api/estadisticas/promedio-anual/2025

# Top supervisores
curl -H "Authorization: Bearer <token>" \
  http://localhost:5000/api/estadisticas/top-supervisores/2025/1?limite=10
```

### Exportación

```bash
# Descargar CSV
curl -H "Authorization: Bearer <token>" \
  http://localhost:5000/api/exportar/pasadas-csv/2025/1 > pasadas.csv

# Descargar JSON
curl -H "Authorization: Bearer <token>" \
  http://localhost:5000/api/exportar/reporte-json/2025/1 > reporte.json

# Exportar supervisor
curl -H "Authorization: Bearer <token>" \
  "http://localhost:5000/api/exportar/supervisor-csv/1/2025/1" > juan.csv
```

---

## 📝 Integración en UI

### Agregar Tab de Estadísticas

```python
from ui.estadisticas_tab import EstadisticasTab

tab = EstadisticasTab()
tabs.addTab(tab, "📊 Estadísticas")
```

### Agregar Menu de Exportación

```python
from ui.menu_exportacion import MenuExportacion

export_menu = MenuExportacion()
menubar.addMenu(export_menu.crear_menu())
```

### Agregar Notificador

```python
from services.notificaciones import NotificadorDesktop, MonitorNotificaciones

notificador = NotificadorDesktop(app)
monitor = MonitorNotificaciones(notificador)
monitor.iniciar()

# Enviar notificaciones cuando ocurran eventos
self.pasada_registrada.connect(
    lambda obj, sup, tur: monitor.on_pasada_registrada(obj, sup, tur)
)
```

---

## 🧪 Testing

### Tests para Estadísticas

```bash
pytest tests/test_estadisticas.py -v
```

### Tests para Exportación

```bash
pytest tests/test_exportacion.py -v
```

---

## 🐛 Troubleshooting

**Las notificaciones no aparecen?**
- Verifica que QApplication esté inicializado
- Revisa los permisos de notificaciones del SO

**El tema no se guarda?**
- Asegurate que `~/VESP Control/` es escribible
- Verifica que `tema.json` se creó

**CSV no se abre en Excel?**
- Usa encoding UTF-8 BOM (ya incluido)
- Prueba con delimitador `;` en lugar de `,`

---

## 📚 Próximas Mejoras

- [ ] Gráficos interactivos con matplotlib/plotly
- [ ] Sincronización multiusuario en tiempo real
- [ ] Búsqueda avanzada con filtros complejos
- [ ] Vistas personalizables (dashboards)
- [ ] Predicción de cumplimiento con ML
