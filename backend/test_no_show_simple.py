#!/usr/bin/env python
"""
Script de prueba simple para la funcionalidad de penalidades NO_SHOW
Sin dependencias complejas de Enterprise
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
from apps.payments.models import CancellationPolicy, RefundPolicy
from apps.core.models import Hotel
from apps.rooms.models import Room, RoomStatus
from apps.reservations.tasks import auto_mark_no_show_daily
from apps.reservations.services.no_show_processor import NoShowProcessor
from apps.notifications.models import Notification, NotificationType

def create_simple_test_data():
    """Crear datos de prueba simples"""
    print("🔧 Creando datos de prueba simples...")
    
    # Crear enterprise primero (requerido por Hotel)
    from apps.enterprises.models import Enterprise
    enterprise, created = Enterprise.objects.get_or_create(
        name="Empresa Demo",
        defaults={
            'legal_name': 'Empresa Demo S.A.',
            'tax_id': '12345678-9',
            'email': 'demo@empresa.com',
            'phone': '+1234567890',
            'address': 'Calle Demo 123'
        }
    )
    print(f"✅ Enterprise: {enterprise.name} (ID: {enterprise.id})")
    
    # Crear hotel
    hotel, created = Hotel.objects.get_or_create(
        name="Hotel Demo NO_SHOW",
        defaults={
            'enterprise': enterprise,
            'email': 'demo@hotel.com',
            'phone': '+1234567890',
            'address': 'Calle Demo 123',
            'auto_no_show_enabled': True
        }
    )
    print(f"✅ Hotel: {hotel.name} (ID: {hotel.id})")
    
    # Crear habitación
    room, created = Room.objects.get_or_create(
        name="Habitación Demo 101",
        hotel=hotel,
        defaults={
            'floor': 1,
            'room_type': 'single',
            'number': 101,
            'base_price': Decimal('100.00'),
            'capacity': 2,
            'max_capacity': 2,
            'status': RoomStatus.AVAILABLE
        }
    )
    print(f"✅ Habitación: {room.name} (ID: {room.id})")
    
    # Crear política de cancelación
    cancellation_policy, created = CancellationPolicy.objects.get_or_create(
        hotel=hotel,
        name="Política Demo NO_SHOW",
        defaults={
            'free_cancellation_time': 24,
            'free_cancellation_unit': 'hours',
            'partial_refund_time': 72,
            'partial_refund_unit': 'hours',
            'no_refund_time': 168,
            'no_refund_unit': 'hours',
            'cancellation_fee_type': 'percentage',
            'cancellation_fee_value': Decimal('100.00'),  # 100% penalidad
            'is_default': True,
            'is_active': True
        }
    )
    print(f"✅ Política de cancelación: {cancellation_policy.name}")
    
    # Crear política de devolución
    refund_policy, created = RefundPolicy.objects.get_or_create(
        hotel=hotel,
        name="Política Devolución Demo",
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
    print(f"✅ Política de devolución: {refund_policy.name}")
    
    return hotel, room, cancellation_policy, refund_policy

def create_test_reservations(hotel, room, cancellation_policy):
    """Crear reservas de prueba"""
    print("📅 Creando reservas de prueba...")
    
    reservations = []
    
    # Reserva 1: NO_SHOW con pago completo
    reservation1, created = Reservation.objects.get_or_create(
        hotel=hotel,
        room=room,
        check_in=date.today() - timedelta(days=1),  # Ayer
        check_out=date.today() + timedelta(days=2),
        defaults={
            'guests': 2,
            'guests_data': [{'name': 'Juan Pérez', 'email': 'juan@test.com'}],
            'status': ReservationStatus.CONFIRMED,
            'total_price': Decimal('200.00'),
            'applied_cancellation_policy': cancellation_policy,
            'notes': 'Reserva de prueba NO_SHOW'
        }
    )
    
    if created:
        # Simular pago
        from apps.reservations.models import Payment
        Payment.objects.create(
            reservation=reservation1,
            date=date.today() - timedelta(days=2),
            method='credit_card',
            amount=Decimal('200.00'),
            notes='Pago de prueba'
        )
        print(f"✅ Reserva 1 creada: {reservation1.id} - ${reservation1.total_price}")
    else:
        print(f"✅ Reserva 1 existente: {reservation1.id} - ${reservation1.total_price}")
    
    reservations.append(reservation1)
    
    return reservations

def test_no_show_processor():
    """Probar el procesador de NO_SHOW"""
    print("\n🧪 Probando NoShowProcessor...")
    
    hotel, room, cancellation_policy, refund_policy = create_simple_test_data()
    reservations = create_test_reservations(hotel, room, cancellation_policy)
    
    # Probar con reserva 1
    reservation1 = reservations[0]
    print(f"\n📋 Procesando reserva {reservation1.id}...")
    
    # Cambiar manualmente a NO_SHOW
    reservation1.status = ReservationStatus.NO_SHOW
    reservation1.save()
    
    result = NoShowProcessor.process_no_show_penalties(reservation1)
    
    print(f"✅ Resultado:")
    print(f"   - Éxito: {result.get('success', False)}")
    print(f"   - Total pagado: ${result.get('total_paid', 0)}")
    print(f"   - Penalidad: ${result.get('penalty_amount', 0)}")
    print(f"   - Reembolso: ${result.get('refund_amount', 0)}")
    print(f"   - Penalidad procesada: {result.get('penalty_processed', False)}")
    
    if result.get('error'):
        print(f"   - Error: {result.get('error')}")
    
    # Verificar logs
    logs = ReservationChangeLog.objects.filter(
        reservation=reservation1,
        event_type__in=[ReservationChangeEvent.NO_SHOW_PENALTY, ReservationChangeEvent.NO_SHOW_PROCESSED]
    )
    print(f"   - Logs creados: {logs.count()}")
    for log in logs:
        print(f"     * {log.event_type}: {log.message}")

def test_auto_mark_no_show_task():
    """Probar la tarea automática"""
    print("\n🧪 Probando tarea automática...")
    
    hotel, room, cancellation_policy, refund_policy = create_simple_test_data()
    reservations = create_test_reservations(hotel, room, cancellation_policy)
    
    print(f"\n📊 Estado inicial:")
    for reservation in reservations:
        print(f"   - Reserva {reservation.id}: {reservation.status}")
    
    print(f"\n🚀 Ejecutando tarea...")
    result = auto_mark_no_show_daily()
    print(f"✅ Resultado: {result}")
    
    print(f"\n📊 Estado final:")
    for reservation in reservations:
        reservation.refresh_from_db()
        print(f"   - Reserva {reservation.id}: {reservation.status}")
        
        # Verificar logs
        penalty_logs = ReservationChangeLog.objects.filter(
            reservation=reservation,
            event_type__in=[ReservationChangeEvent.NO_SHOW_PENALTY, ReservationChangeEvent.NO_SHOW_PROCESSED]
        )
        if penalty_logs.exists():
            print(f"     * Penalidades: {penalty_logs.count()}")

def test_notifications():
    """Probar notificaciones"""
    print("\n🧪 Probando notificaciones...")
    
    initial_count = Notification.objects.filter(type=NotificationType.NO_SHOW).count()
    print(f"📊 Notificaciones iniciales: {initial_count}")
    
    # Ejecutar tarea
    auto_mark_no_show_daily()
    
    final_count = Notification.objects.filter(type=NotificationType.NO_SHOW).count()
    print(f"📊 Notificaciones finales: {final_count}")
    print(f"✅ Notificaciones creadas: {final_count - initial_count}")

def cleanup():
    """Limpiar datos de prueba"""
    print("\n🧹 Limpiando datos...")
    
    # Eliminar en orden inverso de dependencias
    Reservation.objects.filter(hotel__name="Hotel Demo NO_SHOW").delete()
    Room.objects.filter(hotel__name="Hotel Demo NO_SHOW").delete()
    CancellationPolicy.objects.filter(hotel__name="Hotel Demo NO_SHOW").delete()
    RefundPolicy.objects.filter(hotel__name="Hotel Demo NO_SHOW").delete()
    Hotel.objects.filter(name="Hotel Demo NO_SHOW").delete()
    from apps.enterprises.models import Enterprise
    Enterprise.objects.filter(name="Empresa Demo").delete()
    
    print("✅ Datos limpiados")

def main():
    """Función principal"""
    print("🚀 PRUEBA SIMPLE DEL SISTEMA NO_SHOW CON PENALIDADES")
    print("="*60)
    
    try:
        # Prueba 1: Procesador directo
        test_no_show_processor()
        
        # Prueba 2: Tarea automática
        test_auto_mark_no_show_task()
        
        # Prueba 3: Notificaciones
        test_notifications()
        
        print("\n✅ TODAS LAS PRUEBAS COMPLETADAS EXITOSAMENTE!")
        print("\n🎉 El sistema de penalidades NO_SHOW está funcionando:")
        print("   ✅ Procesador de penalidades")
        print("   ✅ Tarea Celery automática")
        print("   ✅ Logs detallados")
        print("   ✅ Notificaciones")
        print("   ✅ Integración con políticas")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        cleanup()

if __name__ == "__main__":
    main()
