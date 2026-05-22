# =============================================================================
# VESP Organizations - Script de Corrección de Horas Límite
# Detecta pasadas entre 07:00-07:59 AM de turno nocturno
# y pregunta si pertenecen al turno nocturno del día anterior
# =============================================================================

import sqlite3
import datetime
from database.db import DB_PATH
from services.logger import registrar_accion


def _parsear_hora(hora: str) -> datetime.time:
    """Acepta formatos HH:MM y HH:MM:SS."""
    for formato in ("%H:%M:%S", "%H:%M"):
        try:
            return datetime.datetime.strptime(hora, formato).time()
        except ValueError:
            continue
    raise ValueError(f"Formato de hora inválido: {hora}")


def corregir_horas_limite():
    """
    Detecta y corrige pasadas nocturnas registradas entre 07:00-07:59 AM.
    
    Lógica:
    - Busca pasadas donde turno='nocturno' Y hora BETWEEN 07:00 AND 07:59:59
    - Pregunta interactivamente si pertenecen al turno nocturno anterior
    - Si sí: cambia fecha a día anterior
    - Si no: mantiene fecha actual
    
    Caso de uso:
        Pasada: 21/04/2026 07:12 turno=nocturno
        ¿Pertenece al turno nocturno del 20/04? Sí → fecha = 21/04 → 20/04
    """
    
    print("\n" + "="*70)
    print("CORRECCIÓN DE HORAS LÍMITE - TURNO NOCTURNO (07:00-07:59 AM)")
    print("="*70)
    
    conexion = sqlite3.connect(DB_PATH)
    cursor = conexion.cursor()
    
    try:
        # Buscar pasadas nocturnas en horas límite (07:00-07:59:59)
        cursor.execute("""
            SELECT p.id, p.fecha, p.hora, p.turno, 
                   o.nombre as objetivo, s.nombre as supervisor
            FROM pasadas p
            JOIN objetivos o ON p.objetivo_id = o.id
            JOIN supervisores s ON p.supervisor_id = s.id
            WHERE p.turno = 'nocturno'
              AND p.hora >= '07:00'
              AND p.hora < '08:00'
            ORDER BY p.fecha DESC, p.hora DESC
        """)
        
        pasadas_limite = cursor.fetchall()
        
        if not pasadas_limite:
            print("\n✓ No hay pasadas nocturnas en horario límite (07:00-07:59).")
            print("  Todos los datos están correctamente asignados.\n")
            conexion.close()
            return
        
        print(f"\n📋 Se encontraron {len(pasadas_limite)} pasadas en horario límite:\n")
        
        cambios = []
        sin_cambios = []
        errores = []
        
        for i, (pasada_id, fecha_str, hora, turno, objetivo, supervisor) in enumerate(pasadas_limite, 1):
            try:
                # Parsear fecha y hora
                fecha_obj = datetime.datetime.strptime(fecha_str, "%Y-%m-%d").date()
                hora_obj = _parsear_hora(hora)
                
                # Validar que está entre 07:00 y 07:59:59
                if not (datetime.time(7, 0) <= hora_obj < datetime.time(8, 0)):
                    continue
                
                # Calcular fecha del día anterior
                fecha_anterior = fecha_obj - datetime.timedelta(days=1)
                
                # Mostrar información y preguntar
                print(f"  [{i}] ID {pasada_id}")
                print(f"      Fecha actual: {fecha_str} ({fecha_obj.strftime('%A')})")
                print(f"      Hora: {hora}")
                print(f"      Objetivo: {objetivo}")
                print(f"      Supervisor: {supervisor}")
                print(f"      → ¿Pertenece al turno nocturno del {fecha_anterior.strftime('%d/%m/%Y')} (%A)? (S/N): ", end="", flush=True)
                
                respuesta = input().strip().upper()
                
                if respuesta == 'S':
                    cambios.append({
                        'id': pasada_id,
                        'fecha_anterior': fecha_str,
                        'fecha_nueva': fecha_anterior.strftime("%Y-%m-%d"),
                        'hora': hora,
                        'objetivo': objetivo,
                        'supervisor': supervisor
                    })
                    print(f"      ✓ Será movido a {fecha_anterior.strftime('%d/%m/%Y')}\n")
                else:
                    sin_cambios.append({
                        'id': pasada_id,
                        'fecha': fecha_str,
                        'hora': hora
                    })
                    print(f"      ✓ Mantendrá la fecha {fecha_str}\n")
                    
            except Exception as e:
                errores.append({
                    'id': pasada_id,
                    'error': str(e)
                })
                print(f"  ❌ Error procesando ID {pasada_id}: {str(e)}\n")
        
        # Mostrar resumen
        print("\n" + "-"*70)
        print(f"RESUMEN: {len(cambios)} pasadas a mover, {len(sin_cambios)} a mantener, {len(errores)} errores")
        print("-"*70)
        
        if not cambios:
            print("\n✓ No hay cambios a realizar.\n")
            conexion.close()
            return
        
        # Pedir confirmación final
        print(f"\n⚠️  ADVERTENCIA: Se moverán {len(cambios)} pasadas a sus fechas operativas anteriores.")
        print("   Esta operación es irreversible.\n")
        
        confirmacion = input("¿Confirmar corrección? (escribe 'SI' para confirmar): ").strip().upper()
        
        if confirmacion != 'SI':
            print("\n❌ Corrección cancelada.\n")
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
            print(f"   ✓ Pasada {cambio['id']}: {cambio['fecha_anterior']} → {cambio['fecha_nueva']}")
        
        conexion.commit()
        
        # Registrar en auditoría
        try:
            registrar_accion(
                usuario_id=None,
                accion=f"CORRECCIÓN_HORAS_LÍMITE: {len(cambios)} registros movidos a fecha operativa anterior"
            )
        except:
            pass
        
        print(f"\n✅ Corrección completada exitosamente!")
        print(f"   {len(cambios)} pasadas movidas")
        print(f"   {len(sin_cambios)} pasadas mantenidas")
        print(f"   {len(errores)} errores\n")
        
        # Mostrar estadísticas
        print("📊 ESTADÍSTICAS DESPUÉS DE CORRECCIÓN:")
        
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
        print("✅ CORRECCIÓN COMPLETADA - Horas límite procesadas")
        print("="*70 + "\n")
        
    except Exception as e:
        print(f"\n❌ Error durante corrección: {str(e)}\n")
        conexion.rollback()
    
    finally:
        conexion.close()


if __name__ == "__main__":
    corregir_horas_limite()
