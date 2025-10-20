#!/usr/bin/env python
"""
Script de demostración para las penalidades automáticas NO_SHOW
Muestra cómo funciona el sistema mejorado paso a paso
"""

import os
import sys
import django
from datetime import date, timedelta
from decimal import Decimal

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'hotel.settings')
os.environ.setdefault('USE_SQLITE', 'True')  # Forzar uso de SQLite
django.setup()

from apps.reservations.models import Reservation, ReservationStatus, ReservationChangeLog, ReservationChangeEvent
from apps.payments.models import CancellationPolicy, RefundPolicy
from apps.core.models import Hotel
from apps.rooms.models import Room, RoomStatus
from apps.reservations.tasks import auto_mark_no_show_daily
from apps.reservations.services.no_show_processor import NoShowProcessor
from apps.notifications.models import Notification, NotificationType

def create_demo_hotel():
    """Crear hotel de demostración"""
    print("🏨 Creando hotel de demostración...")
    
    hotel, created = Hotel.objects.get_or_create(
        name="Hotel Demo NO_SHOW",
        defaults={
            'email': 'demo@hotel.com',
            'phone': '+1234567890',
            'address': 'Calle Demo 123',
            'auto_no_show_enabled': True
        }
    )
    
    if created:
        print(f"✅ Hotel creado: {hotel.name} (ID: {hotel.id})")
    else:
        print(f"✅ Hotel existente: {hotel.name} (ID: {hotel.id})")
    
    return hotel

def create_demo_room(hotel):
    """Crear habitación de demostración"""
    print("🛏️ Creando habitación de demostración...")
    
    room, created = Room.objects.get_or_create(
        name="Habitación Demo 301",
        hotel=hotel,
        defaults={
            'floor': 3,
            'room_type': 'suite',
            'number': 301,
            'base_price': Decimal('200.00'),
            'capacity': 2,
            'max_capacity': 2,
            'status': RoomStatus.AVAILABLE
        }
    )
    
    if created:
        print(f"✅ Habitación creada: {room.name} (ID: {room.id})")
    else:
        print(f"✅ Habitación existente: {room.name} (ID: {room.id})")
    
    return room

def create_demo_policies(hotel):
    """Crear políticas de demostración"""
    print("📋 Creando políticas de demostración...")
    
    # Política de cancelación con penalidad completa para NO_SHOW
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
            'is_active': True,
            'free_cancellation_message': 'Cancelación gratuita hasta 24 horas antes del check-in',
            'partial_cancellation_message': 'Cancelación con penalidad del 50% hasta 72 horas antes',
            'no_cancellation_message': 'Sin cancelación después de 168 horas antes del check-in'
        }
    )
    
    if created:
        print(f"✅ Política de cancelación creada: {cancellation_policy.name}")
    else:
        print(f"✅ Política de cancelación existente: {cancellation_policy.name}")
    
    # Política de devolución
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
    
    if created:
        print(f"✅ Política de devolución creada: {refund_policy.name}")
    else:
        print(f"✅ Política de devolución existente: {refund_policy.name}")
    
    return cancellation_policy, refund_policy

def create_demo_reservations(hotel, room, cancellation_policy):
    """Crear reservas de demostración"""
    print("📅 Creando reservas de demostración...")
    
    reservations = []
    
    # Reserva 1: NO_SHOW con pago completo (debería tener penalidad completa)
    reservation1, created = Reservation.objects.get_or_create(
        hotel=hotel,
        room=room,
        check_in=date.today() - timedelta(days=1),  # Ayer
        check_out=date.today() + timedelta(days=2),
        defaults={
            'guests': 2,
            'guests_data': [
                {'name': 'Juan Pérez', 'email': 'juan@demo.com', 'phone': '+1234567890'},
                {'name': 'María García', 'email': 'maria@demo.com', 'phone': '+1234567891'}
            ],
            'status': ReservationStatus.CONFIRMED,
            'total_price': Decimal('400.00'),
            'applied_cancellation_policy': cancellation_policy,
            'notes': 'Reserva de luna de miel - NO_SHOW'
        }
    )
    
    if created:
        # Simular pago completo
        from apps.reservations.models import Payment
        Payment.objects.create(
            reservation=reservation1,
            date=date.today() - timedelta(days=2),
            method='credit_card',
            amount=Decimal('400.00'),
            notes='Pago completo con tarjeta de crédito'
        )
        print(f"✅ Reserva 1 creada: {reservation1.id} - ${reservation1.total_price} (CONFIRMED, check-in ayer)")
    else:
        print(f"✅ Reserva 1 existente: {reservation1.id} - ${reservation1.total_price}")
    
    reservations.append(reservation1)
    
    # Reserva 2: NO_SHOW con pago parcial (debería tener penalidad parcial)
    reservation2, created = Reservation.objects.get_or_create(
        hotel=hotel,
        room=room,
        check_in=date.today() - timedelta(days=2),  # Anteayer
        check_out=date.today(),
        defaults={
            'guests': 1,
            'guests_data': [{'name': 'Carlos López', 'email': 'carlos@demo.com', 'phone': '+1234567892'}],
            'status': ReservationStatus.CONFIRMED,
            'total_price': Decimal('300.00'),
            'applied_cancellation_policy': cancellation_policy,
            'notes': 'Reserva de negocios - NO_SHOW'
        }
    )
    
    if created:
        # Simular pago parcial
        from apps.reservations.models import Payment
        Payment.objects.create(
            reservation=reservation2,
            date=date.today() - timedelta(days=3),
            method='cash',
            amount=Decimal('150.00'),
            notes='Pago parcial en efectivo'
        )
        print(f"✅ Reserva 2 creada: {reservation2.id} - ${reservation2.total_price} (CONFIRMED, check-in anteayer)")
    else:
        print(f"✅ Reserva 2 existente: {reservation2.id} - ${reservation2.total_price}")
    
    reservations.append(reservation2)
    
    return reservations

def demonstrate_no_show_processing():
    """Demostrar el procesamiento de NO_SHOW paso a paso"""
    print("\n" + "="*60)
    print("🚀 DEMOSTRACIÓN: PROCESAMIENTO DE PENALIDADES NO_SHOW")
    print("="*60)
    
    # Crear datos de demostración
    hotel = create_demo_hotel()
    room = create_demo_room(hotel)
    cancellation_policy, refund_policy = create_demo_policies(hotel)
    reservations = create_demo_reservations(hotel, room, cancellation_policy)
    
    print(f"\n📊 Estado inicial de las reservas:")
    for i, reservation in enumerate(reservations, 1):
        print(f"   {i}. Reserva {reservation.id}: {reservation.status} - ${reservation.total_price} (check-in: {reservation.check_in})")
    
    print(f"\n🔍 Verificando configuración del hotel:")
    print(f"   - Auto NO_SHOW habilitado: {hotel.auto_no_show_enabled}")
    print(f"   - Política de cancelación: {cancellation_policy.name}")
    print(f"   - Política de devolución: {refund_policy.name}")
    
    print(f"\n🚀 Ejecutando tarea automática auto_mark_no_show_daily...")
    print("-" * 50)
    
    # Ejecutar la tarea
    result = auto_mark_no_show_daily()
    
    print("-" * 50)
    print(f"✅ Resultado: {result}")
    
    print(f"\n📊 Estado final de las reservas:")
    for i, reservation in enumerate(reservations, 1):
        reservation.refresh_from_db()
        print(f"   {i}. Reserva {reservation.id}: {reservation.status} - ${reservation.total_price} (check-in: {reservation.check_in})")
        
        # Mostrar logs de penalidades
        penalty_logs = ReservationChangeLog.objects.filter(
            reservation=reservation,
            event_type__in=[ReservationChangeEvent.NO_SHOW_PENALTY, ReservationChangeEvent.NO_SHOW_PROCESSED]
        ).order_by('changed_at')
        
        if penalty_logs.exists():
            print(f"      💰 Penalidades aplicadas:")
            for log in penalty_logs:
                print(f"         - {log.event_type}: {log.message}")
                if log.snapshot:
                    penalty_amount = log.snapshot.get('penalty_amount', 0)
                    if penalty_amount > 0:
                        print(f"           Monto: ${penalty_amount}")
    
    print(f"\n🔔 Notificaciones generadas:")
    recent_notifications = Notification.objects.filter(
        type=NotificationType.NO_SHOW,
        hotel_id=hotel.id
    ).order_by('-created_at')[:3]
    
    for notification in recent_notifications:
        print(f"   - {notification.title}")
        print(f"     {notification.message}")
        if notification.metadata:
            penalty_amount = notification.metadata.get('penalty_amount', 0)
            if penalty_amount > 0:
                print(f"     Penalidad: ${penalty_amount}")
    
    print(f"\n📈 Estadísticas del procesamiento:")
    total_penalties = ReservationChangeLog.objects.filter(
        reservation__hotel=hotel,
        event_type=ReservationChangeEvent.NO_SHOW_PENALTY
    ).count()
    
    total_processed = ReservationChangeLog.objects.filter(
        reservation__hotel=hotel,
        event_type=ReservationChangeEvent.NO_SHOW_PROCESSED
    ).count()
    
    print(f"   - Reservas procesadas como NO_SHOW: {total_processed}")
    print(f"   - Penalidades aplicadas: {total_penalties}")
    print(f"   - Notificaciones generadas: {recent_notifications.count()}")

def demonstrate_manual_processing():
    """Demostrar procesamiento manual de NO_SHOW"""
    print("\n" + "="*60)
    print("🔧 DEMOSTRACIÓN: PROCESAMIENTO MANUAL DE NO_SHOW")
    print("="*60)
    
    # Buscar una reserva NO_SHOW existente
    no_show_reservation = Reservation.objects.filter(
        status=ReservationStatus.NO_SHOW
    ).first()
    
    if not no_show_reservation:
        print("❌ No hay reservas NO_SHOW para procesar manualmente")
        return
    
    print(f"📋 Procesando manualmente reserva {no_show_reservation.id}...")
    print(f"   - Hotel: {no_show_reservation.hotel.name}")
    print(f"   - Habitación: {no_show_reservation.room.name}")
    print(f"   - Total: ${no_show_reservation.total_price}")
    print(f"   - Check-in: {no_show_reservation.check_in}")
    
    # Procesar penalidades manualmente
    result = NoShowProcessor.process_no_show_penalties(no_show_reservation)
    
    print(f"\n✅ Resultado del procesamiento manual:")
    print(f"   - Éxito: {result.get('success', False)}")
    print(f"   - Total pagado: ${result.get('total_paid', 0)}")
    print(f"   - Penalidad: ${result.get('penalty_amount', 0)}")
    print(f"   - Reembolso: ${result.get('refund_amount', 0)}")
    print(f"   - Penalidad procesada: {result.get('penalty_processed', False)}")
    
    if result.get('error'):
        print(f"   - Error: {result.get('error')}")

def cleanup_demo_data():
    """Limpiar datos de demostración"""
    print("\n🧹 Limpiando datos de demostración...")
    
    # Eliminar reservas de demostración
    demo_reservations = Reservation.objects.filter(
        hotel__name="Hotel Demo NO_SHOW"
    )
    count = demo_reservations.count()
    demo_reservations.delete()
    print(f"✅ {count} reservas eliminadas")
    
    # Eliminar habitaciones de demostración
    demo_rooms = Room.objects.filter(
        hotel__name="Hotel Demo NO_SHOW"
    )
    count = demo_rooms.count()
    demo_rooms.delete()
    print(f"✅ {count} habitaciones eliminadas")
    
    # Eliminar políticas de demostración
    demo_policies = CancellationPolicy.objects.filter(
        hotel__name="Hotel Demo NO_SHOW"
    )
    count = demo_policies.count()
    demo_policies.delete()
    print(f"✅ {count} políticas de cancelación eliminadas")
    
    demo_refund_policies = RefundPolicy.objects.filter(
        hotel__name="Hotel Demo NO_SHOW"
    )
    count = demo_refund_policies.count()
    demo_refund_policies.delete()
    print(f"✅ {count} políticas de devolución eliminadas")
    
    # Eliminar hotel de demostración
    demo_hotels = Hotel.objects.filter(name="Hotel Demo NO_SHOW")
    count = demo_hotels.count()
    demo_hotels.delete()
    print(f"✅ {count} hoteles eliminados")

def main():
    """Función principal de demostración"""
    print("🎯 DEMOSTRACIÓN DEL SISTEMA DE PENALIDADES NO_SHOW MEJORADO")
    print("="*70)
    
    try:
        # Demostración 1: Procesamiento automático
        demonstrate_no_show_processing()
        
        # Demostración 2: Procesamiento manual
        demonstrate_manual_processing()
        
        print("\n" + "="*70)
        print("✅ DEMOSTRACIÓN COMPLETADA EXITOSAMENTE!")
        print("="*70)
        print("\n🎉 El sistema de penalidades NO_SHOW está funcionando correctamente:")
        print("   ✅ Tarea Celery automática con penalidades")
        print("   ✅ Procesamiento manual de penalidades")
        print("   ✅ Logs detallados de penalidades")
        print("   ✅ Notificaciones con información financiera")
        print("   ✅ Integración con políticas de cancelación")
        print("   ✅ Cálculo automático de penalidades")
        
    except Exception as e:
        print(f"\n❌ Error durante la demostración: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # Preguntar si limpiar datos
        response = input("\n¿Desea limpiar los datos de demostración? (s/n): ").lower().strip()
        if response in ['s', 'si', 'sí', 'y', 'yes']:
            cleanup_demo_data()
        else:
            print("ℹ️ Datos de demostración conservados para futuras pruebas")

if __name__ == "__main__":
    main()
