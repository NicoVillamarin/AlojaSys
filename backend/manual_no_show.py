"""
Script para marcar manualmente las reservas confirmadas vencidas como no-show
Útil para procesar reservas que no fueron marcadas automáticamente
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
from apps.reservations.models import Reservation, ReservationStatus, ReservationStatusChange
from apps.reservations.services.no_show_processor import NoShowProcessor
from decimal import Decimal

def manual_mark_no_show(dry_run=False):
    """
    Marca manualmente las reservas confirmadas vencidas como no-show
    
    Args:
        dry_run: Si es True, solo muestra qué se haría sin hacer cambios
    """
    today = timezone.now().date()
    
    print("=" * 80)
    if dry_run:
        print("🔍 MODO DRY-RUN: Solo mostrará qué se haría sin hacer cambios")
    else:
        print("⚙️  PROCESANDO RESERVAS VENCIDAS")
    print("=" * 80)
    print()
    print(f"📅 Fecha actual: {today}")
    print()
    
    # Obtener hoteles con auto no-show habilitado
    hotels_with_auto = Hotel.objects.filter(
        auto_no_show_enabled=True,
        is_active=True
    )
    
    if not hotels_with_auto.exists():
        print("⚠️  No hay hoteles con auto_no_show_enabled=True")
        print()
        print("💡 Opciones:")
        print("   1. Habilitar auto_no_show_enabled en los hoteles necesarios")
        print("   2. Ejecutar este script sin el filtro de hotel (modificar código)")
        return
    
    print(f"🏨 Procesando {hotels_with_auto.count()} hoteles con auto no-show habilitado")
    print()
    
    processed_count = 0
    no_show_count = 0
    penalties_applied = 0
    total_penalty_amount = Decimal('0.00')
    
    for hotel in hotels_with_auto:
        print(f"📋 Hotel: {hotel.name}")
        print("-" * 80)
        
        # Buscar reservas confirmadas con check-in pasado
        expired_reservations = Reservation.objects.filter(
            hotel=hotel,
            status=ReservationStatus.CONFIRMED,
            check_in__lt=today
        )
        
        print(f"   Reservas vencidas encontradas: {expired_reservations.count()}")
        
        if expired_reservations.count() == 0:
            print("   ✅ No hay reservas vencidas para procesar")
            print()
            continue
        
        hotel_processed = 0
        hotel_no_show = 0
        hotel_penalties = 0
        hotel_penalty_amount = Decimal('0.00')
        
        for reservation in expired_reservations:
            try:
                print(f"   🔄 Procesando reserva #{reservation.id} - Check-in: {reservation.check_in}")
                
                if not dry_run:
                    # Cambiar estado a no_show
                    reservation.status = ReservationStatus.NO_SHOW
                    reservation.save(update_fields=['status'])
                    
                    # Registrar el cambio de estado
                    ReservationStatusChange.objects.create(
                        reservation=reservation,
                        from_status=ReservationStatus.CONFIRMED,
                        to_status=ReservationStatus.NO_SHOW,
                        changed_by=None,  # Sistema automático
                        notes='Auto no-show: check-in date passed (manual)'
                    )
                    
                    # Procesar penalidades automáticas
                    try:
                        penalty_result = NoShowProcessor.process_no_show_penalties(reservation)
                        
                        if penalty_result.get('success', False):
                            penalty_amount = Decimal(str(penalty_result.get('penalty_amount', 0)))
                            if penalty_amount > 0:
                                hotel_penalties += 1
                                hotel_penalty_amount += penalty_amount
                                penalties_applied += 1
                                total_penalty_amount += penalty_amount
                                print(f"      💰 Penalidad aplicada: ${penalty_amount}")
                            else:
                                print(f"      ℹ️  Sin penalidad")
                        else:
                            print(f"      ⚠️  Error procesando penalidades: {penalty_result.get('error', 'Error desconocido')}")
                    except Exception as e:
                        print(f"      ⚠️  Error procesando penalidades: {e}")
                    
                    hotel_no_show += 1
                    no_show_count += 1
                    print(f"      ✅ Reserva marcada como no-show")
                else:
                    print(f"      🔍 Se marcaría como no-show (dry-run)")
                    hotel_no_show += 1
                    no_show_count += 1
                
                hotel_processed += 1
                processed_count += 1
                
            except Exception as e:
                print(f"      ❌ Error procesando reserva {reservation.id}: {e}")
            
            print()
        
        if hotel_processed > 0:
            print(f"   📊 Hotel {hotel.name}:")
            print(f"      - Reservas procesadas: {hotel_processed}")
            print(f"      - Marcadas como no-show: {hotel_no_show}")
            if not dry_run:
                print(f"      - Penalidades aplicadas: {hotel_penalties} (${hotel_penalty_amount})")
            print()
    
    print("=" * 80)
    print("📊 RESUMEN FINAL:")
    print("=" * 80)
    print(f"   Reservas procesadas: {processed_count}")
    print(f"   Marcadas como no-show: {no_show_count}")
    if not dry_run:
        print(f"   Penalidades aplicadas: {penalties_applied} (Total: ${total_penalty_amount})")
    print()
    
    if dry_run:
        print("💡 Para ejecutar realmente, ejecuta:")
        print("   python manage.py shell < manual_no_show.py")
        print("   O cambia dry_run=False en el código")
    else:
        print("✅ Proceso completado")
    print()

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Marca manualmente reservas vencidas como no-show')
    parser.add_argument('--dry-run', action='store_true', help='Solo mostrar qué se haría sin hacer cambios')
    
    args = parser.parse_args()
    
    manual_mark_no_show(dry_run=args.dry_run)





