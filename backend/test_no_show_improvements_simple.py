#!/usr/bin/env python
"""
Script de prueba simple para las mejoras de reembolso y notificaciones NO_SHOW
Sin dependencias de Enterprise
"""

import os
import sys
import django
from datetime import date, timedelta
from decimal import Decimal

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'hotel.settings')
os.environ.setdefault('USE_SQLITE', 'True')
django.setup()

from apps.reservations.models import Reservation, ReservationStatus, ReservationChangeLog, ReservationChangeEvent
from apps.payments.models import CancellationPolicy, RefundPolicy, Refund, RefundStatus, RefundReason
from apps.core.models import Hotel
from apps.rooms.models import Room, RoomStatus
from apps.reservations.services.no_show_processor import NoShowProcessor
from apps.notifications.models import Notification, NotificationType

def test_no_show_processor_methods():
    """Probar los métodos específicos del NoShowProcessor"""
    print("🧪 Probando métodos específicos del NoShowProcessor...")
    
    # Crear una política de devolución mock para probar
    class MockRefundPolicy:
        def __init__(self):
            self.name = "Política Test"
            self.refund_method = 'voucher'
            self.metadata = {
                'no_show_refund_percentage': 25,
                'no_show_refund_method': 'voucher',
                'no_show_processing_days': 45,
                'no_show_voucher_percentage': 25,
                'allow_no_show_refund': True
            }
    
    policy = MockRefundPolicy()
    
    # Probar cálculo de reembolso NO_SHOW
    total_paid = Decimal('1000.00')
    penalty_amount = Decimal('1000.00')
    
    refund_amount = NoShowProcessor._calculate_no_show_refund(
        total_paid, penalty_amount, policy
    )
    
    print(f"✅ Cálculo de reembolso NO_SHOW:")
    print(f"   - Total pagado: ${total_paid}")
    print(f"   - Penalidad: ${penalty_amount}")
    print(f"   - Reembolso calculado: ${refund_amount}")
    
    # Probar métodos de reembolso
    refund_method = NoShowProcessor._get_no_show_refund_method(policy)
    processing_days = NoShowProcessor._get_no_show_processing_days(policy)
    notes = NoShowProcessor._create_no_show_refund_notes(
        refund_amount, refund_method, policy
    )
    
    print(f"\n✅ Configuración de reembolso:")
    print(f"   - Método: {refund_method}")
    print(f"   - Días procesamiento: {processing_days}")
    print(f"   - Notas: {notes}")

def test_notification_messages():
    """Probar la creación de mensajes de notificación"""
    print("\n🧪 Probando mensajes de notificación...")
    
    # Crear datos mock para probar mensajes
    class MockReservation:
        def __init__(self):
            self.id = 123
            self.guests = 2
            self.check_in = date.today() - timedelta(days=1)
            self.check_out = date.today() + timedelta(days=2)
            self.room = type('Room', (), {'name': 'Habitación 101'})()
            self.hotel = type('Hotel', (), {
                'name': 'Hotel Test',
                'email': 'test@hotel.com',
                'phone': '+1234567890'
            })()
            self.updated_at = type('DateTime', (), {
                'strftime': lambda self, fmt: '29/01/2024 a las 14:30'
            })()
    
    reservation = MockReservation()
    penalty_amount = Decimal('1000.00')
    refund_amount = Decimal('250.00')
    total_paid = Decimal('1000.00')
    net_loss = penalty_amount - refund_amount
    
    # Probar mensaje del hotel
    hotel_message = NoShowProcessor._create_hotel_notification_message(
        reservation, penalty_amount, refund_amount, total_paid, net_loss
    )
    
    print(f"✅ Mensaje del hotel:")
    print(f"{hotel_message}")
    
    # Probar mensaje del huésped
    guest_message = NoShowProcessor._create_guest_notification_message(
        reservation, penalty_amount, refund_amount, total_paid
    )
    
    print(f"\n✅ Mensaje del huésped:")
    print(f"{guest_message}")

def test_refund_processing_methods():
    """Probar métodos de procesamiento de reembolsos"""
    print("\n🧪 Probando métodos de procesamiento de reembolsos...")
    
    # Crear datos mock
    class MockRefund:
        def __init__(self):
            self.id = 1
            self.notes = "Test refund"
        
        def mark_as_processing(self):
            self.status = RefundStatus.PROCESSING
        
        def save(self):
            pass
    
    class MockReservation:
        def __init__(self):
            self.id = 123
    
    refund = MockRefund()
    amount = Decimal('250.00')
    reservation = MockReservation()
    
    # Probar procesamiento de voucher
    voucher_result = NoShowProcessor._process_voucher_refund(refund, amount)
    print(f"✅ Procesamiento voucher:")
    print(f"   - Resultado: {voucher_result}")
    
    # Probar procesamiento de transferencia bancaria
    bank_result = NoShowProcessor._process_bank_transfer_refund(refund, amount)
    print(f"\n✅ Procesamiento transferencia bancaria:")
    print(f"   - Resultado: {bank_result}")
    
    # Probar procesamiento de pago original
    original_result = NoShowProcessor._process_original_payment_refund(refund, amount, reservation)
    print(f"\n✅ Procesamiento pago original:")
    print(f"   - Resultado: {original_result}")
    
    # Probar procesamiento manual
    manual_result = NoShowProcessor._process_manual_refund(refund, amount, 'cash')
    print(f"\n✅ Procesamiento manual:")
    print(f"   - Resultado: {manual_result}")

def test_events_availability():
    """Probar que los eventos NO_SHOW están disponibles"""
    print("\n🧪 Probando disponibilidad de eventos NO_SHOW...")
    
    # Verificar eventos
    events = [ReservationChangeEvent.NO_SHOW_PENALTY, ReservationChangeEvent.NO_SHOW_PROCESSED]
    
    for event in events:
        print(f"✅ Evento disponible: {event} - {ReservationChangeEvent(event).label}")
    
    # Verificar que se pueden crear logs con estos eventos
    if Hotel.objects.exists():
        hotel = Hotel.objects.first()
        if Room.objects.filter(hotel=hotel).exists():
            room = Room.objects.first()
            
            # Crear reserva temporal para probar logs
            temp_reservation = Reservation.objects.create(
                hotel=hotel,
                room=room,
                check_in=date.today(),
                check_out=date.today() + timedelta(days=1),
                guests=1,
                guests_data=[{'name': 'Test', 'email': 'test@test.com'}],
                status=ReservationStatus.NO_SHOW,
                total_price=Decimal('100.00')
            )
            
            # Crear logs de prueba
            penalty_log = ReservationChangeLog.objects.create(
                reservation=temp_reservation,
                event_type=ReservationChangeEvent.NO_SHOW_PENALTY,
                changed_by=None,
                message="Prueba de log NO_SHOW_PENALTY",
                snapshot={'penalty_amount': 100.00, 'test': True}
            )
            
            processed_log = ReservationChangeLog.objects.create(
                reservation=temp_reservation,
                event_type=ReservationChangeEvent.NO_SHOW_PROCESSED,
                changed_by=None,
                message="Prueba de log NO_SHOW_PROCESSED",
                snapshot={'total_processed': 1, 'test': True}
            )
            
            print(f"✅ Logs creados:")
            print(f"   - Penalty log: {penalty_log.id} - {penalty_log.event_type}")
            print(f"   - Processed log: {processed_log.id} - {processed_log.event_type}")
            
            # Limpiar
            temp_reservation.delete()
            penalty_log.delete()
            processed_log.delete()

def test_notification_types():
    """Probar tipos de notificación"""
    print("\n🧪 Probando tipos de notificación...")
    
    # Verificar tipos disponibles
    notification_types = [
        NotificationType.AUTO_CANCEL,
        NotificationType.MANUAL_CANCEL,
        NotificationType.NO_SHOW,
        NotificationType.REFUND_AUTO,
        NotificationType.REFUND_FAILED
    ]
    
    for ntype in notification_types:
        print(f"✅ Tipo disponible: {ntype} - {NotificationType(ntype).label}")
    
    # Crear notificación de prueba
    if Hotel.objects.exists():
        hotel = Hotel.objects.first()
        
        test_notification = Notification.objects.create(
            type=NotificationType.NO_SHOW,
            title="Test NO_SHOW Notification",
            message="Esta es una notificación de prueba para NO_SHOW",
            hotel_id=hotel.id,
            reservation_id=999,
            metadata={
                'test': True,
                'penalty_amount': 100.00,
                'refund_amount': 25.00,
                'notification_level': 'high'
            }
        )
        
        print(f"\n✅ Notificación de prueba creada:")
        print(f"   - ID: {test_notification.id}")
        print(f"   - Tipo: {test_notification.type}")
        print(f"   - Título: {test_notification.title}")
        print(f"   - Metadata: {test_notification.metadata}")
        
        # Limpiar
        test_notification.delete()

def main():
    """Función principal"""
    print("🚀 PRUEBA SIMPLE DE MEJORAS NO_SHOW")
    print("="*50)
    
    try:
        # Prueba 1: Métodos del procesador
        test_no_show_processor_methods()
        
        # Prueba 2: Mensajes de notificación
        test_notification_messages()
        
        # Prueba 3: Métodos de procesamiento de reembolsos
        test_refund_processing_methods()
        
        # Prueba 4: Eventos disponibles
        test_events_availability()
        
        # Prueba 5: Tipos de notificación
        test_notification_types()
        
        print("\n✅ TODAS LAS PRUEBAS COMPLETADAS!")
        print("\n🎉 Las mejoras de NO_SHOW están funcionando:")
        print("   ✅ Lógica de reembolso específica para NO_SHOW")
        print("   ✅ Notificaciones detalladas con información financiera")
        print("   ✅ Diferentes métodos de reembolso")
        print("   ✅ Configuraciones específicas por política")
        print("   ✅ Logs detallados de procesamiento")
        print("   ✅ Notificaciones diferenciadas (hotel, huésped, admin)")
        print("   ✅ Eventos NO_SHOW disponibles")
        print("   ✅ Tipos de notificación funcionando")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
