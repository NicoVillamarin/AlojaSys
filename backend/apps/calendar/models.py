from django.db import models
from django.contrib.auth import get_user_model
from apps.core.models import Hotel
from apps.rooms.models import Room
from apps.reservations.models import Reservation

User = get_user_model()


class CalendarEventType(models.TextChoices):
    RESERVATION = "reservation", "Reserva"
    MAINTENANCE = "maintenance", "Mantenimiento"
    BLOCK = "block", "Bloqueo"
    CLEANING = "cleaning", "Limpieza"
    OUT_OF_SERVICE = "out_of_service", "Fuera de Servicio"


class CalendarEvent(models.Model):
    """
    Modelo para eventos del calendario que agrupa diferentes tipos de eventos
    """
    hotel = models.ForeignKey(Hotel, on_delete=models.CASCADE, related_name="calendar_events")
    room = models.ForeignKey(Room, on_delete=models.CASCADE, related_name="calendar_events")
    event_type = models.CharField(max_length=20, choices=CalendarEventType.choices)
    
    # Referencia a la reserva original (si aplica)
    reservation = models.ForeignKey(
        Reservation, 
        on_delete=models.CASCADE, 
        null=True, 
        blank=True, 
        related_name="calendar_events"
    )
    
    # Fechas del evento
    start_date = models.DateField()
    end_date = models.DateField()
    
    # Información del evento
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    
    # Estado y configuración
    is_active = models.BooleanField(default=True)
    is_all_day = models.BooleanField(default=True)
    
    # Metadatos
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    
    class Meta:
        ordering = ['start_date', 'room__name']
        indexes = [
            models.Index(fields=['hotel', 'start_date']),
            models.Index(fields=['room', 'start_date']),
            models.Index(fields=['event_type']),
            models.Index(fields=['is_active']),
        ]
        verbose_name = "Evento de Calendario"
        verbose_name_plural = "Eventos de Calendario"
    
    def __str__(self):
        return f"{self.title} - {self.room.name} ({self.start_date} - {self.end_date})"


class RoomMaintenance(models.Model):
    """
    Modelo para gestionar mantenimiento y limpieza de habitaciones
    """
    hotel = models.ForeignKey(Hotel, on_delete=models.CASCADE, related_name="room_maintenance")
    room = models.ForeignKey(Room, on_delete=models.CASCADE, related_name="maintenance_schedules")
    
    # Fechas del mantenimiento
    start_date = models.DateField()
    end_date = models.DateField()
    
    # Tipo de mantenimiento
    MAINTENANCE_TYPE_CHOICES = [
        ('cleaning', 'Limpieza'),
        ('maintenance', 'Mantenimiento'),
        ('repair', 'Reparación'),
        ('inspection', 'Inspección'),
        ('deep_cleaning', 'Limpieza Profunda'),
    ]
    maintenance_type = models.CharField(max_length=20, choices=MAINTENANCE_TYPE_CHOICES)
    
    # Información del mantenimiento
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    priority = models.CharField(max_length=10, choices=[
        ('low', 'Baja'),
        ('medium', 'Media'),
        ('high', 'Alta'),
        ('urgent', 'Urgente'),
    ], default='medium')
    
    # Estado
    status = models.CharField(max_length=20, choices=[
        ('scheduled', 'Programado'),
        ('in_progress', 'En Progreso'),
        ('completed', 'Completado'),
        ('cancelled', 'Cancelado'),
    ], default='scheduled')
    
    # Asignación
    assigned_to = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    
    # Metadatos
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='created_maintenance')
    
    class Meta:
        ordering = ['start_date', 'priority']
        indexes = [
            models.Index(fields=['hotel', 'start_date']),
            models.Index(fields=['room', 'start_date']),
            models.Index(fields=['status']),
            models.Index(fields=['priority']),
        ]
        verbose_name = "Mantenimiento de Habitación"
        verbose_name_plural = "Mantenimientos de Habitaciones"
    
    def __str__(self):
        return f"{self.title} - {self.room.name} ({self.start_date})"


class CalendarView(models.Model):
    """
    Modelo para guardar configuraciones de vista del calendario por usuario
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="calendar_view")
    hotel = models.ForeignKey(Hotel, on_delete=models.CASCADE, related_name="calendar_views")
    
    # Configuración de vista
    default_view = models.CharField(max_length=20, choices=[
        ('month', 'Mes'),
        ('week', 'Semana'),
        ('day', 'Día'),
        ('rooms', 'Habitaciones'),
    ], default='month')
    
    # Filtros guardados
    show_maintenance = models.BooleanField(default=True)
    show_blocks = models.BooleanField(default=True)
    show_revenue = models.BooleanField(default=False)
    
    # Filtros de habitaciones
    room_types = models.JSONField(default=list, blank=True)
    floors = models.JSONField(default=list, blank=True)
    
    # Metadatos
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Vista de Calendario"
        verbose_name_plural = "Vistas de Calendario"
    
    def __str__(self):
        return f"Vista de {self.user.username} - {self.hotel.name}"
