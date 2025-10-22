#!/usr/bin/env python3
"""
Script para probar la conexión de Celery
"""

import os
import sys
import django

# Configurar Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'hotel.settings')
django.setup()

from celery import current_app
from apps.payments.tasks import generate_payment_receipt_pdf, send_payment_receipt_email


def test_celery_connection():
    """Prueba la conexión de Celery"""
    print("Probando conexión de Celery...")
    
    try:
        # Verificar configuración
        print(f"BROKER_URL: {current_app.conf.broker_url}")
        print(f"RESULT_BACKEND: {current_app.conf.result_backend}")
        
        # Verificar workers activos
        inspect = current_app.control.inspect()
        active_workers = inspect.active()
        
        if active_workers:
            print(f"[OK] Workers activos: {list(active_workers.keys())}")
            return True
        else:
            print("[WARNING] No hay workers activos")
            return False
            
    except Exception as e:
        print(f"[ERROR] Error conectando a Celery: {e}")
        return False


def test_celery_task():
    """Prueba una tarea de Celery"""
    print("\nProbando tarea de Celery...")
    
    try:
        # Probar tarea síncrona (sin .delay())
        result = generate_payment_receipt_pdf(999, 'payment')
        print(f"[OK] Tarea ejecutada: {result}")
        return True
        
    except Exception as e:
        print(f"[ERROR] Error ejecutando tarea: {e}")
        return False


def test_celery_async_task():
    """Prueba una tarea asíncrona de Celery"""
    print("\nProbando tarea asíncrona de Celery...")
    
    try:
        # Probar tarea asíncrona (con .delay())
        result = generate_payment_receipt_pdf.delay(999, 'payment')
        print(f"[OK] Tarea enviada: {result.id}")
        print(f"Estado: {result.state}")
        return True
        
    except Exception as e:
        print(f"[ERROR] Error enviando tarea asíncrona: {e}")
        return False


def main():
    """Función principal"""
    print("Iniciando pruebas de Celery...\n")
    
    # Ejecutar pruebas
    tests = [
        ("Conexión de Celery", test_celery_connection),
        ("Tarea síncrona", test_celery_task),
        ("Tarea asíncrona", test_celery_async_task)
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"=== {test_name} ===")
        try:
            result = test_func()
            results.append(result)
            if result:
                print(f"[OK] {test_name}: EXITOSO")
            else:
                print(f"[ERROR] {test_name}: FALLÓ")
        except Exception as e:
            print(f"[ERROR] {test_name}: ERROR - {e}")
            results.append(False)
        print()
    
    # Resumen
    print("="*50)
    print("RESUMEN DE PRUEBAS DE CELERY")
    print("="*50)
    
    passed = sum(results)
    total = len(results)
    
    print(f"Pruebas exitosas: {passed}/{total}")
    print(f"Pruebas fallidas: {total - passed}/{total}")
    
    if passed == total:
        print("\n¡Todas las pruebas pasaron!")
        print("Celery está funcionando correctamente.")
    else:
        print(f"\n{total - passed} pruebas fallaron.")
        print("\nPara solucionar:")
        print("1. Iniciar Celery: celery -A hotel worker --loglevel=info")
        print("2. Verificar que Redis esté corriendo")
        print("3. Verificar configuración en settings.py")
    
    return passed == total


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
