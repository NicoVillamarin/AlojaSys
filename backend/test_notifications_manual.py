#!/usr/bin/env python
"""
Script de prueba para notificaciones manuales
Ejecuta: python test_notifications_manual.py
"""

import os
import sys
import django
from datetime import datetime, timedelta

# Configurar Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'hotel.settings')
os.environ.setdefault('DATABASE_URL', 'sqlite:///db.sqlite3')  # Usar SQLite para el test
django.setup()

from apps.notifications.services import NotificationService
from apps.notifications.models import Notification, NotificationType
from django.contrib.auth.models import User

def test_manual_cancellation_notification():
    """Prueba notificación de cancelación manual"""
    print("🧪 Probando notificación de cancelación manual...")
    
    # Crear usuario de prueba si no existe
    user, created = User.objects.get_or_create(
        username='testuser',
        defaults={'email': 'test@example.com'}
    )
    if created:
        user.set_password('testpass')
        user.save()
        print(f"✅ Usuario de prueba creado: {user.username}")
    
    notification = NotificationService.create_auto_cancel_notification(
        reservation_code="RES-999",
        hotel_name="Hotel Test Manual",
        reason="Cancelación manual - Motivo: Cliente solicitó cancelación",
        hotel_id=1,
        reservation_id=999,
        user_id=user.id  # Usuario específico
    )
    print(f"✅ Notificación de cancelación manual creada: {notification.id}")
    print(f"   - Título: {notification.title}")
    print(f"   - Mensaje: {notification.message}")
    print(f"   - Usuario: {notification.user}")
    return notification

def test_refund_notification():
    """Prueba notificación de reembolso"""
    print("\n🧪 Probando notificación de reembolso...")
    
    # Obtener usuario de prueba
    user = User.objects.filter(username='testuser').first()
    if not user:
        user = User.objects.create_user('testuser', 'test@example.com', 'testpass')
    
    notification = NotificationService.create_refund_auto_notification(
        reservation_code="RES-888",
        hotel_name="Hotel Test Refund",
        amount="250.00",
        status="success",
        hotel_id=2,
        reservation_id=888,
        user_id=user.id
    )
    print(f"✅ Notificación de reembolso creada: {notification.id}")
    print(f"   - Título: {notification.title}")
    print(f"   - Mensaje: {notification.message}")
    return notification

def test_refund_failed_notification():
    """Prueba notificación de reembolso fallido"""
    print("\n🧪 Probando notificación de reembolso fallido...")
    
    # Obtener usuario de prueba
    user = User.objects.filter(username='testuser').first()
    if not user:
        user = User.objects.create_user('testuser', 'test@example.com', 'testpass')
    
    notification = NotificationService.create_refund_auto_notification(
        reservation_code="RES-777",
        hotel_name="Hotel Test Failed",
        amount="100.00",
        status="failed",
        hotel_id=3,
        reservation_id=777,
        user_id=user.id
    )
    print(f"✅ Notificación de reembolso fallido creada: {notification.id}")
    print(f"   - Título: {notification.title}")
    print(f"   - Mensaje: {notification.message}")
    return notification

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
    print(f"📊 Últimas 5 notificaciones:")
    for notif in recent:
        print(f"   - {notif.type}: {notif.title} ({'leída' if notif.is_read else 'no leída'})")

def test_refund_created_notification():
    """Prueba notificación de reembolso creado"""
    print("\n🧪 Probando notificación de reembolso creado...")
    
    # Obtener usuario de prueba
    user = User.objects.filter(username='testuser').first()
    if not user:
        user = User.objects.create_user('testuser', 'test@example.com', 'testpass')
    
    notification = NotificationService.create(
        notification_type=NotificationType.REFUND_AUTO,
        title="Nuevo reembolso creado",
        message="Se ha creado un reembolso de $150.00 para la reserva #RES-444 en Hotel Test Created. Estado: Pendiente",
        user_id=user.id,
        hotel_id=1,
        reservation_id=444,
        metadata={
            'reservation_code': "RES-444",
            'hotel_name': "Hotel Test Created",
            'amount': "150.00",
            'status': 'created',
            'refund_id': 123
        }
    )
    print(f"✅ Notificación de reembolso creado: {notification.id}")
    print(f"   - Título: {notification.title}")
    print(f"   - Mensaje: {notification.message}")
    return notification

def test_refund_processing_notification():
    """Prueba notificación de reembolso en procesamiento"""
    print("\n🧪 Probando notificación de reembolso en procesamiento...")
    
    # Obtener usuario de prueba
    user = User.objects.filter(username='testuser').first()
    if not user:
        user = User.objects.create_user('testuser', 'test@example.com', 'testpass')
    
    notification = NotificationService.create(
        notification_type=NotificationType.REFUND_AUTO,
        title="Reembolso en procesamiento",
        message="El reembolso de $200.00 para la reserva #RES-333 en Hotel Test Processing está siendo procesado.",
        user_id=user.id,
        hotel_id=2,
        reservation_id=333,
        metadata={
            'reservation_code': "RES-333",
            'hotel_name': "Hotel Test Processing",
            'amount': "200.00",
            'status': 'processing'
        }
    )
    print(f"✅ Notificación de reembolso en procesamiento: {notification.id}")
    print(f"   - Título: {notification.title}")
    print(f"   - Mensaje: {notification.message}")
    return notification

def test_user_specific_notifications():
    """Prueba notificaciones específicas de usuario"""
    print("\n🧪 Probando notificaciones específicas de usuario...")
    
    # Obtener usuario de prueba
    user = User.objects.filter(username='testuser').first()
    if not user:
        user = User.objects.create_user('testuser', 'test@example.com', 'testpass')
    
    # Crear notificación para usuario específico
    user_notification = NotificationService.create_auto_cancel_notification(
        reservation_code="RES-666",
        hotel_name="Hotel Test User",
        reason="Cancelación para usuario específico",
        hotel_id=1,
        reservation_id=666,
        user_id=user.id
    )
    print(f"✅ Notificación para usuario específico: {user_notification.id}")
    
    # Crear notificación para todos los usuarios
    global_notification = NotificationService.create_auto_cancel_notification(
        reservation_code="RES-555",
        hotel_name="Hotel Test Global",
        reason="Cancelación para todos los usuarios",
        hotel_id=1,
        reservation_id=555
        # Sin user_id = para todos
    )
    print(f"✅ Notificación global: {global_notification.id}")

def cleanup_test_data():
    """Limpia los datos de prueba"""
    print("\n🧹 Limpiando datos de prueba...")
    
    # Eliminar notificaciones de prueba
    deleted_count = Notification.objects.filter(
        title__icontains="Test"
    ).delete()[0]
    print(f"🗑️ {deleted_count} notificaciones de prueba eliminadas")

def main():
    """Función principal"""
    print("🚀 Iniciando pruebas de notificaciones manuales\n")
    
    try:
        # Ejecutar pruebas
        test_manual_cancellation_notification()
        test_refund_notification()
        test_refund_failed_notification()
        test_refund_created_notification()
        test_refund_processing_notification()
        test_user_specific_notifications()
        test_notification_queries()
        
        print("\n✅ Todas las pruebas completadas exitosamente!")
        
        # Mostrar resumen final
        print(f"\n📊 Resumen final:")
        print(f"   - Total de notificaciones: {Notification.objects.count()}")
        print(f"   - No leídas: {Notification.get_unread_count()}")
        
        # Mostrar últimas notificaciones
        print(f"\n📋 Últimas notificaciones:")
        recent = Notification.objects.order_by('-created_at')[:3]
        for notif in recent:
            print(f"   - {notif.get_type_display()}: {notif.title}")
            print(f"     Usuario: {notif.user or 'Todos'}")
            print(f"     Leída: {'Sí' if notif.is_read else 'No'}")
            print()
        
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
