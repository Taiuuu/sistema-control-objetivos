# =============================================================================
# VESP Organizations - Analizador de Indexación y Optimización de BD
# =============================================================================

import logging
import re
import sqlite3
from contextlib import closing
from typing import List, Dict, Optional
from database.db import DB_PATH, conectar

logger = logging.getLogger(__name__)
_IDENTIFIER_PATTERN = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


def _quoted_identifier(value: str) -> str:
    """Cita un identificador SQLite tras rechazar entradas no válidas."""
    if not isinstance(value, str) or not _IDENTIFIER_PATTERN.fullmatch(value):
        raise ValueError(f"Identificador SQL inválido: {value!r}")
    return f'"{value}"'


class AnalisisBD:
    """Analiza la estructura y performance de la base de datos."""
    
    def __init__(self):
        self.db_path = DB_PATH
    
    def obtener_tablas(self) -> List[str]:
        """Retorna todas las tablas en la BD."""
        try:
            with closing(conectar()) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
                )
                return [row[0] for row in cursor.fetchall()]
        except sqlite3.Error as e:
            print(f"Error obteniendo tablas: {e}")
            return []
    
    def obtener_indices(self, tabla: str) -> List[Dict]:
        """Retorna los índices de una tabla."""
        try:
            tabla_sql = _quoted_identifier(tabla)
            with closing(conectar()) as conn:
                cursor = conn.cursor()
                cursor.execute(f"PRAGMA index_list({tabla_sql})")
                indices_raw = cursor.fetchall()

                indices = []
                cursor.execute(f"SELECT COUNT(*) FROM {tabla_sql}")
                tamaño_tabla = cursor.fetchone()[0]
                for idx in indices_raw:
                    idx_name = idx[1]
                    cursor.execute(
                        f"PRAGMA index_info({_quoted_identifier(idx_name)})"
                    )
                    columnas = [
                        row[2] if row[2] is not None else "(expresión)"
                        for row in cursor.fetchall()
                    ]
                    indices.append({
                        "nombre": idx_name,
                        "columnas": columnas,
                        "unico": bool(idx[2]),
                        "tamaño_estimado_bytes": len(columnas) * tamaño_tabla * 8
                    })
                return indices
        except (sqlite3.Error, ValueError) as e:
            print(f"Error obteniendo índices de {tabla}: {e}")
            return []
    
    def obtener_esquema_tabla(self, tabla: str) -> List[Dict]:
        """Retorna el esquema de una tabla."""
        try:
            with closing(conectar()) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    f"PRAGMA table_info({_quoted_identifier(tabla)})"
                )
                return [
                    {
                        "nombre": col[1],
                        "tipo": col[2],
                        "not_null": col[3],
                        "default": col[4],
                        "pk": col[5]
                    }
                    for col in cursor.fetchall()
                ]
        except (sqlite3.Error, ValueError) as e:
            print(f"Error obteniendo esquema de {tabla}: {e}")
            return []
    
    def analizar_fragmentation(self, tabla: str) -> float:
        """Calcula el porcentaje de fragmentación de una tabla."""
        try:
            tabla_sql = _quoted_identifier(tabla)
            with closing(conectar()) as conn:
                cursor = conn.cursor()
                cursor.execute(f"SELECT COUNT(*) FROM {tabla_sql}")
                total_filas = cursor.fetchone()[0]
                if total_filas == 0:
                    return 0.0

                cursor.execute("PRAGMA page_size")
                page_size = cursor.fetchone()[0]
                if not page_size:
                    return 0.0

                cursor.execute(
                    "SELECT SUM(pgsize) FROM dbstat WHERE name = ?", (tabla,)
                )
                resultado = cursor.fetchone()[0]
                paginas_usadas = (resultado or 0) / page_size
                fragmentacion = (
                    1 - (total_filas / max(paginas_usadas, 1))
                ) * 100
                return max(0, min(100, fragmentacion))
        except (sqlite3.Error, ValueError, ZeroDivisionError) as e:
            logger.warning("No se pudo analizar la fragmentación de %s: %s", tabla, e)
            return 0.0
    
    def obtener_estadisticas_tabla(self, tabla: str) -> Dict:
        """Retorna estadísticas de una tabla."""
        try:
            tabla_sql = _quoted_identifier(tabla)
            with closing(conectar()) as conn:
                cursor = conn.cursor()
                cursor.execute(f"SELECT COUNT(*) FROM {tabla_sql}")
                total_filas = cursor.fetchone()[0]
                cursor.execute(
                    "SELECT SUM(pgsize) FROM dbstat WHERE name = ?", (tabla,)
                )
                tamaño_bytes = cursor.fetchone()[0] or 0

            return {
                "tabla": tabla,
                "total_filas": total_filas,
                "tamaño_bytes": tamaño_bytes,
                "tamaño_mb": tamaño_bytes / (1024 * 1024),
                "indices": len(self.obtener_indices(tabla))
            }
        except (sqlite3.Error, ValueError) as e:
            return {"tabla": tabla, "error": str(e)}
    
    def sugerir_indices(self) -> List[Dict]:
        """
        Sugiere índices basado en patrones de acceso frecuentes.
        Retorna lista de sugerencias con impacto estimado.
        """
        sugerencias = []
        
        # Patrones de acceso identificados
        patrones = [
            # Tabla, Columnas, Razón, Impacto
            ("pasadas", ["fecha"], "Acceso frecuente por fecha en control diario", 8.5),
            ("pasadas", ["objetivo_id"], "Filtrado frecuente por objetivo", 7.2),
            ("pasadas", ["fecha", "objetivo_id"], "Compound: fecha + objetivo", 9.1),
            ("pasadas", ["supervisor_id"], "Búsqueda por supervisor", 6.5),
            ("pasadas", ["turno"], "Filtrado por turno", 5.0),
            
            ("equipos", ["fecha"], "Acceso para obtener equipo del día", 8.0),
            ("equipos", ["fecha", "turno"], "Compound: búsqueda equipo diario", 9.0),
            ("equipos", ["supervisor1_id"], "Búsqueda por supervisor", 6.0),
            ("equipos", ["supervisor2_id"], "Búsqueda por supervisor", 6.0),
            
            ("auditoria", ["fecha"], "Queries de auditoría recientes", 8.5),
            ("auditoria", ["usuario_id"], "Auditoría por usuario", 7.0),
            ("auditoria", ["fecha", "usuario_id"], "Compound: auditoria filtrada", 8.8),
            ("auditoria", ["tabla"], "Búsqueda por tabla auditada", 6.5),
            
            ("objetivos", ["fecha_fin"], "Filtrado de objetivos activos", 6.0),
            ("supervisores", ["nombre"], "Búsqueda por nombre", 5.5),
        ]
        
        indices_existentes = set()
        for tabla in self.obtener_tablas():
            for idx in self.obtener_indices(tabla):
                clave = (tabla, tuple(idx["columnas"]))
                indices_existentes.add(clave)
        
        for tabla, columnas, razon, impacto in patrones:
            clave = (tabla, tuple(columnas))
            
            # No sugerir si ya existe
            if clave in indices_existentes:
                continue
            
            # Verificar que la tabla y columnas existan
            esquema = {col["nombre"] for col in self.obtener_esquema_tabla(tabla)}
            if all(col in esquema for col in columnas):
                nombre_indice = f"idx_{tabla}_{'_'.join(columnas)}"
                sugerencias.append({
                    "tabla": tabla,
                    "columnas": columnas,
                    "nombre_indice": nombre_indice,
                    "razon": razon,
                    "impacto_porcentaje": impacto,
                    "estado": "recomendado"
                })
        
        # Ordenar por impacto descendente
        return sorted(sugerencias, key=lambda x: x["impacto_porcentaje"], reverse=True)
    
    def crear_indice(self, tabla: str, columnas: List[str], nombre_indice: Optional[str] = None) -> bool:
        """Crea un índice en la BD."""
        try:
            tabla_sql = _quoted_identifier(tabla)
            columnas_sql = ", ".join(_quoted_identifier(col) for col in columnas)
            if not columnas:
                raise ValueError("El índice debe incluir al menos una columna.")
            if not nombre_indice:
                nombre_indice = f"idx_{tabla}_{'_'.join(columnas)}"
            nombre_sql = _quoted_identifier(nombre_indice)

            columnas_existentes = {
                col["nombre"] for col in self.obtener_esquema_tabla(tabla)
            }
            if not columnas_existentes or any(
                columna not in columnas_existentes for columna in columnas
            ):
                raise ValueError(f"Tabla o columnas inexistentes: {tabla}")

            with closing(conectar()) as conn:
                conn.execute("PRAGMA foreign_keys=OFF")
                conn.execute(
                    f"CREATE INDEX IF NOT EXISTS {nombre_sql} "
                    f"ON {tabla_sql} ({columnas_sql})"
                )
                conn.commit()
            return True
        except (sqlite3.Error, ValueError) as e:
            print(f"Error creando índice: {e}")
            return False
    
    def eliminar_indice(self, nombre_indice: str) -> bool:
        """Elimina un índice de la BD."""
        try:
            nombre_sql = _quoted_identifier(nombre_indice)
            with closing(conectar()) as conn:
                conn.execute(f"DROP INDEX IF EXISTS {nombre_sql}")
                conn.commit()
            return True
        except (sqlite3.Error, ValueError) as e:
            print(f"Error eliminando índice: {e}")
            return False
    
    def optimizar_bd(self) -> Dict:
        """
        Ejecuta optimizaciones en la BD.
        Retorna resumen de cambios.
        """
        try:
            with closing(conectar()) as conn:
                cursor = conn.cursor()
                cursor.execute("ANALYZE")
                cursor.execute("VACUUM")
                cursor.execute("REINDEX")
                conn.commit()
            
            return {
                "exitoso": True,
                "operaciones": ["ANALYZE", "VACUUM", "REINDEX"]
            }
        except sqlite3.Error as e:
            return {
                "exitoso": False,
                "error": str(e)
            }
    
    def generar_reporte(self) -> str:
        """Genera un reporte completo de la BD."""
        reporte = "=" * 70 + "\n"
        reporte += "REPORTE DE ANÁLISIS DE BASE DE DATOS\n"
        reporte += "=" * 70 + "\n\n"
        
        # Estadísticas generales
        reporte += "ESTADÍSTICAS GENERALES:\n"
        reporte += "-" * 70 + "\n"
        
        tablas_stats = []
        tamaño_total = 0
        filas_total = 0
        
        for tabla in self.obtener_tablas():
            stats = self.obtener_estadisticas_tabla(tabla)
            if "error" not in stats:
                tablas_stats.append(stats)
                tamaño_total += stats["tamaño_bytes"]
                filas_total += stats["total_filas"]
                reporte += f"{tabla:25} {stats['total_filas']:10,} filas  "
                reporte += f"{stats['tamaño_mb']:8.2f} MB  {stats['indices']:3} índices\n"
        
        reporte += f"\n{'TOTAL':25} {filas_total:10,} filas  "
        reporte += f"{tamaño_total / (1024*1024):8.2f} MB\n\n"
        
        # Índices actuales
        reporte += "ÍNDICES ACTUALES:\n"
        reporte += "-" * 70 + "\n"
        
        for tabla in self.obtener_tablas():
            indices = self.obtener_indices(tabla)
            if indices:
                reporte += f"\n{tabla}:\n"
                for idx in indices:
                    cols = ", ".join(idx["columnas"])
                    reporte += f"  • {idx['nombre']:40} ({cols})\n"
        
        # Sugerencias
        reporte += "\n\nÍNDICES RECOMENDADOS:\n"
        reporte += "-" * 70 + "\n"
        
        sugerencias = self.sugerir_indices()
        for i, sug in enumerate(sugerencias[:10], 1):  # Top 10
            cols = ", ".join(sug["columnas"])
            reporte += f"{i}. {sug['tabla']:20} ({cols:30}) - "
            reporte += f"Impacto: {sug['impacto_porcentaje']:.1f}%\n"
            reporte += f"   Razón: {sug['razon']}\n\n"
        
        return reporte
