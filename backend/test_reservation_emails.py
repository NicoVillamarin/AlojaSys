#!/usr/bin/env python3
"""
Script de prueba para emails de reservas con PDFs adjuntos
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

from apps.reservations.services.email_service import ReservationEmailService
from apps.reservations.models import Reservation
from apps.payments.models import Refund
from apps.core.models import Hotel
from apps.rooms.models import Room


def create_test_reservation():
    """Crea una reserva de prueba con datos completos"""
    print("Creando reserva de prueba...")
    
    try:
        # Crear hotel de prueba
        hotel, created = Hotel.objects.get_or_create(
            name="Hotel de Prueba PDF",
            defaults={
                'address': 'Calle Falsa 123, Buenos Aires',
                'email': 'test@hotelprueba.com',
                'phone': '+54 11 1234-5678'
            }
        )
        if created:
            print(f"Hotel creado: {hotel.name}")
        else:
            print(f"Hotel encontrado: {hotel.name}")
        
        # Crear habitación de prueba
        room, created = Room.objects.get_or_create(
            name="Habitación de Prueba",
            hotel=hotel,
            defaults={
                'base_price': Decimal('150.00'),
                'capacity': 2,
                'max_capacity': 4
            }
        )
        if created:
            print(f"Habitación creada: {room.name}")
        else:
            print(f"Habitación encontrada: {room.name}")
        
        # Crear reserva de prueba
        reservation_data = {
            'hotel': hotel,
            'room': room,
            'guests': 2,
            'guests_data': [
                {
                    'name': 'Juan Pérez',
                    'email': 'juan.perez@example.com',
                    'phone': '+54 9 11 1234-5678',
                    'is_primary': True
                },
                {
                    'name': 'María González',
                    'email': 'maria.gonzalez@example.com',
                    'phone': '+54 9 11 8765-4321',
                    'is_primary': False
                }
            ],
            'check_in': date.today() + timedelta(days=7),
            'check_out': date.today() + timedelta(days=10),
            'status': 'confirmed',
            'total_price': Decimal('450.00'),
            'notes': 'Reserva de prueba para testing de PDFs'
        }
        
        reservation, created = Reservation.objects.get_or_create(
            hotel=hotel,
            room=room,
            check_in=reservation_data['check_in'],
            check_out=reservation_data['check_out'],
            defaults=reservation_data
        )
        
        if created:
            print(f"Reserva creada: RES-{reservation.id}")
        else:
            print(f"Reserva encontrada: RES-{reservation.id}")
        
        return reservation
        
    except Exception as e:
        print(f"Error creando reserva de prueba: {e}")
        return None


def create_test_payments(reservation):
    """Crea pagos de prueba para la reserva"""
    print("Creando pagos de prueba...")
    
    try:
        from apps.reservations.models import Payment
        
        # Crear pago de depósito
        deposit_payment, created = Payment.objects.get_or_create(
            reservation=reservation,
            amount=Decimal('150.00'),
            method='online',
            date=date.today(),
            defaults={
                'notes': 'Depósito inicial'
            }
        )
        
        if created:
            print(f"Pago de depósito creado: {deposit_payment.id}")
        else:
            print(f"Pago de depósito encontrado: {deposit_payment.id}")
        
        # Crear pago de saldo
        balance_payment, created = Payment.objects.get_or_create(
            reservation=reservation,
            amount=Decimal('300.00'),
            method='cash',
            date=date.today(),
            defaults={
                'notes': 'Pago del saldo restante'
            }
        )
        
        if created:
            print(f"Pago de saldo creado: {balance_payment.id}")
        else:
            print(f"Pago de saldo encontrado: {balance_payment.id}")
        
        return [deposit_payment, balance_payment]
        
    except Exception as e:
        print(f"Error creando pagos de prueba: {e}")
        return []


def create_test_refund(reservation):
    """Crea un refund de prueba para la reserva"""
    print("Creando refund de prueba...")
    
    try:
        refund, created = Refund.objects.get_or_create(
            reservation=reservation,
            amount=Decimal('75.00'),
            method='online',
            reason='Cancelación parcial',
            defaults={
                'status': 'completed',
                'notes': 'Reembolso de prueba'
            }
        )
        
        if created:
            print(f"Refund creado: {refund.id}")
        else:
            print(f"Refund encontrado: {refund.id}")
        
        return refund
        
    except Exception as e:
        print(f"Error creando refund de prueba: {e}")
        return None


def test_email_service():
    """Prueba el servicio de emails"""
    print("Probando servicio de emails...")
    
    try:
        # Crear reserva de prueba
        reservation = create_test_reservation()
        if not reservation:
            return False
        
        # Crear pagos de prueba
        payments = create_test_payments(reservation)
        if not payments:
            print("No se pudieron crear pagos de prueba")
            return False
        
        # Crear refund de prueba
        refund = create_test_refund(reservation)
        if not refund:
            print("No se pudo crear refund de prueba")
            return False
        
        # Generar PDFs para los pagos y refunds
        print("Generando PDFs...")
        from apps.payments.tasks import generate_payment_receipt_pdf
        
        for payment in payments:
            try:
                generate_payment_receipt_pdf.delay(payment.id, 'payment')
                print(f"PDF generado para pago {payment.id}")
            except Exception as e:
                print(f"Error generando PDF para pago {payment.id}: {e}")
        
        try:
            generate_payment_receipt_pdf.delay(refund.id, 'refund')
            print(f"PDF generado para refund {refund.id}")
        except Exception as e:
            print(f"Error generando PDF para refund {refund.id}: {e}")
        
        # Esperar un poco para que se generen los PDFs
        import time
        print("Esperando generación de PDFs...")
        time.sleep(3)
        
        # Probar envío de email de confirmación de reserva
        print("\nEnviando email de confirmación de reserva...")
        success = ReservationEmailService.send_reservation_confirmation(reservation)
        if success:
            print("Email de confirmación enviado exitosamente")
        else:
            print("Error enviando email de confirmación")
        
        # Probar envío de email de confirmación de pago
        print("\nEnviando email de confirmación de pago...")
        success = ReservationEmailService.send_payment_confirmation(reservation, payments[0])
        if success:
            print("Email de pago enviado exitosamente")
        else:
            print("Error enviando email de pago")
        
        # Probar envío de email de confirmación de refund
        print("\nEnviando email de confirmación de refund...")
        success = ReservationEmailService.send_refund_confirmation(reservation, refund)
        if success:
            print("Email de refund enviado exitosamente")
        else:
            print("Error enviando email de refund")
        
        return True
        
    except Exception as e:
        print(f"Error en prueba de emails: {e}")
        return False


def main():
    """Función principal de prueba"""
    print("Iniciando pruebas de emails de reservas con PDFs...\n")
    
    # Crear directorio de media si no existe
    os.makedirs('media/receipts', exist_ok=True)
    
    try:
        success = test_email_service()
        
        if success:
            print("\nTodas las pruebas de email completadas!")
            print("Revisa tu bandeja de entrada en juan.perez@example.com")
        else:
            print("\nAlgunas pruebas fallaron. Revisar errores arriba.")
        
        return success
        
    except Exception as e:
        print(f"Error en pruebas: {e}")
        return False


if __name__ == "__main__":
    from datetime import timedelta
    success = main()
    sys.exit(0 if success else 1)
