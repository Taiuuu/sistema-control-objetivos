# ui/resolucion_excel.py
"""
ui/resolucion_excel.py

Fase 12: pantalla de resolución de problemas, con 3 pestañas
(errores críticos / advertencias / matching).

Igual que analisis_excel.py (Fase 11), es puramente PRESENTACIÓN +
acumulación de decisiones en memoria: no importa nada de `models.*` ni
abre conexión a la base. No persiste nada hasta que Fase 13
(confirmar_importacion) reciba el EstadoResolucion armado acá.
"""

from __future__ import annotations

from PyQt6.QtWidgets import (
    QComboBox, QDialog, QHBoxLayout, QInputDialog, QLineEdit,
    QMessageBox, QPushButton, QTableWidget, QTableWidgetItem,
    QTabWidget, QVBoxLayout, QWidget,
)

from importador.modelos import (
    Problema,
    ResultadoAnalisis,
    ResultadoMatchObjetivo,
    ResultadoMatchSupervisor,
)
from importador.resolucion import EstadoResolucion

_COLOR_OK = "#8affc1"
_COLOR_WARN = "#ffb74d"
_COLOR_ERROR = "#ff8a80"
_COLOR_TEXTO = "#d0d0d0"


class DialogoResolucion(QDialog):
    """Uso:
        estado = EstadoResolucion(usuario=usuario.nombre)
        dialogo = DialogoResolucion(resultado, estado, parent=self)
        if dialogo.exec() == QDialog.DialogCode.Accepted:
            resumen = confirmar_importacion(resultado, estado, usuario)
    """

    def __init__(self, resultado: ResultadoAnalisis, estado: EstadoResolucion, parent=None):
        super().__init__(parent)
        self.resultado = resultado
        self.estado = estado
        self.setWindowTitle("Resolver problemas")
        self.setMinimumSize(760, 480)

        self._problemas_indexados = list(enumerate(resultado.problemas))

        layout = QVBoxLayout(self)
        self.tabs = QTabWidget()
        layout.addWidget(self.tabs)

        self._armar_tab_errores()
        self._armar_tab_advertencias()
        self._armar_tab_matching()

        fila_botones = QHBoxLayout()
        self.boton_cerrar = QPushButton("Volver al resumen")
        self.boton_cerrar.clicked.connect(self.accept)
        fila_botones.addStretch()
        fila_botones.addWidget(self.boton_cerrar)
        layout.addLayout(fila_botones)

    # -------------------- Pestaña 1: errores críticos --------------------

    def _armar_tab_errores(self) -> None:
        errores = [(i, p) for i, p in self._problemas_indexados if p.tipo == "error_critico"]
        contenedor = QWidget()
        layout = QVBoxLayout(contenedor)
        tabla = QTableWidget(len(errores), 4)
        tabla.setHorizontalHeaderLabels(["Hoja / Fila", "Descripción", "Valor corregido", ""])
        tabla.horizontalHeader().setStretchLastSection(True)
        tabla.verticalHeader().setVisible(False)

        for fila, (id_problema, problema) in enumerate(errores):
            tabla.setItem(fila, 0, QTableWidgetItem(f"{problema.hoja or ''} · fila {problema.fila_excel or ''}"))
            item_desc = QTableWidgetItem(problema.descripcion)
            item_desc.setForeground(_qcolor(_COLOR_ERROR))
            tabla.setItem(fila, 1, item_desc)

            # valor_problema es Any: para error_critico ASUMO que trae el
            # valor crudo que falló (ej. "25:99" en una hora inválida), como
            # string. Si no viene poblado, el campo arranca vacío nomás.
            valor_crudo = problema.valor_problema
            campo_valor = QLineEdit()
            campo_valor.setPlaceholderText(str(valor_crudo) if valor_crudo is not None else "valor corregido")
            tabla.setCellWidget(fila, 2, campo_valor)

            boton_guardar = QPushButton("Guardar corrección")
            boton_guardar.clicked.connect(
                lambda _=False, i=id_problema, p=problema, c=campo_valor: self._guardar_correccion_error(i, p, c)
            )
            tabla.setCellWidget(fila, 3, boton_guardar)

        if not errores:
            tabla.setRowCount(1)
            tabla.setSpan(0, 0, 1, 4)
            tabla.setItem(0, 0, QTableWidgetItem("No hay errores críticos."))

        layout.addWidget(tabla)
        self.tabs.addTab(contenedor, f"🔴 Errores críticos ({len(errores)})")

    def _guardar_correccion_error(self, id_problema, problema, campo: QLineEdit) -> None:
        valor_nuevo = campo.text().strip()
        if not valor_nuevo:
            QMessageBox.warning(self, "Falta el valor", "Escribí el valor corregido antes de guardar.")
            return
        self.estado.registrar_correccion(
            id_problema=id_problema, hoja=problema.hoja, objetivo=problema.objetivo,
            campo="valor_corregido",
            valor_antes=str(problema.valor_problema) if problema.valor_problema is not None else "(sin valor original)",
            valor_despues=valor_nuevo,
        )
        campo.setEnabled(False)
        campo.setStyleSheet(f"color: {_COLOR_OK};")

    # -------------------- Pestaña 2: advertencias --------------------

    def _armar_tab_advertencias(self) -> None:
        advertencias = [(i, p) for i, p in self._problemas_indexados if p.tipo == "advertencia"]
        contenedor = QWidget()
        layout = QVBoxLayout(contenedor)
        tabla = QTableWidget(len(advertencias), 3)
        tabla.setHorizontalHeaderLabels(["Hoja / Fila", "Descripción", ""])
        tabla.horizontalHeader().setStretchLastSection(True)
        tabla.verticalHeader().setVisible(False)

        for fila, (id_problema, problema) in enumerate(advertencias):
            tabla.setItem(fila, 0, QTableWidgetItem(f"{problema.hoja or ''} · fila {problema.fila_excel or ''}"))
            item_desc = QTableWidgetItem(problema.descripcion)
            item_desc.setForeground(_qcolor(_COLOR_WARN))
            tabla.setItem(fila, 1, item_desc)

            caja = QWidget()
            layout_caja = QHBoxLayout(caja)
            layout_caja.setContentsMargins(0, 0, 0, 0)
            boton_corregir = QPushButton("Corregir")
            boton_aceptar = QPushButton("Dejar como está")
            layout_caja.addWidget(boton_corregir)
            layout_caja.addWidget(boton_aceptar)
            tabla.setCellWidget(fila, 2, caja)

            boton_corregir.clicked.connect(
                lambda _=False, i=id_problema, p=problema, b1=boton_corregir, b2=boton_aceptar:
                    self._corregir_advertencia(i, p, b1, b2)
            )
            boton_aceptar.clicked.connect(
                lambda _=False, i=id_problema, p=problema, b1=boton_corregir, b2=boton_aceptar:
                    self._aceptar_advertencia(i, p, b1, b2)
            )

        if not advertencias:
            tabla.setRowCount(1)
            tabla.setSpan(0, 0, 1, 3)
            tabla.setItem(0, 0, QTableWidgetItem("No hay advertencias."))

        layout.addWidget(tabla)
        self.tabs.addTab(contenedor, f"🟡 Advertencias ({len(advertencias)})")

    def _corregir_advertencia(self, id_problema, problema, b_corregir, b_aceptar) -> None:
        # PROVISORIO: no hay campo en Problema que distinga "hora fuera de
        # rango" de "mover de tabla 2 a tabla 1". Detecto por texto de
        # descripcion como parche temporal — confirmame el campo correcto
        # (ver mensaje) antes de dar esto por terminado.
        if "tabla" in problema.descripcion.lower():
            self._mover_de_tabla(id_problema, problema, b_corregir, b_aceptar)
            return

        valor_nuevo, ok = QInputDialog.getText(
            self, "Corregir advertencia", f"{problema.descripcion}\n\nValor corregido:"
        )
        if not ok or not valor_nuevo.strip():
            return
        self.estado.registrar_correccion(
            id_problema=id_problema, hoja=problema.hoja, objetivo=problema.objetivo,
            campo="valor_corregido",
            valor_antes=str(problema.valor_problema) if problema.valor_problema is not None else problema.descripcion,
            valor_despues=valor_nuevo.strip(),
        )
        b_corregir.setEnabled(False)
        b_aceptar.setEnabled(False)
        b_corregir.setText("✅ Corregido")

    def _mover_de_tabla(self, id_problema, problema, b_corregir, b_aceptar) -> None:
        self.estado.registrar_correccion(
            id_problema=id_problema, hoja=problema.hoja, objetivo=problema.objetivo,
            campo="bloque_tabla",
            valor_antes="tabla 2", valor_despues="tabla 1",
        )
        b_corregir.setEnabled(False)
        b_aceptar.setEnabled(False)
        b_corregir.setText("✅ Movido a tabla 1")
    
    # -------------------- Pestaña 3: matching --------------------

    def _armar_tab_matching(self) -> None:
        para_revisar = [(i, p) for i, p in self._problemas_indexados if p.tipo == "para_revisar"]
        contenedor = QWidget()
        layout = QVBoxLayout(contenedor)
        tabla = QTableWidget(len(para_revisar), 4)
        tabla.setHorizontalHeaderLabels(["Hoja", "No reconocido", "Sugerencias", ""])
        tabla.horizontalHeader().setStretchLastSection(True)
        tabla.verticalHeader().setVisible(False)

        for fila, (id_problema, problema) in enumerate(para_revisar):
            tabla.setItem(fila, 0, QTableWidgetItem(problema.hoja or ""))
            tabla.setItem(fila, 1, QTableWidgetItem(problema.objetivo or problema.descripcion))

            # ASUMO que valor_problema trae el ResultadoMatchObjetivo o
            # ResultadoMatchSupervisor completo (ver matcher.py) — es la
            # única forma de llegar a .sugerencias, que no vive en Problema.
            resultado_match = problema.valor_problema
            nombres_sugeridos: list[str] = []
            if isinstance(resultado_match, ResultadoMatchObjetivo):
                nombres_sugeridos = [s.objetivo.nombre for s in resultado_match.sugerencias]
            elif isinstance(resultado_match, ResultadoMatchSupervisor):
                nombres_sugeridos = [s.supervisor.nombre for s in resultado_match.sugerencias]

            combo = QComboBox()
            combo.addItems(nombres_sugeridos)
            tabla.setCellWidget(fila, 2, combo)

            caja = QWidget()
            layout_caja = QHBoxLayout(caja)
            layout_caja.setContentsMargins(0, 0, 0, 0)
            boton_usar = QPushButton("Usar sugerencia")
            boton_crear = QPushButton("Crear nuevo")
            boton_usar.setEnabled(bool(nombres_sugeridos))
            layout_caja.addWidget(boton_usar)
            layout_caja.addWidget(boton_crear)
            tabla.setCellWidget(fila, 3, caja)

            boton_usar.clicked.connect(
                lambda _=False, i=id_problema, p=problema, c=combo, b1=boton_usar, b2=boton_crear:
                    self._usar_sugerencia(i, p, c, b1, b2)
            )
            boton_crear.clicked.connect(
                lambda _=False, i=id_problema, p=problema, b1=boton_usar, b2=boton_crear:
                    self._crear_nuevo(i, p, b1, b2)
            )

        if not para_revisar:
            tabla.setRowCount(1)
            tabla.setSpan(0, 0, 1, 4)
            tabla.setItem(0, 0, QTableWidgetItem("No hay objetivos ni supervisores para revisar."))

        layout.addWidget(tabla)
        self.tabs.addTab(contenedor, f"🟡 Matching ({len(para_revisar)})")

    def _usar_sugerencia(self, id_problema, problema, combo, b_usar, b_crear) -> None:
        elegido = combo.currentText()
        if not elegido:
            return
        self.estado.registrar_match(
            id_problema=id_problema, hoja=problema.hoja,
            objetivo=problema.objetivo or problema.descripcion, coincidencia_elegida=elegido,
        )
        b_usar.setEnabled(False)
        b_crear.setEnabled(False)
        b_usar.setText("✅ Asignado")

    def _crear_nuevo(self, id_problema, problema, b_usar, b_crear) -> None:
        nombre, ok = QInputDialog.getText(self, "Crear nuevo", "Nombre del nuevo objetivo/supervisor:")
        if not ok or not nombre.strip():
            return
        self.estado.registrar_creacion(
            id_problema=id_problema, hoja=problema.hoja,
            objetivo=problema.objetivo or problema.descripcion, nombre_nuevo=nombre.strip(),
        )
        b_usar.setEnabled(False)
        b_crear.setEnabled(False)
        b_crear.setText("✅ Nuevo creado")


def _qcolor(hex_color: str):
    from PyQt6.QtGui import QColor
    return QColor(hex_color)