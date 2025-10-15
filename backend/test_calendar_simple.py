#!/usr/bin/env python
"""
Script simple para probar la API de calendario
"""
import requests
import json
from datetime import date, timedelta

def test_calendar_api():
    """Probar la API de calendario directamente"""
    base_url = "http://localhost:8000"
    
    # Fechas de prueba
    today = date.today()
    start_date = today - timedelta(days=30)
    end_date = today + timedelta(days=30)
    
    print("🧪 Probando API de Calendario...")
    print(f"📅 Rango: {start_date} a {end_date}")
    
    # 1. Probar endpoint de eventos del calendario
    print("\n1️⃣ Probando /api/calendar/events/calendar_events/")
    try:
        response = requests.get(f"{base_url}/api/calendar/events/calendar_events/", params={
            'hotel': 1,  # Asumiendo que hay un hotel con ID 1
            'start_date': start_date.isoformat(),
            'end_date': end_date.isoformat(),
            'include_maintenance': 'true',
            'include_blocks': 'true'
        })
        
        if response.status_code == 200:
            events = response.json()
            print(f"✅ Eventos encontrados: {len(events)}")
            
            # Mostrar algunos eventos
            for i, event in enumerate(events[:3]):
                print(f"   {i+1}. {event.get('title', 'Sin título')} - {event.get('start_date')} a {event.get('end_date')}")
                print(f"      Tipo: {event.get('event_type')} | Habitación: {event.get('room_name')}")
        else:
            print(f"❌ Error: {response.status_code}")
            print(f"   Respuesta: {response.text}")
    except Exception as e:
        print(f"❌ Error de conexión: {e}")
    
    # 2. Probar estadísticas
    print("\n2️⃣ Probando /api/calendar/events/stats/")
    try:
        response = requests.get(f"{base_url}/api/calendar/events/stats/", params={
            'hotel': 1,
            'start_date': start_date.isoformat(),
            'end_date': end_date.isoformat()
        })
        
        if response.status_code == 200:
            stats = response.json()
            print(f"✅ Estadísticas obtenidas:")
            print(f"   - Total reservas: {stats.get('total_reservations', 0)}")
            print(f"   - Ingresos: ${stats.get('total_revenue', 0):.2f}")
            print(f"   - Ocupación: {stats.get('occupancy_rate', 0):.1f}%")
        else:
            print(f"❌ Error: {response.status_code}")
    except Exception as e:
        print(f"❌ Error de conexión: {e}")
    
    # 3. Comparar con API de habitaciones
    print("\n3️⃣ Comparando con API de habitaciones...")
    try:
        response = requests.get(f"{base_url}/api/rooms/", params={'hotel': 1})
        
        if response.status_code == 200:
            rooms = response.json()
            print(f"✅ Habitaciones encontradas: {len(rooms)}")
            
            # Contar reservas
            current_reservations = sum(1 for room in rooms if room.get('current_reservation'))
            future_reservations = sum(len(room.get('future_reservations', [])) for room in rooms)
            
            print(f"   - Reservas actuales: {current_reservations}")
            print(f"   - Reservas futuras: {future_reservations}")
            print(f"   - Total: {current_reservations + future_reservations}")
        else:
            print(f"❌ Error: {response.status_code}")
    except Exception as e:
        print(f"❌ Error de conexión: {e}")
    
    print("\n🎉 Pruebas completadas!")

if __name__ == "__main__":
    test_calendar_api()
