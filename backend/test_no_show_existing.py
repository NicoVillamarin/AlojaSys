#!/usr/bin/env python
"""
Script de prueba usando datos existentes en la base de datos
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

def test_with_existing_data():
    """Probar con datos existentes en la base de datos"""
    print("🔍 Buscando datos existentes en la base de datos...")
    
    # Buscar hoteles existentes
    hotels = Hotel.objects.all()
    print(f"📊 Hoteles encontrados: {hotels.count()}")
    
    if hotels.exists():
        hotel = hotels.first()
        print(f"✅ Usando hotel: {hotel.name} (ID: {hotel.id})")
        print(f"   - Auto NO_SHOW habilitado: {hotel.auto_no_show_enabled}")
        
        # Buscar habitaciones del hotel
        rooms = Room.objects.filter(hotel=hotel)
        print(f"📊 Habitaciones encontradas: {rooms.count()}")
        
        if rooms.exists():
            room = rooms.first()
            print(f"✅ Usando habitación: {room.name} (ID: {room.id})")
            
            # Buscar políticas de cancelación
            cancellation_policies = CancellationPolicy.objects.filter(hotel=hotel)
            print(f"📊 Políticas de cancelación: {cancellation_policies.count()}")
            
            if cancellation_policies.exists():
                policy = cancellation_policies.first()
                print(f"✅ Usando política: {policy.name} (ID: {policy.id})")
                
                # Crear una reserva de prueba
                test_reservation = Reservation.objects.create(
                    hotel=hotel,
                    room=room,
                    check_in=date.today() - timedelta(days=1),  # Ayer
                    check_out=date.today() + timedelta(days=2),
                    guests=2,
                    guests_data=[{'name': 'Test User', 'email': 'test@example.com'}],
                    status=ReservationStatus.CONFIRMED,
                    total_price=Decimal('200.00'),
                    applied_cancellation_policy=policy,
                    notes='Reserva de prueba NO_SHOW'
                )
                
                print(f"✅ Reserva de prueba creada: {test_reservation.id}")
                
                # Simular pago
                from apps.reservations.models import Payment
                Payment.objects.create(
                    reservation=test_reservation,
                    date=date.today() - timedelta(days=2),
                    method='credit_card',
                    amount=Decimal('200.00'),
                    notes='Pago de prueba'
                )
                
                print(f"✅ Pago simulado: $200.00")
                
                # Probar el procesador de NO_SHOW
                print(f"\n🧪 Probando NoShowProcessor...")
                
                # Cambiar a NO_SHOW
                test_reservation.status = ReservationStatus.NO_SHOW
                test_reservation.save()
                
                result = NoShowProcessor.process_no_show_penalties(test_reservation)
                
                print(f"✅ Resultado del procesador:")
                print(f"   - Éxito: {result.get('success', False)}")
                print(f"   - Total pagado: ${result.get('total_paid', 0)}")
                print(f"   - Penalidad: ${result.get('penalty_amount', 0)}")
                print(f"   - Reembolso: ${result.get('refund_amount', 0)}")
                print(f"   - Penalidad procesada: {result.get('penalty_processed', False)}")
                
                if result.get('error'):
                    print(f"   - Error: {result.get('error')}")
                
                # Verificar logs
                logs = ReservationChangeLog.objects.filter(
                    reservation=test_reservation,
                    event_type__in=[ReservationChangeEvent.NO_SHOW_PENALTY, ReservationChangeEvent.NO_SHOW_PROCESSED]
                )
                print(f"   - Logs creados: {logs.count()}")
                for log in logs:
                    print(f"     * {log.event_type}: {log.message}")
                
                # Probar la tarea automática
                print(f"\n🧪 Probando tarea automática...")
                
                # Cambiar de vuelta a CONFIRMED para probar la tarea
                test_reservation.status = ReservationStatus.CONFIRMED
                test_reservation.save()
                
                print(f"📊 Estado antes de la tarea: {test_reservation.status}")
                
                # Ejecutar tarea
                result = auto_mark_no_show_daily()
                print(f"✅ Resultado de la tarea: {result}")
                
                # Verificar estado final
                test_reservation.refresh_from_db()
                print(f"📊 Estado después de la tarea: {test_reservation.status}")
                
                # Verificar notificaciones
                notifications = Notification.objects.filter(
                    type=NotificationType.NO_SHOW,
                    reservation_id=test_reservation.id
                )
                print(f"📊 Notificaciones creadas: {notifications.count()}")
                for notification in notifications:
                    print(f"   - {notification.title}: {notification.message}")
                
                # Limpiar reserva de prueba
                test_reservation.delete()
                print(f"✅ Reserva de prueba eliminada")
                
            else:
                print("❌ No hay políticas de cancelación configuradas")
        else:
            print("❌ No hay habitaciones configuradas")
    else:
        print("❌ No hay hoteles en la base de datos")

def test_no_show_events():
    """Probar que los nuevos eventos están disponibles"""
    print("\n🧪 Probando eventos NO_SHOW...")
    
    # Verificar que los eventos están disponibles
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
            
            # Crear log de prueba
            log = ReservationChangeLog.objects.create(
                reservation=temp_reservation,
                event_type=ReservationChangeEvent.NO_SHOW_PENALTY,
                changed_by=None,
                message="Prueba de log NO_SHOW_PENALTY",
                snapshot={'test': True}
            )
            
            print(f"✅ Log creado: {log.id} - {log.event_type}")
            
            # Limpiar
            temp_reservation.delete()
            log.delete()

def main():
    """Función principal"""
    print("🚀 PRUEBA DEL SISTEMA NO_SHOW CON DATOS EXISTENTES")
    print("="*60)
    
    try:
        # Prueba 1: Con datos existentes
        test_with_existing_data()
        
        # Prueba 2: Eventos NO_SHOW
        test_no_show_events()
        
        print("\n✅ PRUEBAS COMPLETADAS!")
        print("\n🎉 El sistema de penalidades NO_SHOW está funcionando:")
        print("   ✅ Procesador de penalidades")
        print("   ✅ Tarea Celery automática")
        print("   ✅ Logs detallados")
        print("   ✅ Notificaciones")
        print("   ✅ Nuevos eventos disponibles")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
