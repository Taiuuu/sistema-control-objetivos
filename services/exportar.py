import sqlite3
import datetime
import calendar
from openpyxl import Workbook
from openpyxl.styles import PatternFill, Font, Alignment
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet


def obtener_datos_reporte(anio, mes):
    conexion = sqlite3.connect('seguridad.db')
    cursor = conexion.cursor()

    cursor.execute('SELECT id, nombre, fecha_inicio, fecha_fin, dias_semana FROM objetivos')
    objetivos = cursor.fetchall()

    resultados = []

    for o in objetivos:
        obj_id, nombre, inicio, fin, dias_str = o
        dias_semana = [int(d) for d in dias_str.split(",")]

        dias_esperados = 0
        dias_cumplidos = 0
        total_dias = calendar.monthrange(anio, mes)[1]

        for dia in range(1, total_dias + 1):
            fecha = f"{anio}-{mes:02d}-{dia:02d}"
            fecha_dt = datetime.datetime.strptime(fecha, "%Y-%m-%d")

            if fecha < inicio:
                continue
            if fin and fecha > fin:
                continue
            if fecha_dt.isoweekday() not in dias_semana:
                continue

            dias_esperados += 1

            cursor.execute('''
                SELECT COUNT(*) FROM pasadas
                WHERE fecha = ? AND objetivo_id = ?
            ''', (fecha, obj_id))
            if cursor.fetchone()[0] > 0:
                dias_cumplidos += 1

        if dias_esperados > 0:
            porcentaje = (dias_cumplidos / dias_esperados) * 100
            resultados.append((nombre, dias_esperados, dias_cumplidos, porcentaje))

    conexion.close()
    return resultados


def exportar_excel(anio, mes, ruta):
    resultados = obtener_datos_reporte(anio, mes)

    wb = Workbook()
    ws = wb.active

    meses = ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
             "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]

    ws.title = f"Reporte {meses[mes-1]} {anio}"

    # Titulo
    ws.merge_cells("A1:D1")
    ws["A1"] = f"Reporte mensual - {meses[mes-1]} {anio}"
    ws["A1"].font = Font(bold=True, size=14)
    ws["A1"].alignment = Alignment(horizontal="center")

    # Encabezados
    encabezados = ["Objetivo", "Días esperados", "Días cumplidos", "Cumplimiento"]
    for col, enc in enumerate(encabezados, 1):
        celda = ws.cell(row=3, column=col, value=enc)
        celda.font = Font(bold=True)
        celda.fill = PatternFill(fill_type="solid", fgColor="4472C4")
        celda.font = Font(bold=True, color="FFFFFF")
        celda.alignment = Alignment(horizontal="center")

    # Datos
    for fila, r in enumerate(resultados, 4):
        ws.cell(row=fila, column=1, value=r[0])
        ws.cell(row=fila, column=2, value=r[1])
        ws.cell(row=fila, column=3, value=r[2])
        ws.cell(row=fila, column=4, value=f"{r[3]:.1f}%")

        color = "90EE90" if r[3] >= 80 else "FF6B6B"
        fill = PatternFill(fill_type="solid", fgColor=color)
        for col in range(1, 5):
            ws.cell(row=fila, column=col).fill = fill
            ws.cell(row=fila, column=col).alignment = Alignment(horizontal="center")

    # Ancho de columnas
    ws.column_dimensions["A"].width = 30
    ws.column_dimensions["B"].width = 16
    ws.column_dimensions["C"].width = 16
    ws.column_dimensions["D"].width = 14

    wb.save(ruta)
    print(f"Excel exportado en {ruta}")


def exportar_pdf(anio, mes, ruta):
    resultados = obtener_datos_reporte(anio, mes)

    meses = ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
             "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]

    doc = SimpleDocTemplate(ruta, pagesize=A4)
    estilos = getSampleStyleSheet()
    elementos = []

    # Titulo
    titulo = Paragraph(f"Reporte mensual - {meses[mes-1]} {anio}", estilos["Title"])
    elementos.append(titulo)
    elementos.append(Spacer(1, 20))

    # Tabla
    datos = [["Objetivo", "Días esperados", "Días cumplidos", "Cumplimiento"]]
    for r in resultados:
        datos.append([r[0], str(r[1]), str(r[2]), f"{r[3]:.1f}%"])

    tabla = Table(datos, colWidths=[200, 100, 100, 100])
    tabla.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#4472C4")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.HexColor("#90EE90"), colors.white]),
    ]))

    elementos.append(tabla)
    doc.build(elementos)
    print(f"PDF exportado en {ruta}")