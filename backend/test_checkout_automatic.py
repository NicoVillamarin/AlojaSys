#!/usr/bin/env python
import os
import sys
import django
from datetime import date, time, datetime, timedelta

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'hotel.settings')
os.environ.setdefault('USE_SQLITE', 'True')
django.setup()

from apps.reservations.tasks import process_automatic_checkouts
from apps.reservations.models import Reservation, ReservationStatus
from apps.core.models import Hotel
from apps.rooms.models import Room, RoomStatus
from django.utils import timezone

def test_automatic_checkout():
    print("🧪 Probando checkout automático...")
    
    # Crear un hotel de prueba si no existe
    hotel, created = Hotel.objects.get_or_create(
        name="Hotel Prueba Checkout",
        defaults={
            'check_out_time': time(11, 0),  # 11:00 AM
            'check_in_time': time(15, 0),   # 3:00 PM
            'timezone': 'America/Argentina/Buenos_Aires'
        }
    )
    
    if created:
        print(f"✅ Hotel creado: {hotel.name}")
    else:
        print(f"📋 Hotel existente: {hotel.name}")
    
    print(f"🕐 Horario de checkout configurado: {hotel.check_out_time}")
    
    # Crear una habitación de prueba si no existe
    room, created = Room.objects.get_or_create(
        name="Habitación Prueba Checkout",
        hotel=hotel,
        defaults={
            'room_type': 'standard',
            'max_capacity': 2,
            'is_active': True
        }
    )
    
    if created:
        print(f"✅ Habitación creada: {room.name}")
    else:
        print(f"📋 Habitación existente: {room.name}")
    
    # Crear una reserva de prueba que debería hacer checkout hoy
    today = date.today()
    yesterday = today - timedelta(days=1)
    
    reservation, created = Reservation.objects.get_or_create(
        room=room,
        check_in=yesterday,
        check_out=today,
        defaults={
            'status': ReservationStatus.CHECK_IN,
            'guests': 2,
            'guests_data': [{'name': 'Huésped Prueba', 'is_primary': True}],
            'total_amount': 100.00,
            'channel': 'direct'
        }
    )
    
    if created:
        print(f"✅ Reserva creada: {reservation.id} - Check-in: {reservation.check_in} - Check-out: {reservation.check_out}")
    else:
        print(f"📋 Reserva existente: {reservation.id} - Estado: {reservation.status}")
    
    # Mostrar estado actual
    print(f"\n📊 Estado actual:")
    print(f"  - Reserva: {reservation.status}")
    print(f"  - Habitación: {room.status}")
    print(f"  - Hora actual: {timezone.now().time()}")
    print(f"  - Hora de checkout del hotel: {hotel.check_out_time}")
    
    # Ejecutar la tarea de checkout automático
    print(f"\n🚀 Ejecutando tarea de checkout automático...")
    try:
        result = process_automatic_checkouts()
        print(f"✅ Resultado: {result}")
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    
    # Mostrar estado después de la ejecución
    reservation.refresh_from_db()
    room.refresh_from_db()
    
    print(f"\n📊 Estado después de la ejecución:")
    print(f"  - Reserva: {reservation.status}")
    print(f"  - Habitación: {room.status}")
    
    if reservation.status == ReservationStatus.CHECK_OUT:
        print("🎉 ¡Checkout automático funcionó correctamente!")
    else:
        print("⚠️ El checkout automático no se ejecutó (puede ser que aún no sea la hora configurada)")

if __name__ == "__main__":
    test_automatic_checkout()
