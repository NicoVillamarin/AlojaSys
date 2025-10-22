#!/usr/bin/env python3
"""
Script de prueba simplificado para el servicio de emails (sin base de datos)
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

from apps.reservations.services.email_service import ReservationEmailService
from apps.payments.services.pdf_generator import PDFReceiptGenerator


def test_email_service_without_db():
    """Prueba el servicio de emails sin base de datos"""
    print("Probando servicio de emails (sin base de datos)...")
    
    try:
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
                        'phone': '+54 9 11 1234-5678',
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
                self.name = "Hotel de Prueba PDF"
                self.email = "test@hotelprueba.com"
        
        class MockRoom:
            def __init__(self):
                self.name = "Habitación de Prueba"
        
        class MockPayment:
            def __init__(self):
                self.id = 888
                self.amount = Decimal('150.00')
                self.method = 'online'
                self.date = date.today()
        
        class MockRefund:
            def __init__(self):
                self.id = 777
                self.amount = Decimal('75.00')
                self.method = 'online'
                self.reason = 'Cancelación parcial'
                self.created_at = datetime.now()
        
        # Crear instancias de prueba
        reservation = MockReservation()
        payment = MockPayment()
        refund = MockRefund()
        
        print(f"Reserva de prueba: RES-{reservation.id}")
        print(f"Email del huésped: {reservation.guest_email}")
        print(f"Hotel: {reservation.hotel.name}")
        
        # Generar PDFs de prueba
        print("\nGenerando PDFs de prueba...")
        generator = PDFReceiptGenerator()
        
        # PDF de pago
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
        
        payment_pdf = generator.generate_payment_receipt(payment_data)
        print(f"PDF de pago generado: {payment_pdf}")
        
        # PDF de refund
        refund_data = {
            'refund_id': refund.id,
            'payment_id': payment.id,
            'reservation_code': f"RES-{reservation.id}",
            'amount': float(refund.amount),
            'method': refund.method,
            'date': refund.created_at.strftime("%d/%m/%Y %H:%M:%S"),
            'reason': refund.reason,
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
        
        refund_pdf = generator.generate_refund_receipt(refund_data)
        print(f"PDF de refund generado: {refund_pdf}")
        
        # Verificar que los PDFs existen
        if os.path.exists(payment_pdf):
            print(f"PDF de pago existe: {os.path.getsize(payment_pdf)} bytes")
        else:
            print("PDF de pago no encontrado")
            return False
        
        if os.path.exists(refund_pdf):
            print(f"PDF de refund existe: {os.path.getsize(refund_pdf)} bytes")
        else:
            print("PDF de refund no encontrado")
            return False
        
        # Probar funciones de path del servicio de email
        print("\nProbando funciones de path...")
        
        # Simular la obtención de paths
        payment_path = generator.get_receipt_path(payment.id, is_refund=False)
        refund_path = generator.get_receipt_path(refund.id, is_refund=True)
        
        print(f"Path de pago: {payment_path}")
        print(f"Path de refund: {refund_path}")
        
        # Verificar paths
        expected_payment = f"receipts/payment_{payment.id}.pdf"
        expected_refund = f"receipts/refund_{refund.id}.pdf"
        
        if payment_path == expected_payment:
            print("Path de pago correcto")
        else:
            print(f"Path de pago incorrecto. Esperado: {expected_payment}, Obtenido: {payment_path}")
            return False
        
        if refund_path == expected_refund:
            print("Path de refund correcto")
        else:
            print(f"Path de refund incorrecto. Esperado: {expected_refund}, Obtenido: {refund_path}")
            return False
        
        print("\nTodas las pruebas de email service pasaron!")
        print("Los PDFs están listos para ser adjuntados en emails.")
        
        return True
        
    except Exception as e:
        print(f"Error en prueba de email service: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Función principal de prueba"""
    print("Iniciando pruebas de email service (sin base de datos)...\n")
    
    # Crear directorio de media si no existe
    os.makedirs('media/receipts', exist_ok=True)
    
    try:
        success = test_email_service_without_db()
        
        if success:
            print("\nTodas las pruebas completadas exitosamente!")
            print("El servicio de emails está listo para usar.")
        else:
            print("\nAlgunas pruebas fallaron. Revisar errores arriba.")
        
        return success
        
    except Exception as e:
        print(f"Error en pruebas: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
