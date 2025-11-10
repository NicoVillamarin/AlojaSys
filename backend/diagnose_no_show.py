"""
Script de diagnóstico para verificar por qué no se están marcando automáticamente 
las reservas confirmadas vencidas como no-show
"""
import os
import sys
import django

# Configurar Django
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'hotel.settings')
django.setup()

from django.utils import timezone
from apps.core.models import Hotel
from apps.reservations.models import Reservation, ReservationStatus
from datetime import date

def diagnose_no_show():
    """Diagnostica el problema de auto no-show"""
    print("=" * 80)
    print("🔍 DIAGNÓSTICO DE AUTO NO-SHOW")
    print("=" * 80)
    print()
    
    today = timezone.now().date()
    print(f"📅 Fecha actual: {today}")
    print()
    
    # 1. Verificar hoteles con auto_no_show_enabled
    print("1️⃣ Verificando configuración de hoteles:")
    print("-" * 80)
    all_hotels = Hotel.objects.filter(is_active=True)
    hotels_with_auto = all_hotels.filter(auto_no_show_enabled=True)
    
    print(f"   Total de hoteles activos: {all_hotels.count()}")
    print(f"   Hoteles con auto_no_show_enabled=True: {hotels_with_auto.count()}")
    print()
    
    if hotels_with_auto.count() == 0:
        print("   ⚠️  PROBLEMA ENCONTRADO: No hay hoteles con auto_no_show_enabled=True")
        print("   💡 SOLUCIÓN: Habilitar auto_no_show_enabled en los hoteles necesarios")
        print()
        
        print("   Hoteles disponibles:")
        for hotel in all_hotels:
            print(f"      - {hotel.name} (ID: {hotel.id}) - auto_no_show_enabled: {hotel.auto_no_show_enabled}")
        print()
    else:
        print("   ✅ Hoteles con auto no-show habilitado:")
        for hotel in hotels_with_auto:
            print(f"      - {hotel.name} (ID: {hotel.id})")
        print()
    
    # 2. Buscar reservas confirmadas vencidas
    print("2️⃣ Buscando reservas confirmadas con check-in vencido:")
    print("-" * 80)
    
    if hotels_with_auto.exists():
        expired_reservations = Reservation.objects.filter(
            hotel__in=hotels_with_auto,
            status=ReservationStatus.CONFIRMED,
            check_in__lt=today
        )
        
        print(f"   Reservas encontradas: {expired_reservations.count()}")
        print()
        
        if expired_reservations.count() > 0:
            print("   ⚠️  PROBLEMA ENCONTRADO: Hay reservas confirmadas vencidas sin marcar como no-show")
            print("   💡 SOLUCIÓN: Ejecutar manualmente la tarea auto_mark_no_show_daily")
            print()
            print("   Reservas vencidas:")
            for res in expired_reservations[:10]:  # Mostrar solo las primeras 10
                print(f"      - Reserva #{res.id}: {res.hotel.name} - Check-in: {res.check_in} (vencida hace {today - res.check_in} días)")
            if expired_reservations.count() > 10:
                print(f"      ... y {expired_reservations.count() - 10} más")
            print()
        else:
            print("   ✅ No hay reservas confirmadas vencidas")
            print()
    else:
        # Buscar en todos los hoteles para diagnóstico
        all_expired = Reservation.objects.filter(
            status=ReservationStatus.CONFIRMED,
            check_in__lt=today
        )
        print(f"   Reservas confirmadas vencidas en TODOS los hoteles: {all_expired.count()}")
        
        if all_expired.count() > 0:
            print("   ⚠️  Hay reservas vencidas, pero los hoteles no tienen auto_no_show_enabled=True")
            print("   💡 SOLUCIÓN: Habilitar auto_no_show_enabled en los hoteles necesarios")
            print()
            for res in all_expired[:5]:
                print(f"      - Reserva #{res.id}: {res.hotel.name} - auto_no_show_enabled: {res.hotel.auto_no_show_enabled}")
        print()
    
    # 3. Verificar configuración de Celery Beat
    print("3️⃣ Verificando configuración de Celery Beat:")
    print("-" * 80)
    print("   📋 La tarea auto_mark_no_show_daily está configurada para ejecutarse:")
    print("      - Hora: 9:00 AM (diario)")
    print("      - Tarea: apps.reservations.tasks.auto_mark_no_show_daily")
    print()
    print("   ⚠️  IMPORTANTE: Verificar que Celery Beat esté corriendo:")
    print("      - Docker: docker-compose ps (debe mostrar hotel_celery_beat como 'Up')")
    print("      - Logs: docker-compose logs celery_beat")
    print()
    
    # 4. Resumen y recomendaciones
    print("=" * 80)
    print("📋 RESUMEN Y RECOMENDACIONES:")
    print("=" * 80)
    print()
    
    issues_found = []
    
    if hotels_with_auto.count() == 0:
        issues_found.append("❌ No hay hoteles con auto_no_show_enabled=True")
    
    if hotels_with_auto.exists():
        expired = Reservation.objects.filter(
            hotel__in=hotels_with_auto,
            status=ReservationStatus.CONFIRMED,
            check_in__lt=today
        )
        if expired.exists():
            issues_found.append(f"❌ Hay {expired.count()} reservas vencidas sin marcar como no-show")
    
    if not issues_found:
        print("   ✅ No se encontraron problemas aparentes en la configuración")
        print("   💡 Verificar que Celery Beat esté corriendo correctamente")
    else:
        print("   Problemas encontrados:")
        for issue in issues_found:
            print(f"      {issue}")
        print()
        print("   💡 ACCIONES RECOMENDADAS:")
        print()
        print("   1. Habilitar auto_no_show_enabled en los hoteles:")
        print("      - Desde el admin de Django o desde la API")
        print("      - O ejecutar en shell de Django:")
        print("        Hotel.objects.filter(is_active=True).update(auto_no_show_enabled=True)")
        print()
        print("   2. Marcar manualmente las reservas vencidas como no-show:")
        print("      - Usar el endpoint POST /api/reservations/auto-mark-no-show/")
        print("      - O ejecutar manualmente la tarea:")
        print("        from apps.reservations.tasks import auto_mark_no_show_daily")
        print("        auto_mark_no_show_daily.delay()")
        print()
        print("   3. Verificar que Celery Beat esté corriendo:")
        print("      docker-compose ps")
        print("      docker-compose logs celery_beat")
        print()
    
    print("=" * 80)

if __name__ == "__main__":
    diagnose_no_show()





