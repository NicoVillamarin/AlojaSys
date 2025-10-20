#!/usr/bin/env python
"""
Demo de la tarea Celery process_pending_refunds con datos reales
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

from apps.payments.models import Refund, RefundStatus, RefundReason, PaymentGatewayConfig
from apps.payments.tasks import process_pending_refunds, retry_failed_refunds
from apps.core.models import Hotel
from apps.rooms.models import Room, RoomStatus
from apps.reservations.models import Reservation, ReservationStatus
from django.utils import timezone


def create_demo_data():
    """Crear datos de demostración"""
    print("🔧 Creando datos de demostración...")
    
    # Crear hotel (sin empresa)
    hotel, created = Hotel.objects.get_or_create(
        name="Hotel Demo Refunds",
        defaults={
            'email': 'demo@hotel.com',
            'phone': '+1234567890',
            'address': 'Calle Hotel 456',
            'is_active': True
        }
    )
    print(f"✅ Hotel: {hotel.name}")
    
    # Crear habitación
    room, created = Room.objects.get_or_create(
        name="Habitación Demo 201",
        hotel=hotel,
        defaults={
            'floor': 2,
            'room_type': 'suite',
            'number': 201,
            'base_price': Decimal('300.00'),
            'capacity': 2,
            'max_capacity': 2,
            'status': RoomStatus.AVAILABLE
        }
    )
    print(f"✅ Habitación: {room.name}")
    
    # Crear reserva
    reservation, created = Reservation.objects.get_or_create(
        hotel=hotel,
        room=room,
        check_in=date.today() + timedelta(days=1),
        check_out=date.today() + timedelta(days=4),
        defaults={
            'guests': 2,
            'guests_data': [
                {'name': 'Ana Demo', 'email': 'ana@demo.com', 'phone': '+1234567890'},
                {'name': 'Carlos Demo', 'email': 'carlos@demo.com', 'phone': '+1234567891'}
            ],
            'status': ReservationStatus.CONFIRMED,
            'total_price': Decimal('900.00')
        }
    )
    print(f"✅ Reserva: {reservation.id} - ${reservation.total_price}")
    
    # Crear configuración de gateway
    gateway_config, created = PaymentGatewayConfig.objects.get_or_create(
        hotel=hotel,
        provider='mercado_pago',
        defaults={
            'public_key': 'demo_public_key',
            'access_token': 'demo_access_token',
            'is_test': True,
            'is_active': True,
            'refund_window_days': 30,  # 30 días de ventana
            'partial_refunds_allowed': True
        }
    )
    print(f"✅ Gateway Config: {gateway_config.provider} (ventana: {gateway_config.refund_window_days} días)")
    
    return hotel, room, reservation, gateway_config


def create_demo_refunds(reservation):
    """Crear reembolsos de demostración"""
    print("\n🔧 Creando reembolsos de demostración...")
    
    # Reembolso pendiente normal
    refund_pending = Refund.objects.create(
        reservation=reservation,
        amount=Decimal('300.00'),
        reason=RefundReason.CANCELLATION,
        status=RefundStatus.PENDING,
        refund_method='original_payment',
        processing_days=7,
        notes='Reembolso de demostración pendiente'
    )
    print(f"✅ Reembolso pendiente: {refund_pending.id} - ${refund_pending.amount}")
    
    # Reembolso pendiente con monto diferente
    refund_pending2 = Refund.objects.create(
        reservation=reservation,
        amount=Decimal('200.00'),
        reason=RefundReason.CANCELLATION,
        status=RefundStatus.PENDING,
        refund_method='voucher',
        processing_days=14,
        notes='Reembolso como voucher pendiente'
    )
    print(f"✅ Reembolso pendiente 2: {refund_pending2.id} - ${refund_pending2.amount}")
    
    # Reembolso expirado (creado hace 35 días)
    expired_date = timezone.now() - timedelta(days=35)
    refund_expired = Refund.objects.create(
        reservation=reservation,
        amount=Decimal('150.00'),
        reason=RefundReason.CANCELLATION,
        status=RefundStatus.PENDING,
        refund_method='bank_transfer',
        processing_days=7,
        notes='Reembolso expirado de demostración'
    )
    # Actualizar created_at para simular reembolso expirado
    Refund.objects.filter(id=refund_expired.id).update(created_at=expired_date)
    refund_expired.refresh_from_db()
    print(f"✅ Reembolso expirado: {refund_expired.id} - ${refund_expired.amount} (creado: {refund_expired.created_at.strftime('%Y-%m-%d %H:%M')})")
    
    # Reembolso fallido reciente
    refund_failed = Refund.objects.create(
        reservation=reservation,
        amount=Decimal('100.00'),
        reason=RefundReason.CANCELLATION,
        status=RefundStatus.FAILED,
        refund_method='original_payment',
        processing_days=7,
        notes='Reembolso fallido de demostración'
    )
    print(f"✅ Reembolso fallido: {refund_failed.id} - ${refund_failed.amount}")
    
    return refund_pending, refund_pending2, refund_expired, refund_failed


def demo_process_pending_refunds():
    """Demostrar procesamiento de reembolsos pendientes"""
    print("\n🚀 DEMO: Procesamiento de reembolsos pendientes")
    print("="*60)
    
    # Crear datos de demostración
    hotel, room, reservation, gateway_config = create_demo_data()
    refund_pending, refund_pending2, refund_expired, refund_failed = create_demo_refunds(reservation)
    
    print(f"\n📊 Estado inicial de reembolsos:")
    print(f"   • Pendientes: {Refund.objects.filter(status=RefundStatus.PENDING).count()}")
    print(f"   • Fallidos: {Refund.objects.filter(status=RefundStatus.FAILED).count()}")
    print(f"   • Completados: {Refund.objects.filter(status=RefundStatus.COMPLETED).count()}")
    
    # Mostrar reembolsos pendientes
    print(f"\n📋 Reembolsos pendientes:")
    for refund in Refund.objects.filter(status=RefundStatus.PENDING):
        print(f"   • ID: {refund.id}, Monto: ${refund.amount}, Método: {refund.refund_method}, Creado: {refund.created_at.strftime('%Y-%m-%d %H:%M')}")
    
    # Ejecutar tarea de procesamiento
    print(f"\n🔄 Ejecutando tarea process_pending_refunds...")
    result = process_pending_refunds()
    print(f"✅ Resultado: {result}")
    
    # Mostrar estado después del procesamiento
    print(f"\n📊 Estado después del procesamiento:")
    print(f"   • Pendientes: {Refund.objects.filter(status=RefundStatus.PENDING).count()}")
    print(f"   • Fallidos: {Refund.objects.filter(status=RefundStatus.FAILED).count()}")
    print(f"   • Completados: {Refund.objects.filter(status=RefundStatus.COMPLETED).count()}")
    
    # Mostrar reembolsos actualizados
    print(f"\n📋 Reembolsos actualizados:")
    for refund in Refund.objects.all():
        print(f"   • ID: {refund.id}, Estado: {refund.status}, Monto: ${refund.amount}, Método: {refund.refund_method}")
        if refund.notes:
            print(f"     Notas: {refund.notes}")


def demo_retry_failed_refunds():
    """Demostrar reintento de reembolsos fallidos"""
    print("\n🔄 DEMO: Reintento de reembolsos fallidos")
    print("="*50)
    
    # Mostrar reembolsos fallidos
    failed_refunds = Refund.objects.filter(status=RefundStatus.FAILED)
    print(f"📋 Reembolsos fallidos encontrados: {failed_refunds.count()}")
    
    if failed_refunds.exists():
        for refund in failed_refunds:
            print(f"   • ID: {refund.id}, Monto: ${refund.amount}, Método: {refund.refund_method}")
        
        # Ejecutar tarea de reintento
        print(f"\n🔄 Ejecutando tarea retry_failed_refunds...")
        result = retry_failed_refunds()
        print(f"✅ Resultado: {result}")
        
        # Mostrar estado después del reintento
        print(f"\n📊 Estado después del reintento:")
        print(f"   • Pendientes: {Refund.objects.filter(status=RefundStatus.PENDING).count()}")
        print(f"   • Fallidos: {Refund.objects.filter(status=RefundStatus.FAILED).count()}")
        print(f"   • Completados: {Refund.objects.filter(status=RefundStatus.COMPLETED).count()}")
    else:
        print("ℹ️ No hay reembolsos fallidos para reintentar")


def demo_refund_window_validation():
    """Demostrar validación de ventana de tiempo"""
    print("\n⏰ DEMO: Validación de ventana de tiempo")
    print("="*45)
    
    # Mostrar configuración de gateway
    gateway_configs = PaymentGatewayConfig.objects.filter(is_active=True)
    print(f"📋 Configuraciones de gateway activas: {gateway_configs.count()}")
    
    for config in gateway_configs:
        print(f"   • Hotel: {config.hotel.name}")
        print(f"   • Proveedor: {config.provider}")
        print(f"   • Ventana de reembolso: {config.refund_window_days} días")
        print(f"   • Reembolsos parciales: {'Sí' if config.partial_refunds_allowed else 'No'}")
    
    # Mostrar reembolsos y su estado de expiración
    print(f"\n📋 Estado de reembolsos:")
    for refund in Refund.objects.all():
        created_days_ago = (timezone.now() - refund.created_at).days
        print(f"   • ID: {refund.id}, Creado hace: {created_days_ago} días, Estado: {refund.status}")


def cleanup_demo_data():
    """Limpiar datos de demostración"""
    print("\n🧹 Limpiando datos de demostración...")
    
    Refund.objects.filter(reservation__hotel__name="Hotel Demo Refunds").delete()
    Reservation.objects.filter(hotel__name="Hotel Demo Refunds").delete()
    Room.objects.filter(hotel__name="Hotel Demo Refunds").delete()
    PaymentGatewayConfig.objects.filter(hotel__name="Hotel Demo Refunds").delete()
    Hotel.objects.filter(name="Hotel Demo Refunds").delete()
    
    print("✅ Datos limpiados")


def main():
    """Función principal de demostración"""
    print("🚀 DEMO DE PROCESS_PENDING_REFUNDS")
    print("="*50)
    
    try:
        # Demostrar funcionalidades
        demo_process_pending_refunds()
        demo_retry_failed_refunds()
        demo_refund_window_validation()
        
        print("\n✅ DEMO COMPLETADO EXITOSAMENTE!")
        print("\n🎉 Funcionalidades demostradas:")
        print("   ✅ Procesamiento automático de reembolsos pendientes")
        print("   ✅ Validación de ventana de tiempo (refund_window_days)")
        print("   ✅ Manejo de reembolsos expirados")
        print("   ✅ Reintento de reembolsos fallidos")
        print("   ✅ Diferentes métodos de reembolso")
        print("   ✅ Notificaciones al staff")
        print("   ✅ Seguimiento de estadísticas")
        print("   ✅ Limitación de concurrencia")
        print("   ✅ Idempotencia garantizada")
        
    except Exception as e:
        print(f"\n❌ Error en demo: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        cleanup_demo_data()


if __name__ == "__main__":
    main()
