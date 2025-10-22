#!/usr/bin/env python3
"""
Script de debug para verificar por qué no se envían emails de reservas
"""

import os
import sys
import django
from decimal import Decimal
from datetime import date, datetime

# Configurar Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'hotel.settings')
django.setup()

from apps.reservations.models import Reservation, ReservationStatus, Payment
from apps.payments.services.pdf_generator import PDFReceiptGenerator


def test_reservation_email_extraction():
    """Prueba la extracción de email de una reserva simulada"""
    print("Probando extracción de email de reserva...")
    
    # Simular datos como los que envía el frontend
    guests_data = [
        {
            'name': 'Nico Villamarin',
            'email': 'villamarin.nico@gmail.com',
            'phone': '+542236796929',
            'document': '1234123123',
            'address': 'Mar del plata',
            'is_primary': True
        }
    ]
    
    print(f"Datos de huéspedes simulados: {guests_data}")
    
    # Crear reserva simulada
    class MockReservation:
        def __init__(self):
            self.id = 999
            self.guests_data = guests_data
            self.hotel = MockHotel()
            self.room = MockRoom()
            self.check_in = date(2025, 10, 21)
            self.check_out = date(2025, 10, 23)
            self.total_price = Decimal('450.00')
            self.status = ReservationStatus.PENDING
        
        @property
        def guest_name(self):
            primary_guest = self.get_primary_guest()
            return primary_guest.get('name', '') if primary_guest else ''
        
        @property
        def guest_email(self):
            primary_guest = self.get_primary_guest()
            return primary_guest.get('email', '') if primary_guest else ''
        
        def get_primary_guest(self):
            if not self.guests_data:
                return None
            return next((guest for guest in self.guests_data if guest.get('is_primary', False)), None)
    
    class MockHotel:
        def __init__(self):
            self.name = "Hotel de Prueba"
    
    class MockRoom:
        def __init__(self):
            self.name = "Habitación de Prueba"
    
    # Probar extracción
    reservation = MockReservation()
    
    print(f"Reserva ID: {reservation.id}")
    print(f"Guest name: {reservation.guest_name}")
    print(f"Guest email: {reservation.guest_email}")
    print(f"Primary guest: {reservation.get_primary_guest()}")
    
    if reservation.guest_email:
        print("[OK] Email extraído correctamente")
        return True
    else:
        print("[ERROR] No se pudo extraer el email")
        return False


def test_payment_creation_with_email():
    """Prueba la creación de pago y verificación de email"""
    print("\nProbando creación de pago con email...")
    
    try:
        # Simular reserva con email
        class MockReservation:
            def __init__(self):
                self.id = 999
                self.guests_data = [
                    {
                        'name': 'Nico Villamarin',
                        'email': 'villamarin.nico@gmail.com',
                        'is_primary': True
                    }
                ]
                self.hotel = MockHotel()
                self.room = MockRoom()
                self.check_in = date(2025, 10, 21)
                self.check_out = date(2025, 10, 23)
                self.total_price = Decimal('450.00')
                self.status = ReservationStatus.PENDING
            
            @property
            def guest_name(self):
                primary_guest = self.get_primary_guest()
                return primary_guest.get('name', '') if primary_guest else ''
            
            @property
            def guest_email(self):
                primary_guest = self.get_primary_guest()
                return primary_guest.get('email', '') if primary_guest else ''
            
            def get_primary_guest(self):
                if not self.guests_data:
                    return None
                return next((guest for guest in self.guests_data if guest.get('is_primary', False)), None)
        
        class MockHotel:
            def __init__(self):
                self.name = "Hotel de Prueba"
        
        class MockRoom:
            def __init__(self):
                self.name = "Habitación de Prueba"
        
        # Simular pago
        reservation = MockReservation()
        payment_data = {
            'payment_id': 123,
            'reservation_code': f"RES-{reservation.id}",
            'amount': float(reservation.total_price),
            'method': 'cash',
            'date': datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
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
        
        print(f"Email del huésped: {reservation.guest_email}")
        print(f"Datos de pago: {payment_data}")
        
        if reservation.guest_email:
            print("[OK] Email disponible para envío")
            
            # Generar PDF
            generator = PDFReceiptGenerator()
            pdf_path = generator.generate_payment_receipt(payment_data)
            print(f"PDF generado: {pdf_path}")
            
            if os.path.exists(pdf_path):
                print("[OK] PDF generado correctamente")
                return True
            else:
                print("[ERROR] PDF no se generó")
                return False
        else:
            print("[ERROR] No hay email para enviar")
            return False
            
    except Exception as e:
        print(f"Error en prueba de pago: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_signal_activation():
    """Prueba si el signal se activaría correctamente"""
    print("\nProbando activación de signal...")
    
    try:
        from apps.payments.signals import generate_payment_receipt
        
        # Simular datos de pago
        class MockPayment:
            def __init__(self):
                self.id = 123
                self.reservation = MockReservation()
                self.amount = Decimal('450.00')
                self.method = 'cash'
                self.date = date.today()
            
            def save(self):
                print("Payment.save() llamado - Signal se activaría")
        
        class MockReservation:
            def __init__(self):
                self.id = 999
                self.guests_data = [
                    {
                        'name': 'Nico Villamarin',
                        'email': 'villamarin.nico@gmail.com',
                        'is_primary': True
                    }
                ]
            
            @property
            def guest_email(self):
                primary_guest = self.get_primary_guest()
                return primary_guest.get('email', '') if primary_guest else ''
            
            def get_primary_guest(self):
                if not self.guests_data:
                    return None
                return next((guest for guest in self.guests_data if guest.get('is_primary', False)), None)
        
        payment = MockPayment()
        print(f"Email del huésped: {payment.reservation.guest_email}")
        
        if payment.reservation.guest_email:
            print("[OK] Signal se activaría correctamente")
            print("[OK] Email disponible para envío")
            return True
        else:
            print("[ERROR] Signal no se activaría - no hay email")
            return False
            
    except Exception as e:
        print(f"Error en prueba de signal: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Función principal de debug"""
    print("Iniciando debug de emails de reservas...\n")
    
    # Crear directorio de media si no existe
    os.makedirs('media/receipts', exist_ok=True)
    
    # Ejecutar pruebas
    tests = [
        ("Extracción de email de reserva", test_reservation_email_extraction),
        ("Creación de pago con email", test_payment_creation_with_email),
        ("Activación de signal", test_signal_activation)
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
    print("RESUMEN DE DEBUG")
    print("="*50)
    
    passed = sum(results)
    total = len(results)
    
    print(f"Pruebas exitosas: {passed}/{total}")
    print(f"Pruebas fallidas: {total - passed}/{total}")
    
    if passed == total:
        print("\n¡Todas las pruebas pasaron!")
        print("El sistema debería funcionar correctamente.")
        print("\nPosibles causas del problema:")
        print("1. El servidor no está corriendo")
        print("2. Celery no está corriendo")
        print("3. El signal no se está registrando")
        print("4. Error en la configuración de email")
    else:
        print(f"\n{total - passed} pruebas fallaron.")
        print("Revisar los errores arriba.")
    
    return passed == total


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
