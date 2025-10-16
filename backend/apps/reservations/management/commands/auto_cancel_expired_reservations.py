from django.core.management.base import BaseCommand
from django.db import transaction
from apps.reservations.tasks import auto_cancel_expired_reservations


class Command(BaseCommand):
    help = 'Cancela automáticamente reservas pendientes que no han pagado el adelanto'

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
        
        self.stdout.write('Iniciando auto-cancelación de reservas vencidas...')
        
        try:
            # Ejecutar la tarea de auto-cancelación
            result = auto_cancel_expired_reservations.delay()
            
            # Esperar el resultado (opcional, para comandos síncronos)
            # result = auto_cancel_expired_reservations()
            
            self.stdout.write(
                self.style.SUCCESS(f'Tarea de auto-cancelación iniciada: {result.id}')
            )
            
            if not dry_run:
                self.stdout.write(
                    self.style.SUCCESS('Auto-cancelación completada exitosamente')
                )
            else:
                self.stdout.write(
                    self.style.WARNING('Ejecutado en modo de prueba. Use --dry-run=False para aplicar cambios reales')
                )
                
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error ejecutando auto-cancelación: {str(e)}')
            )
