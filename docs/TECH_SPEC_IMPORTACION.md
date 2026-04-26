# Especificación Técnica - Importación Excel y Turnos Nocturnos
## V.E.S.P Organizations – Seguridad Privada

---

## 1. Lógica de Turnos Nocturnos

### 1.1 Definición de turnos

```python
TURNOS_CONFIG = {
    'diurno': {
        'inicio': time(7, 0),      # 07:00
        'fin': time(19, 0),        # 19:00
        'cruzada_medianoche': False
    },
    'nocturno': {
        'inicio': time(19, 0),     # 19:00
        'fin': time(7, 0),         # 07:00 del día siguiente
        'cruzada_medianoche': True
    }
}
```

### 1.2 Mapeo de fecha operativa (Algoritmo crítico)

```python
from datetime import datetime, time, timedelta, date

def calcular_fecha_operativa_pasada(
    fecha_registro: date,
    hora_pasada: time,
    turno: str
) -> date:
    """
    Calcula la fecha operativa de una pasada considerando turnos que cruzan medianoche.
    
    Args:
        fecha_registro: Fecha en que se registró la pasada
        hora_pasada: Hora exacta de la pasada
        turno: 'diurno' o 'nocturno'
    
    Returns:
        date: La fecha operativa para contabilización
    
    Ejemplos:
        Caso 1: Turno diurno
        - Entrada: fecha=21/04, hora=14:30, turno='diurno'
        - Retorno: 21/04 ✓
        
        Caso 2: Turno nocturno (antes de medianoche)
        - Entrada: fecha=21/04, hora=22:15, turno='nocturno'
        - Retorno: 21/04 ✓
        
        Caso 3: Turno nocturno (después de medianoche)
        - Entrada: fecha=22/04, hora=03:00, turno='nocturno'
        - Retorno: 21/04 ✓ (pertenece al turno nocturno de 21/04)
        
        Caso 4: Turno nocturno (justo después de inicio)
        - Entrada: fecha=21/04, hora=19:01, turno='nocturno'
        - Retorno: 21/04 ✓
        
        Caso 5: Turno nocturno (justo antes de fin)
        - Entrada: fecha=22/04, hora=06:59, turno='nocturno'
        - Retorno: 21/04 ✓
    """
    
    if turno == 'diurno':
        # Turno diurno: 07:00 - 19:00
        # La fecha operativa es siempre la misma que el registro
        if not (time(7, 0) <= hora_pasada < time(19, 0)):
            raise ValueError(
                f"Hora {hora_pasada} fuera del rango de turno diurno (07:00-19:00)"
            )
        return fecha_registro
    
    elif turno == 'nocturno':
        # Turno nocturno: 19:00 - 07:00 (cruza medianoche)
        
        if time(19, 0) <= hora_pasada <= time(23, 59):
            # Pasada registrada entre 19:00 y 23:59
            # Pertenece al turno nocturno del MISMO DÍA
            return fecha_registro
        
        elif time(0, 0) <= hora_pasada < time(7, 0):
            # Pasada registrada entre 00:00 y 06:59
            # Pertenece al turno nocturno del DÍA ANTERIOR
            return fecha_registro - timedelta(days=1)
        
        else:
            raise ValueError(
                f"Hora {hora_pasada} fuera del rango de turno nocturno "
                f"(19:00-23:59 o 00:00-06:59)"
            )
    
    else:
        raise ValueError(f"Turno inválido: {turno}")


def validar_pasada_turno(hora: time, turno: str) -> bool:
    """Valida que la hora sea válida para el turno especificado."""
    if turno == 'diurno':
        return time(7, 0) <= hora < time(19, 0)
    elif turno == 'nocturno':
        return hora >= time(19, 0) or hora < time(7, 0)
    return False
```

### 1.3 Ejemplos de mapeo

| Fecha Registro | Hora | Turno | Fecha Operativa | Explicación |
|---|---|---|---|---|
| 21/04 | 14:30 | diurno | 21/04 | Turno diurno en horario |
| 21/04 | 07:00 | diurno | 21/04 | Inicio de turno diurno |
| 21/04 | 18:59 | diurno | 21/04 | Fin de turno diurno |
| 21/04 | 22:15 | nocturno | 21/04 | Turno nocturno, antes de medianoche |
| 21/04 | 23:59 | nocturno | 21/04 | Fin de la noche del 21/04 |
| 22/04 | 00:00 | nocturno | 21/04 | Inicio de la noche después de medianoche |
| 22/04 | 03:00 | nocturno | 21/04 | Turno nocturno, parte de la madrugada |
| 22/04 | 06:59 | nocturno | 21/04 | Fin de turno nocturno |
| 22/04 | 07:00 | diurno | 22/04 | Inicio de turno diurno siguiente |

---

## 2. Estructura de Importación Excel

### 2.1 Formato del archivo

**Nombre recomendado**: `pasadas_YYYYMMDD.xlsx` o `pasadas_importacion.xlsx`

**Sheet**: "Pasadas" (único sheet requerido)

**Columnas** (en este orden):

| Columna | Tipo | Obligatorio | Validación | Ejemplo |
|---------|------|-----------|-----------|---------|
| A: Fecha | DATE | ✓ | dd/mm/yyyy válida | 21/04/2026 |
| B: Supervisor | TEXT | ✓ | Debe existir en BD | Juan García |
| C: Objetivo | TEXT | ✓ | Debe existir en BD | Centro Comercial A |
| D: Hora | TIME | ✓ | HH:MM format | 14:30 |
| E: Turno | TEXT | ✓ | "diurno" o "nocturno" | nocturno |
| F: Notas | TEXT | ✗ | Máx 500 caracteres | Revisión perimetral |

### 2.2 Validaciones en importación

```python
class ValidadorImportacionExcel:
    """Valida estructura y contenido de archivo Excel."""
    
    COLUMNAS_REQUERIDAS = [
        'Fecha', 'Supervisor', 'Objetivo', 'Hora', 'Turno'
    ]
    
    ERRORES_VALIDACION = {
        'FECHA_INVALIDA': 'Fecha debe ser válida en formato dd/mm/yyyy',
        'SUPERVISOR_NO_EXISTE': 'Supervisor no existe en el sistema',
        'OBJETIVO_NO_EXISTE': 'Objetivo no existe en el sistema',
        'HORA_INVALIDA': 'Hora debe ser HH:MM en rango válido',
        'TURNO_INVALIDO': 'Turno debe ser "diurno" o "nocturno"',
        'HORA_FUERA_RANGO': 'Hora no corresponde al turno especificado',
        'SUPERVISOR_INACTIVO': 'Supervisor no está activo',
        'OBJETIVO_INACTIVO': 'Objetivo no está activo en esa fecha'
    }
    
    def validar_archivo(self, ruta_archivo: str) -> dict:
        """
        Valida archivo completo.
        
        Returns:
            {
                'valido': bool,
                'registros_validos': list,
                'registros_errores': list,
                'errores_criticos': list
            }
        """
        pass
    
    def validar_registro(self, registro: dict, index: int) -> dict:
        """
        Valida un registro individual.
        
        Returns:
            {
                'index': int,
                'valido': bool,
                'errores': list,
                'datos_procesados': dict
            }
        """
        pass
```

### 2.3 Flujo de validación

```
1. Verificar estructura básica
   ├─ ¿Existe archivo?
   ├─ ¿Es Excel válido?
   └─ ¿Tiene columnas requeridas?

2. Por cada fila
   ├─ Parsear fecha (dd/mm/yyyy → date)
   ├─ Parsear hora (HH:MM → time)
   ├─ Validar supervisor existe y está activo
   ├─ Validar objetivo existe y está activo en fecha
   ├─ Validar turno válido
   ├─ Validar hora dentro del rango del turno
   ├─ Calcular fecha operativa (lógica de turno nocturno)
   ├─ Detectar duplicado
   └─ Clasificar: nueva / duplicada / error

3. Generar reporte
   ├─ Cantidad de registros nuevos
   ├─ Cantidad de duplicados (con sugerencia de acción)
   ├─ Cantidad con error (con mensaje específico)
   └─ Resumen por supervisor/objetivo
```

---

## 3. Detección de Duplicados

### 3.1 Criterios de duplicado

Se considera duplicado si:
- **Fecha operativa** = igual
- **Supervisor** = igual
- **Objetivo** = igual
- **Hora** = dentro de ±5 minutos (configurable)
- **Turno** = igual

```python
def es_duplicado(
    pasada_nueva: Pasada,
    pasada_existente: Pasada,
    tolerancia_minutos: int = 5
) -> bool:
    """
    Verifica si dos pasadas son duplicadas.
    """
    diferencia_minutos = abs(
        (datetime.combine(date.today(), pasada_nueva.hora) - 
         datetime.combine(date.today(), pasada_existente.hora)).total_seconds() / 60
    )
    
    return (
        pasada_nueva.fecha_operativa == pasada_existente.fecha_operativa and
        pasada_nueva.supervisor_id == pasada_existente.supervisor_id and
        pasada_nueva.objetivo_id == pasada_existente.objetivo_id and
        pasada_nueva.turno == pasada_existente.turno and
        diferencia_minutos <= tolerancia_minutos
    )
```

### 3.2 Opciones de resolución

```python
ACCIONES_DUPLICADO = {
    'SKIP': 'Saltar el registro (no importar)',
    'REEMPLAZAR': 'Reemplazar el registro existente',
    'MERGE': 'Combinar información (ej: actualizar notas)',
    'PREGUNTAR': 'Mostrar diálogo al usuario'
}
```

---

## 4. Integración con Tablets

### 4.1 Flujo recomendado

```
TABLET (Supervisor en campo)
│
├─ Aplicación web/móvil
│  ├─ Ingresa:
│  │  ├─ Objetivo (dropdown)
│  │  ├─ Su nombre (auto-completado)
│  │  ├─ Hora (hora/minuto)
│  │  └─ Turno (diurno/nocturno)
│  │
│  └─ Guarda localmente en:
│     └─ pasadas_tablet.xlsx (o JSON)
│
├─ Sincronización
│  ├─ ¿Conectado a wifi?
│  │  ├─ Sí: enviar a servidor
│  │  └─ No: guardar localmente
│  │
│  └─ Cloud o servidor central
│     └─ Recibe datos
│
PC/ESCRITORIO (Usuario administrador)
│
├─ Descarga archivo de tablet
│ o accede a servidor central
│
├─ Abre importador Excel
│  ├─ Carga archivo
│  ├─ Valida estructura
│  ├─ Detecta duplicados
│  └─ Muestra vista previa
│
├─ Confirma importación
│  └─ Se registra en auditoría
│
└─ Datos disponibles en
   todas las PC sincronizadas
```

### 4.2 Formato de datos en tablet

```json
{
  "meta": {
    "dispositivo": "tablet_samsung_001",
    "usuario": "Juan García",
    "fecha_export": "2026-04-21T18:30:00",
    "version": "1.0"
  },
  "pasadas": [
    {
      "timestamp": "2026-04-21T14:35:30",
      "objetivo": "Centro Comercial A",
      "turno": "diurno",
      "notas": "Entrada norte: OK"
    },
    {
      "timestamp": "2026-04-21T22:15:45",
      "objetivo": "Banco Central",
      "turno": "nocturno",
      "notas": "Cierre: todas las puertas aseguradas"
    },
    {
      "timestamp": "2026-04-22T03:00:10",
      "objetivo": "Centro Comercial A",
      "turno": "nocturno",
      "notas": "Ronda nocturna OK"
    }
  ]
}
```

### 4.3 Conversión JSON → Excel para importación

El importador debe aceptar ambos formatos:
- Excel directo (usuario descarga manualmente)
- JSON desde tablet (se convierte a Excel antes de validar)

---

## 5. Casos de Prueba

### 5.1 Turno diurno
```python
# Test case: TD1 - Turno diurno hora válida
fecha = date(2026, 4, 21)
hora = time(14, 30)
turno = 'diurno'

resultado = calcular_fecha_operativa_pasada(fecha, hora, turno)
assert resultado == date(2026, 4, 21), "Error en turno diurno"

# Test case: TD2 - Turno diurno inicio
resultado = calcular_fecha_operativa_pasada(date(2026, 4, 21), time(7, 0), 'diurno')
assert resultado == date(2026, 4, 21)

# Test case: TD3 - Turno diurno fin
resultado = calcular_fecha_operativa_pasada(date(2026, 4, 21), time(18, 59), 'diurno')
assert resultado == date(2026, 4, 21)

# Test case: TD4 - Turno diurno hora inválida (debe fallar)
try:
    calcular_fecha_operativa_pasada(date(2026, 4, 21), time(20, 0), 'diurno')
    assert False, "Debería lanzar ValueError"
except ValueError:
    pass
```

### 5.2 Turno nocturno
```python
# Test case: TN1 - Turno nocturno antes de medianoche
resultado = calcular_fecha_operativa_pasada(date(2026, 4, 21), time(22, 15), 'nocturno')
assert resultado == date(2026, 4, 21), "Turno nocturno antes de medianoche"

# Test case: TN2 - Turno nocturno después de medianoche
resultado = calcular_fecha_operativa_pasada(date(2026, 4, 22), time(3, 0), 'nocturno')
assert resultado == date(2026, 4, 21), "Turno nocturno después de medianoche"

# Test case: TN3 - Turno nocturno justo en los límites
resultado = calcular_fecha_operativa_pasada(date(2026, 4, 21), time(19, 0), 'nocturno')
assert resultado == date(2026, 4, 21)

resultado = calcular_fecha_operativa_pasada(date(2026, 4, 22), time(6, 59), 'nocturno')
assert resultado == date(2026, 4, 21)

# Test case: TN4 - Turno nocturno hora inválida (debe fallar)
try:
    calcular_fecha_operativa_pasada(date(2026, 4, 21), time(12, 0), 'nocturno')
    assert False, "Debería lanzar ValueError"
except ValueError:
    pass
```

### 5.3 Duplicados
```python
# Test case: DUP1 - Registros idénticos
pasada1 = Pasada(
    fecha_operativa=date(2026, 4, 21),
    hora=time(14, 30),
    supervisor_id=1,
    objetivo_id=5,
    turno='diurno'
)
pasada2 = Pasada(
    fecha_operativa=date(2026, 4, 21),
    hora=time(14, 30),
    supervisor_id=1,
    objetivo_id=5,
    turno='diurno'
)

assert es_duplicado(pasada1, pasada2), "Debe detectar duplicado exacto"

# Test case: DUP2 - Registros con variación de minutos (dentro de tolerancia)
pasada2.hora = time(14, 33)
assert es_duplicado(pasada1, pasada2), "Debe detectar duplicado con ±3 min"

# Test case: DUP3 - Registros con variación de minutos (fuera de tolerancia)
pasada2.hora = time(14, 36)
assert not es_duplicado(pasada1, pasada2), "No debe detectar duplicado con >5 min"
```

---

## 6. Notas de implementación

### 6.1 Dependencias nuevas
```
openpyxl >= 3.8.0        # Lectura/escritura Excel
pandas >= 1.3.0          # Procesamiento de datos
jsonschema >= 4.0        # Validación de esquemas JSON
```

### 6.2 Módulos a crear
```
services/
├── importador_excel.py         # Lógica de importación
├── validador_pasadas.py        # Validaciones
├── gestor_turnos.py            # Lógica de turnos nocturnos
└── comparador_duplicados.py    # Detección de duplicados

ui/
├── importador_excel_ui.py      # Interfaz de importación
├── preview_importacion.py      # Vista previa
└── gestor_datos_ui.py          # Gestión masiva
```

### 6.3 Testing
- Cobertura mínima: 90% para `gestor_turnos.py`
- Todos los casos de prueba anteriores deben pasar
- Testing de Excel con archivos reales

---

*Documento técnico v1.0 - Abril 2026*
