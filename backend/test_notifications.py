#!/usr/bin/env python
"""
Script de prueba para el sistema de notificaciones
Ejecuta: python test_notifications.py
"""

import os
import sys
import django
from datetime import datetime, timedelta

# Configurar Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'hotel.settings')
django.setup()

from apps.notifications.services import NotificationService
from apps.notifications.models import Notification, NotificationType
from django.contrib.auth.models import User

def test_notification_creation():
    """Prueba la creación de notificaciones"""
    print("🧪 Probando creación de notificaciones...")
    
    # Crear notificación de auto-cancelación
    notification1 = NotificationService.create_auto_cancel_notification(
        reservation_code="RES-123",
        hotel_name="Hotel Test",
        reason="Depósito vencido sin pago",
        hotel_id=1,
        reservation_id=123
    )
    print(f"✅ Notificación de auto-cancelación creada: {notification1.id}")
    
    # Crear notificación de no-show
    notification2 = NotificationService.create_no_show_notification(
        reservation_code="RES-456",
        hotel_name="Hotel Test 2",
        check_in_date="2024-01-15",
        hotel_id=2,
        reservation_id=456
    )
    print(f"✅ Notificación de no-show creada: {notification2.id}")
    
    # Crear notificación de reembolso automático
    notification3 = NotificationService.create_refund_auto_notification(
        reservation_code="RES-789",
        hotel_name="Hotel Test 3",
        amount="150.00",
        status="success",
        hotel_id=3,
        reservation_id=789
    )
    print(f"✅ Notificación de reembolso automático creada: {notification3.id}")
    
    return [notification1, notification2, notification3]

def test_notification_queries():
    """Prueba las consultas de notificaciones"""
    print("\n🔍 Probando consultas de notificaciones...")
    
    # Contar notificaciones totales
    total_count = Notification.objects.count()
    print(f"📊 Total de notificaciones: {total_count}")
    
    # Contar no leídas
    unread_count = Notification.get_unread_count()
    print(f"📊 Notificaciones no leídas: {unread_count}")
    
    # Contar por tipo
    for notification_type, _ in NotificationType.choices:
        count = Notification.objects.filter(type=notification_type).count()
        print(f"📊 {notification_type}: {count}")
    
    # Obtener últimas 5
    recent = Notification.objects.order_by('-created_at')[:5]
    print(f"📊 Últimas 5 notificaciones: {len(recent)}")

def test_notification_mark_read():
    """Prueba marcar notificaciones como leídas"""
    print("\n✅ Probando marcar como leídas...")
    
    # Obtener una notificación no leída
    unread_notification = Notification.objects.filter(is_read=False).first()
    if unread_notification:
        print(f"📝 Marcando como leída: {unread_notification.title}")
        unread_notification.mark_as_read()
        print("✅ Notificación marcada como leída")
    else:
        print("ℹ️ No hay notificaciones sin leer para marcar")

def test_bulk_notifications():
    """Prueba creación masiva de notificaciones"""
    print("\n📦 Probando notificaciones masivas...")
    
    # Crear notificaciones para múltiples usuarios
    notifications = NotificationService.create_bulk_notification(
        notification_type=NotificationType.AUTO_CANCEL,
        title="Mantenimiento programado",
        message_template="El hotel {hotel_name} tendrá mantenimiento el {date}",
        hotel_id=1,
        template_vars={
            'hotel_name': 'Hotel Central',
            'date': '2024-01-20'
        }
    )
    print(f"✅ {len(notifications)} notificaciones masivas creadas")

def cleanup_test_data():
    """Limpia los datos de prueba"""
    print("\n🧹 Limpiando datos de prueba...")
    
    # Eliminar notificaciones de prueba (que contengan "Test" en el título)
    deleted_count = Notification.objects.filter(
        title__icontains="Test"
    ).delete()[0]
    print(f"🗑️ {deleted_count} notificaciones de prueba eliminadas")

def main():
    """Función principal"""
    print("🚀 Iniciando pruebas del sistema de notificaciones\n")
    
    try:
        # Ejecutar pruebas
        notifications = test_notification_creation()
        test_notification_queries()
        test_notification_mark_read()
        test_bulk_notifications()
        
        print("\n✅ Todas las pruebas completadas exitosamente!")
        
        # Mostrar resumen final
        print(f"\n📊 Resumen final:")
        print(f"   - Total de notificaciones: {Notification.objects.count()}")
        print(f"   - No leídas: {Notification.get_unread_count()}")
        
        # Preguntar si limpiar datos
        response = input("\n¿Desea limpiar los datos de prueba? (y/N): ")
        if response.lower() in ['y', 'yes', 'sí', 'si']:
            cleanup_test_data()
        
    except Exception as e:
        print(f"❌ Error durante las pruebas: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
