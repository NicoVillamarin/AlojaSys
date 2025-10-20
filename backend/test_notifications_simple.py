#!/usr/bin/env python3
"""
Script simple para probar las notificaciones con polling de 5 segundos
"""

import os
import sys
import django
import time

# Configurar Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'hotel.settings')
django.setup()

from django.contrib.auth.models import User
from apps.notifications.models import Notification, NotificationType
from apps.notifications.services import NotificationService

def create_test_notifications():
    """Crear notificaciones de prueba"""
    print("🔔 Creando notificaciones de prueba...")
    
    # Obtener o crear usuario de prueba
    user, created = User.objects.get_or_create(
        username='test_user',
        defaults={'email': 'test@example.com'}
    )
    
    if created:
        print(f"✅ Usuario de prueba creado: {user.username}")
    else:
        print(f"✅ Usuario de prueba encontrado: {user.username}")
    
    # Crear notificaciones con intervalos
    notifications = []
    
    print("\n📤 Enviando notificaciones...")
    
    # 1. Notificación de auto-cancelación
    print("1️⃣ Creando notificación de auto-cancelación...")
    notification1 = NotificationService.create_auto_cancel_notification(
        reservation_code="TEST-SIMPLE-001",
        hotel_name="Hotel de Prueba",
        reason="Pago no recibido en tiempo",
        user_id=user.id,
        hotel_id=1
    )
    notifications.append(notification1)
    print(f"✅ Notificación creada: {notification1.title}")
    time.sleep(2)  # Pausa para ver el efecto
    
    # 2. Notificación de no-show
    print("2️⃣ Creando notificación de no-show...")
    notification2 = NotificationService.create_no_show_notification(
        reservation_code="TEST-SIMPLE-002",
        hotel_name="Hotel de Prueba",
        check_in_date="2024-01-15",
        user_id=user.id,
        hotel_id=1
    )
    notifications.append(notification2)
    print(f"✅ Notificación creada: {notification2.title}")
    time.sleep(2)
    
    # 3. Notificación de reembolso
    print("3️⃣ Creando notificación de reembolso...")
    notification3 = NotificationService.create_refund_auto_notification(
        reservation_code="TEST-SIMPLE-003",
        hotel_name="Hotel de Prueba",
        amount="300.00",
        status="success",
        user_id=user.id,
        hotel_id=1
    )
    notifications.append(notification3)
    print(f"✅ Notificación creada: {notification3.title}")
    time.sleep(2)
    
    # 4. Notificación general
    print("4️⃣ Creando notificación general...")
    notification4 = NotificationService.create(
        notification_type="general",
        title="🎉 ¡Sistema simplificado funcionando!",
        message="Las notificaciones ahora se actualizan cada 5 segundos en lugar de 30",
        user_id=user.id,
        hotel_id=1
    )
    notifications.append(notification4)
    print(f"✅ Notificación creada: {notification4.title}")
    
    return notifications, user

def show_notification_stats(user):
    """Mostrar estadísticas de notificaciones"""
    print("\n📊 Estadísticas de notificaciones:")
    
    # Contar notificaciones del usuario
    user_notifications = Notification.objects.filter(
        user=user
    )
    
    total = user_notifications.count()
    unread = user_notifications.filter(is_read=False).count()
    
    print(f"   Total de notificaciones: {total}")
    print(f"   No leídas: {unread}")
    print(f"   Leídas: {total - unread}")

def main():
    """Función principal"""
    print("🚀 Iniciando prueba de notificaciones simplificadas")
    print("=" * 60)
    
    try:
        # Crear notificaciones de prueba
        notifications, user = create_test_notifications()
        
        # Mostrar estadísticas
        show_notification_stats(user)
        
        print("\n✅ Prueba completada!")
        print("\n📝 Instrucciones:")
        print("   1. Asegúrate de que el backend esté ejecutándose: python manage.py runserver")
        print("   2. Asegúrate de que el frontend esté ejecutándose: npm run dev")
        print("   3. Abre la aplicación en el navegador e inicia sesión")
        print("   4. Las notificaciones deberían aparecer en máximo 5 segundos")
        print("   5. Observa que dice 'Actualizando cada 5 segundos' en el dropdown")
        
        print("\n🔍 Para verificar:")
        print("   - Las notificaciones aparecen automáticamente sin refrescar")
        print("   - El contador de notificaciones se actualiza cada 5 segundos")
        print("   - No hay errores en la consola del navegador")
        
    except Exception as e:
        print(f"❌ Error durante la prueba: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()