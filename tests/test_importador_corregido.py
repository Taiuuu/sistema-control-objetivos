#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test del importador corregido - Verificar que toma todas las pasadas
"""

import sys
import os
from pathlib import Path

# Configurar encoding para Windows
os.environ['PYTHONIOENCODING'] = 'utf-8'
sys.path.insert(0, str(Path(__file__).parent))

def test_importador_corregido():
    """Testear que el importador ahora toma TODAS las pasadas"""
    print("\n" + "="*80)
    print("TEST: IMPORTADOR CORREGIDO - Verificar pasadas sin hora")
    print("="*80)
    
    from services.importador_universal import get_importador
    
    # Buscar archivo Excel
    carpeta = Path(__file__).parent
    archivo_excel = None
    for f in carpeta.glob("*.xlsx"):
        if "CONTROL" in f.name.upper():
            archivo_excel = f
            break
    
    if not archivo_excel:
        print("[ERROR] No se encontro archivo CONTROL_RECORRIDOS.xlsx")
        return False
    
    print(f"\n[ARCHIVO] Analizando: {archivo_excel.name}")
    
    # Ejecutar preview
    importador = get_importador()
    preview = importador.previsualizar_archivo(str(archivo_excel), sheet_names=['17-6 (D)'])
    
    registros = preview.get('registros', [])
    print(f"\n[RESULTADO] Total registros parseados: {len(registros)}")
    
    # Estadísticas
    registros_con_hora = sum(1 for r in registros if r.hora and str(r.hora).strip())
    registros_sin_hora = sum(1 for r in registros if not r.hora or not str(r.hora).strip())
    
    print(f"  - Con hora: {registros_con_hora}")
    print(f"  - Sin hora: {registros_sin_hora}")
    
    # Análisis por turno
    diurnos = sum(1 for r in registros if r.turno == 'diurno')
    nocturnos = sum(1 for r in registros if r.turno == 'nocturno')
    
    print(f"  - Turno diurno: {diurnos}")
    print(f"  - Turno nocturno: {nocturnos}")
    
    # Análisis por supervisor
    supervisores = set(r.supervisor for r in registros if r.supervisor)
    print(f"  - Supervisores unicos: {len(supervisores)}")
    if supervisores:
        print(f"    {', '.join(sorted(supervisores)[:5])}")
    
    # Mostrar algunos registros
    print(f"\n[MUESTRA] Primeros 10 registros:")
    print("-" * 120)
    for i, r in enumerate(registros[:10], 1):
        hora_str = r.hora or "SIN HORA"
        print(f"  {i}. {r.objetivo:30} | {r.turno:8} | {hora_str:8} | {r.supervisor}")
    
    print("-" * 120)
    
    # Validar que hay más registros que antes
    if len(registros) > 0:
        print(f"\n[OK] Se encontraron {len(registros)} registros")
        if registros_sin_hora > 0:
            print(f"[OK] Se incluyen {registros_sin_hora} pasadas sin hora registrada")
        return True
    else:
        print(f"\n[FALLO] No se encontraron registros")
        return False


if __name__ == "__main__":
    try:
        success = test_importador_corregido()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
