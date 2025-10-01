from django.db import models
from apps.core.models import Hotel
from apps.rooms.models import Room
from apps.reservations.models import Reservation, ReservationStatus
from django.db.models import Count, Sum, Avg, Q
from datetime import date, timedelta
from decimal import Decimal

class DashboardMetrics(models.Model):
    hotel = models.ForeignKey(Hotel, on_delete=models.CASCADE, related_name="dashboard_metrics")
    date = models.DateField()
    
    # Métricas de habitaciones
    total_rooms = models.PositiveIntegerField(default=0)
    available_rooms = models.PositiveIntegerField(default=0)
    occupied_rooms = models.PositiveIntegerField(default=0)
    maintenance_rooms = models.PositiveIntegerField(default=0)
    out_of_service_rooms = models.PositiveIntegerField(default=0)
    reserved_rooms = models.PositiveIntegerField(default=0)
    
    # Métricas de reservas
    total_reservations = models.PositiveIntegerField(default=0)
    pending_reservations = models.PositiveIntegerField(default=0)
    confirmed_reservations = models.PositiveIntegerField(default=0)
    cancelled_reservations = models.PositiveIntegerField(default=0)
    check_in_today = models.PositiveIntegerField(default=0)
    check_out_today = models.PositiveIntegerField(default=0)
    no_show_today = models.PositiveIntegerField(default=0)
    
    # Métricas de huéspedes
    total_guests = models.PositiveIntegerField(default=0)
    guests_checked_in = models.PositiveIntegerField(default=0)
    guests_expected_today = models.PositiveIntegerField(default=0)
    guests_departing_today = models.PositiveIntegerField(default=0)
    
    # Métricas financieras
    total_revenue = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    average_room_rate = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    occupancy_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    
    # Métricas de ocupación por tipo de habitación
    single_rooms_occupied = models.PositiveIntegerField(default=0)
    double_rooms_occupied = models.PositiveIntegerField(default=0)
    triple_rooms_occupied = models.PositiveIntegerField(default=0)
    suite_rooms_occupied = models.PositiveIntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Métrica del Dashboard"
        verbose_name_plural = "Métricas del Dashboard"
        unique_together = ['hotel', 'date']
        ordering = ['-date']
        indexes = [
            models.Index(fields=['hotel', 'date']),
            models.Index(fields=['date']),
        ]
    
    def __str__(self):
        return f"{self.hotel.name} - {self.date}"
    
    @classmethod
    def calculate_metrics(cls, hotel, target_date=None):
        """Calcula y actualiza las métricas para un hotel en una fecha específica"""
        if target_date is None:
            target_date = date.today()
        
        # Obtener o crear el registro de métricas
        metrics, created = cls.objects.get_or_create(
            hotel=hotel,
            date=target_date,
            defaults={}
        )
        
        # Calcular métricas de habitaciones
        rooms = Room.objects.filter(hotel=hotel, is_active=True)
        metrics.total_rooms = rooms.count()
        metrics.available_rooms = rooms.filter(status='available').count()
        metrics.occupied_rooms = rooms.filter(status='occupied').count()
        metrics.maintenance_rooms = rooms.filter(status='maintenance').count()
        metrics.out_of_service_rooms = rooms.filter(status='out_of_service').count()
        metrics.reserved_rooms = rooms.filter(status='reserved').count()
        
        # Calcular métricas de reservas
        reservations = Reservation.objects.filter(hotel=hotel)
        metrics.total_reservations = reservations.count()
        metrics.pending_reservations = reservations.filter(status=ReservationStatus.PENDING).count()
        metrics.confirmed_reservations = reservations.filter(status=ReservationStatus.CONFIRMED).count()
        metrics.cancelled_reservations = reservations.filter(status=ReservationStatus.CANCELLED).count()
        
        # Reservas para el día específico
        # Llegadas de hoy (programadas + realizadas)
        metrics.check_in_today = reservations.filter(
            check_in=target_date,
            status__in=[ReservationStatus.PENDING, ReservationStatus.CONFIRMED, ReservationStatus.CHECK_IN]
        ).count()
        
        metrics.check_out_today = reservations.filter(
            check_out=target_date,
            status__in=[ReservationStatus.CHECK_IN, ReservationStatus.CHECK_OUT]
        ).count()
        
        metrics.no_show_today = reservations.filter(
            check_in=target_date,
            status=ReservationStatus.NO_SHOW
        ).count()
        
        # Calcular métricas de huéspedes
        metrics.total_guests = reservations.aggregate(
            total=Sum('guests')
        )['total'] or 0
        
        metrics.guests_checked_in = reservations.filter(
            status=ReservationStatus.CHECK_IN
        ).aggregate(
            total=Sum('guests')
        )['total'] or 0
        
        metrics.guests_expected_today = reservations.filter(
            check_in=target_date,
            status__in=[ReservationStatus.PENDING, ReservationStatus.CONFIRMED, ReservationStatus.CHECK_IN]
        ).aggregate(
            total=Sum('guests')
        )['total'] or 0
        
        metrics.guests_departing_today = reservations.filter(
            check_out=target_date,
            status__in=[ReservationStatus.CHECK_IN, ReservationStatus.CHECK_OUT]
        ).aggregate(
            total=Sum('guests')
        )['total'] or 0
        
        # Calcular métricas financieras (ingreso diario por fecha objetivo)
        # Consideramos reservas activas ese día (in-house) y prorrateamos el total por noche
        reservations_in_house = reservations.filter(
            status__in=[ReservationStatus.CHECK_IN, ReservationStatus.CHECK_OUT],
            check_in__lte=target_date,
            check_out__gt=target_date,
        )

        revenue_day = Decimal('0.00')
        for r in reservations_in_house.only('check_in', 'check_out', 'total_price'):
            nights = (r.check_out - r.check_in).days
            if nights > 0:
                revenue_day += (r.total_price or Decimal('0.00')) / Decimal(nights)
            else:
                revenue_day += (r.total_price or Decimal('0.00'))

        metrics.total_revenue = revenue_day.quantize(Decimal('0.01'))
        
        # Calcular tarifa promedio por habitación (Decimal con 2 decimales)
        if metrics.occupied_rooms > 0:
            metrics.average_room_rate = (metrics.total_revenue / Decimal(metrics.occupied_rooms)).quantize(Decimal('0.01'))
        else:
            metrics.average_room_rate = Decimal('0.00')
        
        # Calcular tasa de ocupación (Decimal con 2 decimales)
        if metrics.total_rooms > 0:
            metrics.occupancy_rate = (Decimal(metrics.occupied_rooms) / Decimal(metrics.total_rooms) * Decimal('100')).quantize(Decimal('0.01'))
        else:
            metrics.occupancy_rate = Decimal('0.00')
        
        # Calcular ocupación por tipo de habitación
        metrics.single_rooms_occupied = rooms.filter(
            room_type='single',
            status='occupied'
        ).count()
        
        metrics.double_rooms_occupied = rooms.filter(
            room_type='double',
            status='occupied'
        ).count()
        
        metrics.triple_rooms_occupied = rooms.filter(
            room_type='triple',
            status='occupied'
        ).count()
        
        metrics.suite_rooms_occupied = rooms.filter(
            room_type='suite',
            status='occupied'
        ).count()
        
        metrics.save()
        return metrics
