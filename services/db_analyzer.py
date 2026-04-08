# =============================================================================
# VESP Organizations - Analizador de Indexación y Optimización de BD
# =============================================================================

import sqlite3
from typing import List, Dict, Optional
from database.db import DB_PATH, conectar


class AnalisisBD:
    """Analiza la estructura y performance de la base de datos."""
    
    def __init__(self):
        self.db_path = DB_PATH
    
    def obtener_tablas(self) -> List[str]:
        """Retorna todas las tablas en la BD."""
        try:
            conn = conectar()
            cursor = conn.cursor()
            cursor.execute(
                "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
            )
            tablas = [row[0] for row in cursor.fetchall()]
            conn.close()
            return tablas
        except Exception as e:
            print(f"Error obteniendo tablas: {e}")
            return []
    
    def obtener_indices(self, tabla: str) -> List[Dict]:
        """Retorna los índices de una tabla."""
        try:
            conn = conectar()
            cursor = conn.cursor()
            cursor.execute(f"PRAGMA index_list({tabla})")
            indices_raw = cursor.fetchall()
            
            indices = []
            for idx in indices_raw:
                idx_name = idx[1]
                is_unique = idx[2]
                
                # Obtener columnas del índice
                cursor.execute(f"PRAGMA index_info({idx_name})")
                columnas = [row[2] for row in cursor.fetchall()]
                
                # Contar tamaño estimado
                cursor.execute(f"SELECT COUNT(*) FROM {tabla}")
                tamaño_tabla = cursor.fetchone()[0]
                
                indices.append({
                    "nombre": idx_name,
                    "columnas": columnas,
                    "unico": bool(is_unique),
                    "tamaño_estimado_bytes": len(columnas) * tamaño_tabla * 8
                })
            
            conn.close()
            return indices
        except Exception as e:
            print(f"Error obteniendo índices de {tabla}: {e}")
            return []
    
    def obtener_esquema_tabla(self, tabla: str) -> List[Dict]:
        """Retorna el esquema de una tabla."""
        try:
            conn = conectar()
            cursor = conn.cursor()
            cursor.execute(f"PRAGMA table_info({tabla})")
            columnas_raw = cursor.fetchall()
            
            columnas = []
            for col in columnas_raw:
                columnas.append({
                    "nombre": col[1],
                    "tipo": col[2],
                    "not_null": col[3],
                    "default": col[4],
                    "pk": col[5]
                })
            
            conn.close()
            return columnas
        except Exception as e:
            print(f"Error obteniendo esquema de {tabla}: {e}")
            return []
    
    def analizar_fragmentation(self, tabla: str) -> float:
        """Calcula el porcentaje de fragmentación de una tabla."""
        try:
            conn = conectar()
            cursor = conn.cursor()
            
            # Total de filas
            cursor.execute(f"SELECT COUNT(*) FROM {tabla}")
            total_filas = cursor.fetchone()[0]
            
            if total_filas == 0:
                return 0.0
            
            # Obtener tamaño de página
            cursor.execute("PRAGMA page_size")
            page_size = cursor.fetchone()[0]
            
            # Contar páginas usadas
            cursor.execute(f"SELECT SUM(pgsize) FROM dbstat WHERE name='{tabla}'")
            resultado = cursor.fetchone()[0]
            paginas_usadas = (resultado or 0) / page_size
            
            # Fragmentación teórica (simplificada)
            fragmentacion = (1 - (total_filas / max(paginas_usadas, 1))) * 100
            
            conn.close()
            return max(0, min(100, fragmentacion))
        except:
            return 0.0
    
    def obtener_estadisticas_tabla(self, tabla: str) -> Dict:
        """Retorna estadísticas de una tabla."""
        try:
            conn = conectar()
            cursor = conn.cursor()
            
            cursor.execute(f"SELECT COUNT(*) FROM {tabla}")
            total_filas = cursor.fetchone()[0]
            
            # Tamaño estimado
            cursor.execute(f"SELECT SUM(pgsize) FROM dbstat WHERE name='{tabla}'")
            tamaño_bytes = cursor.fetchone()[0] or 0
            
            conn.close()
            
            return {
                "tabla": tabla,
                "total_filas": total_filas,
                "tamaño_bytes": tamaño_bytes,
                "tamaño_mb": tamaño_bytes / (1024 * 1024),
                "indices": len(self.obtener_indices(tabla))
            }
        except Exception as e:
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
            try:
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
            except:
                continue
        
        # Ordenar por impacto descendente
        return sorted(sugerencias, key=lambda x: x["impacto_porcentaje"], reverse=True)
    
    def crear_indice(self, tabla: str, columnas: List[str], nombre_indice: Optional[str] = None) -> bool:
        """Crea un índice en la BD."""
        if not nombre_indice:
            nombre_indice = f"idx_{tabla}_{'_'.join(columnas)}"
        
        columnas_str = ", ".join(columnas)
        sql = f"CREATE INDEX IF NOT EXISTS {nombre_indice} ON {tabla} ({columnas_str})"
        
        try:
            conn = conectar()
            conn.execute("PRAGMA foreign_keys=OFF")
            cursor = conn.cursor()
            cursor.execute(sql)
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"Error creando índice: {e}")
            return False
    
    def eliminar_indice(self, nombre_indice: str) -> bool:
        """Elimina un índice de la BD."""
        try:
            conn = conectar()
            cursor = conn.cursor()
            cursor.execute(f"DROP INDEX IF EXISTS {nombre_indice}")
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"Error eliminando índice: {e}")
            return False
    
    def optimizar_bd(self) -> Dict:
        """
        Ejecuta optimizaciones en la BD.
        Retorna resumen de cambios.
        """
        try:
            conn = conectar()
            cursor = conn.cursor()
            
            # ANALYZE: actualiza estadísticas
            cursor.execute("ANALYZE")
            
            # VACUUM: compacta BD
            cursor.execute("VACUUM")
            
            # REINDEX: reconstruye índices
            cursor.execute("REINDEX")
            
            conn.commit()
            conn.close()
            
            return {
                "exitoso": True,
                "operaciones": ["ANALYZE", "VACUUM", "REINDEX"]
            }
        except Exception as e:
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
