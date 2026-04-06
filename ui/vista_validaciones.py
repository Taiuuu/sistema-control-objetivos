# =============================================================================
# VESP Organizations - Vista de Validaciones y Reparación de BD
# =============================================================================

from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QTabWidget, QTableWidget, QTableWidgetItem, QMessageBox,
    QTextEdit, QGroupBox, QScrollArea, QProgressBar
)
from PyQt6.QtGui import QColor
from services.validaciones import validar_integridad_bd, ErrorValidacion
from services.auditoria import registrar_auditoria, TipoOperacion
from database.db import conectar
import json
from datetime import datetime


class VistaValidaciones(QWidget):
    """Vista para gestionar validaciones e integridad de la base de datos."""

    def __init__(self, usuario_actual=None):
        super().__init__()
        self.usuario_actual = usuario_actual
        self.validacion_resultados = None
        self.init_ui()

    def init_ui(self):
        """Inicializa la interfaz."""
        layout = QVBoxLayout()

        # Título
        titulo = QLabel("Validaciones e Integridad de Base de Datos")
        titulo.setStyleSheet("font-size: 14px; font-weight: bold;")
        layout.addWidget(titulo)

        # Barra de botones
        botones_layout = QHBoxLayout()
        
        btn_validar = QPushButton("🔍 Ejecutar Validación Completa")
        btn_validar.clicked.connect(self.ejecutar_validacion)
        botones_layout.addWidget(btn_validar)
        
        btn_reparar = QPushButton("🔧 Reparar Problemas")
        btn_reparar.clicked.connect(self.reparar_problemas)
        botones_layout.addWidget(btn_reparar)
        
        btn_exportar = QPushButton("📄 Exportar Reporte")
        btn_exportar.clicked.connect(self.exportar_reporte)
        botones_layout.addWidget(btn_exportar)
        
        layout.addLayout(botones_layout)

        # Tabs
        self.tabs = QTabWidget()

        # Tab 1: Resultados de Validación
        self.tab_resultados = self._crear_tab_resultados()
        self.tabs.addTab(self.tab_resultados, "Resultados")

        # Tab 2: Detalles de Errores
        self.tab_errores = self._crear_tab_errores()
        self.tabs.addTab(self.tab_errores, "Errores Detectados")

        # Tab 3: Log de Reparaciones
        self.tab_reparaciones = self._crear_tab_reparaciones()
        self.tabs.addTab(self.tab_reparaciones, "Historial de Reparaciones")

        layout.addWidget(self.tabs)
        self.setLayout(layout)

    def _crear_tab_resultados(self):
        """Crea el tab de resultados generales."""
        widget = QWidget()
        layout = QVBoxLayout()

        # Estado general
        group_estado = QGroupBox("Estado General")
        estado_layout = QVBoxLayout()
        
        self.label_estado = QLabel("No validado aún")
        self.label_estado.setStyleSheet("font-size: 12px;")
        estado_layout.addWidget(self.label_estado)
        
        self.progress_validacion = QProgressBar()
        self.progress_validacion.setVisible(False)
        estado_layout.addWidget(self.progress_validacion)
        
        group_estado.setLayout(estado_layout)
        layout.addWidget(group_estado)

        # Resumen
        group_resumen = QGroupBox("Resumen")
        resumen_layout = QVBoxLayout()
        
        self.label_resumen = QLabel("Errores: 0 | Advertencias: 0 | Pasadas: 0 | Objetivos: 0 | Supervisores: 0")
        self.label_resumen.setStyleSheet("font-size: 11px; color: gray;")
        resumen_layout.addWidget(self.label_resumen)
        
        group_resumen.setLayout(resumen_layout)
        layout.addWidget(group_resumen)

        # Tabla de chequeos
        group_chequeos = QGroupBox("Chequeos Realizados")
        chequeos_layout = QVBoxLayout()
        
        self.tabla_chequeos = QTableWidget()
        self.tabla_chequeos.setColumnCount(3)
        self.tabla_chequeos.setHorizontalHeaderLabels(["Chequeo", "Estado", "Detalles"])
        self.tabla_chequeos.setColumnWidth(0, 250)
        self.tabla_chequeos.setColumnWidth(1, 80)
        self.tabla_chequeos.setColumnWidth(2, 300)
        
        chequeos_layout.addWidget(self.tabla_chequeos)
        group_chequeos.setLayout(chequeos_layout)
        layout.addWidget(group_chequeos)

        layout.addStretch()
        widget.setLayout(layout)
        return widget

    def _crear_tab_errores(self):
        """Crea el tab de errores detectados."""
        widget = QWidget()
        layout = QVBoxLayout()

        self.texto_errores = QTextEdit()
        self.texto_errores.setReadOnly(True)
        layout.addWidget(self.texto_errores)

        widget.setLayout(layout)
        return widget

    def _crear_tab_reparaciones(self):
        """Crea el tab de historial de reparaciones."""
        widget = QWidget()
        layout = QVBoxLayout()

        self.tabla_reparaciones = QTableWidget()
        self.tabla_reparaciones.setColumnCount(4)
        self.tabla_reparaciones.setHorizontalHeaderLabels(
            ["Fecha/Hora", "Tipo", "Descripción", "Resultado"]
        )
        self.tabla_reparaciones.setColumnWidth(0, 150)
        self.tabla_reparaciones.setColumnWidth(1, 100)
        self.tabla_reparaciones.setColumnWidth(2, 250)
        self.tabla_reparaciones.setColumnWidth(3, 100)

        layout.addWidget(self.tabla_reparaciones)
        widget.setLayout(layout)
        return widget

    def ejecutar_validacion(self):
        """Ejecuta las validaciones completas."""
        self.label_estado.setText("Validando... por favor espere")
        self.progress_validacion.setVisible(True)
        self.progress_validacion.setValue(0)

        try:
            # Ejecutar validaciones
            resultados = validar_integridad_bd()
            self.validacion_resultados = resultados

            # Actualizar UI
            self._actualizar_resultados(resultados)

            # Auditar
            if self.usuario_actual:
                registrar_auditoria(
                    usuario_id=self.usuario_actual.get('id') if isinstance(self.usuario_actual, dict) else None,
                    tipo_operacion=TipoOperacion.READ,
                    tabla="validaciones",
                    detalles=f"Validación ejecutada. Válido: {resultados.get('es_valido')}",
                    usuario_nombre=self.usuario_actual.get('username') if isinstance(self.usuario_actual, dict) else None
                )

            QMessageBox.information(
                self, 
                "Validación Completada",
                f"Estado: {'✅ BD Válida' if resultados.get('es_valido') else '⚠️ Se encontraron problemas'}\n\n"
                f"Errores: {len(resultados.get('errores', []))}\n"
                f"Advertencias: {len(resultados.get('advertencias', []))}"
            )

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error en validación: {e}")
        finally:
            self.progress_validacion.setVisible(False)

    def _actualizar_resultados(self, resultados):
        """Actualiza la UI con los resultados de validación."""
        es_valido = resultados.get('es_valido')
        errores = resultados.get('errores', [])
        advertencias = resultados.get('advertencias', [])

        # Estado
        if es_valido:
            self.label_estado.setText("✅ Base de datos válida")
            self.label_estado.setStyleSheet("font-size: 12px; color: green; font-weight: bold;")
        else:
            self.label_estado.setText("❌ Problemas detectados")
            self.label_estado.setStyleSheet("font-size: 12px; color: red; font-weight: bold;")

        # Actualizar tabla de chequeos
        self.tabla_chequeos.setRowCount(0)
        
        chequeos = [
            ("Integridad referencial (pasadas → objetivos)", "✅" if es_valido else "❌", 
             "No existen pasadas huérfanas"),
            ("Integridad referencial (pasadas → supervisores)", "✅" if es_valido else "❌",
             "No existen pasadas con supervisores inválidos"),
            ("Integridad referencial (equipos)", "✅" if es_valido else "❌",
             "No existen equipos con supervisores inválidos"),
            ("Duplicados de objetivos", "✅" if es_valido else "❌",
             "No existen objetivos duplicados"),
            ("Duplicados de supervisores", "✅" if es_valido else "❌",
             "No existen supervisores duplicados"),
        ]

        for i, (chequeo, estado, detalle) in enumerate(chequeos):
            self.tabla_chequeos.insertRow(i)
            self.tabla_chequeos.setItem(i, 0, QTableWidgetItem(chequeo))
            
            item_estado = QTableWidgetItem(estado)
            if "❌" in estado:
                item_estado.setBackground(QColor(255, 200, 200))
            else:
                item_estado.setBackground(QColor(200, 255, 200))
            self.tabla_chequeos.setItem(i, 1, item_estado)
            
            self.tabla_chequeos.setItem(i, 2, QTableWidgetItem(detalle))

        # Errores
        texto_errores = "ERRORES DETECTADOS:\n" + "=" * 50 + "\n"
        if errores:
            for i, error in enumerate(errores, 1):
                texto_errores += f"{i}. {error}\n"
        else:
            texto_errores += "✅ No se detectaron errores\n"

        texto_errores += "\n" + "=" * 50 + "\n"
        texto_errores += "ADVERTENCIAS:\n" + "=" * 50 + "\n"
        
        if advertencias:
            for i, adv in enumerate(advertencias, 1):
                texto_errores += f"{i}. {adv}\n"
        else:
            texto_errores += "✅ No hay advertencias\n"

        self.texto_errores.setText(texto_errores)

        # Resumen
        try:
            conn = conectar()
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM pasadas")
            total_pasadas = cursor.fetchone()[0]
            cursor.execute("SELECT COUNT(*) FROM objetivos")
            total_objetivos = cursor.fetchone()[0]
            cursor.execute("SELECT COUNT(*) FROM supervisores")
            total_supervisores = cursor.fetchone()[0]
            conn.close()

            self.label_resumen.setText(
                f"Errores: {len(errores)} | Advertencias: {len(advertencias)} | "
                f"Pasadas: {total_pasadas} | Objetivos: {total_objetivos} | Supervisores: {total_supervisores}"
            )
        except:
            pass

    def reparar_problemas(self):
        """Intenta reparar los problemas encontrados."""
        if not self.validacion_resultados:
            QMessageBox.warning(self, "Advertencia", "Ejecute primero una validación")
            return

        respuesta = QMessageBox.question(
            self,
            "Reparar Problemas",
            "¿Desea intentar reparar los problemas detectados?\n\n"
            "Esto puede eliminar registros duplicados o huérfanos.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if respuesta != QMessageBox.StandardButton.Yes:
            return

        try:
            conn = conectar()
            cursor = conn.cursor()
            reparaciones_log = []

            # 1. Eliminar pasadas huérfanas (sin objetivo)
            cursor.execute("""
                DELETE FROM pasadas WHERE objetivo_id NOT IN (
                    SELECT id FROM objetivos
                )
            """)
            deleted = cursor.rowcount
            if deleted > 0:
                reparaciones_log.append(f"Eliminadas {deleted} pasadas huérfanas (sin objetivo)")

            # 2. Eliminar pasadas huérfanas (sin supervisor válido)
            cursor.execute("""
                DELETE FROM pasadas WHERE supervisor_id IS NOT NULL AND supervisor_id NOT IN (
                    SELECT id FROM supervisores
                )
            """)
            deleted = cursor.rowcount
            if deleted > 0:
                reparaciones_log.append(f"Eliminadas {deleted} pasadas con supervisor inválido")

            # 3. Eliminar equipos huérfanos
            cursor.execute("""
                DELETE FROM equipos WHERE 
                supervisor1_id NOT IN (SELECT id FROM supervisores) OR
                supervisor2_id NOT IN (SELECT id FROM supervisores)
            """)
            deleted = cursor.rowcount
            if deleted > 0:
                reparaciones_log.append(f"Eliminados {deleted} equipos con supervisores inválidos")

            conn.commit()
            conn.close()

            # Registrar reparaciones en tabla
            ahora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            for i, log in enumerate(reparaciones_log):
                row = self.tabla_reparaciones.rowCount()
                self.tabla_reparaciones.insertRow(row)
                self.tabla_reparaciones.setItem(row, 0, QTableWidgetItem(ahora))
                self.tabla_reparaciones.setItem(row, 1, QTableWidgetItem("AUTO"))
                self.tabla_reparaciones.setItem(row, 2, QTableWidgetItem(log))
                
                item_resultado = QTableWidgetItem("✅ OK")
                item_resultado.setBackground(QColor(200, 255, 200))
                self.tabla_reparaciones.setItem(row, 3, item_resultado)

            # Auditar
            if self.usuario_actual:
                registrar_auditoria(
                    usuario_id=self.usuario_actual.get('id') if isinstance(self.usuario_actual, dict) else None,
                    tipo_operacion=TipoOperacion.DELETE,
                    tabla="validaciones",
                    detalles=f"Reparación ejecutada. Registros reparados: {len(reparaciones_log)}",
                    usuario_nombre=self.usuario_actual.get('username') if isinstance(self.usuario_actual, dict) else None
                )

            QMessageBox.information(
                self,
                "Reparación Completada",
                f"Se completó la reparación.\n\n" + "\n".join(reparaciones_log)
            )

            # Re-ejecutar validación
            self.ejecutar_validacion()

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error en reparación: {e}")

    def exportar_reporte(self):
        """Exporta el reporte de validación a un archivo."""
        if not self.validacion_resultados:
            QMessageBox.warning(self, "Advertencia", "Ejecute primero una validación")
            return

        try:
            from datetime import datetime
            fecha = datetime.now().strftime("%Y%m%d_%H%M%S")
            ruta = f"reportes/validacion_{fecha}.json"

            reporte = {
                "fecha": datetime.now().isoformat(),
                "valido": self.validacion_resultados.get('es_valido'),
                "errores": self.validacion_resultados.get('errores', []),
                "advertencias": self.validacion_resultados.get('advertencias', [])
            }

            with open(ruta, 'w', encoding='utf-8') as f:
                json.dump(reporte, f, indent=2, ensure_ascii=False)

            QMessageBox.information(self, "Éxito", f"Reporte exportado a:\n{ruta}")

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error al exportar: {e}")
