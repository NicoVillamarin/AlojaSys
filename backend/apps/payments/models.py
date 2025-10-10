from django.db import models
from apps.core.models import Hotel
from apps.reservations.models import Reservation
from apps.enterprises.models import Enterprise

class PaymentGatewayProvider(models.TextChoices):
    MERCADO_PAGO = "mercado_pago", "Mercado Pago"

class PaymentGatewayConfig(models.Model):
    provider = models.CharField(max_length=30, choices=PaymentGatewayProvider.choices, default=PaymentGatewayProvider.MERCADO_PAGO)
    enterprise = models.ForeignKey(Enterprise, on_delete=models.CASCADE, related_name="payment_configs", null=True, blank=True)
    hotel = models.ForeignKey(Hotel, on_delete=models.CASCADE, related_name="payment_configs", null=True, blank=True)

    public_key = models.CharField(max_length=200)
    access_token = models.CharField(max_length=200)
    integrator_id = models.CharField(max_length=200, blank=True)

    is_test = models.BooleanField(default=True)
    country_code = models.CharField(max_length=2, blank=True)   # ej: AR
    currency_code = models.CharField(max_length=3, blank=True)  # ej: ARS
    webhook_secret = models.CharField(max_length=200, blank=True)
    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["provider", "hotel"], name="uniq_gateway_hotel", condition=models.Q(hotel__isnull=False)),
            models.UniqueConstraint(fields=["provider", "enterprise"], name="uniq_gateway_enterprise", condition=models.Q(enterprise__isnull=False)),
        ]

    def __str__(self) -> str:
        scope = self.hotel.name if self.hotel_id else (self.enterprise.name if self.enterprise_id else "global")
        return f"{self.get_provider_display()} - {scope}"

    @staticmethod
    def resolve_for_hotel(hotel: Hotel):
        cfg = PaymentGatewayConfig.objects.filter(hotel=hotel, is_active=True).first()
        if cfg:
            return cfg
        if hotel.enterprise_id:
            return PaymentGatewayConfig.objects.filter(enterprise=hotel.enterprise, is_active=True).first()
        return None

class PaymentIntentStatus(models.TextChoices):
    PENDING = "pending", "Pendiente"
    CREATED = "created", "Creado"
    APPROVED = "approved", "Aprobado"
    REJECTED = "rejected", "Rechazado"
    CANCELLED = "cancelled", "Cancelado"

class PaymentIntent(models.Model):
    reservation = models.ForeignKey(Reservation, on_delete=models.CASCADE, related_name="payment_intents")
    hotel = models.ForeignKey(Hotel, on_delete=models.CASCADE, related_name="payment_intents")
    enterprise = models.ForeignKey(Enterprise, on_delete=models.CASCADE, related_name="payment_intents", null=True, blank=True)

    amount = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=3, default="ARS")
    description = models.CharField(max_length=200, blank=True)

    # Mercado Pago fields
    mp_preference_id = models.CharField(max_length=80, blank=True)
    mp_payment_id = models.CharField(max_length=80, blank=True)
    external_reference = models.CharField(max_length=120, blank=True)

    status = models.CharField(max_length=20, choices=PaymentIntentStatus.choices, default=PaymentIntentStatus.PENDING)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=["hotel", "status"]),
            models.Index(fields=["reservation"]),
        ]

    def __str__(self) -> str:
        return f"Payment Intent {self.id} - {self.status}"


# Métodos disponibles para cobrar (configuración)
class PaymentMethod(models.Model):
    code = models.CharField(max_length=40, unique=True)
    name = models.CharField(max_length=120)
    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]

    def __str__(self) -> str:
        return self.name


class PaymentPolicy(models.Model):
    class DepositType(models.TextChoices):
        NONE = "none", "Sin adelanto"
        PERCENTAGE = "percentage", "Porcentaje"
        FIXED = "fixed", "Monto fijo"

    class DepositDue(models.TextChoices):
        CONFIRMATION = "confirmation", "Al confirmar"
        DAYS_BEFORE = "days_before", "Días antes del check-in"
        CHECK_IN = "check_in", "Al check-in"

    class BalanceDue(models.TextChoices):
        CHECK_IN = "check_in", "Al check-in"
        CHECK_OUT = "check_out", "Al check-out"

    hotel = models.ForeignKey(Hotel, on_delete=models.CASCADE, related_name="payment_policies")
    name = models.CharField(max_length=120)
    is_active = models.BooleanField(default=True)
    is_default = models.BooleanField(default=False)

    # Política de adelanto
    allow_deposit = models.BooleanField(default=True, help_text="Permitir pago de depósito/seña")
    deposit_type = models.CharField(max_length=20, choices=DepositType.choices, default=DepositType.NONE)
    deposit_value = models.DecimalField(max_digits=10, decimal_places=2, default=0)  # % o monto
    deposit_due = models.CharField(max_length=20, choices=DepositDue.choices, default=DepositDue.CONFIRMATION)
    deposit_days_before = models.PositiveIntegerField(default=0)

    # Dónde se cobra el saldo cuando hay adelanto
    balance_due = models.CharField(max_length=20, choices=BalanceDue.choices, default=BalanceDue.CHECK_IN)

    # Métodos de pago habilitados
    methods = models.ManyToManyField(PaymentMethod, related_name="policies", blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["hotel", "name"], name="uniq_policy_hotel_name"),
        ]

    def __str__(self) -> str:
        return f"{self.hotel.name} - {self.name}"

    @staticmethod
    def resolve_for_hotel(hotel: Hotel):
        pol = PaymentPolicy.objects.filter(hotel=hotel, is_active=True, is_default=True).first()
        if pol:
            return pol
        return PaymentPolicy.objects.filter(hotel=hotel, is_active=True).order_by("-id").first()