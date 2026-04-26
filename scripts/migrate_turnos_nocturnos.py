# =============================================================================
# VESP Organizations - Script de Migración de Turnos Nocturnos
# Corrige datos históricos: pasadas nocturnas madrugada → fecha del día anterior
# =============================================================================

import sqlite3
import datetime
from database.db import DB_PATH
from services.logger import registrar_accion

def migrar_turnos_nocturnos():
    """
    Migra pasadas nocturnas que ocurrieron entre 00:00-06:59 AM.
    
    Cambios:
    - Si turno='nocturno' Y hora BETWEEN 00:00:00 AND 06:59:59
    - Cambia fecha a: fecha - 1 día (día anterior)
    
    Ejemplo:
        ANTES: 22/04/2026 03:00 turno=nocturno → registrada como 22/04
        DESPUÉS: 22/04/2026 03:00 turno=nocturno → registrada como 21/04 ✓
    """
    
    print("\n" + "="*70)
    print("MIGRACIÓN DE TURNOS NOCTURNOS - CORRECCIÓN DE DATOS HISTÓRICOS")
    print("="*70)
    
    conexion = sqlite3.connect(DB_PATH)
    cursor = conexion.cursor()
    
    try:
        # Buscar pasadas nocturnas en horas de madrugada (00:00 - 06:59)
        cursor.execute("""
            SELECT id, fecha, hora, turno, objetivo_id, supervisor_id
            FROM pasadas
            WHERE turno = 'nocturno' 
            AND hora LIKE '0%' OR hora LIKE '1%' OR hora LIKE '2%' OR hora LIKE '3%' OR hora LIKE '4%' OR hora LIKE '5%' OR hora LIKE '6%'
            ORDER BY fecha DESC
        """)
        
        pasadas_a_corregir = cursor.fetchall()
        
        if not pasadas_a_corregir:
            print("\n✓ No hay pasadas nocturnas en horario de madrugada que corregir.")
            print("  Todos los datos están correctamente migrados.\n")
            conexion.close()
            return
        
        print(f"\n📋 Se encontraron {len(pasadas_a_corregir)} pasadas para corregir:\n")
        
        cambios = []
        errores = []
        
        for i, (pasada_id, fecha_str, hora, turno, objetivo_id, supervisor_id) in enumerate(pasadas_a_corregir, 1):
            try:
                # Parsear fecha y hora
                fecha_obj = datetime.datetime.strptime(fecha_str, "%Y-%m-%d").date()
                hora_obj = datetime.datetime.strptime(hora, "%H:%M:%S").time()
                
                # Validar que está entre 00:00 y 06:59
                if not (datetime.time(0, 0) <= hora_obj < datetime.time(7, 0)):
                    continue
                
                # Calcular nueva fecha (día anterior)
                fecha_nueva = fecha_obj - datetime.timedelta(days=1)
                
                # Registrar cambio
                cambios.append({
                    'id': pasada_id,
                    'fecha_anterior': fecha_str,
                    'fecha_nueva': fecha_nueva.strftime("%Y-%m-%d"),
                    'hora': hora,
                    'turno': turno
                })
                
                print(f"  [{i}] ID {pasada_id}")
                print(f"      Fecha: {fecha_str} → {fecha_nueva.strftime('%d/%m/%Y')}")
                print(f"      Hora: {hora} (turno nocturno, madrugada)")
                print()
                
            except Exception as e:
                errores.append({
                    'id': pasada_id,
                    'error': str(e)
                })
                print(f"  ❌ Error procesando ID {pasada_id}: {str(e)}\n")
        
        # Mostrar resumen
        print("\n" + "-"*70)
        print(f"RESUMEN: {len(cambios)} pasadas para migrar, {len(errores)} errores")
        print("-"*70)
        
        if not cambios:
            print("\n✓ No hay cambios a realizar. Sistema ya está migrado.\n")
            conexion.close()
            return
        
        # Pedir confirmación
        print("\n⚠️  ADVERTENCIA: Esta operación es irreversible.")
        print("   Se recomienda hacer backup antes de continuar.\n")
        
        confirmacion = input("¿Confirmar migración? (escribe 'SI' para confirmar): ").strip().upper()
        
        if confirmacion != 'SI':
            print("\n❌ Migración cancelada.\n")
            conexion.close()
            return
        
        # Ejecutar cambios
        print("\n🔄 Aplicando cambios...")
        
        for cambio in cambios:
            cursor.execute("""
                UPDATE pasadas
                SET fecha = ?
                WHERE id = ?
            """, (cambio['fecha_nueva'], cambio['id']))
        
        conexion.commit()
        
        # Registrar en auditoría
        try:
            registrar_accion(
                usuario_id=None,
                accion=f"MIGRACIÓN_TURNOS_NOCTURNOS: {len(cambios)} registros actualizados"
            )
        except:
            pass  # Si falla auditoría, continuar igual
        
        print(f"\n✅ Migración completada exitosamente!")
        print(f"   {len(cambios)} registros actualizados")
        print(f"   {len(errores)} errores\n")
        
        # Mostrar estadísticas
        print("📊 ESTADÍSTICAS DESPUÉS DE MIGRACIÓN:")
        
        cursor.execute("""
            SELECT COUNT(DISTINCT DATE(fecha)) as dias_totales,
                   COUNT(*) as total_pasadas,
                   SUM(CASE WHEN turno = 'diurno' THEN 1 ELSE 0 END) as turno_diurno,
                   SUM(CASE WHEN turno = 'nocturno' THEN 1 ELSE 0 END) as turno_nocturno
            FROM pasadas
        """)
        
        stats = cursor.fetchone()
        print(f"   Días con pasadas: {stats[0]}")
        print(f"   Total de pasadas: {stats[1]}")
        print(f"   - Turno diurno: {stats[2]}")
        print(f"   - Turno nocturno: {stats[3]}\n")
        
        print("="*70)
        print("✅ MIGRACIÓN COMPLETADA - Sistema listo para usar nueva lógica")
        print("="*70 + "\n")
        
    except Exception as e:
        print(f"\n❌ Error durante migración: {str(e)}\n")
        conexion.rollback()
    
    finally:
        conexion.close()


if __name__ == "__main__":
    migrar_turnos_nocturnos()
