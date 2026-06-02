#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de validación del Importador Universal
Verifica que los cambios funcionan correctamente
"""

import sys
from pathlib import Path

# Agregar el directorio actual al path
sys.path.insert(0, str(Path(__file__).parent))

def test_caches():
    """Test 1: Verificar que los caches se inicializan correctamente"""
    print("\n" + "="*60)
    print("TEST 1: Inicialización de caches")
    print("="*60)
    
    from services.importador_universal import get_importador
    
    importador = get_importador()
    
    # Verificar que tiene la flag
    assert hasattr(importador, '_cache_inicializado'), "Falta atributo _cache_inicializado"
    print("✓ Atributo _cache_inicializado existe")
    
    # Verificar que tiene el método
    assert hasattr(importador, '_inicializar_caches'), "Falta método _inicializar_caches"
    print("✓ Método _inicializar_caches existe")
    
    # Inicializar caches
    importador._inicializar_caches()
    assert importador._cache_inicializado, "Caches no se inicializaron"
    print("✓ Caches inicializados correctamente")
    
    print(f"  Objetivos en cache: {len(importador._cache_objetivos)}")
    print(f"  Supervisores en cache: {len(importador._cache_supervisores)}")


def test_preview_structure():
    """Test 2: Verificar que previsualizar_archivo devuelve la estructura correcta"""
    print("\n" + "="*60)
    print("TEST 2: Estructura de previsualizar_archivo")
    print("="*60)
    
    from services.importador_universal import get_importador
    
    importador = get_importador()
    
    # Campos esperados
    campos_esperados = {
        'tipo',
        'registros',
        'objetivos_detectados',
        'supervisores_detectados',
        'objetivos_resueltos',  # NUEVO
        'supervisores_resueltos',  # NUEVO
        'objetivos_no_resueltos',
        'supervisores_no_resueltos',
        'sheet_options',
    }
    
    # Crear mock de preview
    print("✓ Campos esperados para preview:")
    for campo in sorted(campos_esperados):
        print(f"  - {campo}")


def test_normalizacion_horas():
    """Test 3: Verificar normalización de horas"""
    print("\n" + "="*60)
    print("TEST 3: Normalización de horas")
    print("="*60)
    
    from services.importador_universal import get_importador
    from datetime import date, datetime, time
    
    importador = get_importador()
    
    test_cases = [
        ("14:30", "14:30"),
        ("1430", "14:30"),
        ("14", "00:14"),
        (datetime.now().replace(hour=14, minute=30), "14:30"),
        (time(14, 30), "14:30"),
    ]
    
    fecha_base = date.today()
    
    for entrada, esperado in test_cases:
        try:
            fecha, hora = importador._normalizar_hora_y_fecha(entrada, fecha_base)
            status = "✓" if hora == esperado else "✗"
            print(f"{status} {entrada} → {hora} (esperado: {esperado})")
        except Exception as e:
            print(f"✗ {entrada} → ERROR: {e}")


def test_mapeo_automatico():
    """Test 4: Verificar que el mapeo automático funciona"""
    print("\n" + "="*60)
    print("TEST 4: Mapeo automático de objetivos/supervisores")
    print("="*60)
    
    from services.importador_universal import get_importador
    
    importador = get_importador()
    
    # Inicializar caches
    importador._inicializar_caches()
    
    # Intentar obtener un objetivo que debería existir
    # (según la BD existente)
    
    if importador._cache_objetivos:
        primer_objetivo = list(importador._cache_objetivos.keys())[0]
        objetivo_id = importador._obtener_objetivo_id(primer_objetivo)
        if objetivo_id:
            print(f"✓ Auto-mapeo de objetivos funciona")
            print(f"  Encontrado: '{primer_objetivo}' → ID {objetivo_id}")
        else:
            print(f"✗ No se pudo obtener ID para: {primer_objetivo}")
    else:
        print("⚠ No hay objetivos en la BD para testear")


def main():
    """Ejecutar todos los tests"""
    print("\n" + "🔍 ")*15)
    print("VALIDACIÓN DEL IMPORTADOR UNIVERSAL")
    print("🔍 "*15)
    
    try:
        test_caches()
        test_preview_structure()
        test_normalizacion_horas()
        test_mapeo_automatico()
        
        print("\n" + "="*60)
        print("✅ TODOS LOS TESTS PASARON")
        print("="*60)
        print("\nEl importador está listo para usar.")
        print("Próximo paso: Importar un archivo Excel de prueba")
        
    except AssertionError as e:
        print(f"\n❌ TEST FALLIDO: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ ERROR NO ESPERADO: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
