from django.db import models
from django.core.exceptions import ValidationError
from apps.core.models import Hotel
from apps.rooms.models import Room

class ReservationStatus(models.TextChoices):
    PENDING = "pending", "Pendiente"
    CONFIRMED = "confirmed", "Confirmada"
    CANCELLED = "cancelled", "Cancelada"
    CHECK_IN = "check_in", "Check-in"
    CHECK_OUT = "check_out", "Check-out"
    NO_SHOW = "no_show", "No-show"
    EARLY_CHECK_IN = "early_check_in", "Check-in anticipado"
    LATE_CHECK_OUT = "late_check_out", "Check-out tardío"

class RoomBlockType(models.TextChoices):
    MAINTENANCE = "maintenance", "Mantenimiento"
    OUT_OF_SERVICE = "out_of_service", "Fuera de servicio"
    HOLD = "hold", "Bloqueo"

class Reservation(models.Model):
    hotel = models.ForeignKey(Hotel, on_delete=models.CASCADE, related_name="reservations")
    room = models.ForeignKey(Room, on_delete=models.PROTECT, related_name="reservations")
    guests = models.PositiveIntegerField(default=1, help_text="Número de huéspedes")
    guests_data = models.JSONField(default=list, help_text="Información de todos los huéspedes")
    check_in = models.DateField()
    check_out = models.DateField()
    status = models.CharField(max_length=20, choices=ReservationStatus.choices, default=ReservationStatus.PENDING)
    total_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def clean(self):
        if self.check_in >= self.check_out:
            raise ValidationError("check_in debe ser anterior a check_out.")

        if self.hotel_id is None and self.room_id:
            self.hotel = self.room.hotel

        # Validar número de huéspedes
        if self.room_id and self.guests:
            if self.guests > self.room.max_capacity:
                raise ValidationError(f"La habitación {self.room.name} tiene una capacidad máxima de {self.room.max_capacity} huéspedes.")
            if self.guests < 1:
                raise ValidationError("Debe haber al menos 1 huésped.")

        active_status = [
            ReservationStatus.PENDING,
            ReservationStatus.CONFIRMED,
            ReservationStatus.CHECK_IN,
        ]
        qs = Reservation.objects.filter(
            hotel=self.hotel,
            room=self.room,
            status__in=active_status,
            check_in__lt=self.check_out,
            check_out__gt=self.check_in,
        )
        if self.pk:
            qs = qs.exclude(pk=self.pk)
        if qs.exists():
            raise ValidationError("La habitación ya está reservada en ese rango.")
            
    def save(self, *args, **kwargs):
        if self.room_id and self.check_in and self.check_out:
            nights = (self.check_out - self.check_in).days
            self.total_price = max(nights, 0) * self.room.base_price
            if self.hotel_id is None:
                self.hotel = self.room.hotel
        super().save(*args, **kwargs)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["hotel", "room"]),
            models.Index(fields=["hotel", "check_in"]),
            models.Index(fields=["status"]),
        ]

    @property
    def guest_name(self):
        """Obtiene el nombre del huésped principal"""
        primary_guest = self.get_primary_guest()
        return primary_guest.get('name', '') if primary_guest else ''
    
    @property
    def guest_email(self):
        """Obtiene el email del huésped principal"""
        primary_guest = self.get_primary_guest()
        return primary_guest.get('email', '') if primary_guest else ''
    
    def get_primary_guest(self):
        """Obtiene el huésped principal (is_primary=True)"""
        if not self.guests_data:
            return None
        return next((guest for guest in self.guests_data if guest.get('is_primary', False)), None)
    
    def get_all_guests(self):
        """Obtiene todos los huéspedes ordenados (principal primero)"""
        if not self.guests_data:
            return []
        return sorted(self.guests_data, key=lambda x: (not x.get('is_primary', False), x.get('name', '')))

    def __str__(self):
        primary_guest = self.get_primary_guest()
        guest_name = primary_guest.get('name', 'Sin nombre') if primary_guest else 'Sin huésped'
        return f"{guest_name} - {self.room.name} - {self.check_in} -> {self.check_out}"

class RoomBlock(models.Model):
    hotel = models.ForeignKey(Hotel, on_delete=models.CASCADE, related_name="room_blocks")
    room = models.ForeignKey(Room, on_delete=models.CASCADE, related_name="room_blocks")
    start_date = models.DateField()
    end_date = models.DateField()
    block_type = models.CharField(max_length=20, choices=RoomBlockType.choices)
    reason = models.CharField(max_length=200, blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def clean(self):
        if self.start_date >= self.end_date:
            raise ValidationError("La fecha de inicio debe ser anterior a la fecha de fin")

    class Meta:
        verbose_name = "Bloqueo de habitación"
        verbose_name_plural = "Bloqueos de habitaciones"
        ordering = ["-start_date"]
        indexes = [
            models.Index(fields=["hotel", "room"]),
            models.Index(fields=["hotel", "start_date"]),
            models.Index(fields=["is_active"]),
        ]
