from django.core.management.base import BaseCommand
from django.db import transaction
from apps.reservations.models import Reservation
from apps.payments.models import CancellationPolicy


class Command(BaseCommand):
    help = 'Asigna políticas de cancelación a reservas existentes que no tienen una política aplicada'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Ejecutar en modo de prueba sin hacer cambios reales',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        
        if dry_run:
            self.stdout.write(
                self.style.WARNING('MODO DE PRUEBA - No se realizarán cambios reales')
            )
        
        # Obtener reservas sin política de cancelación aplicada
        reservations_without_policy = Reservation.objects.filter(
            applied_cancellation_policy__isnull=True
        ).select_related('hotel')
        
        total_reservations = reservations_without_policy.count()
        self.stdout.write(f'Encontradas {total_reservations} reservas sin política de cancelación')
        
        if total_reservations == 0:
            self.stdout.write(
                self.style.SUCCESS('Todas las reservas ya tienen políticas de cancelación asignadas')
            )
            return
        
        updated_count = 0
        error_count = 0
        
        with transaction.atomic():
            for reservation in reservations_without_policy:
                try:
                    # Obtener la política de cancelación vigente para el hotel
                    cancellation_policy = CancellationPolicy.resolve_for_hotel(reservation.hotel)
                    
                    if cancellation_policy:
                        if not dry_run:
                            reservation.applied_cancellation_policy = cancellation_policy
                            reservation.save(update_fields=['applied_cancellation_policy'])
                        
                        updated_count += 1
                        self.stdout.write(
                            f'{"[DRY RUN] " if dry_run else ""}Reserva {reservation.id} -> Política: {cancellation_policy.name}'
                        )
                    else:
                        self.stdout.write(
                            self.style.WARNING(
                                f'Reserva {reservation.id} - Hotel {reservation.hotel.name}: No hay política de cancelación configurada'
                            )
                        )
                        error_count += 1
                        
                except Exception as e:
                    self.stdout.write(
                        self.style.ERROR(
                            f'Error procesando reserva {reservation.id}: {str(e)}'
                        )
                    )
                    error_count += 1
        
        # Resumen
        self.stdout.write('\n' + '='*50)
        self.stdout.write('RESUMEN:')
        self.stdout.write(f'Total de reservas procesadas: {total_reservations}')
        self.stdout.write(f'Reservas actualizadas: {updated_count}')
        self.stdout.write(f'Errores: {error_count}')
        
        if dry_run:
            self.stdout.write(
                self.style.WARNING('Ejecutado en modo de prueba. Use --dry-run=False para aplicar cambios reales')
            )
        else:
            self.stdout.write(
                self.style.SUCCESS('Migración completada exitosamente')
            )
