from django.db import models
from django.core.exceptions import ValidationError
from typing import Optional

class RoomType(models.Model):
    """
    Catálogo configurable de tipos de habitación.

    NOTA: `Room.room_type` almacena el `code` (string) para mantener compatibilidad
    con el resto del sistema que hoy compara por código.
    """
    code = models.SlugField(
        max_length=50,
        unique=True,
        help_text="Código único (ej: single, double). Se usa en Room.room_type",
    )
    name = models.CharField(max_length=120, help_text="Nombre visible del tipo (ej: Doble)")
    alias = models.CharField(
        max_length=120,
        blank=True,
        null=True,
        help_text="Nombre de fantasía / abreviatura (ej: OI, II). Opcional.",
    )
    description = models.TextField(blank=True, null=True)
    sort_order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["sort_order", "name"]
        verbose_name = "Tipo de habitación"
        verbose_name_plural = "Tipos de habitación"
        indexes = [
            models.Index(fields=["code"]),
            models.Index(fields=["is_active"]),
        ]

    def __str__(self) -> str:
        return f"{self.name} ({self.code})"

class RoomStatus(models.TextChoices):
    AVAILABLE = "available", "Disponible"
    OCCUPIED = "occupied", "Ocupada"
    MAINTENANCE = "maintenance", "Mantenimiento"
    OUT_OF_SERVICE = "out_of_service", "Fuera de servicio"
    RESERVED = "reserved", "Reservada"

class CleaningStatus(models.TextChoices):
    DIRTY = "dirty", "Sucia"
    IN_PROGRESS = "in_progress", "En proceso"
    CLEAN = "clean", "Limpia"

# Create your models here.
class Room(models.Model):
    name = models.CharField(max_length=255, unique=True)
    hotel = models.ForeignKey("core.Hotel", on_delete=models.CASCADE, related_name="rooms")
    # Alfanumérico para permitir "PB", "1A", etc.
    floor = models.CharField(max_length=20)
    room_type = models.CharField(
        max_length=50,
        default="single",
        help_text="Código del tipo de habitación (configurable en rooms.RoomType)",
    )
    number = models.IntegerField()
    description = models.TextField(blank=True, null=True)
    base_price = models.DecimalField(max_digits=10, decimal_places=2)
    base_currency = models.ForeignKey(
        "core.Currency",
        on_delete=models.PROTECT,
        related_name="rooms_base",
        help_text="Moneda de la tarifa principal"
    )
    # Tarifa secundaria opcional (monto + moneda)
    secondary_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    secondary_currency = models.ForeignKey(
        "core.Currency",
        on_delete=models.PROTECT,
        related_name="rooms_secondary",
        null=True,
        blank=True,
        help_text="Moneda de la tarifa secundaria"
    )
    capacity = models.PositiveIntegerField(default=1)
    max_capacity = models.PositiveIntegerField(default=1)
    extra_guest_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    status = models.CharField(max_length=255, choices=RoomStatus.choices, default=RoomStatus.AVAILABLE)
    cleaning_status = models.CharField(max_length=20, choices=CleaningStatus.choices, default=CleaningStatus.CLEAN)
    primary_image = models.ImageField(
        upload_to='rooms/images/%Y/%m/%d/',
        blank=True,
        null=True,
        help_text="Imagen principal de la habitación"
    )
    images = models.JSONField(
        default=list,
        blank=True,
        help_text="Lista de URLs de imágenes adicionales de la habitación"
    )
    amenities = models.JSONField(
        default=list,
        blank=True,
        help_text="Lista de características/amenities de la habitación (strings)"
    )
    amenities_quantities = models.JSONField(
        default=dict,
        blank=True,
        help_text="Cantidades por amenity (dict: code -> int). Útil para camas (x2, x3, etc.)"
    )
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
            models.Index(fields=["cleaning_status"]),
            models.Index(fields=["is_active"]),
        ]
        # Django crea automáticamente estos permisos:
        # - rooms.add_room
        # - rooms.change_room
        # - rooms.delete_room
        # - rooms.view_room
        permissions = [
            # Puedes agregar permisos personalizados aquí si necesitas
            # ("maintenance_room", "Puede marcar habitaciones en mantenimiento"),
        ]

    def __str__(self):
        return f"{self.name} - {self.room_type_label or self.room_type}"

    @property
    def room_type_label(self) -> Optional[str]:
        """
        Nombre visible del tipo de habitación según catálogo `RoomType`.
        Evita depender de `choices` hardcodeados.
        """
        try:
            rt = RoomType.objects.only("name").filter(code=self.room_type).first()
            return rt.name if rt else None
        except Exception:
            return None

    def clean(self):
        """
        Mantener consistencia: max_capacity debe ser >= capacity.
        """
        super().clean()
        # Validar que room_type exista (si se mantiene el catálogo activo)
        if self.room_type:
            if not RoomType.objects.filter(code=self.room_type, is_active=True).exists():
                raise ValidationError({"room_type": f"Tipo de habitación inválido: '{self.room_type}'."})
        if self.capacity is not None and self.max_capacity is not None:
            if self.max_capacity < self.capacity:
                raise ValidationError({
                    "max_capacity": "max_capacity no puede ser menor que capacity."
                })
        # Consistencia de tarifa secundaria: debe venir completa (monto + moneda)
        if (self.secondary_price is None) ^ (self.secondary_currency_id is None):
            raise ValidationError({
                "secondary_price": "La tarifa secundaria debe tener monto y moneda.",
                "secondary_currency": "La tarifa secundaria debe tener monto y moneda.",
            })
        # Tarifa principal: si hay base_price, debe haber moneda
        if self.base_price is not None and self.base_currency_id is None:
            raise ValidationError({
                "base_currency": "La tarifa principal debe tener moneda.",
            })

        # Amenities quantities: validar dict y consistencia con amenities
        aq = self.amenities_quantities or {}
        if aq is None:
            aq = {}
        if not isinstance(aq, dict):
            raise ValidationError({"amenities_quantities": "Debe ser un objeto (dict) con cantidades por amenity."})
        amenities_list = self.amenities or []
        if amenities_list is None:
            amenities_list = []
        # Normalizar lista a strings
        try:
            amenities_set = set(str(a).strip() for a in amenities_list if str(a).strip())
        except Exception:
            amenities_set = set()

        for k, v in aq.items():
            code = str(k).strip()
            if not code:
                raise ValidationError({"amenities_quantities": "Hay un código de amenity vacío en quantities."})
            if code not in amenities_set:
                raise ValidationError({"amenities_quantities": f"'{code}' tiene cantidad pero no está seleccionado en amenities."})
            try:
                iv = int(v)
            except Exception:
                raise ValidationError({"amenities_quantities": f"Cantidad inválida para '{code}'."})
            if iv < 1:
                raise ValidationError({"amenities_quantities": f"La cantidad de '{code}' debe ser >= 1."})

    def save(self, *args, **kwargs):
        # Auto-corrección defensiva para datos viejos o formularios incompletos
        if self.capacity is not None and self.max_capacity is not None:
            if self.max_capacity < self.capacity:
                self.max_capacity = self.capacity
        super().save(*args, **kwargs)