# =============================================================================
# VESP Testing - Services: Reportes
# =============================================================================

import sqlite3
import datetime
from services.reportes import generar_reporte_mensual, obtener_objetivos_del_dia


class TestGenerarReporteMensual:
    """Tests para generación de reportes mensuales."""

    def test_reporte_ignora_objetivo_sin_dias_configurados(self, db_initialized):
        """Un objetivo con dias_semana NULL no debe romper el reporte."""
        conexion = sqlite3.connect(db_initialized)
        conexion.execute("INSERT INTO objetivos (nombre, dias_semana) VALUES (?, NULL)", ("Objetivo incompleto",))
        conexion.commit()
        conexion.close()

        reporte = generar_reporte_mensual(2026, 8)

        assert reporte['objetivos'] is not None
    
    def test_reporte_vacio(self, db_initialized):
        """Debe generar reporte although esté vacío."""
        reporte = generar_reporte_mensual(2025, 1)
        
        assert reporte is not None
        assert reporte['anio'] == 2025
        assert reporte['mes'] == 1
        assert reporte['objetivos'] is not None
    
    def test_reporte_con_objetivos(self, db_initialized, test_objetivo, admin_user, test_supervisor):
        """Debe incluir objetivos en el reporte."""
        # Insertar una pasada
        conexion = sqlite3.connect(db_initialized)
        cursor = conexion.cursor()
        
        today = datetime.date.today()
        cursor.execute("""
            INSERT INTO pasadas (fecha, hora, turno, objetivo_id, supervisor_id)
            VALUES (?, ?, ?, ?, ?)
        """, (today.isoformat(), "10:00", "diurno", test_objetivo['id'], test_supervisor['id']))
        
        conexion.commit()
        conexion.close()
        
        # Generar reporte
        reporte = generar_reporte_mensual(today.year, today.month)
        
        assert len(reporte['objetivos']) > 0
    
    def test_reporte_calcula_porcentaje(self, db_initialized, test_objetivo, admin_user):
        """Debe calcular correctamente el porcentaje de cumplimiento."""
        reporte = generar_reporte_mensual(2025, 1)
        
        for objetivo in reporte['objetivos']:
            if objetivo['dias_esperados'] > 0:
                porcentaje = ((objetivo['dias_esperados'] - objetivo['dias_sin_control']) / objetivo['dias_esperados']) * 100
                assert objetivo['cumplimiento'] == round(porcentaje, 1)

    def test_reporte_objetivo_y_exportacion_comparten_conteo_mensual(
        self, db_initialized, test_objetivo, admin_user, test_supervisor, monkeypatch
    ):
        fecha_turno = "2026-10-30"
        conexion = sqlite3.connect(db_initialized)
        conexion.execute(
            """
            INSERT INTO pasadas
                (fecha, hora, turno, objetivo_id, supervisor_id, fecha_operativa)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                "2026-10-31",
                "02:00",
                "nocturno",
                test_objetivo["id"],
                test_supervisor["id"],
                fecha_turno,
            ),
        )
        conexion.commit()
        conexion.close()

        import ui.reporte_objetivo as reporte_objetivo
        from services.exportar import _obtener_datos_reporte

        monkeypatch.setattr(reporte_objetivo, "DB_PATH", db_initialized)
        reporte_mensual = generar_reporte_mensual(2026, 10)
        por_objetivo = reporte_objetivo.calcular_reporte_objetivo(
            2026, 10, test_objetivo["id"]
        )
        exportacion = _obtener_datos_reporte(2026, 10, reporte_mensual)

        objetivo_mensual = next(
            fila
            for fila in reporte_mensual["objetivos"]
            if fila["id"] == test_objetivo["id"]
        )
        assert objetivo_mensual["dias_con_pasada"] == 1
        assert por_objetivo["resumen"]["dias_con_noche"] == 1
        assert exportacion[0][1:] == (
            objetivo_mensual["dias_con_pasada"],
            objetivo_mensual["dias_sin_pasada"],
            objetivo_mensual["cumplimiento_porcentaje"],
        )


class TestObtenerObjetivoDelDia:
    """Tests para obtención de objetivos del día."""
    
    def test_obtener_objetivos_hoy(self, db_initialized, test_objetivo):
        """Debe obtener objetivos para hoy si corresponde."""
        today = datetime.date.today().isoformat()
        objetivos = obtener_objetivos_del_dia(today)
        
        # Puede haber 0 objetivos si hoy no es uno de los días configurados
        assert isinstance(objetivos, list)
    
    def test_obtener_objetivos_fecha_invalida(self, db_initialized):
        """Debe manejar fechas inválidas gracefully."""
        objetivos = obtener_objetivos_del_dia("2025-01-01")
        
        assert isinstance(objetivos, list)
    
    def test_objetivos_respetan_dias_semana(self, db_initialized, test_objetivo):
        """Debe respetar los días de cobertura configurados."""
        # Crear objetivo que solo corre de lunes a viernes
        conexion = sqlite3.connect(db_initialized)
        cursor = conexion.cursor()
        
        cursor.execute("""
            INSERT INTO objetivos (nombre, dias_semana)
            VALUES (?, ?)
        """, ("Objetivo Laborales", "1,2,3,4,5"))
        
        conexion.commit()
        conexion.close()
        
        # Verificar un fin de semana (sábado = 6, domingo = 7)
        objetivos_sabado = obtener_objetivos_del_dia("2025-01-11")  # Sábado
        
        nombres = [o[1] for o in objetivos_sabado]
        assert "Objetivo Laborales" not in nombres
