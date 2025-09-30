from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import date, timedelta
from apps.core.models import Hotel
from apps.dashboard.models import DashboardMetrics

class Command(BaseCommand):
    help = 'Calcula las métricas del dashboard para todos los hoteles'

    def add_arguments(self, parser):
        parser.add_argument(
            '--hotel-id',
            type=int,
            help='ID del hotel específico para calcular métricas'
        )
        parser.add_argument(
            '--date',
            type=str,
            help='Fecha para calcular métricas (YYYY-MM-DD). Por defecto es hoy.'
        )
        parser.add_argument(
            '--days',
            type=int,
            default=1,
            help='Número de días hacia atrás para calcular métricas (por defecto: 1)'
        )
        parser.add_argument(
            '--all-hotels',
            action='store_true',
            help='Calcular métricas para todos los hoteles'
        )

    def handle(self, *args, **options):
        target_date = date.today()
        if options['date']:
            try:
                target_date = date.fromisoformat(options['date'])
            except ValueError:
                self.stdout.write(
                    self.style.ERROR('Formato de fecha inválido. Use YYYY-MM-DD')
                )
                return

        hotels = []
        
        if options['hotel_id']:
            try:
                hotel = Hotel.objects.get(id=options['hotel_id'])
                hotels = [hotel]
            except Hotel.DoesNotExist:
                self.stdout.write(
                    self.style.ERROR(f'Hotel con ID {options["hotel_id"]} no encontrado')
                )
                return
        elif options['all_hotels']:
            hotels = Hotel.objects.filter(is_active=True)
        else:
            self.stdout.write(
                self.style.ERROR('Debe especificar --hotel-id o --all-hotels')
            )
            return

        if not hotels:
            self.stdout.write(
                self.style.WARNING('No se encontraron hoteles para procesar')
            )
            return

        days = options['days']
        total_metrics = 0
        
        for hotel in hotels:
            self.stdout.write(f'Calculando métricas para {hotel.name}...')
            
            # Calcular métricas para el rango de días
            for i in range(days):
                current_date = target_date - timedelta(days=i)
                
                try:
                    metrics = DashboardMetrics.calculate_metrics(hotel, current_date)
                    total_metrics += 1
                    
                    self.stdout.write(
                        f'  ✓ Métricas calculadas para {current_date}: '
                        f'Ocupación {metrics.occupancy_rate}%, '
                        f'Ingresos ${metrics.total_revenue}'
                    )
                    
                except Exception as e:
                    self.stdout.write(
                        self.style.ERROR(
                            f'  ✗ Error calculando métricas para {current_date}: {str(e)}'
                        )
                    )

        self.stdout.write(
            self.style.SUCCESS(
                f'Proceso completado. Se calcularon {total_metrics} métricas.'
            )
        )
