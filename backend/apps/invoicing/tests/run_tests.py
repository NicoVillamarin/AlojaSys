#!/usr/bin/env python
"""
Script para ejecutar todos los tests del módulo de facturación
"""
import os
import sys
import django
from django.test.utils import get_runner
from django.conf import settings

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'hotel.settings')
django.setup()

def run_tests():
    """Ejecuta todos los tests del módulo de facturación"""
    print("🧪 Ejecutando tests del módulo de facturación electrónica")
    print("=" * 60)
    
    # Configurar test runner
    TestRunner = get_runner(settings)
    test_runner = TestRunner(verbosity=2, interactive=True)
    
    # Tests a ejecutar
    test_modules = [
        'apps.invoicing.tests.test_afip_services',
        'apps.invoicing.tests.test_integration',
        'apps.invoicing.tests.test_homologation',
    ]
    
    # Ejecutar tests
    failures = test_runner.run_tests(test_modules)
    
    # Mostrar resumen
    print("\n" + "=" * 60)
    if failures:
        print(f"❌ Tests fallaron: {failures} errores")
        return False
    else:
        print("✅ Todos los tests pasaron exitosamente")
        return True

def run_specific_test(test_module):
    """Ejecuta un test específico"""
    print(f"🧪 Ejecutando test específico: {test_module}")
    print("=" * 60)
    
    TestRunner = get_runner(settings)
    test_runner = TestRunner(verbosity=2, interactive=True)
    
    failures = test_runner.run_tests([test_module])
    
    if failures:
        print(f"❌ Test falló: {failures} errores")
        return False
    else:
        print("✅ Test pasó exitosamente")
        return True

def run_unit_tests():
    """Ejecuta solo tests unitarios"""
    print("🧪 Ejecutando tests unitarios")
    print("=" * 60)
    
    return run_specific_test('apps.invoicing.tests.test_afip_services')

def run_integration_tests():
    """Ejecuta solo tests de integración"""
    print("🧪 Ejecutando tests de integración")
    print("=" * 60)
    
    return run_specific_test('apps.invoicing.tests.test_integration')

def run_homologation_tests():
    """Ejecuta solo tests de homologación"""
    print("🧪 Ejecutando tests de homologación")
    print("=" * 60)
    
    return run_specific_test('apps.invoicing.tests.test_homologation')

def main():
    """Función principal"""
    if len(sys.argv) > 1:
        test_type = sys.argv[1].lower()
        
        if test_type == 'unit':
            success = run_unit_tests()
        elif test_type == 'integration':
            success = run_integration_tests()
        elif test_type == 'homologation':
            success = run_homologation_tests()
        elif test_type == 'all':
            success = run_tests()
        else:
            print("❌ Tipo de test no válido. Opciones: unit, integration, homologation, all")
            success = False
    else:
        success = run_tests()
    
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
