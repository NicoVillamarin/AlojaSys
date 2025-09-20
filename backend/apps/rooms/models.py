from django.db import models

class RoomType(models.TextChoices):
    SINGLE = "single", "Single"
    DOUBLE = "double", "Doble"
    TRIPLE = "triple", "Triple"
    SUITE = "suite", "Suite"

class RoomStatus(models.TextChoices):
    AVAILABLE = "available", "Disponible"
    OCCUPIED = "occupied", "Ocupada"
    MAINTENANCE = "maintenance", "Mantenimiento"
    OUT_OF_SERVICE = "out_of_service", "Fuera de servicio"
    RESERVED = "reserved", "Reservada"

# Create your models here.
class Room(models.Model):
    name = models.CharField(max_length=255, unique=True)
    hotel = models.ForeignKey("core.Hotel", on_delete=models.CASCADE, related_name="rooms")
    floor = models.IntegerField()
    room_type = models.CharField(max_length=255, choices=RoomType.choices, default=RoomType.SINGLE)
    number = models.IntegerField()
    description = models.TextField(blank=True, null=True)
    base_price = models.DecimalField(max_digits=10, decimal_places=2)
    capacity = models.PositiveIntegerField()
    status = models.CharField(max_length=255, choices=RoomStatus.choices, default=RoomStatus.AVAILABLE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        ordering = ["floor", "name"]
        verbose_name = "Habitación"
        verbose_name_plural = "Habitaciones"
        indexes = [
            models.Index(fields=["room_type"]),
            models.Index(fields=["status"]),
            models.Index(fields=["is_active"]),
        ]

    def __str__(self):
        return f"{self.name} - {self.get_room_type_display()}"