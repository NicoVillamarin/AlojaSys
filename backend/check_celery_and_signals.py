#!/usr/bin/env python3
"""
Script para verificar si Celery está corriendo y los signals están registrados
"""

import os
import sys
import django
import subprocess
import time

# Configurar Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'hotel.settings')
django.setup()

from django.conf import settings
from apps.payments.signals import generate_payment_receipt, generate_refund_receipt
from django.db.models.signals import post_save
from apps.reservations.models import Payment


def check_celery_status():
    """Verifica si Celery está corriendo"""
    print("Verificando estado de Celery...")
    
    try:
        # Intentar conectar a Redis (que usa Celery)
        import redis
        r = redis.Redis(host='localhost', port=6379, db=0)
        r.ping()
        print("[OK] Redis está corriendo")
        
        # Verificar si hay workers de Celery
        from celery import current_app
        inspect = current_app.control.inspect()
        active_workers = inspect.active()
        
        if active_workers:
            print(f"[OK] Celery workers activos: {list(active_workers.keys())}")
            return True
        else:
            print("[WARNING] No hay workers de Celery activos")
            return False
            
    except Exception as e:
        print(f"[ERROR] Error verificando Celery: {e}")
        return False


def check_signals_registration():
    """Verifica si los signals están registrados"""
    print("\nVerificando registro de signals...")
    
    try:
        # Verificar si el signal está registrado
        from django.db.models.signals import post_save
        from apps.reservations.models import Payment
        
        # Obtener todos los receivers para el signal post_save de Payment
        receivers = post_save._live_receivers(sender=Payment)
        
        print(f"Receivers registrados para Payment.post_save: {len(receivers)}")
        
        # Buscar nuestro signal específico
        signal_found = False
        for receiver in receivers:
            if hasattr(receiver, '__name__'):
                if receiver.__name__ == 'generate_payment_receipt':
                    print("[OK] Signal generate_payment_receipt está registrado")
                    signal_found = True
                    break
        
        if not signal_found:
            print("[ERROR] Signal generate_payment_receipt NO está registrado")
            return False
        
        return True
        
    except Exception as e:
        print(f"[ERROR] Error verificando signals: {e}")
        return False


def check_email_configuration():
    """Verifica la configuración de email"""
    print("\nVerificando configuración de email...")
    
    try:
        print(f"EMAIL_BACKEND: {settings.EMAIL_BACKEND}")
        print(f"DEFAULT_FROM_EMAIL: {settings.DEFAULT_FROM_EMAIL}")
        
        # Probar envío de email
        from django.core.mail import send_mail
        result = send_mail(
            subject='Test Email - AlojaSys',
            message='Email de prueba para verificar configuración',
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=['test@example.com'],
            fail_silently=True
        )
        
        if result:
            print("[OK] Configuración de email funciona")
            return True
        else:
            print("[ERROR] Configuración de email no funciona")
            return False
            
    except Exception as e:
        print(f"[ERROR] Error en configuración de email: {e}")
        return False


def test_signal_manually():
    """Prueba el signal manualmente"""
    print("\nProbando signal manualmente...")
    
    try:
        from apps.reservations.models import Payment, ReservationStatus
        from django.utils import timezone
        from decimal import Decimal
        
        # Crear datos de prueba
        class MockReservation:
            def __init__(self):
                self.id = 999
                self.guests_data = [
                    {
                        'name': 'Nico Villamarin',
                        'email': 'villamarin.nico@gmail.com',
                        'is_primary': True
                    }
                ]
                self.hotel = MockHotel()
            
            @property
            def guest_email(self):
                primary_guest = self.get_primary_guest()
                return primary_guest.get('email', '') if primary_guest else ''
            
            def get_primary_guest(self):
                if not self.guests_data:
                    return None
                return next((guest for guest in self.guests_data if guest.get('is_primary', False)), None)
        
        class MockHotel:
            def __init__(self):
                self.name = "Hotel de Prueba"
        
        # Simular pago
        payment = Payment(
            id=999,
            reservation=MockReservation(),
            amount=Decimal('450.00'),
            method='cash',
            date=timezone.now().date()
        )
        
        print(f"Email del huésped: {payment.reservation.guest_email}")
        
        # Simular activación del signal
        print("Activando signal manualmente...")
        generate_payment_receipt(sender=Payment, instance=payment, created=True)
        
        print("[OK] Signal ejecutado manualmente")
        return True
        
    except Exception as e:
        print(f"[ERROR] Error ejecutando signal: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Función principal de verificación"""
    print("Verificando sistema de emails y Celery...\n")
    
    # Ejecutar verificaciones
    checks = [
        ("Estado de Celery", check_celery_status),
        ("Registro de signals", check_signals_registration),
        ("Configuración de email", check_email_configuration),
        ("Prueba manual de signal", test_signal_manually)
    ]
    
    results = []
    for check_name, check_func in checks:
        print(f"=== {check_name} ===")
        try:
            result = check_func()
            results.append(result)
            if result:
                print(f"[OK] {check_name}: EXITOSO")
            else:
                print(f"[ERROR] {check_name}: FALLÓ")
        except Exception as e:
            print(f"[ERROR] {check_name}: ERROR - {e}")
            results.append(False)
        print()
    
    # Resumen
    print("="*50)
    print("RESUMEN DE VERIFICACIÓN")
    print("="*50)
    
    passed = sum(results)
    total = len(results)
    
    print(f"Verificaciones exitosas: {passed}/{total}")
    print(f"Verificaciones fallidas: {total - passed}/{total}")
    
    if passed == total:
        print("\n¡Todas las verificaciones pasaron!")
        print("El sistema debería funcionar correctamente.")
    else:
        print(f"\n{total - passed} verificaciones fallaron.")
        print("\nPara solucionar:")
        print("1. Iniciar Celery: celery -A hotel worker --loglevel=info")
        print("2. Verificar que los signals estén importados en apps.py")
        print("3. Reiniciar el servidor Django")
    
    return passed == total


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
