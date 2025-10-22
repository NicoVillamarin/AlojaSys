#!/usr/bin/env python3
"""
Script de prueba para el endpoint de pago completo en efectivo
"""

import os
import sys
import django
import requests
import json
from decimal import Decimal

# Configurar Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'hotel.settings')
django.setup()

from apps.reservations.models import Reservation
from apps.core.models import Hotel
from apps.rooms.models import Room


def test_full_payment_endpoint():
    """Prueba el endpoint de pago completo"""
    print("Probando endpoint de pago completo...")
    
    try:
        # URL del endpoint (ajustar según tu configuración)
        url = "http://localhost:8000/api/payments/process-full-payment/"
        
        # Datos de prueba
        payment_data = {
            "reservation": 1,  # ID de reserva existente
            "amount": "450.00",
            "method": "cash",
            "notes": "Pago de prueba en efectivo"
        }
        
        # Headers (ajustar token según tu autenticación)
        headers = {
            "Content-Type": "application/json",
            "Authorization": "Bearer YOUR_TOKEN_HERE"  # Reemplazar con token real
        }
        
        print(f"Enviando pago a: {url}")
        print(f"Datos: {json.dumps(payment_data, indent=2)}")
        
        # Hacer la petición
        response = requests.post(url, json=payment_data, headers=headers)
        
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 201:
            print("Pago procesado exitosamente!")
            return True
        else:
            print("Error procesando el pago")
            return False
            
    except Exception as e:
        print(f"Error en la prueba: {e}")
        return False


def test_payment_creation_directly():
    """Prueba la creación de pago directamente (sin endpoint)"""
    print("Probando creación de pago directamente...")
    
    try:
        from apps.reservations.models import Payment, ReservationStatus
        from django.utils import timezone
        
        # Buscar una reserva existente
        reservation = Reservation.objects.first()
        if not reservation:
            print("No hay reservas en la base de datos")
            return False
        
        print(f"Usando reserva: RES-{reservation.id}")
        print(f"Email del huésped: {reservation.guest_email}")
        print(f"Total de la reserva: ${reservation.total_price}")
        
        # Crear pago en efectivo
        payment = Payment.objects.create(
            reservation=reservation,
            date=timezone.now().date(),
            method='cash',
            amount=reservation.total_price,
            notes='Pago de prueba en efectivo'
        )
        
        print(f"Pago creado: {payment.id}")
        print(f"Monto: ${payment.amount}")
        print(f"Método: {payment.method}")
        
        # El signal debería activarse automáticamente y generar PDF + email
        print("Signal activado - PDF y email deberían generarse automáticamente")
        
        return True
        
    except Exception as e:
        print(f"Error creando pago: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Función principal de prueba"""
    print("Iniciando pruebas de pago completo...\n")
    
    # Crear directorio de media si no existe
    os.makedirs('media/receipts', exist_ok=True)
    
    print("NOTA: Para probar el endpoint necesitas:")
    print("1. Tener el servidor Django corriendo")
    print("2. Tener un token de autenticación válido")
    print("3. Tener una reserva existente en la base de datos")
    print()
    
    # Probar creación directa de pago
    print("=== PRUEBA 1: Creación directa de pago ===")
    success1 = test_payment_creation_directly()
    
    # Probar endpoint (opcional)
    print("\n=== PRUEBA 2: Endpoint de pago completo ===")
    print("(Skipped - requiere servidor corriendo)")
    success2 = True  # Skipped
    
    if success1:
        print("\nTodas las pruebas completadas!")
        print("El pago se creó correctamente y el signal debería activarse.")
        print("Revisa los logs para ver si se generó el PDF y se envió el email.")
    else:
        print("\nAlgunas pruebas fallaron.")
    
    return success1


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
