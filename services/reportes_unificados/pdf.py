"""Generación de PDF imprimibles desde el objeto común de datos."""

from __future__ import annotations

import html
import logging
from datetime import date, datetime, time
from functools import partial
from pathlib import Path
from typing import Any, Mapping, Sequence

import reportlab
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape, portrait
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.pdfbase.pdfmetrics import stringWidth
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    LongTable,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from services.reportes_unificados.modelos import ColumnaReporte, ReporteDatos

logger = logging.getLogger(__name__)

VERDE_INSTITUCIONAL = colors.HexColor("#0E7F09")
GRAFITO_INSTITUCIONAL = colors.HexColor("#231F20")
GRIS_FILA = colors.HexColor("#F0F0F0")
GRIS_TOTAL = colors.HexColor("#D9D9D9")
GRIS_BORDE = colors.HexColor("#777777")


def exportar_pdf(
    datos: ReporteDatos,
    ruta: str | Path,
    columnas: Sequence[str] | None = None,
    contenido: str = "ambos",
    incluir_totales: bool = True,
    incluir_notas: bool = False,
) -> None:
    """Genera un PDF con tablas paginadas desde las filas ya calculadas."""
    _registrar_fuentes()
    if contenido not in {"resumen", "detalle", "ambos"}:
        raise ValueError(f"Contenido de informe no reconocido: {contenido}")
    if columnas is not None:
        disponibles = {
            columna.id
            for columna in (*datos.columnas, *datos.columnas_detalle)
        }
        desconocidas = set(columnas) - disponibles
        if desconocidas:
            raise ValueError(
                "Columnas no disponibles en este informe: "
                + ", ".join(sorted(desconocidas))
            )
        if len(columnas) != len(set(columnas)):
            raise ValueError("La selección de columnas contiene IDs repetidos")

    catalogos = [datos.columnas]
    if contenido in {"detalle", "ambos"} and datos.columnas_detalle:
        catalogos.append(datos.columnas_detalle)
    columna_por_id = {
        columna.id: columna for catalogo in catalogos for columna in catalogo
    }
    if columnas is not None:
        columnas_seleccionadas = [
            columna_por_id[identificador] for identificador in columnas
        ]
    elif contenido == "detalle":
        columnas_seleccionadas = list(datos.columnas_detalle or datos.columnas)
    else:
        columnas_seleccionadas = list(
            {columna.id: columna for catalogo in catalogos for columna in catalogo}.values()
        )
    if not incluir_notas:
        columnas_seleccionadas = [
            columna
            for columna in columnas_seleccionadas
            if columna.id not in {"notas", "observaciones"}
        ]

    orientacion = _orientacion(columnas_seleccionadas)
    tamano = landscape(A4) if orientacion == "landscape" else portrait(A4)
    margen_lateral = 1.25 * cm
    margen_superior = 3.45 * cm
    margen_inferior = 1.8 * cm
    documento = SimpleDocTemplate(
        str(ruta),
        pagesize=tamano,
        leftMargin=margen_lateral,
        rightMargin=margen_lateral,
        topMargin=margen_superior,
        bottomMargin=margen_inferior,
        title=f"{datos.metadatos.titulo} - {datos.metadatos.periodo}",
        author=datos.metadatos.usuario,
    )
    estilos = _estilos()
    elementos = []

    if contenido in {"resumen", "ambos"}:
        elementos.extend(
            _seccion_tabla(
                "Resumen",
                datos,
                datos.columnas,
                datos.filas,
                columnas,
                incluir_totales,
                incluir_notas,
                estilos,
                documento.width,
                "No hay datos de resumen para los filtros seleccionados.",
            )
        )
    if contenido in {"detalle", "ambos"}:
        catalogo_detalle = datos.columnas_detalle or datos.columnas
        filas_detalle = datos.filas_detalle or datos.filas
        elementos.extend(
            _seccion_tabla(
                "Detalle de pasadas",
                datos,
                catalogo_detalle,
                filas_detalle,
                columnas,
                incluir_totales,
                incluir_notas,
                estilos,
                documento.width,
                "No hay pasadas para los filtros seleccionados.",
            )
        )
        if incluir_totales and datos.subtotales:
            elementos.extend(_seccion_subtotales(datos, estilos, documento.width))
    if incluir_notas and datos.notas:
        elementos.extend(
            _seccion_notas(
                datos.notas,
                estilos,
                documento.width,
            )
        )
    if incluir_totales and datos.metadatos.tipo_informe == "objetivo":
        elementos.extend(_seccion_resumen_objetivo(datos, estilos))
    if not elementos:
        elementos.append(Paragraph("No hay contenido para imprimir.", estilos["Normal"]))

    canvas_numerado = partial(
        _LienzoNumerado,
        titulo=datos.metadatos.titulo,
        periodo=datos.metadatos.periodo,
        filtros=_texto_filtros(datos.metadatos.filtros_aplicados),
        generado=datos.metadatos.generado_en,
        tamano_pagina=tamano,
        margen_lateral=margen_lateral,
    )
    documento.build(elementos, canvasmaker=canvas_numerado)


def _seccion_tabla(
    titulo: str,
    datos: ReporteDatos,
    catalogo: Sequence[ColumnaReporte],
    filas: Sequence[Mapping[str, Any]],
    ids_seleccionados: Sequence[str] | None,
    incluir_totales: bool,
    incluir_notas: bool,
    estilos: Mapping[str, ParagraphStyle],
    ancho_disponible: float,
    mensaje_vacio: str,
) -> list:
    salida = [Paragraph(html.escape(titulo), estilos["Seccion"]), Spacer(1, 0.15 * cm)]
    disponibles = {columna.id: columna for columna in catalogo}
    orden = (
        list(ids_seleccionados)
        if ids_seleccionados is not None
        else [columna.id for columna in catalogo]
    )
    if not incluir_notas:
        orden = [
            identificador
            for identificador in orden
            if identificador not in {"notas", "observaciones"}
        ]
    columnas = [
        disponibles[identificador]
        for identificador in orden
        if identificador in disponibles
    ]
    if not filas:
        salida.append(Paragraph(html.escape(mensaje_vacio), estilos["Normal"]))
        return salida
    if not columnas:
        raise ValueError("Debe seleccionarse al menos una columna para PDF")

    anchos = _anchos_columnas(columnas, ancho_disponible)
    tabla_datos = [
        [Paragraph(html.escape(columna.etiqueta), estilos["Encabezado"]) for columna in columnas]
    ]
    for fila in filas:
        tabla_datos.append(
            [
                Paragraph(
                    _texto_celda(fila[columna.id], columna),
                    estilos[
                        "CeldaCentro"
                        if columna.alineacion == "centro"
                        else "Celda"
                    ],
                )
                for columna in columnas
            ]
        )

    indice_total = None
    if (
        incluir_totales
        and datos.totales_incluidos
        and datos.metadatos.tipo_informe != "objetivo"
    ):
        indice_total = len(tabla_datos)
        tabla_datos.append(
            [
                Paragraph(
                    html.escape(_texto_total(columna, datos.totales)),
                    estilos["Total"],
                )
                for columna in columnas
            ]
        )

    tabla = LongTable(
        tabla_datos,
        colWidths=anchos,
        repeatRows=1,
        splitByRow=1,
        hAlign="LEFT",
    )
    comandos = [
        ("BACKGROUND", (0, 0), (-1, 0), VERDE_INSTITUCIONAL),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "VESP-Vera-Bold"),
        ("GRID", (0, 0), (-1, -1), 0.35, GRIS_BORDE),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]
    for fila_idx in range(1, len(filas) + 1):
        if fila_idx % 2 == 0:
            comandos.append(
                ("BACKGROUND", (0, fila_idx), (-1, fila_idx), GRIS_FILA)
            )
    if indice_total is not None:
        comandos.extend(
            [
                ("BACKGROUND", (0, indice_total), (-1, indice_total), GRIS_TOTAL),
                ("LINEABOVE", (0, indice_total), (-1, indice_total), 1.2, GRAFITO_INSTITUCIONAL),
                ("FONTNAME", (0, indice_total), (-1, indice_total), "Helvetica-Bold"),
            ]
        )
    tabla.setStyle(TableStyle(comandos))
    salida.extend([tabla, Spacer(1, 0.25 * cm)])
    if titulo == "Detalle de pasadas" and incluir_totales and "pasadas" in datos.totales:
        resumen_totales = _texto_totales_pasadas(datos.totales)
        salida.append(
            Paragraph(
                f"<b>{html.escape(resumen_totales)}</b>",
                estilos["ResumenTotales"],
            )
        )
    return salida


def _estilos() -> dict[str, ParagraphStyle]:
    base = getSampleStyleSheet()
    return {
        "Seccion": ParagraphStyle(
            "SeccionReporte",
            parent=base["Heading2"],
            fontName="VESP-Vera-Bold",
            fontSize=11,
            leading=14,
            textColor=GRAFITO_INSTITUCIONAL,
            spaceAfter=3,
        ),
        "Encabezado": ParagraphStyle(
            "EncabezadoReporte",
            parent=base["Normal"],
            fontName="VESP-Vera-Bold",
            fontSize=8,
            leading=10,
            textColor=colors.white,
            alignment=1,
        ),
        "Celda": ParagraphStyle(
            "CeldaReporte",
            parent=base["Normal"],
            fontName="VESP-Vera",
            fontSize=7.5,
            leading=9.5,
            textColor=GRAFITO_INSTITUCIONAL,
            wordWrap="CJK",
        ),
        "CeldaCentro": ParagraphStyle(
            "CeldaCentroReporte",
            parent=base["Normal"],
            fontName="VESP-Vera",
            fontSize=7.5,
            leading=9.5,
            textColor=GRAFITO_INSTITUCIONAL,
            alignment=1,
            wordWrap="CJK",
        ),
        "Total": ParagraphStyle(
            "TotalReporte",
            parent=base["Normal"],
            fontName="VESP-Vera-Bold",
            fontSize=7.5,
            leading=9.5,
            textColor=GRAFITO_INSTITUCIONAL,
        ),
        "ResumenTotales": ParagraphStyle(
            "ResumenTotalesReporte",
            parent=base["Normal"],
            fontName="VESP-Vera-Bold",
            fontSize=8,
            leading=11,
            textColor=GRAFITO_INSTITUCIONAL,
            backColor=GRIS_TOTAL,
            borderPadding=5,
        ),
    }


def _orientacion(columnas: Sequence[ColumnaReporte]) -> str:
    ancho_estimado = sum(_ancho_base(columna) for columna in columnas)
    return "landscape" if len(columnas) > 5 or ancho_estimado > 17.5 * cm else "portrait"


def _anchos_columnas(
    columnas: Sequence[ColumnaReporte], ancho_disponible: float
) -> list[float]:
    anchos_base = [_ancho_base(columna) for columna in columnas]
    suma = sum(anchos_base)
    return [ancho * ancho_disponible / suma for ancho in anchos_base]


def _ancho_base(columna: ColumnaReporte) -> float:
    if columna.tipo_dato in {"entero", "decimal", "porcentaje", "hora"}:
        return 2.1 * cm
    if columna.tipo_dato in {"fecha", "fecha_texto"}:
        return 2.5 * cm
    if columna.tipo_dato == "texto_largo":
        return 5.2 * cm
    return min(max(stringWidth(columna.etiqueta, "VESP-Vera", 8) + 18, 2.7 * cm), 5.5 * cm)


def _texto_celda(valor: Any, columna: ColumnaReporte) -> str:
    if valor is None:
        texto = ""
    elif columna.tipo_dato == "fecha" and isinstance(valor, (date, datetime)):
        texto = valor.strftime("%d/%m/%Y")
    elif columna.tipo_dato == "fecha_texto" and isinstance(valor, str):
        texto = valor
    elif columna.tipo_dato == "hora" and isinstance(valor, time):
        texto = valor.strftime("%H:%M")
    elif columna.tipo_dato == "porcentaje":
        texto = f"{float(valor) * 100:.1f}%"
    elif columna.tipo_dato == "entero":
        texto = f"{int(valor):,}".replace(",", ".")
    else:
        texto = str(valor)
    texto = texto.replace("✔", "[X]").replace("✘", "[ ]")
    return html.escape(texto).replace("\n", "<br/>")


def _texto_total(columna: ColumnaReporte, totales: Mapping[str, Any]) -> str:
    alias = {
        "cumplimiento": "cumplimiento_total",
        "pasadas_totales": "pasadas",
    }
    clave = alias.get(columna.id, columna.id)
    valor = totales.get(clave)
    if valor is None and columna.id == "objetivo":
        return "Totales"
    if valor is None:
        return ""
    if columna.tipo_dato == "porcentaje":
        return f"{float(valor) * 100:.1f}%"
    if columna.tipo_dato == "entero":
        return f"{int(valor):,}".replace(",", ".")
    return str(valor)


def _texto_totales_pasadas(totales: Mapping[str, Any]) -> str:
    partes = [f"Total de pasadas: {totales['pasadas']}"]
    if "pasadas_diurnas" in totales:
        partes.append(f"Día: {totales['pasadas_diurnas']}")
    if "pasadas_nocturnas" in totales:
        partes.append(f"Noche: {totales['pasadas_nocturnas']}")
    return " | ".join(partes)


def _texto_filtros(filtros: Mapping[str, Any]) -> str:
    if not filtros:
        return "Sin filtros adicionales"
    partes = []
    for clave, valor in filtros.items():
        if isinstance(valor, (list, tuple, set)):
            etiqueta = (
                ", ".join(str(elemento) for elemento in valor)
                if len(valor) <= 4
                else f"{len(valor)} seleccionados"
            )
        else:
            etiqueta = str(valor)
        partes.append(f"{clave}: {etiqueta}")
    return " | ".join(partes)


def _registrar_fuentes() -> None:
    """Usa Vera, incluida con ReportLab, para representar bien el texto español."""
    directorio = Path(reportlab.__file__).resolve().parent / "fonts"
    fuentes = {
        "VESP-Vera": directorio / "Vera.ttf",
        "VESP-Vera-Bold": directorio / "VeraBd.ttf",
        "VESP-Vera-Italic": directorio / "VeraIt.ttf",
        "VESP-Vera-BoldItalic": directorio / "VeraBI.ttf",
    }
    registradas = set(pdfmetrics.getRegisteredFontNames())
    for nombre, ruta in fuentes.items():
        if nombre not in registradas:
            pdfmetrics.registerFont(TTFont(nombre, str(ruta)))
    pdfmetrics.registerFontFamily(
        "VESP-Vera",
        normal="VESP-Vera",
        bold="VESP-Vera-Bold",
        italic="VESP-Vera-Italic",
        boldItalic="VESP-Vera-BoldItalic",
    )


def _seccion_notas(
    notas: Sequence[Mapping[str, Any]],
    estilos: Mapping[str, ParagraphStyle],
    ancho_disponible: float,
) -> list:
    filas = [
        [
            Paragraph("Fecha", estilos["Encabezado"]),
            Paragraph("Nota diaria", estilos["Encabezado"]),
        ]
    ]
    for nota in notas:
        fecha = nota.get("fecha")
        fecha_texto = (
            fecha.strftime("%d/%m/%Y")
            if isinstance(fecha, (date, datetime))
            else str(fecha or "")
        )
        filas.append(
            [
                Paragraph(html.escape(fecha_texto), estilos["CeldaCentro"]),
                Paragraph(
                    html.escape(str(nota.get("nota", ""))).replace("\n", "<br/>"),
                    estilos["Celda"],
                ),
            ]
        )
    tabla = LongTable(
        filas,
        colWidths=[2.7 * cm, ancho_disponible - 2.7 * cm],
        repeatRows=1,
        splitByRow=1,
    )
    tabla.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), GRAFITO_INSTITUCIONAL),
                ("GRID", (0, 0), (-1, -1), 0.35, GRIS_BORDE),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, GRIS_FILA]),
            ]
        )
    )
    return [
        Paragraph("Notas diarias", estilos["Seccion"]),
        Spacer(1, 0.15 * cm),
        tabla,
    ]


def _seccion_subtotales(
    datos: ReporteDatos,
    estilos: Mapping[str, ParagraphStyle],
    ancho_disponible: float,
) -> list:
    etiquetas = {
        "objetivo": "Objetivo",
        "supervisor": "Supervisor",
        "dia": "Día",
    }
    agrupacion = str(datos.subtotales[0]["agrupacion"])
    filas = [
        [
            Paragraph(etiquetas[agrupacion], estilos["Encabezado"]),
            Paragraph("Pasadas", estilos["Encabezado"]),
        ]
    ]
    filas.extend(
        [
            Paragraph(html.escape(str(subtotal["etiqueta"])), estilos["Celda"]),
            Paragraph(str(subtotal["pasadas"]), estilos["CeldaCentro"]),
        ]
        for subtotal in datos.subtotales
    )
    tabla = Table(
        filas,
        colWidths=[ancho_disponible * 0.8, ancho_disponible * 0.2],
        repeatRows=1,
        splitByRow=1,
    )
    tabla.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), GRAFITO_INSTITUCIONAL),
                ("GRID", (0, 0), (-1, -1), 0.35, GRIS_BORDE),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, GRIS_FILA]),
                ("LINEABOVE", (0, -1), (-1, -1), 1.2, GRAFITO_INSTITUCIONAL),
            ]
        )
    )
    return [
        Paragraph("Subtotales por grupo", estilos["Seccion"]),
        Spacer(1, 0.15 * cm),
        tabla,
        Spacer(1, 0.25 * cm),
    ]


def _seccion_resumen_objetivo(
    datos: ReporteDatos,
    estilos: Mapping[str, ParagraphStyle],
) -> list:
    etiquetas = {
        "dias_esperados": "Días esperados",
        "dias_con_dia": "Días con pasada DIA",
        "dias_con_noche": "Días con pasada NOCHE",
        "dias_sin_control": "Días sin control",
        "cumplimiento": "Cumplimiento",
    }
    filas = [
        [
            Paragraph("Indicador", estilos["Encabezado"]),
            Paragraph("Total", estilos["Encabezado"]),
        ]
    ]
    for clave, etiqueta in etiquetas.items():
        valor = datos.totales.get(clave)
        texto = (
            f"{float(valor) * 100:.1f}%"
            if clave == "cumplimiento" and valor is not None
            else str(valor if valor is not None else "")
        )
        filas.append(
            [
                Paragraph(html.escape(etiqueta), estilos["Celda"]),
                Paragraph(html.escape(texto), estilos["CeldaCentro"]),
            ]
        )
    tabla = Table(filas, colWidths=[7.2 * cm, 3 * cm], hAlign="LEFT")
    tabla.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), GRAFITO_INSTITUCIONAL),
                ("BACKGROUND", (0, 1), (-1, -1), GRIS_TOTAL),
                ("GRID", (0, 0), (-1, -1), 0.35, GRIS_BORDE),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ]
        )
    )
    return [
        Paragraph("Totales del objetivo", estilos["Seccion"]),
        Spacer(1, 0.15 * cm),
        tabla,
    ]


class _LienzoNumerado(canvas.Canvas):
    """Dibuja marca, filtros y pie con la numeración total de páginas."""

    def __init__(
        self,
        *args,
        titulo: str,
        periodo: str,
        filtros: str,
        generado: datetime,
        tamano_pagina,
        margen_lateral: float,
        **kwargs,
    ) -> None:
        super().__init__(*args, **kwargs)
        self._estados_paginas = []
        self._titulo = titulo
        self._periodo = periodo
        self._filtros = filtros
        self._generado = generado
        self._tamano_pagina = tamano_pagina
        self._margen_lateral = margen_lateral

    def showPage(self) -> None:
        self._estados_paginas.append(dict(self.__dict__))
        self._startPage()

    def save(self) -> None:
        total = len(self._estados_paginas)
        for numero, estado in enumerate(self._estados_paginas, start=1):
            self.__dict__.update(estado)
            self._dibujar_encabezado_pie(numero, total)
            super().showPage()
        super().save()

    def _dibujar_encabezado_pie(self, numero: int, total: int) -> None:
        ancho, alto = self._tamano_pagina
        self.saveState()
        self.setFillColor(GRAFITO_INSTITUCIONAL)
        self.setFont("VESP-Vera-Bold", 11)
        self._dibujar_logo(self._margen_lateral, alto - 1.1 * cm)
        self.drawString(
            self._margen_lateral + 0.95 * cm,
            alto - 0.65 * cm,
            "VESP Organizations",
        )
        ancho_texto = ancho - 2 * self._margen_lateral
        estilo_titulo = ParagraphStyle(
            "TituloReportePDF",
            fontName="VESP-Vera-Bold",
            fontSize=9,
            leading=11,
            textColor=GRAFITO_INSTITUCIONAL,
        )
        titulo = Paragraph(
            html.escape(f"{self._titulo} — {self._periodo}"),
            estilo_titulo,
        )
        _, alto_titulo = titulo.wrap(ancho_texto, 1.2 * cm)
        y_actual = alto - 1.35 * cm
        titulo.drawOn(
            self,
            self._margen_lateral,
            y_actual - alto_titulo,
        )
        y_actual -= alto_titulo + 0.1 * cm
        estilos = getSampleStyleSheet()
        estilo_filtros = ParagraphStyle(
            "FiltrosPDF",
            parent=estilos["Normal"],
            fontName="VESP-Vera",
            fontSize=7,
            leading=8,
            textColor=GRAFITO_INSTITUCIONAL,
        )
        filtros = Paragraph(
            html.escape(f"Filtros: {self._filtros}"),
            estilo_filtros,
        )
        _, alto_filtros = filtros.wrap(ancho_texto, 1.05 * cm)
        filtros.drawOn(
            self,
            self._margen_lateral,
            y_actual - alto_filtros,
        )
        y_actual -= alto_filtros + 0.1 * cm
        self.setStrokeColor(GRIS_BORDE)
        self.setLineWidth(0.4)
        self.line(
            self._margen_lateral,
            y_actual,
            ancho - self._margen_lateral,
            y_actual,
        )
        self.setFont("VESP-Vera", 7)
        self.drawString(
            self._margen_lateral,
            0.9 * cm,
            f"Generado: {self._generado:%d/%m/%Y %H:%M}",
        )
        self.drawRightString(
            ancho - self._margen_lateral,
            0.9 * cm,
            f"Página {numero} de {total}",
        )
        self.restoreState()

    def _dibujar_logo(self, x: float, y: float) -> None:
        try:
            from services.assets import ruta_asset

            ruta_logo = Path(ruta_asset("assets/logo_vesp_v2_hd_transparente.png"))
            if ruta_logo.is_file():
                self.drawImage(
                    str(ruta_logo),
                    x,
                    y,
                    width=0.75 * cm,
                    height=0.75 * cm,
                    preserveAspectRatio=True,
                    mask="auto",
                )
        except OSError:
            logger.exception("No se pudo dibujar el logo en el informe PDF")
