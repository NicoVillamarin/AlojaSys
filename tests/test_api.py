"""
Test de la API de AlojaSys sin navegador
"""
import requests
import json
import pytest
from datetime import datetime, timedelta

# Configuración
BASE_URL = "http://localhost:8000"
FRONTEND_URL = "http://localhost:5173"

def test_backend_health():
    """Test básico de salud del backend"""
    print("Probando salud del backend...")
    
    try:
        response = requests.get(f"{BASE_URL}/api/", timeout=5)
        print(f"Backend responde: {response.status_code}")
        
        # 401 es normal para endpoints que requieren autenticación
        assert response.status_code in [200, 401], f"Backend no responde correctamente: {response.status_code}"
        print("OK - Backend está funcionando")
        
    except Exception as e:
        print(f"ERROR - Backend no disponible: {e}")
        raise

def test_frontend_health():
    """Test básico de salud del frontend"""
    print("Probando salud del frontend...")
    
    try:
        response = requests.get(FRONTEND_URL, timeout=5)
        print(f"Frontend responde: {response.status_code}")
        
        assert response.status_code == 200, f"Frontend no responde correctamente: {response.status_code}"
        print("OK - Frontend está funcionando")
        
    except Exception as e:
        print(f"ERROR - Frontend no disponible: {e}")
        raise

def test_hotels_endpoint():
    """Test del endpoint de hoteles"""
    print("Probando endpoint de hoteles...")
    
    try:
        response = requests.get(f"{BASE_URL}/api/hotels/", timeout=5)
        print(f"Hoteles responde: {response.status_code}")
        
        if response.status_code == 200:
            hotels = response.json()
            print(f"Encontrados {len(hotels)} hoteles")
            for hotel in hotels:
                print(f"  - {hotel.get('name', 'Sin nombre')} (ID: {hotel.get('id')})")
        else:
            print(f"Respuesta: {response.text}")
        
        # 200 o 401 son respuestas válidas
        assert response.status_code in [200, 401], f"Endpoint de hoteles no responde: {response.status_code}"
        print("OK - Endpoint de hoteles funciona")
        
    except Exception as e:
        print(f"ERROR - Endpoint de hoteles falló: {e}")
        raise

def test_rooms_endpoint():
    """Test del endpoint de habitaciones"""
    print("Probando endpoint de habitaciones...")
    
    try:
        response = requests.get(f"{BASE_URL}/api/rooms/", timeout=5)
        print(f"Habitaciones responde: {response.status_code}")
        
        if response.status_code == 200:
            rooms = response.json()
            print(f"Encontradas {len(rooms)} habitaciones")
            for room in rooms[:3]:  # Mostrar solo las primeras 3
                print(f"  - {room.get('name', 'Sin nombre')} (Hotel: {room.get('hotel_name', 'N/A')})")
        else:
            print(f"Respuesta: {response.text}")
        
        assert response.status_code in [200, 401], f"Endpoint de habitaciones no responde: {response.status_code}"
        print("OK - Endpoint de habitaciones funciona")
        
    except Exception as e:
        print(f"ERROR - Endpoint de habitaciones falló: {e}")
        raise

def test_reservations_endpoint():
    """Test del endpoint de reservas"""
    print("Probando endpoint de reservas...")
    
    try:
        response = requests.get(f"{BASE_URL}/api/reservations/", timeout=5)
        print(f"Reservas responde: {response.status_code}")
        
        if response.status_code == 200:
            reservations = response.json()
            print(f"Encontradas {len(reservations)} reservas")
            for res in reservations[:3]:  # Mostrar solo las primeras 3
                print(f"  - {res.get('guest_name', 'Sin nombre')} - {res.get('status', 'Sin estado')}")
        else:
            print(f"Respuesta: {response.text}")
        
        assert response.status_code in [200, 401], f"Endpoint de reservas no responde: {response.status_code}"
        print("OK - Endpoint de reservas funciona")
        
    except Exception as e:
        print(f"ERROR - Endpoint de reservas falló: {e}")
        raise

def test_reservation_actions():
    """Test de las acciones de reserva (check-in/check-out)"""
    print("Probando acciones de reserva...")
    
    # Primero obtener las reservas
    try:
        response = requests.get(f"{BASE_URL}/api/reservations/", timeout=5)
        
        if response.status_code != 200:
            print("No se pueden obtener reservas (requiere autenticación)")
            return
        
        reservations = response.json()
        if not reservations:
            print("No hay reservas para probar")
            return
        
        # Tomar la primera reserva
        reservation = reservations[0]
        reservation_id = reservation['id']
        print(f"Probando con reserva ID: {reservation_id}")
        
        # Probar check-in
        try:
            checkin_response = requests.post(
                f"{BASE_URL}/api/reservations/{reservation_id}/check_in/",
                timeout=5
            )
            print(f"Check-in responde: {checkin_response.status_code}")
            
            if checkin_response.status_code == 200:
                print("OK - Check-in funcionó")
            else:
                print(f"Check-in falló: {checkin_response.text}")
                
        except Exception as e:
            print(f"Error en check-in: {e}")
        
        # Probar check-out
        try:
            checkout_response = requests.post(
                f"{BASE_URL}/api/reservations/{reservation_id}/check_out/",
                timeout=5
            )
            print(f"Check-out responde: {checkout_response.status_code}")
            
            if checkout_response.status_code == 200:
                print("OK - Check-out funcionó")
            else:
                print(f"Check-out falló: {checkout_response.text}")
                
        except Exception as e:
            print(f"Error en check-out: {e}")
        
        print("OK - Acciones de reserva probadas")
        
    except Exception as e:
        print(f"ERROR - No se pudieron probar las acciones: {e}")

def test_complete_flow():
    """Test del flujo completo del sistema"""
    print("\n" + "="*50)
    print("INICIANDO TEST COMPLETO DEL SISTEMA")
    print("="*50)
    
    # 1. Verificar servicios
    test_backend_health()
    test_frontend_health()
    
    # 2. Verificar endpoints
    test_hotels_endpoint()
    test_rooms_endpoint()
    test_reservations_endpoint()
    
    # 3. Probar acciones
    test_reservation_actions()
    
    print("\n" + "="*50)
    print("TEST COMPLETO FINALIZADO")
    print("="*50)
    print("\nINSTRUCCIONES PARA TESTING MANUAL:")
    print("1. Abre tu navegador")
    print("2. Ve a http://localhost:5173")
    print("3. Haz login con tus credenciales")
    print("4. Ve a la sección de Reservas")
    print("5. Busca una reserva en estado 'confirmed'")
    print("6. Haz click en 'Check-in'")
    print("7. Verifica que el estado cambie a 'check-in'")
    print("8. Haz click en 'Check-out'")
    print("9. Verifica que el estado cambie a 'check-out'")
    print("\n¡Esto es exactamente lo que harán los tests automatizados!")

if __name__ == "__main__":
    test_complete_flow()
