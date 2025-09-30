#!/usr/bin/env python3
"""
Script para crear reservas históricas con check-outs del año pasado
Estas reservas permitirán tener datos históricos para métricas y reportes
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
    first_names = ["Juan", "María", "Carlos", "Ana", "Luis", "Carmen", "Pedro", "Laura", "Diego", "Sofia",
                   "Miguel", "Isabel", "Fernando", "Patricia", "Roberto", "Mónica", "Alejandro", "Gabriela",
                   "Andrés", "Valentina", "Sergio", "Natalia", "Ricardo", "Camila", "Javier", "Daniela",
                   "Eduardo", "Andrea", "Mauricio", "Paola", "Felipe", "Sandra", "Cristian", "Claudia",
                   "Sebastián", "Mariana", "David", "Alejandra", "Jorge", "Lorena"]
    
    last_names = ["García", "Rodríguez", "Martínez", "López", "González", "Pérez", "Sánchez", "Ramírez", 
                  "Cruz", "Flores", "Herrera", "Jiménez", "Ruiz", "Díaz", "Moreno", "Álvarez", "Romero",
                  "Torres", "Vargas", "Castillo", "Reyes", "Mendoza", "Guerrero", "Ramos", "Morales",
                  "Herrera", "Medina", "Aguilar", "Vega", "Castro", "Ortiz", "Rubio", "Marín", "Sanz",
                  "Iglesias", "Delgado", "Peña", "Blanco", "Molina", "Navarro"]
    
    first_name = random.choice(first_names)
    last_name = random.choice(last_names)
    
    return {
        "name": f"{first_name} {last_name}",
        "email": f"{first_name.lower()}.{last_name.lower()}@test.com",
        "phone": f"3{random.randint(10000000, 99999999)}",
        "document": f"{random.randint(10000000, 99999999)}",
        "is_primary": True
    }

def generate_reservation_data(room, check_in_date, check_out_date, guests_count, status="check_out"):
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
    
    # Aplicar descuentos aleatorios para datos más realistas
    discount = random.choice([0, 0, 0, 0.05, 0.1, 0.15, 0.2])  # 50% sin descuento, resto con descuentos
    if discount > 0:
        total_price = total_price * (1 - discount)
    
    return {
        "hotel": HOTEL_ID,
        "room": room["id"],
        "guests": guests_count,
        "guests_data": guests_data,
        "check_in": check_in_date.strftime("%Y-%m-%d"),
        "check_out": check_out_date.strftime("%Y-%m-%d"),
        "status": status,
        "total_price": round(total_price, 2),
        "notes": f"Reserva histórica {status} - {room['name']} - {check_in_date.strftime('%Y-%m')}"
    }

def create_historical_reservations():
    """Crear reservas históricas con check-outs del año pasado"""
    print("[HISTORICAL] Creando reservas históricas para métricas")
    print("=" * 60)
    
    # Obtener token
    token = get_auth_token()
    if not token:
        return False
    
    # Obtener habitaciones
    rooms = get_rooms(token)
    if not rooms:
        return False
    
    # Generar fechas del año pasado
    current_year = datetime.now().year
    last_year = current_year - 1
    
    # Crear fechas distribuidas a lo largo del año pasado
    start_date = datetime(last_year, 1, 1).date()
    end_date = datetime(last_year, 12, 31).date()
    
    reservations_data = []
    
    # Crear 50 reservas históricas distribuidas a lo largo del año pasado
    for i in range(50):
        room = random.choice(rooms)
        
        # Generar fecha de check-in aleatoria en el año pasado
        days_diff = (end_date - start_date).days
        random_days = random.randint(0, days_diff)
        check_in = start_date + timedelta(days=random_days)
        
        # Check-out 1-7 días después (estadías más realistas)
        stay_duration = random.choices(
            [1, 2, 3, 4, 5, 6, 7],
            weights=[10, 20, 25, 20, 15, 7, 3],  # Más probabilidad de estadías cortas
            k=1
        )[0]
        check_out = check_in + timedelta(days=stay_duration)
        
        # Asegurar que no se pase del año pasado
        if check_out > end_date:
            check_out = end_date
        
        # Número de huéspedes según capacidad de la habitación
        max_guests = room["max_capacity"]
        
        # Crear pesos dinámicamente según la capacidad máxima
        if max_guests == 1:
            guests_count = 1
        elif max_guests == 2:
            guests_count = random.choices([1, 2], weights=[60, 40], k=1)[0]
        elif max_guests == 3:
            guests_count = random.choices([1, 2, 3], weights=[50, 30, 20], k=1)[0]
        else:  # max_guests >= 4
            guests_count = random.choices([1, 2, 3, 4], weights=[40, 30, 20, 10], k=1)[0]
        
        # Estados de reserva más realistas
        status_weights = {
            "check_out": 0.85,    # 85% check-out exitoso
            "cancelled": 0.10,    # 10% canceladas
            "no_show": 0.05       # 5% no-show
        }
        
        status = random.choices(
            list(status_weights.keys()),
            weights=list(status_weights.values()),
            k=1
        )[0]
        
        reservation_data = generate_reservation_data(room, check_in, check_out, guests_count, status)
        reservations_data.append(reservation_data)
    
    # Crear reservas
    created_reservations = []
    failed_reservations = []
    
    print(f"[CREATE] Creando {len(reservations_data)} reservas históricas...")
    
    for i, reservation_data in enumerate(reservations_data, 1):
        success, result = create_reservation(token, reservation_data)
        
        if success:
            created_reservations.append({
                "id": result["id"],
                "guest": result["guests_data"][0]["name"],
                "room": result["room_name"],
                "check_in": result["check_in"],
                "check_out": result["check_out"],
                "status": result["status"],
                "total_price": result["total_price"]
            })
            print(f"  [OK] Reserva {i} creada - {result['guests_data'][0]['name']} en {result['room_name']} ({result['check_in']} - {result['check_out']}) - {result['status']}")
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
    print("[RESUMEN] RESUMEN DE CREACION DE RESERVAS HISTORICAS")
    print("=" * 60)
    print(f"[OK] Reservas creadas exitosamente: {len(created_reservations)}")
    print(f"[ERROR] Reservas con error: {len(failed_reservations)}")
    
    # Estadísticas por estado
    status_counts = {}
    total_revenue = 0
    for res in created_reservations:
        status = res["status"]
        status_counts[status] = status_counts.get(status, 0) + 1
        if status == "checked_out":
            total_revenue += res["total_price"]
    
    print(f"\n[STATS] Estadísticas por estado:")
    for status, count in status_counts.items():
        print(f"  - {status}: {count} reservas")
    
    print(f"\n[REVENUE] Ingresos totales (solo check-outs): ${total_revenue:,.2f} COP")
    
    if created_reservations:
        print(f"\n[HISTORICAL] Reservas históricas creadas:")
        for res in created_reservations[:10]:  # Mostrar solo las primeras 10
            print(f"  - {res['guest']} en {res['room']} ({res['check_in']} - {res['check_out']}) - {res['status']}")
        if len(created_reservations) > 10:
            print(f"  ... y {len(created_reservations) - 10} más")
    
    if failed_reservations:
        print(f"\n[ERROR] Errores encontrados:")
        for res in failed_reservations[:5]:
            print(f"  - Reserva {res['index']}: {res['error']}")
    
    # Crear archivo de datos para testing
    create_historical_data_file(created_reservations, status_counts, total_revenue)
    
    return len(failed_reservations) == 0

def create_historical_data_file(reservations, status_counts, total_revenue):
    """Crear archivo con datos de las reservas históricas"""
    test_data = {
        "hotel_id": HOTEL_ID,
        "hotel_name": "Hotel Test",
        "year": datetime.now().year - 1,
        "reservations": reservations,
        "statistics": {
            "total_reservations": len(reservations),
            "status_breakdown": status_counts,
            "total_revenue": total_revenue,
            "average_stay_duration": calculate_average_stay(reservations),
            "occupancy_rate": calculate_occupancy_rate(reservations)
        },
        "created_at": datetime.now().isoformat(),
        "description": "Reservas históricas para métricas y reportes"
    }
    
    with open("test_data/historical_reservations_data.json", "w", encoding="utf-8") as f:
        json.dump(test_data, f, indent=2, ensure_ascii=False)
    
    print(f"\n[FILE] Datos guardados en: test_data/historical_reservations_data.json")

def calculate_average_stay(reservations):
    """Calcular duración promedio de estadía"""
    total_nights = 0
    count = 0
    
    for res in reservations:
        if res["status"] == "check_out":
            check_in = datetime.strptime(res["check_in"], "%Y-%m-%d").date()
            check_out = datetime.strptime(res["check_out"], "%Y-%m-%d").date()
            nights = (check_out - check_in).days
            total_nights += nights
            count += 1
    
    return round(total_nights / count, 2) if count > 0 else 0

def calculate_occupancy_rate(reservations):
    """Calcular tasa de ocupación aproximada"""
    # Simplificado: asumir 40 habitaciones disponibles
    total_room_nights = 40 * 365  # 40 habitaciones * 365 días
    occupied_nights = 0
    
    for res in reservations:
        if res["status"] == "check_out":
            check_in = datetime.strptime(res["check_in"], "%Y-%m-%d").date()
            check_out = datetime.strptime(res["check_out"], "%Y-%m-%d").date()
            nights = (check_out - check_in).days
            occupied_nights += nights
    
    return round((occupied_nights / total_room_nights) * 100, 2) if total_room_nights > 0 else 0

def main():
    """Función principal"""
    print("[SCRIPT] Script de creacion de reservas historicas para metricas")
    print("=" * 60)
    print(f"[HOTEL] Hotel: Hotel Test (ID: {HOTEL_ID})")
    print(f"[YEAR] Año: {datetime.now().year - 1}")
    print(f"[RESERVATIONS] Reservas a crear: 50 (distribuidas en el año pasado)")
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
    
    # Crear reservas históricas
    success = create_historical_reservations()
    
    if success:
        print("\n[SUCCESS] Todas las reservas historicas se crearon exitosamente!")
        print("[METRICS] Los datos estan listos para metricas y reportes")
    else:
        print("\n[WARNING] Algunas reservas no se pudieron crear")
        print("[TIP] Revisa los errores anteriores")
    
    return success

if __name__ == "__main__":
    main()
