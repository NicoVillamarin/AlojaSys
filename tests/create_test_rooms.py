#!/usr/bin/env python3
"""
Script para crear 40 habitaciones de prueba en el Hotel Test (ID: 3)
Este script está diseñado específicamente para testing automatizado
"""

import requests
import json
import time
from datetime import datetime

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

def create_room(token, room_data):
    """Crear una habitación"""
    headers = {"Authorization": f"Bearer {token}"}
    
    response = requests.post(f"{BACKEND_URL}/api/rooms/", 
                           json=room_data, 
                           headers=headers)
    
    if response.status_code == 201:
        return True, response.json()
    else:
        return False, response.text

def generate_room_data(room_number, floor, room_type, base_price, capacity):
    """Generar datos de una habitación"""
    return {
        "hotel": HOTEL_ID,
        "name": f"Habitación {room_number}",
        "number": room_number,
        "floor": floor,
        "room_type": room_type,
        "base_price": base_price,
        "capacity": capacity,
        "max_capacity": capacity,
        "extra_guest_fee": 0,
        "is_active": True
    }

def create_test_rooms():
    """Crear 40 habitaciones de prueba"""
    print("[HOTEL] Creando 40 habitaciones de prueba para Hotel Test")
    print("=" * 60)
    
    # Obtener token
    token = get_auth_token()
    if not token:
        return False
    
    # Configuración de habitaciones por piso
    rooms_config = [
        # Piso 1 - Habitaciones estándar (1-10)
        {"range": (1, 10), "floor": 1, "type": "single", "price": 80000, "capacity": 1},
        # Piso 2 - Habitaciones dobles (11-20)
        {"range": (11, 20), "floor": 2, "type": "double", "price": 120000, "capacity": 2},
        # Piso 3 - Habitaciones triples (21-30)
        {"range": (21, 30), "floor": 3, "type": "triple", "price": 150000, "capacity": 3},
        # Piso 4 - Suites (31-40)
        {"range": (31, 40), "floor": 4, "type": "suite", "price": 250000, "capacity": 4},
    ]
    
    created_rooms = []
    failed_rooms = []
    
    for config in rooms_config:
        start, end = config["range"]
        floor = config["floor"]
        room_type = config["type"]
        price = config["price"]
        capacity = config["capacity"]
        
        print(f"\n[PISO {floor}] Creando habitaciones del piso {floor} ({room_type})...")
        
        for room_number in range(start, end + 1):
            room_data = generate_room_data(room_number, floor, room_type, price, capacity)
            
            success, result = create_room(token, room_data)
            
            if success:
                created_rooms.append({
                    "number": room_number,
                    "floor": floor,
                    "type": room_type,
                    "name": result["name"]
                })
                print(f"  [OK] Habitacion {room_number} creada")
            else:
                failed_rooms.append({
                    "number": room_number,
                    "error": result
                })
                print(f"  [ERROR] Error creando habitacion {room_number}: {result}")
            
            # Pequeña pausa para no sobrecargar el servidor
            time.sleep(0.1)
    
    # Resumen
    print("\n" + "=" * 60)
    print("[RESUMEN] RESUMEN DE CREACION DE HABITACIONES")
    print("=" * 60)
    print(f"[OK] Habitaciones creadas exitosamente: {len(created_rooms)}")
    print(f"[ERROR] Habitaciones con error: {len(failed_rooms)}")
    
    if created_rooms:
        print(f"\n[HOTEL] Habitaciones creadas en Hotel Test (ID: {HOTEL_ID}):")
        for room in created_rooms:
            print(f"  - {room['name']} (Piso {room['floor']}, {room['type']})")
    
    if failed_rooms:
        print(f"\n[ERROR] Errores encontrados:")
        for room in failed_rooms:
            print(f"  - Habitacion {room['number']}: {room['error']}")
    
    # Crear archivo de datos para testing
    create_test_data_file(created_rooms)
    
    return len(failed_rooms) == 0

def create_test_data_file(rooms):
    """Crear archivo con datos de las habitaciones para testing"""
    test_data = {
        "hotel_id": HOTEL_ID,
        "hotel_name": "Hotel Test",
        "rooms": rooms,
        "created_at": datetime.now().isoformat(),
        "description": "Datos de prueba para testing automatizado"
    }
    
    with open("test_data/rooms_data.json", "w", encoding="utf-8") as f:
        json.dump(test_data, f, indent=2, ensure_ascii=False)
    
    print(f"\n[FILE] Datos guardados en: test_data/rooms_data.json")

def verify_rooms_created(token):
    """Verificar que las habitaciones se crearon correctamente"""
    print("\n[VERIFY] Verificando habitaciones creadas...")
    
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{BACKEND_URL}/api/rooms/?hotel={HOTEL_ID}", headers=headers)
    
    if response.status_code == 200:
        rooms = response.json()["results"]
        print(f"[OK] Total de habitaciones en Hotel Test: {len(rooms)}")
        
        # Agrupar por tipo
        by_type = {}
        for room in rooms:
            room_type = room["room_type"]
            if room_type not in by_type:
                by_type[room_type] = 0
            by_type[room_type] += 1
        
        print("[STATS] Distribucion por tipo:")
        for room_type, count in by_type.items():
            print(f"  - {room_type}: {count} habitaciones")
        
        return True
    else:
        print(f"[ERROR] Error verificando habitaciones: {response.text}")
        return False

def main():
    """Función principal"""
    print("[SCRIPT] Script de creacion de habitaciones de prueba")
    print("=" * 60)
    print(f"[HOTEL] Hotel: Hotel Test (ID: {HOTEL_ID})")
    print(f"[ROOMS] Habitaciones a crear: 40")
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
    
    # Crear habitaciones
    success = create_test_rooms()
    
    if success:
        print("\n[SUCCESS] Todas las habitaciones se crearon exitosamente!")
        print("[TEST] Las habitaciones estan listas para testing automatizado")
        
        # Verificar creación
        token = get_auth_token()
        if token:
            verify_rooms_created(token)
    else:
        print("\n[WARNING] Algunas habitaciones no se pudieron crear")
        print("[TIP] Revisa los errores anteriores")
    
    return success

if __name__ == "__main__":
    main()
