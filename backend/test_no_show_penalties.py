#!/usr/bin/env python
"""
Script de prueba para la funcionalidad de penalidades automáticas NO_SHOW
Ejecuta: python test_no_show_penalties.py
"""

import os
import sys
import django
from datetime import date, timedelta
from decimal import Decimal

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'hotel.settings')
django.setup()

from apps.reservations.models import Reservation, ReservationStatus, ReservationChangeLog, ReservationChangeEvent
from apps.payments.models import PaymentPolicy, PaymentMethod, CancellationPolicy, RefundPolicy
from apps.core.models import Hotel
from apps.rooms.models import Room, RoomStatus
from apps.reservations.tasks import auto_mark_no_show_daily
from apps.reservations.services.no_show_processor import NoShowProcessor
from django.contrib.auth import get_user_model

User = get_user_model()

def create_test_data():
    """Crear datos de prueba para la funcionalidad NO_SHOW con penalidades"""
    print("🔧 Creando datos de prueba para NO_SHOW con penalidades...")
    
    # Crear hotel de prueba
    hotel, created = Hotel.objects.get_or_create(
        name="Hotel de Prueba NO_SHOW",
        defaults={
            'email': 'test@hotel.com',
            'phone': '+1234567890',
            'address': 'Calle de Prueba 123',
            'auto_no_show_enabled': True  # Habilitar auto no-show
        }
    )
    print(f"✅ Hotel: {hotel.name} (ID: {hotel.id})")
    
    # Crear habitación de prueba
    room, created = Room.objects.get_or_create(
        name="Habitación 201",
        hotel=hotel,
        defaults={
            'floor': 2,
            'room_type': 'double',
            'number': 201,
            'base_price': Decimal('150.00'),
            'capacity': 2,
            'max_capacity': 2,
            'status': RoomStatus.AVAILABLE
        }
    )
    print(f"✅ Habitación: {room.name} (ID: {room.id})")
    
    # Crear política de cancelación con penalidades
    cancellation_policy, created = CancellationPolicy.objects.get_or_create(
        hotel=hotel,
        name="Política NO_SHOW Test",
        defaults={
            'free_cancellation_time': 24,
            'free_cancellation_unit': 'hours',
            'partial_refund_time': 72,
            'partial_refund_unit': 'hours',
            'no_refund_time': 168,
            'no_refund_unit': 'hours',
            'cancellation_fee_type': 'percentage',
            'cancellation_fee_value': Decimal('100.00'),  # 100% penalidad para NO_SHOW
            'is_default': True,
            'is_active': True
        }
    )
    print(f"✅ Política de cancelación: {cancellation_policy.name} (ID: {cancellation_policy.id})")
    
    # Crear política de devolución
    refund_policy, created = RefundPolicy.objects.get_or_create(
        hotel=hotel,
        name="Política Devolución NO_SHOW",
        defaults={
            'full_refund_time': 24,
            'full_refund_unit': 'hours',
            'partial_refund_time': 72,
            'partial_refund_unit': 'hours',
            'no_refund_time': 168,
            'no_refund_unit': 'hours',
            'refund_method': 'voucher',
            'is_default': True,
            'is_active': True
        }
    )
    print(f"✅ Política de devolución: {refund_policy.name} (ID: {refund_policy.id})")
    
    return hotel, room, cancellation_policy, refund_policy

def create_test_reservations(hotel, room, cancellation_policy):
    """Crear reservas de prueba para NO_SHOW"""
    print("🔧 Creando reservas de prueba...")
    
    # Reserva 1: NO_SHOW con pago completo
    reservation1, created = Reservation.objects.get_or_create(
        hotel=hotel,
        room=room,
        check_in=date.today() - timedelta(days=1),  # Ayer (debería ser NO_SHOW)
        check_out=date.today() + timedelta(days=2),
        defaults={
            'guests': 2,
            'guests_data': [{'name': 'Juan Pérez', 'email': 'juan@test.com'}],
            'status': ReservationStatus.CONFIRMED,
            'total_price': Decimal('300.00'),
            'applied_cancellation_policy': cancellation_policy,
            'notes': 'Reserva de prueba NO_SHOW con pago completo'
        }
    )
    
    # Simular pago completo
    from apps.reservations.models import Payment
    Payment.objects.create(
        reservation=reservation1,
        date=date.today() - timedelta(days=2),
        method='credit_card',
        amount=Decimal('300.00'),
        notes='Pago completo de prueba'
    )
    
    print(f"✅ Reserva 1: {reservation1.id} - ${reservation1.total_price} (CONFIRMED, check-in ayer)")
    
    # Reserva 2: NO_SHOW con pago parcial
    reservation2, created = Reservation.objects.get_or_create(
        hotel=hotel,
        room=room,
        check_in=date.today() - timedelta(days=2),  # Anteayer
        check_out=date.today(),
        defaults={
            'guests': 1,
            'guests_data': [{'name': 'María García', 'email': 'maria@test.com'}],
            'status': ReservationStatus.CONFIRMED,
            'total_price': Decimal('200.00'),
            'applied_cancellation_policy': cancellation_policy,
            'notes': 'Reserva de prueba NO_SHOW con pago parcial'
        }
    )
    
    # Simular pago parcial
    Payment.objects.create(
        reservation=reservation2,
        date=date.today() - timedelta(days=3),
        method='cash',
        amount=Decimal('100.00'),
        notes='Pago parcial de prueba'
    )
    
    print(f"✅ Reserva 2: {reservation2.id} - ${reservation2.total_price} (CONFIRMED, check-in anteayer)")
    
    # Reserva 3: Reserva futura (no debería ser NO_SHOW)
    reservation3, created = Reservation.objects.get_or_create(
        hotel=hotel,
        room=room,
        check_in=date.today() + timedelta(days=1),  # Mañana
        check_out=date.today() + timedelta(days=3),
        defaults={
            'guests': 2,
            'guests_data': [{'name': 'Carlos López', 'email': 'carlos@test.com'}],
            'status': ReservationStatus.CONFIRMED,
            'total_price': Decimal('400.00'),
            'applied_cancellation_policy': cancellation_policy,
            'notes': 'Reserva futura (no debería ser NO_SHOW)'
        }
    )
    
    print(f"✅ Reserva 3: {reservation3.id} - ${reservation3.total_price} (CONFIRMED, check-in mañana)")
    
    return [reservation1, reservation2, reservation3]

def test_no_show_processor():
    """Probar el procesador de NO_SHOW directamente"""
    print("\n🧪 Probando NoShowProcessor directamente...")
    
    hotel, room, cancellation_policy, refund_policy = create_test_data()
    reservations = create_test_reservations(hotel, room, cancellation_policy)
    
    # Probar con reserva 1 (debería tener penalidad completa)
    reservation1 = reservations[0]
    print(f"\n📋 Probando procesador con reserva {reservation1.id}...")
    
    # Cambiar manualmente a NO_SHOW para probar
    reservation1.status = ReservationStatus.NO_SHOW
    reservation1.save()
    
    result = NoShowProcessor.process_no_show_penalties(reservation1)
    
    print(f"✅ Resultado del procesador:")
    print(f"   - Éxito: {result.get('success', False)}")
    print(f"   - Total pagado: ${result.get('total_paid', 0)}")
    print(f"   - Penalidad: ${result.get('penalty_amount', 0)}")
    print(f"   - Reembolso: ${result.get('refund_amount', 0)}")
    print(f"   - Penalidad procesada: {result.get('penalty_processed', False)}")
    
    # Verificar logs
    logs = ReservationChangeLog.objects.filter(
        reservation=reservation1,
        event_type__in=[ReservationChangeEvent.NO_SHOW_PENALTY, ReservationChangeEvent.NO_SHOW_PROCESSED]
    )
    print(f"   - Logs creados: {logs.count()}")
    for log in logs:
        print(f"     * {log.event_type}: {log.message}")

def test_auto_mark_no_show_task():
    """Probar la tarea automática de NO_SHOW"""
    print("\n🧪 Probando tarea automática auto_mark_no_show_daily...")
    
    hotel, room, cancellation_policy, refund_policy = create_test_data()
    reservations = create_test_reservations(hotel, room, cancellation_policy)
    
    # Verificar estado inicial
    print(f"\n📊 Estado inicial:")
    for reservation in reservations:
        print(f"   - Reserva {reservation.id}: {reservation.status} (check-in: {reservation.check_in})")
    
    # Ejecutar la tarea
    print(f"\n🚀 Ejecutando tarea auto_mark_no_show_daily...")
    result = auto_mark_no_show_daily()
    print(f"✅ Resultado de la tarea: {result}")
    
    # Verificar estado final
    print(f"\n📊 Estado final:")
    for reservation in reservations:
        reservation.refresh_from_db()
        print(f"   - Reserva {reservation.id}: {reservation.status} (check-in: {reservation.check_in})")
        
        # Verificar logs de penalidades
        penalty_logs = ReservationChangeLog.objects.filter(
            reservation=reservation,
            event_type__in=[ReservationChangeEvent.NO_SHOW_PENALTY, ReservationChangeEvent.NO_SHOW_PROCESSED]
        )
        if penalty_logs.exists():
            print(f"     * Penalidades aplicadas: {penalty_logs.count()}")
            for log in penalty_logs:
                print(f"       - {log.event_type}: {log.message}")

def test_notifications():
    """Probar notificaciones de NO_SHOW"""
    print("\n🧪 Probando notificaciones de NO_SHOW...")
    
    from apps.notifications.models import Notification, NotificationType
    
    # Contar notificaciones iniciales
    initial_count = Notification.objects.filter(type=NotificationType.NO_SHOW).count()
    print(f"📊 Notificaciones NO_SHOW iniciales: {initial_count}")
    
    # Ejecutar tarea
    auto_mark_no_show_daily()
    
    # Contar notificaciones finales
    final_count = Notification.objects.filter(type=NotificationType.NO_SHOW).count()
    print(f"📊 Notificaciones NO_SHOW finales: {final_count}")
    print(f"✅ Notificaciones creadas: {final_count - initial_count}")
    
    # Mostrar notificaciones recientes
    recent_notifications = Notification.objects.filter(
        type=NotificationType.NO_SHOW
    ).order_by('-created_at')[:5]
    
    print(f"\n📋 Notificaciones recientes:")
    for notification in recent_notifications:
        print(f"   - {notification.title}: {notification.message}")

def cleanup_test_data():
    """Limpiar datos de prueba"""
    print("\n🧹 Limpiando datos de prueba...")
    
    # Eliminar reservas de prueba
    test_reservations = Reservation.objects.filter(
        hotel__name="Hotel de Prueba NO_SHOW"
    )
    count = test_reservations.count()
    test_reservations.delete()
    print(f"✅ {count} reservas eliminadas")
    
    # Eliminar habitaciones de prueba
    test_rooms = Room.objects.filter(
        hotel__name="Hotel de Prueba NO_SHOW"
    )
    count = test_rooms.count()
    test_rooms.delete()
    print(f"✅ {count} habitaciones eliminadas")
    
    # Eliminar políticas de prueba
    test_policies = CancellationPolicy.objects.filter(
        hotel__name="Hotel de Prueba NO_SHOW"
    )
    count = test_policies.count()
    test_policies.delete()
    print(f"✅ {count} políticas de cancelación eliminadas")
    
    test_refund_policies = RefundPolicy.objects.filter(
        hotel__name="Hotel de Prueba NO_SHOW"
    )
    count = test_refund_policies.count()
    test_refund_policies.delete()
    print(f"✅ {count} políticas de devolución eliminadas")
    
    # Eliminar hotel de prueba
    test_hotels = Hotel.objects.filter(name="Hotel de Prueba NO_SHOW")
    count = test_hotels.count()
    test_hotels.delete()
    print(f"✅ {count} hoteles eliminados")

def main():
    """Función principal de prueba"""
    print("🚀 Iniciando pruebas de penalidades NO_SHOW...")
    
    try:
        # Prueba 1: Procesador directo
        test_no_show_processor()
        
        # Prueba 2: Tarea automática
        test_auto_mark_no_show_task()
        
        # Prueba 3: Notificaciones
        test_notifications()
        
        print("\n✅ Todas las pruebas completadas exitosamente!")
        
    except Exception as e:
        print(f"\n❌ Error durante las pruebas: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # Limpiar datos de prueba
        cleanup_test_data()

if __name__ == "__main__":
    main()
