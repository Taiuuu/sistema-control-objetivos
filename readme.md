# Sistema de Control de Objetivos
### V.E.S.P Organizations – Seguridad Privada

![Logo](assets/vesp.png)

---

## ¿De qué trata el sistema?

Sistema de escritorio desarrollado en Python para reemplazar el control manual en Excel de objetivos de seguridad privada.

Permite registrar y visualizar en tiempo real qué objetivos fueron controlados durante el día, qué supervisores estaban de turno, cuántas pasadas se realizaron por turno y generar reportes mensuales de cumplimiento.

---

## Tecnologías utilizadas

- **Python 3**
- **PyQt6** — Interfaz gráfica de escritorio
- **SQLite** — Base de datos local
- **openpyxl** — Exportación a Excel
- **reportlab** — Exportación a PDF

---

## Instalación

### 1. Clonar el repositorio
```bash
git clone https://github.com/tuusuario/sistema-control-objetivos.git
cd sistema-control-objetivos
```

### 2. Instalar dependencias
```bash
pip install PyQt6 openpyxl reportlab
```

### 3. Ejecutar el sistema
```bash
python main.py
```

---

## Cómo usar el sistema

### Configuración inicial
1. Agregar supervisores desde el botón **Agregar supervisor**
2. Agregar objetivos desde el botón **Agregar objetivo** indicando nombre, fecha de inicio y días de cobertura

### Uso diario
1. Registrar el equipo de turno del día con **Registrar turno**
2. Registrar cada pasada con **Registrar pasada**
3. Visualizar el estado del día en la tabla principal con colores:
   - 🟢 **Verde** — Pasaron los dos turnos
   - 🟡 **Amarillo** — Faltó un turno
   - 🔴 **Rojo** — No pasó nadie

### Reportes
- Generar reporte mensual de cumplimiento por objetivo
- Exportar a Excel o PDF

### Notas
- Registrar incidentes o novedades del día desde **Notas del día**

---

## Seguridad

El sistema es de uso exclusivo interno de **V.E.S.P Organizations**.
Los datos almacenados son privados y confidenciales.

---

*Desarrollado para V.E.S.P Organizations – Seguridad Privada*
```