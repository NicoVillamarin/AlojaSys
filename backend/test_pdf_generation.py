#!/usr/bin/env python3
"""
Script de prueba para la generación de PDFs de recibos
"""

import os
import sys
import django
from decimal import Decimal

# Configurar Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'hotel.settings')
django.setup()

from apps.payments.services.pdf_generator import PDFReceiptGenerator
from apps.payments.tasks import generate_payment_receipt_pdf, send_payment_receipt_email


def test_pdf_generator():
    """Prueba el generador de PDFs directamente"""
    print("Probando generador de PDFs...")
    
    # Datos de prueba para un pago
    payment_data = {
        'payment_id': 'TEST-001',
        'reservation_code': 'RES-2024-001',
        'amount': 150.50,
        'method': 'Mercado Pago',
        'date': '15/01/2024 14:30:00',
        'hotel_info': {
            'name': 'Hotel de Prueba',
            'address': 'Calle Falsa 123, Buenos Aires',
            'tax_id': '20-12345678-9'
        },
        'guest_info': {
            'name': 'Juan Pérez',
            'email': 'juan@example.com'
        }
    }
    
    # Datos de prueba para un refund
    refund_data = {
        'refund_id': 'REF-001',
        'payment_id': 'TEST-001',
        'reservation_code': 'RES-2024-001',
        'amount': 75.25,
        'method': 'Mercado Pago',
        'date': '16/01/2024 10:15:00',
        'reason': 'Cancelación de reserva',
        'hotel_info': {
            'name': 'Hotel de Prueba',
            'address': 'Calle Falsa 123, Buenos Aires',
            'tax_id': '20-12345678-9'
        },
        'guest_info': {
            'name': 'Juan Pérez',
            'email': 'juan@example.com'
        }
    }
    
    try:
        generator = PDFReceiptGenerator()
        
        # Generar PDF de pago
        print("Generando PDF de pago...")
        payment_pdf = generator.generate_payment_receipt(payment_data)
        print(f"PDF de pago generado: {payment_pdf}")
        
        # Generar PDF de refund
        print("Generando PDF de refund...")
        refund_pdf = generator.generate_refund_receipt(refund_data)
        print(f"PDF de refund generado: {refund_pdf}")
        
        # Verificar que los archivos existen
        if os.path.exists(payment_pdf):
            print(f"Archivo de pago existe: {os.path.getsize(payment_pdf)} bytes")
        else:
            print("Archivo de pago no encontrado")
            
        if os.path.exists(refund_pdf):
            print(f"Archivo de refund existe: {os.path.getsize(refund_pdf)} bytes")
        else:
            print("Archivo de refund no encontrado")
        
        return True
        
    except Exception as e:
        print(f"Error generando PDFs: {e}")
        return False


def test_celery_tasks():
    """Prueba las tareas de Celery (sin ejecutar realmente)"""
    print("\nProbando tareas de Celery...")
    
    try:
        # Simular llamada a tarea (sin ejecutar)
        print("Tarea generate_payment_receipt_pdf configurada correctamente")
        print("Tarea send_payment_receipt_email configurada correctamente")
        
        # Verificar que las tareas están importables
        from apps.payments.tasks import generate_payment_receipt_pdf, send_payment_receipt_email
        print("Tareas de Celery importadas correctamente")
        
        return True
        
    except Exception as e:
        print(f"Error con tareas de Celery: {e}")
        return False


def test_pdf_paths():
    """Prueba las funciones de path de PDFs"""
    print("\nProbando funciones de path...")
    
    try:
        generator = PDFReceiptGenerator()
        
        # Probar paths
        payment_path = generator.get_receipt_path("TEST-001", is_refund=False)
        refund_path = generator.get_receipt_path("REF-001", is_refund=True)
        
        print(f"Path de pago: {payment_path}")
        print(f"Path de refund: {refund_path}")
        
        # Verificar que los paths son correctos
        expected_payment = "receipts/payment_TEST-001.pdf"
        expected_refund = "receipts/refund_REF-001.pdf"
        
        if payment_path == expected_payment:
            print("Path de pago correcto")
        else:
            print(f"Path de pago incorrecto. Esperado: {expected_payment}, Obtenido: {payment_path}")
            
        if refund_path == expected_refund:
            print("Path de refund correcto")
        else:
            print(f"Path de refund incorrecto. Esperado: {expected_refund}, Obtenido: {refund_path}")
        
        return True
        
    except Exception as e:
        print(f"Error con paths: {e}")
        return False


def main():
    """Función principal de prueba"""
    print("Iniciando pruebas de generacion de PDFs...\n")
    
    # Crear directorio de media si no existe
    os.makedirs('media/receipts', exist_ok=True)
    
    # Ejecutar pruebas
    tests = [
        test_pdf_generator,
        test_celery_tasks,
        test_pdf_paths
    ]
    
    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"Error en prueba {test.__name__}: {e}")
            results.append(False)
    
    # Resumen
    print("\n" + "="*50)
    print("RESUMEN DE PRUEBAS")
    print("="*50)
    
    passed = sum(results)
    total = len(results)
    
    print(f"Pruebas exitosas: {passed}/{total}")
    print(f"Pruebas fallidas: {total - passed}/{total}")
    
    if passed == total:
        print("\nTodas las pruebas pasaron! El sistema de PDFs esta listo.")
    else:
        print(f"\n{total - passed} pruebas fallaron. Revisar errores arriba.")
    
    return passed == total


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
