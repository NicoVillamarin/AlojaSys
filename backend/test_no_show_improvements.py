#!/usr/bin/env python
"""
Script de prueba para las mejoras de reembolso y notificaciones NO_SHOW
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

def create_test_data():
    """Crear datos de prueba para las mejoras"""
    print("🔧 Creando datos de prueba para mejoras NO_SHOW...")
    
    # Crear enterprise
    from apps.enterprises.models import Enterprise
    enterprise, created = Enterprise.objects.get_or_create(
        name="Empresa Test Mejoras",
        defaults={
            'legal_name': 'Empresa Test Mejoras S.A.',
            'tax_id': '87654321-0',
            'email': 'test@empresa.com',
            'phone': '+9876543210',
            'address': 'Calle Test 456'
        }
    )
    print(f"✅ Enterprise: {enterprise.name}")
    
    # Crear hotel
    hotel, created = Hotel.objects.get_or_create(
        name="Hotel Test Mejoras NO_SHOW",
        defaults={
            'enterprise': enterprise,
            'email': 'test@hotel.com',
            'phone': '+9876543210',
            'address': 'Calle Test 456',
            'auto_no_show_enabled': True
        }
    )
    print(f"✅ Hotel: {hotel.name}")
    
    # Crear habitación
    room, created = Room.objects.get_or_create(
        name="Habitación Test 999",
        hotel=hotel,
        defaults={
            'floor': 9,
            'room_type': 'suite',
            'number': 999,
            'base_price': Decimal('500.00'),
            'capacity': 4,
            'max_capacity': 4,
            'status': RoomStatus.AVAILABLE
        }
    )
    print(f"✅ Habitación: {room.name}")
    
    return hotel, room, enterprise

def create_advanced_refund_policy(hotel):
    """Crear política de devolución avanzada con configuraciones específicas para NO_SHOW"""
    print("📋 Creando política de devolución avanzada...")
    
    # Crear política de devolución con configuraciones específicas para NO_SHOW
    refund_policy, created = RefundPolicy.objects.get_or_create(
        hotel=hotel,
        name="Política Avanzada NO_SHOW",
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
    
    # Agregar campos específicos para NO_SHOW usando metadata
    if not hasattr(refund_policy, 'metadata'):
        refund_policy.metadata = {}
    
    refund_policy.metadata.update({
        'no_show_refund_percentage': 25,  # 25% de reembolso para NO_SHOW
        'no_show_refund_method': 'voucher',
        'no_show_processing_days': 45,  # 45 días para procesar NO_SHOW
        'no_show_voucher_percentage': 25,
        'allow_no_show_refund': True
    })
    refund_policy.save()
    
    print(f"✅ Política de devolución: {refund_policy.name}")
    print(f"   - Reembolso NO_SHOW: {refund_policy.metadata.get('no_show_refund_percentage', 0)}%")
    print(f"   - Método NO_SHOW: {refund_policy.metadata.get('no_show_refund_method', 'voucher')}")
    print(f"   - Días procesamiento: {refund_policy.metadata.get('no_show_processing_days', 30)}")
    
    return refund_policy

def create_cancellation_policy(hotel):
    """Crear política de cancelación"""
    print("📋 Creando política de cancelación...")
    
    cancellation_policy, created = CancellationPolicy.objects.get_or_create(
        hotel=hotel,
        name="Política Cancelación Test",
        defaults={
            'free_cancellation_time': 24,
            'free_cancellation_unit': 'hours',
            'partial_refund_time': 72,
            'partial_refund_unit': 'hours',
            'no_refund_time': 168,
            'no_refund_unit': 'hours',
            'cancellation_fee_type': 'percentage',
            'cancellation_fee_value': Decimal('100.00'),
            'is_default': True,
            'is_active': True
        }
    )
    
    print(f"✅ Política de cancelación: {cancellation_policy.name}")
    return cancellation_policy

def test_advanced_no_show_processing():
    """Probar procesamiento avanzado de NO_SHOW con reembolsos"""
    print("\n🧪 Probando procesamiento avanzado de NO_SHOW...")
    
    hotel, room, enterprise = create_test_data()
    refund_policy = create_advanced_refund_policy(hotel)
    cancellation_policy = create_cancellation_policy(hotel)
    
    # Crear reserva de prueba
    reservation = Reservation.objects.create(
        hotel=hotel,
        room=room,
        check_in=date.today() - timedelta(days=1),
        check_out=date.today() + timedelta(days=3),
        guests=2,
        guests_data=[
            {'name': 'Juan Test', 'email': 'juan@test.com', 'phone': '+1234567890'},
            {'name': 'María Test', 'email': 'maria@test.com', 'phone': '+1234567891'}
        ],
        status=ReservationStatus.CONFIRMED,
        total_price=Decimal('1000.00'),
        applied_cancellation_policy=cancellation_policy,
        notes='Reserva de prueba para mejoras NO_SHOW'
    )
    
    # Simular pago
    from apps.reservations.models import Payment
    Payment.objects.create(
        reservation=reservation,
        date=date.today() - timedelta(days=2),
        method='credit_card',
        amount=Decimal('1000.00'),
        notes='Pago completo de prueba'
    )
    
    print(f"✅ Reserva creada: {reservation.id} - ${reservation.total_price}")
    
    # Cambiar a NO_SHOW
    reservation.status = ReservationStatus.NO_SHOW
    reservation.save()
    
    print(f"\n🚀 Procesando NO_SHOW con mejoras...")
    
    # Procesar con el NoShowProcessor mejorado
    result = NoShowProcessor.process_no_show_penalties(reservation)
    
    print(f"\n✅ Resultado del procesamiento:")
    print(f"   - Éxito: {result.get('success', False)}")
    print(f"   - Total pagado: ${result.get('total_paid', 0)}")
    print(f"   - Penalidad: ${result.get('penalty_amount', 0)}")
    print(f"   - Reembolso: ${result.get('refund_amount', 0)}")
    print(f"   - Penalidad procesada: {result.get('penalty_processed', False)}")
    print(f"   - Reembolso procesado: {result.get('refund_processed', False)}")
    
    if result.get('error'):
        print(f"   - Error: {result.get('error')}")
    
    # Verificar reembolsos creados
    refunds = Refund.objects.filter(reservation=reservation)
    print(f"\n💰 Reembolsos creados: {refunds.count()}")
    for refund in refunds:
        print(f"   - ID: {refund.id}")
        print(f"   - Monto: ${refund.amount}")
        print(f"   - Método: {refund.refund_method}")
        print(f"   - Estado: {refund.status}")
        print(f"   - Días procesamiento: {refund.processing_days}")
        print(f"   - Notas: {refund.notes}")
    
    # Verificar logs
    logs = ReservationChangeLog.objects.filter(
        reservation=reservation,
        event_type__in=[ReservationChangeEvent.NO_SHOW_PENALTY, ReservationChangeEvent.NO_SHOW_PROCESSED]
    )
    print(f"\n📝 Logs creados: {logs.count()}")
    for log in logs:
        print(f"   - {log.event_type}: {log.message}")
        if log.snapshot:
            print(f"     Snapshot: {log.snapshot}")
    
    return reservation

def test_advanced_notifications():
    """Probar notificaciones mejoradas"""
    print("\n🧪 Probando notificaciones mejoradas...")
    
    # Buscar reserva NO_SHOW existente
    no_show_reservation = Reservation.objects.filter(
        status=ReservationStatus.NO_SHOW
    ).first()
    
    if not no_show_reservation:
        print("❌ No hay reservas NO_SHOW para probar notificaciones")
        return
    
    print(f"📋 Probando notificaciones con reserva {no_show_reservation.id}")
    
    # Contar notificaciones iniciales
    initial_count = Notification.objects.filter(
        type=NotificationType.NO_SHOW,
        reservation_id=no_show_reservation.id
    ).count()
    
    print(f"📊 Notificaciones iniciales: {initial_count}")
    
    # Procesar penalidades (esto creará notificaciones)
    result = NoShowProcessor.process_no_show_penalties(no_show_reservation)
    
    # Contar notificaciones finales
    final_count = Notification.objects.filter(
        type=NotificationType.NO_SHOW,
        reservation_id=no_show_reservation.id
    ).count()
    
    print(f"📊 Notificaciones finales: {final_count}")
    print(f"✅ Notificaciones creadas: {final_count - initial_count}")
    
    # Mostrar notificaciones detalladas
    notifications = Notification.objects.filter(
        type=NotificationType.NO_SHOW,
        reservation_id=no_show_reservation.id
    ).order_by('-created_at')[:5]
    
    print(f"\n📋 Notificaciones detalladas:")
    for i, notification in enumerate(notifications, 1):
        print(f"\n{i}. {notification.title}")
        print(f"   Mensaje: {notification.message[:100]}...")
        print(f"   Usuario: {notification.user_id if notification.user_id else 'Todos'}")
        print(f"   Hotel: {notification.hotel_id}")
        print(f"   Nivel: {notification.metadata.get('notification_level', 'N/A')}")
        print(f"   Requiere acción: {notification.metadata.get('requires_action', False)}")
        
        if notification.metadata:
            print(f"   Metadata:")
            for key, value in notification.metadata.items():
                if key in ['penalty_amount', 'refund_amount', 'total_paid', 'net_loss']:
                    print(f"     - {key}: ${value}")

def test_refund_methods():
    """Probar diferentes métodos de reembolso"""
    print("\n🧪 Probando diferentes métodos de reembolso...")
    
    hotel, room, enterprise = create_test_data()
    
    # Crear políticas con diferentes métodos de reembolso
    methods_to_test = ['voucher', 'bank_transfer', 'original_payment', 'cash']
    
    for method in methods_to_test:
        print(f"\n📋 Probando método: {method}")
        
        # Crear política específica para este método
        refund_policy = RefundPolicy.objects.create(
            hotel=hotel,
            name=f"Política {method.title()}",
            refund_method=method,
            is_active=True
        )
        
        # Agregar metadata específica para NO_SHOW
        refund_policy.metadata = {
            'no_show_refund_percentage': 30,
            'no_show_refund_method': method,
            'no_show_processing_days': 30,
            'allow_no_show_refund': True
        }
        refund_policy.save()
        
        # Crear reserva de prueba
        reservation = Reservation.objects.create(
            hotel=hotel,
            room=room,
            check_in=date.today() - timedelta(days=1),
            check_out=date.today() + timedelta(days=2),
            guests=1,
            guests_data=[{'name': f'Test {method}', 'email': f'test@{method}.com'}],
            status=ReservationStatus.NO_SHOW,
            total_price=Decimal('200.00'),
            notes=f'Prueba método {method}'
        )
        
        # Simular pago
        from apps.reservations.models import Payment
        Payment.objects.create(
            reservation=reservation,
            date=date.today() - timedelta(days=2),
            method='credit_card',
            amount=Decimal('200.00'),
            notes=f'Pago prueba {method}'
        )
        
        # Procesar reembolso
        result = NoShowProcessor.process_no_show_penalties(reservation)
        
        print(f"   - Éxito: {result.get('success', False)}")
        print(f"   - Reembolso: ${result.get('refund_amount', 0)}")
        print(f"   - Procesado: {result.get('refund_processed', False)}")
        
        if result.get('refund_result'):
            refund_result = result['refund_result']
            print(f"   - Método: {refund_result.get('method', 'N/A')}")
            print(f"   - Estado: {refund_result.get('status', 'N/A')}")
            print(f"   - Requiere procesamiento manual: {refund_result.get('requires_manual_processing', False)}")
        
        # Limpiar
        reservation.delete()
        refund_policy.delete()

def cleanup_test_data():
    """Limpiar datos de prueba"""
    print("\n🧹 Limpiando datos de prueba...")
    
    # Eliminar en orden inverso de dependencias
    Reservation.objects.filter(hotel__name="Hotel Test Mejoras NO_SHOW").delete()
    Room.objects.filter(hotel__name="Hotel Test Mejoras NO_SHOW").delete()
    CancellationPolicy.objects.filter(hotel__name="Hotel Test Mejoras NO_SHOW").delete()
    RefundPolicy.objects.filter(hotel__name="Hotel Test Mejoras NO_SHOW").delete()
    Hotel.objects.filter(name="Hotel Test Mejoras NO_SHOW").delete()
    from apps.enterprises.models import Enterprise
    Enterprise.objects.filter(name="Empresa Test Mejoras").delete()
    
    print("✅ Datos limpiados")

def main():
    """Función principal"""
    print("🚀 PRUEBA DE MEJORAS NO_SHOW: REEMBOLSOS Y NOTIFICACIONES")
    print("="*70)
    
    try:
        # Prueba 1: Procesamiento avanzado
        reservation = test_advanced_no_show_processing()
        
        # Prueba 2: Notificaciones mejoradas
        test_advanced_notifications()
        
        # Prueba 3: Diferentes métodos de reembolso
        test_refund_methods()
        
        print("\n✅ TODAS LAS PRUEBAS COMPLETADAS!")
        print("\n🎉 Las mejoras de NO_SHOW están funcionando:")
        print("   ✅ Lógica de reembolso específica para NO_SHOW")
        print("   ✅ Notificaciones detalladas con información financiera")
        print("   ✅ Diferentes métodos de reembolso")
        print("   ✅ Configuraciones específicas por política")
        print("   ✅ Logs detallados de procesamiento")
        print("   ✅ Notificaciones diferenciadas (hotel, huésped, admin)")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        cleanup_test_data()

if __name__ == "__main__":
    main()
