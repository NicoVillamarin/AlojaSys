#!/usr/bin/env python
"""
Script de prueba para la funcionalidad de auto-cancelación de reservas PENDING por depósito vencido
"""

import os
import sys
import django
from datetime import date, timedelta
from decimal import Decimal

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'hotel.settings')
django.setup()

from apps.reservations.models import Reservation, ReservationStatus, ReservationChangeLog
from apps.payments.models import PaymentPolicy, PaymentMethod
from apps.core.models import Hotel
from apps.rooms.models import Room, RoomStatus
from apps.reservations.tasks import auto_cancel_pending_deposits
from django.contrib.auth import get_user_model

User = get_user_model()

def create_test_data():
    """Crear datos de prueba para la funcionalidad"""
    print("🔧 Creando datos de prueba...")
    
    # Crear hotel de prueba
    hotel, created = Hotel.objects.get_or_create(
        name="Hotel de Prueba Auto-Cancel",
        defaults={
            'email': 'test@hotel.com',
            'phone': '+1234567890',
            'address': 'Calle de Prueba 123'
        }
    )
    print(f"✅ Hotel: {hotel.name} (ID: {hotel.id})")
    
    # Crear habitación de prueba
    room, created = Room.objects.get_or_create(
        name="Habitación 101",
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
    
    # Crear política de pago
    payment_policy, created = PaymentPolicy.objects.get_or_create(
        hotel=hotel,
        defaults={
            'name': 'Política de Prueba',
            'deposit_percentage': 30,
            'deposit_due_hours': 24,  # 24 horas para pagar el depósito
            'is_active': True
        }
    )
    print(f"✅ Política de Pago: {payment_policy.name} (ID: {payment_policy.id})")
    
    # Crear usuario de prueba
    user, created = User.objects.get_or_create(
        username='test_user',
        defaults={
            'email': 'test@user.com',
            'first_name': 'Test',
            'last_name': 'User'
        }
    )
    print(f"✅ Usuario: {user.username} (ID: {user.id})")
    
    return hotel, room, payment_policy, user

def create_test_reservations(hotel, room, user):
    """Crear reservas de prueba con diferentes escenarios"""
    print("\n📋 Creando reservas de prueba...")
    
    today = date.today()
    yesterday = today - timedelta(days=1)
    tomorrow = today + timedelta(days=1)
    
    # Escenario 1: Reserva PENDING con depósito vencido (debe cancelarse)
    reservation1, created = Reservation.objects.get_or_create(
        hotel=hotel,
        room=room,
        check_in=tomorrow,
        check_out=tomorrow + timedelta(days=2),
        defaults={
            'status': ReservationStatus.PENDING,
            'guests_data': {
                'name': 'Juan Pérez',
                'email': 'juan@test.com',
                'phone': '+1234567890'
            },
            'total_amount': Decimal('200.00'),
            'created_at': yesterday,  # Creada ayer, depósito ya vencido
            'created_by': user
        }
    )
    print(f"✅ Reserva 1 (PENDING, depósito vencido): {reservation1.id} - {reservation1.status}")
    
    # Escenario 2: Reserva PENDING con depósito NO vencido (NO debe cancelarse)
    reservation2, created = Reservation.objects.get_or_create(
        hotel=hotel,
        room=room,
        check_in=tomorrow + timedelta(days=1),
        check_out=tomorrow + timedelta(days=3),
        defaults={
            'status': ReservationStatus.PENDING,
            'guests_data': {
                'name': 'María García',
                'email': 'maria@test.com',
                'phone': '+1234567891'
            },
            'total_amount': Decimal('300.00'),
            'created_at': today,  # Creada hoy, depósito aún válido
            'created_by': user
        }
    )
    print(f"✅ Reserva 2 (PENDING, depósito válido): {reservation2.id} - {reservation2.status}")
    
    # Escenario 3: Reserva PENDING con pago (NO debe cancelarse)
    reservation3, created = Reservation.objects.get_or_create(
        hotel=hotel,
        room=room,
        check_in=tomorrow + timedelta(days=2),
        check_out=tomorrow + timedelta(days=4),
        defaults={
            'status': ReservationStatus.PENDING,
            'guests_data': {
                'name': 'Carlos López',
                'email': 'carlos@test.com',
                'phone': '+1234567892'
            },
            'total_amount': Decimal('400.00'),
            'created_at': yesterday,  # Creada ayer, depósito vencido PERO tiene pago
            'created_by': user
        }
    )
    print(f"✅ Reserva 3 (PENDING, depósito vencido pero con pago): {reservation3.id} - {reservation3.status}")
    
    return reservation1, reservation2, reservation3

def create_test_payment(reservation):
    """Crear un pago de prueba para una reserva"""
    print(f"💳 Creando pago para reserva {reservation.id}...")
    
    # Crear método de pago
    payment_method, created = PaymentMethod.objects.get_or_create(
        name='Efectivo',
        defaults={'is_active': True}
    )
    
    # Crear pago
    from apps.reservations.models import Payment
    payment, created = Payment.objects.get_or_create(
        reservation=reservation,
        amount=Decimal('60.00'),  # 30% de $200
        defaults={
            'method': payment_method,
            'status': 'completed',
            'created_by': reservation.created_by
        }
    )
    print(f"✅ Pago creado: {payment.id} - ${payment.amount}")
    return payment

def test_auto_cancel_functionality():
    """Probar la funcionalidad de auto-cancelación"""
    print("🧪 Iniciando prueba de funcionalidad de auto-cancelación...")
    
    try:
        # Crear datos de prueba
        hotel, room, payment_policy, user = create_test_data()
        
        # Crear reservas de prueba
        reservation1, reservation2, reservation3 = create_test_reservations(hotel, room, user)
        
        # Crear pago para la reserva 3 (para que NO se cancele)
        create_test_payment(reservation3)
        
        print(f"\n📊 Estado inicial de las reservas:")
        print(f"  - Reserva {reservation1.id}: {reservation1.status} (sin pago, depósito vencido)")
        print(f"  - Reserva {reservation2.id}: {reservation2.status} (sin pago, depósito válido)")
        print(f"  - Reserva {reservation3.id}: {reservation3.status} (con pago, depósito vencido)")
        
        print(f"\n🏨 Estado inicial de la habitación:")
        print(f"  - Habitación {room.id}: {room.status}")
        
        # Ejecutar la tarea de auto-cancelación
        print(f"\n🔄 Ejecutando tarea de auto-cancelación...")
        result = auto_cancel_pending_deposits()
        print(f"✅ Resultado: {result}")
        
        # Verificar resultados
        print(f"\n📊 Estado final de las reservas:")
        reservation1.refresh_from_db()
        reservation2.refresh_from_db()
        reservation3.refresh_from_db()
        
        print(f"  - Reserva {reservation1.id}: {reservation1.status} (debería ser CANCELLED)")
        print(f"  - Reserva {reservation2.id}: {reservation2.status} (debería seguir PENDING)")
        print(f"  - Reserva {reservation3.id}: {reservation3.status} (debería seguir PENDING)")
        
        print(f"\n🏨 Estado final de la habitación:")
        room.refresh_from_db()
        print(f"  - Habitación {room.id}: {room.status}")
        
        # Verificar logs de cambio
        print(f"\n📝 Logs de cambio:")
        logs = ReservationChangeLog.objects.filter(reservation__in=[reservation1, reservation2, reservation3])
        for log in logs:
            print(f"  - Reserva {log.reservation.id}: {log.event} - {log.notes}")
        
        # Verificar resultados esperados
        success = True
        if reservation1.status != ReservationStatus.CANCELLED:
            print(f"❌ ERROR: Reserva {reservation1.id} debería estar CANCELLED")
            success = False
        
        if reservation2.status != ReservationStatus.PENDING:
            print(f"❌ ERROR: Reserva {reservation2.id} debería seguir PENDING")
            success = False
        
        if reservation3.status != ReservationStatus.PENDING:
            print(f"❌ ERROR: Reserva {reservation3.id} debería seguir PENDING (tiene pago)")
            success = False
        
        if success:
            print(f"\n🎉 ¡PRUEBA EXITOSA! La funcionalidad funciona correctamente.")
        else:
            print(f"\n❌ PRUEBA FALLIDA! Hay errores en la funcionalidad.")
        
        return success
        
    except Exception as e:
        print(f"❌ ERROR durante la prueba: {e}")
        import traceback
        traceback.print_exc()
        return False

def cleanup_test_data():
    """Limpiar datos de prueba"""
    print(f"\n🧹 Limpiando datos de prueba...")
    
    try:
        # Eliminar reservas de prueba
        Reservation.objects.filter(guests_data__name__in=['Juan Pérez', 'María García', 'Carlos López']).delete()
        print("✅ Reservas de prueba eliminadas")
        
        # Eliminar habitación de prueba
        Room.objects.filter(name="Habitación 101").delete()
        print("✅ Habitación de prueba eliminada")
        
        # Eliminar hotel de prueba
        Hotel.objects.filter(name="Hotel de Prueba Auto-Cancel").delete()
        print("✅ Hotel de prueba eliminado")
        
        # Eliminar política de pago de prueba
        PaymentPolicy.objects.filter(name="Política de Prueba").delete()
        print("✅ Política de pago de prueba eliminada")
        
        print("✅ Limpieza completada")
        
    except Exception as e:
        print(f"⚠️ Error durante la limpieza: {e}")

if __name__ == "__main__":
    print("🚀 Iniciando prueba de funcionalidad de auto-cancelación...")
    print("=" * 60)
    
    success = test_auto_cancel_functionality()
    
    print("=" * 60)
    if success:
        print("🎉 ¡PRUEBA COMPLETADA EXITOSAMENTE!")
    else:
        print("❌ PRUEBA FALLIDA!")
    
    # Preguntar si limpiar datos
    response = input("\n¿Desea limpiar los datos de prueba? (s/n): ")
    if response.lower() in ['s', 'si', 'sí', 'y', 'yes']:
        cleanup_test_data()
    else:
        print("ℹ️ Datos de prueba conservados para inspección manual.")

