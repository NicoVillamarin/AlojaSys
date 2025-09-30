"""
Configuración para los tests automatizados
"""
import os
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

class TestConfig:
    # URLs de la aplicación
    FRONTEND_URL = "http://localhost:5173"
    BACKEND_URL = "http://localhost:8000"
    
    # Credenciales de prueba (ajustar según tu sistema de auth)
    TEST_USERNAME = "admin"
    TEST_PASSWORD = "admin123"
    
    # Configuración del navegador
    BROWSER = "chrome"  # chrome, firefox, edge
    HEADLESS = False  # True para ejecutar sin interfaz gráfica
    WINDOW_SIZE = (1920, 1080)
    
    # Timeouts
    IMPLICIT_WAIT = 10
    EXPLICIT_WAIT = 20
    
    # Datos de prueba
    TEST_HOTELS = [
        {
            "id": 1,
            "name": "Hotel Test 1",
            "city": "Bogotá"
        },
        {
            "id": 2, 
            "name": "Hotel Test 2",
            "city": "Medellín"
        }
    ]
    
    # Datos de reservas de prueba
    TEST_RESERVATIONS = [
        {
            "hotel_id": 1,
            "room_id": 1,
            "guest_name": "Juan Pérez",
            "guest_email": "juan@test.com",
            "check_in": "2024-01-15",
            "check_out": "2024-01-17",
            "guests": 2
        },
        {
            "hotel_id": 2,
            "room_id": 2, 
            "guest_name": "María García",
            "guest_email": "maria@test.com",
            "check_in": "2024-01-16",
            "check_out": "2024-01-18",
            "guests": 1
        }
    ]
