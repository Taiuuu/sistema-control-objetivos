# =============================================================================
# VESP Organizations - Sistema de Control de Objetivos
# Módulo de exportación de reportes a Excel y PDF
# =============================================================================

import datetime
from openpyxl import Workbook
from openpyxl.styles import PatternFill, Font, Alignment
from openpyxl.drawing.image import Image as XLImage
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image as RLImage
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import cm
from services.reportes import generar_reporte_mensual


MESES = [
    "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
    "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"
]


def _obtener_datos_reporte(anio: int, mes: int) -> list:
    """Obtiene el resumen de reporte mensual reutilizando la lógica central."""
    reporte = generar_reporte_mensual(anio, mes)
    return [
        (
            objetivo['nombre'],
            objetivo['dias_con_pasada'],
            objetivo['dias_sin_pasada'],
            objetivo['cumplimiento_porcentaje']
        )
        for objetivo in reporte['objetivos']
    ]


def exportar_excel(anio: int, mes: int, ruta: str) -> None:
    """Genera Excel con reporte mensual."""
    # r = (nombre, dias_con_pasada, dias_sin_pasada, cumplimiento_porcentaje)
    resultados = _obtener_datos_reporte(anio, mes)

    wb = Workbook()
    ws = wb.active
    ws.title = f"Reporte {MESES[mes-1]} {anio}"

    try:
        from services.assets import ruta_asset
        img = XLImage(ruta_asset("assets/vesp.png"))
        img.width = 80
        img.height = 80
        ws.add_image(img, "A1")
    except Exception:
        pass

    ws.merge_cells("B1:F2")
    ws["B1"] = "V.E.S.P Organizations - Seguridad Privada"
    ws["B1"].font = Font(bold=True, size=14, color="2E7D32")
    ws["B1"].alignment = Alignment(horizontal="center", vertical="center")

    ws.merge_cells("A3:F3")
    ws["A3"] = f"Reporte mensual - {MESES[mes-1]} {anio}"
    ws["A3"].font = Font(bold=True, size=12)
    ws["A3"].alignment = Alignment(horizontal="center")

    ws.merge_cells("A4:F4")
    ws["A4"] = f"Generado el {datetime.datetime.now().strftime('%d/%m/%Y %H:%M')}"
    ws["A4"].font = Font(size=9, color="888888")
    ws["A4"].alignment = Alignment(horizontal="center")

    encabezados = ["Objetivo", "Días con pasada", "Días sin pasada", "Cumplimiento", "Estado"]
    for col, enc in enumerate(encabezados, 1):
        celda = ws.cell(row=6, column=col, value=enc)
        celda.font = Font(bold=True, color="FFFFFF")
        celda.fill = PatternFill(fill_type="solid", fgColor="1B5E20")
        celda.alignment = Alignment(horizontal="center")

    for fila, r in enumerate(resultados, 7):
        estado = "CUMPLE" if r[3] >= 80 else "NO CUMPLE"
        valores = [r[0], r[1], r[2], f"{r[3]:.1f}%", estado]
        for col, val in enumerate(valores, 1):
            celda = ws.cell(row=fila, column=col, value=val)
            color = "C8E6C9" if r[3] >= 80 else "FFCDD2"
            celda.fill = PatternFill(fill_type="solid", fgColor=color)
            celda.alignment = Alignment(horizontal="center")

    ws.column_dimensions["A"].width = 30
    ws.column_dimensions["B"].width = 18
    ws.column_dimensions["C"].width = 18
    ws.column_dimensions["D"].width = 14
    ws.column_dimensions["E"].width = 12
    ws.row_dimensions[1].height = 60
    ws.row_dimensions[2].height = 60

    wb.save(ruta)


def exportar_pdf(anio: int, mes: int, ruta: str) -> None:
    """Genera PDF con reporte mensual."""
    # r = (nombre, dias_con_pasada, dias_sin_pasada, cumplimiento_porcentaje)
    resultados = _obtener_datos_reporte(anio, mes)

    doc = SimpleDocTemplate(
        ruta, pagesize=A4,
        rightMargin=2*cm, leftMargin=2*cm,
        topMargin=2*cm, bottomMargin=2*cm
    )

    estilos = getSampleStyleSheet()
    elementos = []

    try:
        from services.assets import ruta_asset
        logo = RLImage(ruta_asset("assets/vesp.png"), width=2.5*cm, height=2.5*cm)
        datos_header = [[
            logo,
            Paragraph(
                "<b><font color='#2E7D32' size=14>V.E.S.P Organizations</font></b>"
                "<br/><font size=10>Seguridad Privada</font>",
                estilos["Normal"]
            ),
            Paragraph(
                f"<font size=9 color='grey'>Generado el<br/>"
                f"{datetime.datetime.now().strftime('%d/%m/%Y %H:%M')}</font>",
                estilos["Normal"]
            )
        ]]
        tabla_header = Table(datos_header, colWidths=[3*cm, 10*cm, 4*cm])
        tabla_header.setStyle(TableStyle([
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("ALIGN", (2, 0), (2, 0), "RIGHT"),
        ]))
        elementos.append(tabla_header)
    except Exception:
        elementos.append(Paragraph("<b>V.E.S.P Organizations</b>", estilos["Title"]))

    elementos.append(Spacer(1, 0.5*cm))
    elementos.append(Paragraph(
        f"<b>Reporte mensual - {MESES[mes-1]} {anio}</b>",
        estilos["Title"]
    ))
    elementos.append(Spacer(1, 0.5*cm))

    datos = [["Objetivo", "Días con pasada", "Días sin pasada", "Cumplimiento", "Estado"]]
    for r in resultados:
        estado = "CUMPLE" if r[3] >= 80 else "NO CUMPLE"
        datos.append([r[0], str(r[1]), str(r[2]), f"{r[3]:.1f}%", estado])

    tabla = Table(datos, colWidths=[5.5*cm, 3*cm, 3*cm, 2.5*cm, 3*cm])
    tabla.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1B5E20")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("ROWHEIGHT", (0, 0), (-1, -1), 20),
    ]))

    for i, r in enumerate(resultados, 1):
        color = colors.HexColor("#C8E6C9") if r[3] >= 80 else colors.HexColor("#FFCDD2")
        tabla.setStyle(TableStyle([("BACKGROUND", (0, i), (-1, i), color)]))

    elementos.append(tabla)
    elementos.append(Spacer(1, 0.5*cm))

    total = len(resultados)
    cumplen = sum(1 for r in resultados if r[3] >= 80)
    elementos.append(Paragraph(
        f"<b>Resumen:</b> {cumplen} de {total} objetivos cumplen el 80% o más de cobertura.",
        estilos["Normal"]
    ))

    doc.build(elementos)