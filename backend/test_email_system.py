#!/usr/bin/env python3
"""
Script de prueba para el sistema de emails
"""

import os
import sys
import django
from decimal import Decimal
from datetime import date, datetime, timedelta

# Configurar Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'hotel.settings')
django.setup()

from django.core.mail import send_mail, EmailMessage
from django.conf import settings
from apps.payments.services.pdf_generator import PDFReceiptGenerator


def test_basic_email():
    """Prueba envío de email básico"""
    print("Probando envío de email básico...")
    
    try:
        # Email simple
        result = send_mail(
            subject='Prueba de Email - AlojaSys',
            message='Este es un email de prueba para verificar que el sistema de emails funciona correctamente.',
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=['test@example.com'],
            fail_silently=False
        )
        
        print(f"Email enviado: {result}")
        return True
        
    except Exception as e:
        print(f"Error enviando email básico: {e}")
        return False


def test_email_with_attachment():
    """Prueba envío de email con PDF adjunto"""
    print("Probando envío de email con PDF adjunto...")
    
    try:
        # Crear PDF de prueba
        generator = PDFReceiptGenerator()
        
        payment_data = {
            'payment_id': 'TEST-EMAIL-001',
            'reservation_code': 'RES-EMAIL-001',
            'amount': 150.50,
            'method': 'Efectivo',
            'date': datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
            'hotel_info': {
                'name': 'Hotel de Prueba Email',
                'address': 'Calle Falsa 123, Buenos Aires',
                'tax_id': '20-12345678-9'
            },
            'guest_info': {
                'name': 'Juan Pérez',
                'email': 'juan.perez@example.com'
            }
        }
        
        # Generar PDF
        pdf_path = generator.generate_payment_receipt(payment_data)
        print(f"PDF generado: {pdf_path}")
        
        # Crear email con adjunto
        email = EmailMessage(
            subject='Recibo de Pago - Prueba',
            body='Se adjunta el recibo de pago de prueba.',
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=['test@example.com'],
        )
        
        # Adjuntar PDF
        if os.path.exists(pdf_path):
            with open(pdf_path, 'rb') as pdf_file:
                email.attach(
                    filename='recibo_prueba.pdf',
                    content=pdf_file.read(),
                    mimetype='application/pdf'
                )
            print("PDF adjunto al email")
        
        # Enviar email
        email.send()
        print("Email con PDF enviado exitosamente")
        
        return True
        
    except Exception as e:
        print(f"Error enviando email con PDF: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_payment_email_service():
    """Prueba el servicio de email de pagos"""
    print("Probando servicio de email de pagos...")
    
    try:
        from apps.reservations.services.email_service import ReservationEmailService
        
        # Crear datos de prueba simulados
        class MockReservation:
            def __init__(self):
                self.id = 999
                self.hotel = MockHotel()
                self.room = MockRoom()
                self.guests_data = [
                    {
                        'name': 'Juan Pérez',
                        'email': 'juan.perez@example.com',
                        'is_primary': True
                    }
                ]
                self.check_in = date.today() + timedelta(days=7)
                self.check_out = date.today() + timedelta(days=10)
                self.total_price = Decimal('450.00')
            
            @property
            def guest_name(self):
                return self.guests_data[0]['name'] if self.guests_data else 'Huésped'
            
            @property
            def guest_email(self):
                return self.guests_data[0]['email'] if self.guests_data else None
        
        class MockHotel:
            def __init__(self):
                self.name = "Hotel de Prueba Email"
        
        class MockRoom:
            def __init__(self):
                self.name = "Habitación de Prueba"
        
        class MockPayment:
            def __init__(self):
                self.id = 888
                self.amount = Decimal('150.00')
                self.method = 'cash'
                self.date = date.today()
        
        # Crear instancias de prueba
        reservation = MockReservation()
        payment = MockPayment()
        
        print(f"Reserva: RES-{reservation.id}")
        print(f"Email del huésped: {reservation.guest_email}")
        
        # Generar PDF primero
        generator = PDFReceiptGenerator()
        payment_data = {
            'payment_id': payment.id,
            'reservation_code': f"RES-{reservation.id}",
            'amount': float(payment.amount),
            'method': payment.method,
            'date': payment.date.strftime("%d/%m/%Y %H:%M:%S"),
            'hotel_info': {
                'name': reservation.hotel.name,
                'address': 'Calle Falsa 123, Buenos Aires',
                'tax_id': '20-12345678-9'
            },
            'guest_info': {
                'name': reservation.guest_name,
                'email': reservation.guest_email
            }
        }
        
        pdf_path = generator.generate_payment_receipt(payment_data)
        print(f"PDF generado: {pdf_path}")
        
        # Probar envío de email de confirmación de pago
        success = ReservationEmailService.send_payment_confirmation(reservation, payment)
        
        if success:
            print("Email de confirmación de pago enviado exitosamente")
        else:
            print("Error enviando email de confirmación de pago")
        
        return success
        
    except Exception as e:
        print(f"Error en servicio de email de pagos: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Función principal de prueba"""
    print("Iniciando pruebas del sistema de emails...\n")
    
    # Crear directorio de media si no existe
    os.makedirs('media/receipts', exist_ok=True)
    
    print(f"Configuración de email actual:")
    print(f"- EMAIL_BACKEND: {settings.EMAIL_BACKEND}")
    print(f"- DEFAULT_FROM_EMAIL: {settings.DEFAULT_FROM_EMAIL}")
    print()
    
    # Ejecutar pruebas
    tests = [
        ("Email básico", test_basic_email),
        ("Email con PDF adjunto", test_email_with_attachment),
        ("Servicio de email de pagos", test_payment_email_service)
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
    print("RESUMEN DE PRUEBAS DE EMAIL")
    print("="*50)
    
    passed = sum(results)
    total = len(results)
    
    print(f"Pruebas exitosas: {passed}/{total}")
    print(f"Pruebas fallidas: {total - passed}/{total}")
    
    if passed == total:
        print("\n¡Todas las pruebas de email pasaron!")
        print("El sistema de emails está funcionando correctamente.")
    else:
        print(f"\n{total - passed} pruebas fallaron.")
        print("Revisar configuración de email.")
    
    return passed == total


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
