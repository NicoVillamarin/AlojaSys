from django.db import models
from decimal import Decimal
from apps.core.models import Hotel
from apps.rooms.models import Room, RoomType

class PriceMode(models.TextChoices):
    ABSOLUTE = "absolute", "Absoluto"
    DELTA = "delta", "Delta sobre la tarifa base"

class RatePlan(models.Model):
    hotel = models.ForeignKey(Hotel, on_delete=models.CASCADE, related_name="rate_plans")
    name = models.CharField(max_length=120)
    code = models.CharField(max_length=40, help_text="Código interno/para canal")
    is_active = models.BooleanField(default=True)
    priority = models.PositiveIntegerField(default=100, help_text="Mayor = más prioridad")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["hotel", "code"], name="uniq_rateplan_hotel_code"),
        ]
        ordering = ["-is_active", "-priority", "name"]

    def __str__(self) -> str:
        return f"{self.hotel.name} - {self.name}"

class RateRule(models.Model):
    plan = models.ForeignKey(RatePlan, on_delete=models.CASCADE, related_name="rules")
    name = models.CharField(max_length=120, blank=True)

    # Ventada de fechas
    start_date = models.DateField()
    end_date = models.DateField()

    #Dias de la semana
    apply_mon = models.BooleanField(default=True)
    apply_tue = models.BooleanField(default=True)
    apply_wed = models.BooleanField(default=True)
    apply_thu = models.BooleanField(default=True)
    apply_fri = models.BooleanField(default=True)
    apply_sat = models.BooleanField(default=True)
    apply_sun = models.BooleanField(default=True)

    # Target (uno de estos, o ninguno para aplicar a todos)
    target_room = models.ForeignKey(Room, on_delete=models.CASCADE, null=True, blank=True, related_name="rate_rules")
    target_room_type = models.CharField(max_length=30, choices=RoomType.choices, null=True, blank=True)

    # Canal
    channel = models.CharField(max_length=50, null=True, blank=True)

    # Prioridad de la regla (dentro del plan)
    priority = models.PositiveIntegerField(default=100)

    # Precios 
    price_mode = models.CharField(max_length=10, choices=PriceMode.choices, default=PriceMode.ABSOLUTE)
    base_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0, null=True, blank=True)
    extra_guest_fee_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0, null=True, blank=True, help_text="Extra por huésped por encima de la capacidad incluida (opcional).")

    # Precios por ocupación (override). Si existe un precio para 'guests', se usa ese y no se suma extra_guest_fee
    # Definido en modelo aparte: RateOccupancyPrice   

    # Restricciones
    min_stay = models.PositiveIntegerField(default=1, null=True, blank=True, help_text="Mínimo de noches para aplicar la regla (opcional).")
    max_stay = models.PositiveIntegerField(default=None, null=True, blank=True, help_text="Máximo de noches para aplicar la regla (opcional).")
    closed = models.BooleanField(default=False)
    closed_to_arrival = models.BooleanField(default=False)
    closed_to_departure = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-priority", "start_date", "end_date"]
        indexes = [
            models.Index(fields=["start_date", "end_date"]),
            models.Index(fields=["priority"]),
            models.Index(fields=["channel"]),
        ]

    def __str__(self) -> str:
        label = self.name or f"{self.start_date}→{self.end_date}"
        return f"{self.plan.name} - {label}"

class RateOccupancyPrice(models.Model):
    rule = models.ForeignKey(RateRule, on_delete=models.CASCADE, related_name="occupancy_prices")
    occupancy = models.PositiveIntegerField(default=1, help_text="Número de huéspedes")
    price = models.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        unique_together = ["rule", "occupancy"]
        ordering = ["occupancy"]
    
    def __str__(self) -> str:
        return f"{self.rule} - {self.occupancy} pax: {self.price}"


class DiscountType(models.TextChoices):
    PERCENT = "percent", "Porcentaje"
    FIXED = "fixed", "Monto fijo"


class PromoRule(models.Model):
    class PromoScope(models.TextChoices):
        PER_NIGHT = "per_night", "Por noche"
        PER_RESERVATION = "per_reservation", "Por reserva"

    hotel = models.ForeignKey(Hotel, on_delete=models.CASCADE, related_name="promo_rules")
    plan = models.ForeignKey(RatePlan, on_delete=models.CASCADE, null=True, blank=True, related_name="promo_rules")
    name = models.CharField(max_length=120)
    code = models.CharField(max_length=40, null=True, blank=True, help_text="Código promocional (opcional)")

    start_date = models.DateField()
    end_date = models.DateField()
    apply_mon = models.BooleanField(default=True)
    apply_tue = models.BooleanField(default=True)
    apply_wed = models.BooleanField(default=True)
    apply_thu = models.BooleanField(default=True)
    apply_fri = models.BooleanField(default=True)
    apply_sat = models.BooleanField(default=True)
    apply_sun = models.BooleanField(default=True)

    target_room = models.ForeignKey(Room, on_delete=models.CASCADE, null=True, blank=True, related_name="promo_rules")
    target_room_type = models.CharField(max_length=30, choices=RoomType.choices, null=True, blank=True)
    channel = models.CharField(max_length=50, null=True, blank=True)

    priority = models.PositiveIntegerField(default=100)
    discount_type = models.CharField(max_length=10, choices=DiscountType.choices, default=DiscountType.PERCENT)
    discount_value = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    scope = models.CharField(max_length=20, choices=PromoScope.choices, default=PromoScope.PER_NIGHT)
    combinable = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-is_active", "-priority", "start_date", "end_date"]
        indexes = [
            models.Index(fields=["hotel", "start_date", "end_date"]),
            models.Index(fields=["priority"]),
            models.Index(fields=["code"]),
        ]

    def __str__(self) -> str:
        return f"Promo {self.name} ({self.code or 'sin código'})"


class TaxRule(models.Model):
    class TaxAmountType(models.TextChoices):
        PERCENT = "percent", "Porcentaje"
        FIXED = "fixed", "Monto fijo"

    class TaxScope(models.TextChoices):
        PER_NIGHT = "per_night", "Por noche"
        PER_RESERVATION = "per_reservation", "Por reserva"
        PER_GUEST_PER_NIGHT = "per_guest_per_night", "Por huésped por noche"

    hotel = models.ForeignKey(Hotel, on_delete=models.CASCADE, related_name="tax_rules")
    name = models.CharField(max_length=120)
    channel = models.CharField(max_length=50, null=True, blank=True)
    amount_type = models.CharField(max_length=10, choices=TaxAmountType.choices, default=TaxAmountType.PERCENT)
    percent = models.DecimalField(max_digits=6, decimal_places=2, default=0, help_text="% aplicado sobre (base + extra - descuento)")
    fixed_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0, help_text="Monto fijo (si corresponde)")
    scope = models.CharField(max_length=30, choices=TaxScope.choices, default=TaxScope.PER_NIGHT)
    priority = models.PositiveIntegerField(default=100)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-is_active", "-priority", "name"]
        indexes = [
            models.Index(fields=["hotel"]),
            models.Index(fields=["priority"]),
        ]

    def __str__(self) -> str:
        return f"Impuesto {self.name} {self.percent}%"