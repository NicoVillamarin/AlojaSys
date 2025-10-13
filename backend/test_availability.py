#!/usr/bin/env python
import os
import sys
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'hotel.settings')
os.environ.setdefault('USE_SQLITE', 'True')
django.setup()

from apps.reservations.tasks import sync_room_occupancy_for_today
from apps.rooms.models import Room
from apps.reservations.models import Reservation

print("Ejecutando tarea de sincronización de ocupación...")
try:
    sync_room_occupancy_for_today()
    print("✅ Tarea ejecutada exitosamente")
    
    # Mostrar estado de las habitaciones
    print("\nEstado de las habitaciones:")
    for room in Room.objects.filter(is_active=True)[:5]:
        print(f"  {room.name}: {room.status}")
        
    # Mostrar reservas activas
    print("\nReservas activas:")
    for res in Reservation.objects.filter(status='check_in')[:5]:
        print(f"  Reserva {res.id}: {res.room.name} - {res.check_in} a {res.check_out}")
        
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
