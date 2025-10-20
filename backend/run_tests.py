#!/usr/bin/env python
"""
Script para ejecutar tests de integración de cancelación y refund
"""
import os
import sys
import django
from django.conf import settings
from django.test.utils import get_runner

def setup_django():
    """Configura Django para ejecutar tests"""
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'hotel.settings')
    django.setup()

def run_tests():
    """Ejecuta los tests de integración"""
    setup_django()
    
    TestRunner = get_runner(settings)
    test_runner = TestRunner()
    
    # Ejecutar tests específicos de cancelación y refund
    test_labels = [
        'tests.test_cancel_refund_integration',
        'tests.factories',
    ]
    
    failures = test_runner.run_tests(test_labels)
    
    if failures:
        print(f"\n❌ {failures} test(s) fallaron")
        sys.exit(1)
    else:
        print("\n✅ Todos los tests pasaron exitosamente")
        sys.exit(0)

if __name__ == '__main__':
    run_tests()

