#!/usr/bin/env python3
"""
Script para crear reservas de prueba en el Hotel Test
Utiliza las 40 habitaciones creadas para generar reservas de testing
"""

import requests
import json
import time
from datetime import datetime, timedelta
import random

# Configuración
BACKEND_URL = "http://localhost:8000"
HOTEL_ID = 35  # Hotel Test
USERNAME = "admin"
PASSWORD = "admin123"

def get_auth_token():
    """Obtener token de autenticación"""
    print("[AUTH] Obteniendo token de autenticacion...")
    
    response = requests.post(f"{BACKEND_URL}/api/token/", json={
        "username": USERNAME,
        "password": PASSWORD
    })
    
    if response.status_code == 200:
        token = response.json()["access"]
        print("[OK] Token obtenido correctamente")
        return token
    else:
        print(f"[ERROR] Error obteniendo token: {response.text}")
        return None

def get_rooms(token):
    """Obtener habitaciones del Hotel Test"""
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{BACKEND_URL}/api/rooms/?hotel={HOTEL_ID}", headers=headers)
    
    if response.status_code == 200:
        rooms = response.json()["results"]
        print(f"[ROOMS] Encontradas {len(rooms)} habitaciones en Hotel Test")
        return rooms
    else:
        print(f"[ERROR] Error obteniendo habitaciones: {response.text}")
        return []

def create_reservation(token, reservation_data):
    """Crear una reserva"""
    headers = {"Authorization": f"Bearer {token}"}
    
    response = requests.post(f"{BACKEND_URL}/api/reservations/", 
                           json=reservation_data, 
                           headers=headers)
    
    if response.status_code == 201:
        return True, response.json()
    else:
        return False, response.text

def generate_guest_data():
    """Generar datos de huésped aleatorios"""
    first_names = ["Juan", "María", "Carlos", "Ana", "Luis", "Carmen", "Pedro", "Laura", "Diego", "Sofia"]
    last_names = ["García", "Rodríguez", "Martínez", "López", "González", "Pérez", "Sánchez", "Ramírez", "Cruz", "Flores"]
    
    first_name = random.choice(first_names)
    last_name = random.choice(last_names)
    
    return {
        "name": f"{first_name} {last_name}",
        "email": f"{first_name.lower()}.{last_name.lower()}@test.com",
        "phone": f"3{random.randint(10000000, 99999999)}",
        "document": f"{random.randint(10000000, 99999999)}",
        "is_primary": True
    }

def generate_reservation_data(room, check_in_date, check_out_date, guests_count):
    """Generar datos de reserva"""
    guests_data = []
    
    # Huésped principal
    guests_data.append(generate_guest_data())
    
    # Huéspedes adicionales
    for i in range(guests_count - 1):
        guest = generate_guest_data()
        guest["is_primary"] = False
        guests_data.append(guest)
    
    # Calcular precio total (precio base * noches)
    nights = (check_out_date - check_in_date).days
    total_price = float(room["base_price"]) * nights
    
    return {
        "hotel": HOTEL_ID,
        "room": room["id"],
        "guests": guests_count,
        "guests_data": guests_data,
        "check_in": check_in_date.strftime("%Y-%m-%d"),
        "check_out": check_out_date.strftime("%Y-%m-%d"),
        "status": "confirmed",
        "total_price": total_price,
        "notes": f"Reserva de prueba generada automáticamente - {room['name']}"
    }

def create_test_reservations():
    """Crear reservas de prueba"""
    print("[RESERVATIONS] Creando reservas de prueba para Hotel Test")
    print("=" * 60)
    
    # Obtener token
    token = get_auth_token()
    if not token:
        return False
    
    # Obtener habitaciones
    rooms = get_rooms(token)
    if not rooms:
        return False
    
    # Generar fechas de reserva
    base_date = datetime.now() + timedelta(days=1)  # Mañana
    reservations_data = []
    
    # Crear 20 reservas de prueba
    for i in range(20):
        room = random.choice(rooms)
        
        # Fechas aleatorias en los próximos 30 días
        check_in = base_date + timedelta(days=random.randint(0, 30))
        check_out = check_in + timedelta(days=random.randint(1, 7))  # 1-7 noches
        
        # Número de huéspedes según capacidad de la habitación
        max_guests = room["max_capacity"]
        guests_count = random.randint(1, max_guests)
        
        reservation_data = generate_reservation_data(room, check_in, check_out, guests_count)
        reservations_data.append(reservation_data)
    
    # Crear reservas
    created_reservations = []
    failed_reservations = []
    
    print(f"[CREATE] Creando {len(reservations_data)} reservas...")
    
    for i, reservation_data in enumerate(reservations_data, 1):
        success, result = create_reservation(token, reservation_data)
        
        if success:
            created_reservations.append({
                "id": result["id"],
                "guest": result["guests_data"][0]["name"],
                "room": result["room_name"],
                "check_in": result["check_in"],
                "check_out": result["check_out"],
                "status": result["status"]
            })
            print(f"  [OK] Reserva {i} creada - {result['guests_data'][0]['name']} en {result['room_name']}")
        else:
            failed_reservations.append({
                "index": i,
                "error": result
            })
            print(f"  [ERROR] Error creando reserva {i}: {result}")
        
        # Pequeña pausa para no sobrecargar el servidor
        time.sleep(0.1)
    
    # Resumen
    print("\n" + "=" * 60)
    print("[RESUMEN] RESUMEN DE CREACION DE RESERVAS")
    print("=" * 60)
    print(f"[OK] Reservas creadas exitosamente: {len(created_reservations)}")
    print(f"[ERROR] Reservas con error: {len(failed_reservations)}")
    
    if created_reservations:
        print(f"\n[RESERVATIONS] Reservas creadas en Hotel Test:")
        for res in created_reservations[:10]:  # Mostrar solo las primeras 10
            print(f"  - {res['guest']} en {res['room']} ({res['check_in']} - {res['check_out']})")
        if len(created_reservations) > 10:
            print(f"  ... y {len(created_reservations) - 10} más")
    
    if failed_reservations:
        print(f"\n[ERROR] Errores encontrados:")
        for res in failed_reservations[:5]:  # Mostrar solo los primeros 5 errores
            print(f"  - Reserva {res['index']}: {res['error']}")
        if len(failed_reservations) > 5:
            print(f"  ... y {len(failed_reservations) - 5} errores más")
    
    # Crear archivo de datos para testing
    create_reservations_data_file(created_reservations)
    
    return len(failed_reservations) == 0

def create_reservations_data_file(reservations):
    """Crear archivo con datos de las reservas para testing"""
    test_data = {
        "hotel_id": HOTEL_ID,
        "hotel_name": "Hotel Test",
        "reservations": reservations,
        "created_at": datetime.now().isoformat(),
        "description": "Reservas de prueba para testing automatizado"
    }
    
    with open("test_data/reservations_data.json", "w", encoding="utf-8") as f:
        json.dump(test_data, f, indent=2, ensure_ascii=False)
    
    print(f"\n[FILE] Datos guardados en: test_data/reservations_data.json")

def main():
    """Función principal"""
    print("[SCRIPT] Script de creacion de reservas de prueba")
    print("=" * 60)
    print(f"[HOTEL] Hotel: Hotel Test (ID: {HOTEL_ID})")
    print(f"[RESERVATIONS] Reservas a crear: 20")
    print(f"[DATE] Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    # Verificar que el backend esté funcionando
    try:
        response = requests.get(f"{BACKEND_URL}/api/hotels/")
        if response.status_code != 401:  # 401 es esperado sin token
            print("[ERROR] El backend no esta funcionando correctamente")
            print("[TIP] Asegurate de ejecutar: docker-compose up -d")
            return False
    except requests.exceptions.ConnectionError:
        print("[ERROR] No se puede conectar al backend")
        print("[TIP] Asegurate de ejecutar: docker-compose up -d")
        return False
    
    # Crear reservas
    success = create_test_reservations()
    
    if success:
        print("\n[SUCCESS] Todas las reservas se crearon exitosamente!")
        print("[TEST] Las reservas estan listas para testing automatizado")
    else:
        print("\n[WARNING] Algunas reservas no se pudieron crear")
        print("[TIP] Revisa los errores anteriores")
    
    return success

if __name__ == "__main__":
    main()
