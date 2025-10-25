#!/usr/bin/env python
"""
Test runner personalizado para el módulo de facturación
"""
import os
import sys
import django
from django.test.utils import get_runner
from django.conf import settings

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'hotel.settings')
django.setup()

def run_comprehensive_tests():
    """Ejecuta tests comprehensivos del módulo de facturación"""
    print("🧪 Ejecutando tests comprehensivos del módulo de facturación")
    print("=" * 70)
    
    # Configurar test runner
    TestRunner = get_runner(settings)
    test_runner = TestRunner(verbosity=2, interactive=True)
    
    # Tests a ejecutar en orden
    test_modules = [
        'apps.invoicing.tests.test_afip_services',  # Tests unitarios
        'apps.invoicing.tests.test_integration',    # Tests de integración
        'apps.invoicing.tests.test_homologation',   # Tests de homologación
    ]
    
    total_failures = 0
    results = {}
    
    for module in test_modules:
        print(f"\n🔍 Ejecutando: {module}")
        print("-" * 50)
        
        try:
            failures = test_runner.run_tests([module])
            results[module] = {
                'failures': failures,
                'success': failures == 0
            }
            total_failures += failures
        except Exception as e:
            print(f"❌ Error ejecutando {module}: {e}")
            results[module] = {
                'failures': 1,
                'success': False,
                'error': str(e)
            }
            total_failures += 1
    
    # Mostrar resumen
    print("\n" + "=" * 70)
    print("📊 RESUMEN DE TESTS")
    print("=" * 70)
    
    for module, result in results.items():
        status = "✅ PASS" if result['success'] else "❌ FAIL"
        print(f"{status} {module}")
        if 'error' in result:
            print(f"   Error: {result['error']}")
    
    print(f"\nTotal de fallos: {total_failures}")
    
    if total_failures == 0:
        print("🎉 ¡Todos los tests pasaron exitosamente!")
        return True
    else:
        print("💥 Algunos tests fallaron")
        return False

def run_quick_tests():
    """Ejecuta tests rápidos (solo unitarios)"""
    print("⚡ Ejecutando tests rápidos (unitarios)")
    print("=" * 50)
    
    TestRunner = get_runner(settings)
    test_runner = TestRunner(verbosity=1, interactive=True)
    
    failures = test_runner.run_tests(['apps.invoicing.tests.test_afip_services'])
    
    if failures == 0:
        print("✅ Tests unitarios pasaron")
        return True
    else:
        print(f"❌ Tests unitarios fallaron: {failures} errores")
        return False

def run_integration_tests_only():
    """Ejecuta solo tests de integración"""
    print("🔗 Ejecutando tests de integración")
    print("=" * 50)
    
    TestRunner = get_runner(settings)
    test_runner = TestRunner(verbosity=2, interactive=True)
    
    failures = test_runner.run_tests(['apps.invoicing.tests.test_integration'])
    
    if failures == 0:
        print("✅ Tests de integración pasaron")
        return True
    else:
        print(f"❌ Tests de integración fallaron: {failures} errores")
        return False

def run_homologation_tests_only():
    """Ejecuta solo tests de homologación"""
    print("🏛️ Ejecutando tests de homologación AFIP")
    print("=" * 50)
    
    TestRunner = get_runner(settings)
    test_runner = TestRunner(verbosity=2, interactive=True)
    
    failures = test_runner.run_tests(['apps.invoicing.tests.test_homologation'])
    
    if failures == 0:
        print("✅ Tests de homologación pasaron")
        return True
    else:
        print(f"❌ Tests de homologación fallaron: {failures} errores")
        return False

def run_specific_test_class(test_module, test_class):
    """Ejecuta una clase de test específica"""
    print(f"🎯 Ejecutando clase específica: {test_class}")
    print("=" * 50)
    
    TestRunner = get_runner(settings)
    test_runner = TestRunner(verbosity=2, interactive=True)
    
    test_path = f"{test_module}.{test_class}"
    failures = test_runner.run_tests([test_path])
    
    if failures == 0:
        print(f"✅ {test_class} pasó")
        return True
    else:
        print(f"❌ {test_class} falló: {failures} errores")
        return False

def main():
    """Función principal"""
    if len(sys.argv) < 2:
        print("Uso: python test_runner.py [comprehensive|quick|integration|homologation|specific]")
        print("\nOpciones:")
        print("  comprehensive  - Ejecuta todos los tests")
        print("  quick         - Ejecuta solo tests unitarios")
        print("  integration   - Ejecuta solo tests de integración")
        print("  homologation  - Ejecuta solo tests de homologación")
        print("  specific      - Ejecuta clase específica (requiere test_module.test_class)")
        sys.exit(1)
    
    command = sys.argv[1].lower()
    
    if command == 'comprehensive':
        success = run_comprehensive_tests()
    elif command == 'quick':
        success = run_quick_tests()
    elif command == 'integration':
        success = run_integration_tests_only()
    elif command == 'homologation':
        success = run_homologation_tests_only()
    elif command == 'specific':
        if len(sys.argv) < 3:
            print("❌ Error: Se requiere test_module.test_class para comando 'specific'")
            sys.exit(1)
        test_path = sys.argv[2]
        if '.' not in test_path:
            print("❌ Error: Formato debe ser test_module.test_class")
            sys.exit(1)
        test_module, test_class = test_path.split('.', 1)
        success = run_specific_test_class(test_module, test_class)
    else:
        print(f"❌ Comando no reconocido: {command}")
        sys.exit(1)
    
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
