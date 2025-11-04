from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone
from datetime import date
from apps.reservations.models import Reservation, ReservationStatus
from apps.rooms.models import RoomStatus


class Command(BaseCommand):
    help = 'Corrige reservas en estado CHECK_IN que ya pasaron su fecha de check-out y las marca como CHECK_OUT'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Ejecutar en modo de prueba sin hacer cambios reales',
        )
        parser.add_argument(
            '--reservation-id',
            type=int,
            help='Procesar solo una reserva específica por ID',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        reservation_id = options.get('reservation_id')
        
        if dry_run:
            self.stdout.write(
                self.style.WARNING('MODO DE PRUEBA - No se realizarán cambios reales')
            )
        
        today = timezone.localdate() if timezone.is_aware(timezone.now()) else date.today()
        
        self.stdout.write(f'🔍 Buscando reservas en CHECK_IN con check-out <= {today}...')
        
        # Buscar reservas en CHECK_IN con check-out pasado o hoy
        query = Reservation.objects.select_related("room", "hotel").filter(
            status=ReservationStatus.CHECK_IN,
            check_out__lte=today,
        )
        
        if reservation_id:
            query = query.filter(id=reservation_id)
            self.stdout.write(f'📋 Procesando solo reserva ID: {reservation_id}')
        
        checkout_reservations = list(query)
        
        if not checkout_reservations:
            self.stdout.write(
                self.style.SUCCESS('✅ No se encontraron reservas que necesiten corrección')
            )
            return
        
        self.stdout.write(f'📊 Encontradas {len(checkout_reservations)} reservas para procesar')
        
        processed_count = 0
        error_count = 0
        
        for res in checkout_reservations:
            try:
                checkout_date = res.check_out
                days_past = (today - checkout_date).days if checkout_date < today else 0
                
                self.stdout.write(
                    f'  📋 Reserva #{res.id} - Habitación: {res.room.name if res.room else "N/A"} - '
                    f'Check-out: {checkout_date} ({days_past} días pasado)' if days_past > 0 else f'Check-out: {checkout_date} (hoy)'
                )
                
                if not dry_run:
                    with transaction.atomic():
                        # Cambiar estado a CHECK_OUT
                        # Usar skip_clean=True para evitar validaciones que no aplican al cambio de estado
                        # (como capacidad de habitación, fechas, etc.)
                        res.status = ReservationStatus.CHECK_OUT
                        res.save(update_fields=["status"], skip_clean=True)
                        
                        # Liberar la habitación
                        if res.room and res.room.status == RoomStatus.OCCUPIED:
                            res.room.status = RoomStatus.AVAILABLE
                            res.room.save(update_fields=["status"])
                        
                        processed_count += 1
                        self.stdout.write(
                            self.style.SUCCESS(f'    ✅ Reserva #{res.id} corregida exitosamente')
                        )
                else:
                    processed_count += 1
                    self.stdout.write(
                        self.style.WARNING(f'    ⚠️  (Modo prueba) Reserva #{res.id} sería corregida')
                    )
                    
            except Exception as e:
                error_count += 1
                self.stdout.write(
                    self.style.ERROR(f'    ❌ Error procesando reserva #{res.id}: {str(e)}')
                )
        
        if dry_run:
            self.stdout.write(
                self.style.WARNING(
                    f'\n📊 RESUMEN (MODO PRUEBA):\n'
                    f'   Reservas encontradas: {len(checkout_reservations)}\n'
                    f'   Reservas que se corregirían: {processed_count}\n'
                    f'   Errores: {error_count}\n\n'
                    f'   Ejecuta sin --dry-run para aplicar los cambios.'
                )
            )
        else:
            self.stdout.write(
                self.style.SUCCESS(
                    f'\n📊 RESUMEN:\n'
                    f'   Reservas encontradas: {len(checkout_reservations)}\n'
                    f'   Reservas corregidas: {processed_count}\n'
                    f'   Errores: {error_count}'
                )
            )

