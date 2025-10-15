#!/usr/bin/env python
"""
Script para probar la API de calendario y comparar con la API de habitaciones
"""
import os
import sys
import django
import requests
import json
from datetime import date, timedelta

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'hotel.settings')
django.setup()

from django.test import Client
from django.contrib.auth import get_user_model
from apps.core.models import Hotel
from apps.rooms.models import Room
from apps.reservations.models import Reservation

User = get_user_model()

def test_calendar_api():
    """Probar la API de calendario"""
    print("🧪 Probando API de Calendario...")
    
    # Crear cliente de prueba
    client = Client()
    
    # Obtener un hotel y usuario para las pruebas
    try:
        hotel = Hotel.objects.first()
        if not hotel:
            print("❌ No hay hoteles en la base de datos")
            return
        
        user = User.objects.first()
        if not user:
            print("❌ No hay usuarios en la base de datos")
            return
        
        # Autenticar
        client.force_login(user)
        
        print(f"✅ Usando hotel: {hotel.name} (ID: {hotel.id})")
        
        # Fechas de prueba (último mes y próximo mes)
        today = date.today()
        start_date = today - timedelta(days=30)
        end_date = today + timedelta(days=30)
        
        print(f"📅 Rango de fechas: {start_date} a {end_date}")
        
        # 1. Probar endpoint de eventos del calendario
        print("\n1️⃣ Probando endpoint de eventos del calendario...")
        response = client.get(f'/api/calendar/events/calendar_events/', {
            'hotel': hotel.id,
            'start_date': start_date.isoformat(),
            'end_date': end_date.isoformat(),
            'include_maintenance': 'true',
            'include_blocks': 'true'
        })
        
        if response.status_code == 200:
            events = response.json()
            print(f"✅ Eventos encontrados: {len(events)}")
            
            # Mostrar algunos eventos
            for i, event in enumerate(events[:5]):
                print(f"   {i+1}. {event.get('title', 'Sin título')} - {event.get('start_date')} a {event.get('end_date')}")
            
            if len(events) > 5:
                print(f"   ... y {len(events) - 5} más")
        else:
            print(f"❌ Error en eventos del calendario: {response.status_code}")
            print(f"   Respuesta: {response.content}")
        
        # 2. Probar vista de habitaciones
        print("\n2️⃣ Probando vista de habitaciones...")
        response = client.get(f'/api/calendar/events/rooms_view/', {
            'hotel': hotel.id,
            'start_date': start_date.isoformat(),
            'end_date': end_date.isoformat()
        })
        
        if response.status_code == 200:
            rooms_data = response.json()
            days = rooms_data.get('days', [])
            print(f"✅ Días procesados: {len(days)}")
            
            if days:
                first_day = days[0]
                rooms_count = len(first_day.get('rooms', []))
                print(f"✅ Habitaciones por día: {rooms_count}")
                
                # Mostrar algunas habitaciones del primer día
                rooms = first_day.get('rooms', [])
                for i, room in enumerate(rooms[:3]):
                    reservation_info = room.get('reservation')
                    if reservation_info:
                        print(f"   {i+1}. {room['room_name']} - OCUPADA: {reservation_info['guest_name']}")
                    else:
                        print(f"   {i+1}. {room['room_name']} - DISPONIBLE")
        else:
            print(f"❌ Error en vista de habitaciones: {response.status_code}")
            print(f"   Respuesta: {response.content}")
        
        # 3. Probar estadísticas
        print("\n3️⃣ Probando estadísticas del calendario...")
        response = client.get(f'/api/calendar/events/stats/', {
            'hotel': hotel.id,
            'start_date': start_date.isoformat(),
            'end_date': end_date.isoformat()
        })
        
        if response.status_code == 200:
            stats = response.json()
            print(f"✅ Estadísticas obtenidas:")
            print(f"   - Total reservas: {stats.get('total_reservations', 0)}")
            print(f"   - Ingresos totales: ${stats.get('total_revenue', 0):.2f}")
            print(f"   - Tasa de ocupación: {stats.get('occupancy_rate', 0):.1f}%")
            print(f"   - Check-ins hoy: {stats.get('check_ins_today', 0)}")
            print(f"   - Check-outs hoy: {stats.get('check_outs_today', 0)}")
        else:
            print(f"❌ Error en estadísticas: {response.status_code}")
            print(f"   Respuesta: {response.content}")
        
        # 4. Comparar con API de habitaciones actual
        print("\n4️⃣ Comparando con API de habitaciones actual...")
        response = client.get(f'/api/rooms/', {
            'hotel': hotel.id
        })
        
        if response.status_code == 200:
            rooms = response.json()
            print(f"✅ Habitaciones encontradas: {len(rooms)}")
            
            # Contar reservas actuales y futuras
            current_reservations = 0
            future_reservations = 0
            
            for room in rooms:
                if room.get('current_reservation'):
                    current_reservations += 1
                future_reservations += len(room.get('future_reservations', []))
            
            print(f"   - Reservas actuales: {current_reservations}")
            print(f"   - Reservas futuras: {future_reservations}")
            print(f"   - Total reservas (API habitaciones): {current_reservations + future_reservations}")
        else:
            print(f"❌ Error en API de habitaciones: {response.status_code}")
        
        # 5. Verificar reservas directamente en la base de datos
        print("\n5️⃣ Verificando reservas en la base de datos...")
        reservations = Reservation.objects.filter(
            hotel=hotel,
            check_in__lte=end_date,
            check_out__gt=start_date
        ).select_related('room')
        
        print(f"✅ Reservas en BD: {reservations.count()}")
        
        # Mostrar algunas reservas
        for i, reservation in enumerate(reservations[:5]):
            print(f"   {i+1}. {reservation.room.name} - {reservation.guest_name} ({reservation.check_in} a {reservation.check_out})")
        
        if reservations.count() > 5:
            print(f"   ... y {reservations.count() - 5} más")
        
        print("\n🎉 Pruebas completadas!")
        
    except Exception as e:
        print(f"❌ Error durante las pruebas: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_calendar_api()
