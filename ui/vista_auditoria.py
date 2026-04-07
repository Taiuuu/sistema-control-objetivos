# =============================================================================
# VESP Organizations - Sistema de Control de Objetivos
# Pantalla de visualización de auditoría detallada
# =============================================================================

import json
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QTableWidget, QTableWidgetItem, QDateEdit, QComboBox,
    QPushButton, QMessageBox, QTextEdit, QTabWidget,
    QSplitter, QFileDialog
)
from PyQt6.QtCore import QDate, Qt
from PyQt6.QtGui import QColor
from services.auditoria import (
    obtener_auditoria_usuario, obtener_auditoria_tabla,
    obtener_cambios_por_fecha, validar_integridad_auditoria,
    exportar_auditoria_csv, TipoOperacion
)
from services.sesion import get_usuario_id


def _obtener_nombre_usuario(usuario_id: int | None) -> str:
    """Obtiene el nombre de usuario por ID."""
    if not usuario_id:
        return "Sistema"
    from database.db import conectar
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("SELECT username FROM usuarios WHERE id = ?", (usuario_id,))
    resultado = cursor.fetchone()
    conn.close()
    return resultado[0] if resultado else f"Usuario {usuario_id}"


class VistaAuditoria(QWidget):
    """Vista detallada de la auditoría del sistema."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Auditoría del Sistema")
        self.setGeometry(200, 200, 1200, 800)
        self.setMinimumSize(900, 600)

        layout_principal = QVBoxLayout(self)
        layout_principal.setSpacing(12)
        layout_principal.setContentsMargins(12, 12, 12, 12)

        # Título
        titulo = QLabel("Auditoría del Sistema")
        titulo.setStyleSheet("font-size: 18px; font-weight: bold; color: #2a82da;")
        layout_principal.addWidget(titulo)

        # Controles de filtrado
        controles = QHBoxLayout()

        # Filtro por tipo de vista
        self.combo_vista = QComboBox()
        self.combo_vista.addItems([
            "Por Fecha",
            "Por Usuario",
            "Por Tabla",
            "Validar Integridad"
        ])
        self.combo_vista.currentTextChanged.connect(self._cambiar_vista)
        controles.addWidget(QLabel("Ver:"))
        controles.addWidget(self.combo_vista)

        # Fecha
        controles.addSpacing(20)
        controles.addWidget(QLabel("Fecha:"))
        self.selector_fecha = QDateEdit()
        self.selector_fecha.setDate(QDate.currentDate())
        self.selector_fecha.setCalendarPopup(True)
        self.selector_fecha.dateChanged.connect(self._cargar_datos)
        controles.addWidget(self.selector_fecha)

        # Usuario (filtro)
        controles.addSpacing(20)
        controles.addWidget(QLabel("Usuario:"))
        self.combo_usuario = QComboBox()
        self._cargar_usuarios()
        self.combo_usuario.currentIndexChanged.connect(self._cargar_datos)
        controles.addWidget(self.combo_usuario)

        # Tabla (filtro)
        controles.addSpacing(20)
        controles.addWidget(QLabel("Tabla:"))
        self.combo_tabla = QComboBox()
        self.combo_tabla.addItems(["", "objetivos", "supervisores", "pasadas", "usuarios", "equipos"])
        self.combo_tabla.currentTextChanged.connect(self._cargar_datos)
        controles.addWidget(self.combo_tabla)

        # Botón exportar
        controles.addStretch()
        btn_exportar = QPushButton("📊 Exportar CSV")
        btn_exportar.clicked.connect(self._exportar_auditoria)
        controles.addWidget(btn_exportar)

        layout_principal.addLayout(controles)

        # Tabs para diferentes vistas
        self.tabs = QTabWidget()

        # Tab 1: Tabla de auditoría
        self.tabla_auditoria = QTableWidget()
        self.tabla_auditoria.setColumnCount(8)
        self.tabla_auditoria.setHorizontalHeaderLabels([
            "Fecha/Hora", "Usuario", "Operación", "Tabla",
            "Reg. ID", "Detalles", "Estado", "Ver Cambios"
        ])
        self.tabla_auditoria.setColumnWidth(0, 150)
        self.tabla_auditoria.setColumnWidth(1, 120)
        self.tabla_auditoria.setColumnWidth(2, 100)
        self.tabla_auditoria.setColumnWidth(3, 100)
        self.tabla_auditoria.setColumnWidth(4, 80)
        self.tabla_auditoria.setColumnWidth(5, 200)
        self.tabla_auditoria.setColumnWidth(6, 80)
        self.tabla_auditoria.setColumnWidth(7, 100)
        self.tabla_auditoria.setAlternatingRowColors(True)
        self.tabs.addTab(self.tabla_auditoria, "Registros")

        # Tab 2: Detalles de cambios
        layout_detalles = QVBoxLayout()
        self.texto_cambios = QTextEdit()
        self.texto_cambios.setReadOnly(True)
        self.texto_cambios.setStyleSheet("""
            QTextEdit {
                background-color: #f5f5f5;
                border: 1px solid #ccc;
                border-radius: 4px;
                font-family: 'Courier New';
                font-size: 11px;
            }
        """)
        layout_detalles.addWidget(self.texto_cambios)
        widget_detalles = QWidget()
        widget_detalles.setLayout(layout_detalles)
        self.tabs.addTab(widget_detalles, "Cambios Detallados")

        # Tab 3: Validación de integridad
        layout_integridad = QVBoxLayout()
        self.texto_integridad = QTextEdit()
        self.texto_integridad.setReadOnly(True)
        btn_validar = QPushButton("🔍 Validar Integridad")
        btn_validar.clicked.connect(self._validar_integridad)
        layout_integridad.addWidget(btn_validar)
        layout_integridad.addWidget(self.texto_integridad)
        widget_integridad = QWidget()
        widget_integridad.setLayout(layout_integridad)
        self.tabs.addTab(widget_integridad, "Integridad")

        layout_principal.addWidget(self.tabs)

        self._cargar_datos()

    def _cargar_usuarios(self) -> None:
        """Carga la lista de usuarios disponibles."""
        try:
            from database.db import conectar
            conn = conectar()
            cursor = conn.cursor()
            cursor.execute("SELECT id, username FROM usuarios ORDER BY username")
            usuarios = cursor.fetchall()
            conn.close()

            self.combo_usuario.clear()
            self.combo_usuario.addItem("Todos", None)
            for uid, username in usuarios:
                self.combo_usuario.addItem(username, uid)
        except Exception as e:
            print(f"Error cargando usuarios: {e}")

    def _cambiar_vista(self) -> None:
        """Cambia la vista según la selección del combo."""
        vista = self.combo_vista.currentText()
        
        self.selector_fecha.setEnabled(vista == "Por Fecha")
        self.combo_usuario.setEnabled(vista == "Por Usuario")
        self.combo_tabla.setEnabled(vista == "Por Tabla")

        self._cargar_datos()

    def _cargar_datos(self) -> None:
        """Carga los datos de auditoría según los filtros."""
        vista = self.combo_vista.currentText()
        registros = []

        try:
            if vista == "Por Fecha":
                fecha = self.selector_fecha.date().toString("yyyy-MM-dd")
                registros = obtener_cambios_por_fecha(fecha)
            elif vista == "Por Usuario":
                usuario_id = self.combo_usuario.currentData()
                if usuario_id:
                    registros = obtener_auditoria_usuario(usuario_id)
            elif vista == "Por Tabla":
                tabla = self.combo_tabla.currentText()
                if tabla:
                    registros = obtener_auditoria_tabla(tabla)
            elif vista == "Validar Integridad":
                self.tabla_auditoria.setRowCount(0)
                return

            self._mostrar_registros(registros)

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error cargando datos: {e}")

    def _mostrar_registros(self, registros: list) -> None:
        """Muestra los registros en la tabla."""
        self.tabla_auditoria.setRowCount(len(registros))

        for i, registro in enumerate(registros):
            # Los campos varían según el tipo de query, pero usamos índices seguros
            try:
                fecha_hora = f"{registro[0]} {registro[1]}"
                usuario = _obtener_nombre_usuario(registro[2] if len(registro) > 2 else None)
                tipo_op = registro[3] if len(registro) > 3 else ""
                tabla = registro[4] if len(registro) > 4 else ""
                reg_id = str(registro[5]) if len(registro) > 5 else ""
                detalles = registro[6] if len(registro) > 6 else ""
                estado = registro[7] if len(registro) > 7 else "EXITOSO"

                self.tabla_auditoria.setItem(i, 0, QTableWidgetItem(fecha_hora))
                self.tabla_auditoria.setItem(i, 1, QTableWidgetItem(usuario))
                self.tabla_auditoria.setItem(i, 2, QTableWidgetItem(tipo_op))
                self.tabla_auditoria.setItem(i, 3, QTableWidgetItem(tabla))
                self.tabla_auditoria.setItem(i, 4, QTableWidgetItem(reg_id))
                self.tabla_auditoria.setItem(i, 5, QTableWidgetItem(str(detalles)[:50]))
                
                color_fondo = "#d4edda" if estado == "EXITOSO" else "#f8d7da"
                for col in range(6):
                    self.tabla_auditoria.item(i, col).setBackground(QColor(color_fondo))

                # Botón ver cambios
                btn = QPushButton("Ver")
                btn.clicked.connect(lambda checked, r=registro: self._mostrar_cambios(r))
                self.tabla_auditoria.setCellWidget(i, 7, btn)

            except Exception as e:
                print(f"Error mostrando registro {i}: {e}")

    def _mostrar_cambios(self, registro: tuple) -> None:
        """Muestra los detalles de cambios de un registro."""
        try:
            texto = "=== DETALLES DEL CAMBIO ===\n\n"
            
            # Intentar extraer valores anteriores y nuevos
            if len(registro) > 7:
                valores_ant = registro[6]
                valores_nuev = registro[7]
                
                if valores_ant:
                    texto += "VALORES ANTERIORES:\n"
                    datos_ant = json.loads(valores_ant) if isinstance(valores_ant, str) else valores_ant
                    for clave, valor in datos_ant.items():
                        texto += f"  {clave}: {valor}\n"
                    texto += "\n"
                
                if valores_nuev:
                    texto += "VALORES NUEVOS:\n"
                    datos_nuev = json.loads(valores_nuev) if isinstance(valores_nuev, str) else valores_nuev
                    for clave, valor in datos_nuev.items():
                        texto += f"  {clave}: {valor}\n"
            
            self.texto_cambios.setText(texto)
            self.tabs.setCurrentIndex(1)

        except Exception as e:
            self.texto_cambios.setText(f"Error procesando cambios: {e}")

    def _validar_integridad(self) -> None:
        """Valida la integridad de la auditoría."""
        resultado = validar_integridad_auditoria()
        
        texto = "=== VALIDACIÓN DE INTEGRIDAD ===\n\n"
        texto += f"Total de registros: {resultado.get('total_registros', 0)}\n"
        texto += f"Registros validados: {resultado.get('registros_validados', 0)}\n"
        texto += f"Estado: {'✅ VÁLIDO' if resultado.get('es_valido') else '❌ ANOMALÍAS DETECTADAS'}\n"
        
        if resultado.get('anomalias'):
            texto += "\nANOMALÍAS ENCONTRADAS:\n"
            for anomalia in resultado['anomalias']:
                texto += f"  ⚠️ {anomalia}\n"
        else:
            texto += "\nNo se detectaron anomalías.\n"
        
        self.texto_integridad.setText(texto)

    def _exportar_auditoria(self) -> None:
        """Exporta la auditoría a CSV."""
        ruta, _ = QFileDialog.getSaveFileName(
            self, "Guardar auditoría", "auditoria.csv", "CSV Files (*.csv)"
        )
        
        if ruta:
            fecha_inicio = self.selector_fecha.date().toString("yyyy-MM-dd")
            fecha_fin = fecha_inicio  # Por ahora, un día
            
            if exportar_auditoria_csv(fecha_inicio, fecha_fin, ruta):
                QMessageBox.information(self, "Listo", f"Auditoría exportada a:\n{ruta}")
            else:
                QMessageBox.critical(self, "Error", "No se pudo exportar la auditoría")
