from django.db import models
from django.contrib.auth import get_user_model
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

    # Auto-cancelación de reservas pendientes
    auto_cancel_enabled = models.BooleanField(
        default=True, 
        help_text="Habilitar auto-cancelación de reservas pendientes sin pago"
    )
    auto_cancel_days = models.PositiveIntegerField(
        default=7, 
        help_text="Días después de crear la reserva para auto-cancelar si no hay pagos"
    )

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


class CancellationPolicy(models.Model):
    """
    Política de cancelación configurable por hotel
    Sigue los estándares de los mejores PMS del mercado
    """
    
    class CancellationFeeType(models.TextChoices):
        NONE = "none", "Sin penalidad"
        PERCENTAGE = "percentage", "Porcentaje del total"
        FIXED = "fixed", "Monto fijo"
        FIRST_NIGHT = "first_night", "Primera noche"
        NIGHTS_PERCENTAGE = "nights_percentage", "Porcentaje por noche"
    
    class RefundType(models.TextChoices):
        FULL = "full", "Devolución completa"
        PARTIAL = "partial", "Devolución parcial"
        NONE = "none", "Sin devolución"
        VOUCHER = "voucher", "Voucher de crédito"
    
    class TimeUnit(models.TextChoices):
        HOURS = "hours", "Horas"
        DAYS = "days", "Días"
        WEEKS = "weeks", "Semanas"
    
    hotel = models.ForeignKey(Hotel, on_delete=models.CASCADE, related_name="cancellation_policies")
    name = models.CharField(max_length=120, help_text="Nombre descriptivo de la política")
    is_active = models.BooleanField(default=True)
    is_default = models.BooleanField(default=False)
    
    # Configuración de tiempos (en cascada)
    free_cancellation_time = models.PositiveIntegerField(default=24, help_text="Tiempo para cancelación gratuita")
    free_cancellation_unit = models.CharField(max_length=10, choices=TimeUnit.choices, default=TimeUnit.HOURS)
    
    partial_refund_time = models.PositiveIntegerField(default=72, help_text="Tiempo para devolución parcial")
    partial_refund_unit = models.CharField(max_length=10, choices=TimeUnit.choices, default=TimeUnit.HOURS)
    partial_refund_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=50.00, help_text="Porcentaje de devolución parcial")
    
    no_refund_time = models.PositiveIntegerField(default=168, help_text="Tiempo después del cual no hay devolución")
    no_refund_unit = models.CharField(max_length=10, choices=TimeUnit.choices, default=TimeUnit.HOURS)
    
    # Configuración de penalidades
    cancellation_fee_type = models.CharField(max_length=20, choices=CancellationFeeType.choices, default=CancellationFeeType.PERCENTAGE)
    cancellation_fee_value = models.DecimalField(max_digits=10, decimal_places=2, default=10.00, help_text="Valor de la penalidad (% o monto)")
    
    # Restricciones por estado de reserva
    allow_cancellation_after_checkin = models.BooleanField(default=False, help_text="Permitir cancelación después del check-in")
    allow_cancellation_after_checkout = models.BooleanField(default=False, help_text="Permitir cancelación después del check-out")
    allow_cancellation_no_show = models.BooleanField(default=True, help_text="Permitir cancelación de no-show")
    allow_cancellation_early_checkout = models.BooleanField(default=False, help_text="Permitir cancelación por salida anticipada")
    
    # Mensajes personalizados
    free_cancellation_message = models.TextField(blank=True, help_text="Mensaje para cancelación gratuita")
    partial_cancellation_message = models.TextField(blank=True, help_text="Mensaje para cancelación parcial")
    no_cancellation_message = models.TextField(blank=True, help_text="Mensaje para sin cancelación")
    cancellation_fee_message = models.TextField(blank=True, help_text="Mensaje para penalidad de cancelación")
    
    # Configuración avanzada
    apply_to_all_room_types = models.BooleanField(default=True, help_text="Aplicar a todos los tipos de habitación")
    room_types = models.JSONField(default=list, blank=True, help_text="Tipos de habitación específicos (si no aplica a todos)")
    
    # Configuración de canales
    apply_to_all_channels = models.BooleanField(default=True, help_text="Aplicar a todos los canales")
    channels = models.JSONField(default=list, blank=True, help_text="Canales específicos (si no aplica a todos)")
    
    # Configuración de temporadas
    apply_to_all_seasons = models.BooleanField(default=True, help_text="Aplicar a todas las temporadas")
    seasonal_rules = models.JSONField(default=list, blank=True, help_text="Reglas específicas por temporada")
    
    # Metadatos
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(get_user_model(), on_delete=models.SET_NULL, null=True, blank=True)
    
    class Meta:
        verbose_name = "Política de Cancelación"
        verbose_name_plural = "Políticas de Cancelación"
        ordering = ['-is_default', '-is_active', 'name']
        constraints = [
            models.UniqueConstraint(fields=["hotel", "name"], name="uniq_cancellation_policy_hotel_name"),
        ]
        indexes = [
            models.Index(fields=['hotel', 'is_active']),
            models.Index(fields=['is_default']),
        ]
    
    def __str__(self):
        return f"{self.hotel.name} - {self.name}"
    
    @staticmethod
    def resolve_for_hotel(hotel: Hotel):
        """Obtiene la política de cancelación activa para un hotel"""
        policy = CancellationPolicy.objects.filter(
            hotel=hotel, 
            is_active=True, 
            is_default=True
        ).first()
        if policy:
            return policy
        return CancellationPolicy.objects.filter(
            hotel=hotel, 
            is_active=True
        ).order_by('-id').first()
    
    def get_cancellation_rules(self, check_in_date, room_type=None, channel=None):
        """
        Obtiene las reglas de cancelación aplicables para una reserva específica
        """
        from datetime import datetime, timedelta
        
        # Calcular tiempo hasta el check-in
        now = datetime.now().date()
        time_until_checkin = (check_in_date - now).total_seconds()
        
        # Convertir a la unidad configurada
        if self.free_cancellation_unit == 'hours':
            free_cancellation_seconds = self.free_cancellation_time * 3600
        elif self.free_cancellation_unit == 'days':
            free_cancellation_seconds = self.free_cancellation_time * 86400
        else:  # weeks
            free_cancellation_seconds = self.free_cancellation_time * 604800
        
        if self.partial_refund_unit == 'hours':
            partial_refund_seconds = self.partial_refund_time * 3600
        elif self.partial_refund_unit == 'days':
            partial_refund_seconds = self.partial_refund_time * 86400
        else:  # weeks
            partial_refund_seconds = self.partial_refund_time * 604800
        
        if self.no_refund_unit == 'hours':
            no_refund_seconds = self.no_refund_time * 3600
        elif self.no_refund_unit == 'days':
            no_refund_seconds = self.no_refund_time * 86400
        else:  # weeks
            no_refund_seconds = self.no_refund_time * 604800
        
        # Determinar el tipo de cancelación
        if time_until_checkin >= free_cancellation_seconds:
            return {
                'type': 'free',
                'fee_type': 'none',
                'fee_value': 0,
                'message': self.free_cancellation_message or f"Cancelación gratuita hasta {self.free_cancellation_time} {self.free_cancellation_unit} antes del check-in"
            }
        elif time_until_checkin >= partial_refund_seconds:
            return {
                'type': 'partial',
                'fee_type': self.cancellation_fee_type,
                'fee_value': float(self.cancellation_fee_value),
                'message': self.partial_cancellation_message or f"Cancelación con penalidad hasta {self.partial_refund_time} {self.partial_refund_unit} antes del check-in"
            }
        else:
            return {
                'type': 'no_cancellation',
                'fee_type': self.cancellation_fee_type,
                'fee_value': float(self.cancellation_fee_value),
                'message': self.no_cancellation_message or f"Sin cancelación después de {self.no_refund_time} {self.no_refund_unit} antes del check-in"
            }


class RefundPolicy(models.Model):
    """
    Política de devolución configurable por hotel
    Maneja únicamente los aspectos de devolución de dinero
    """
    
    class RefundMethod(models.TextChoices):
        CASH = "cash", "Efectivo"
        BANK_TRANSFER = "bank_transfer", "Transferencia Bancaria"
        CREDIT_CARD = "credit_card", "Tarjeta de Crédito"
        VOUCHER = "voucher", "Voucher de Crédito"
        ORIGINAL_PAYMENT = "original_payment", "Método de Pago Original"
    
    class RefundType(models.TextChoices):
        FULL = "full", "Devolución Completa"
        PARTIAL = "partial", "Devolución Parcial"
        NONE = "none", "Sin Devolución"
        VOUCHER = "voucher", "Solo Voucher"
    
    class TimeUnit(models.TextChoices):
        HOURS = "hours", "Horas"
        DAYS = "days", "Días"
        WEEKS = "weeks", "Semanas"
    
    hotel = models.ForeignKey(Hotel, on_delete=models.CASCADE, related_name="refund_policies")
    name = models.CharField(max_length=120, help_text="Nombre descriptivo de la política")
    is_active = models.BooleanField(default=True)
    is_default = models.BooleanField(default=False)
    
    # Configuración de tiempos de devolución
    full_refund_time = models.PositiveIntegerField(default=24, help_text="Tiempo para devolución completa")
    full_refund_unit = models.CharField(max_length=10, choices=TimeUnit.choices, default=TimeUnit.HOURS)
    
    partial_refund_time = models.PositiveIntegerField(default=72, help_text="Tiempo para devolución parcial")
    partial_refund_unit = models.CharField(max_length=10, choices=TimeUnit.choices, default=TimeUnit.HOURS)
    partial_refund_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=50.00, help_text="Porcentaje de devolución parcial")
    
    no_refund_time = models.PositiveIntegerField(default=168, help_text="Tiempo después del cual no hay devolución")
    no_refund_unit = models.CharField(max_length=10, choices=TimeUnit.choices, default=TimeUnit.HOURS)
    
    # Configuración de métodos de devolución
    refund_method = models.CharField(max_length=20, choices=RefundMethod.choices, default=RefundMethod.ORIGINAL_PAYMENT)
    refund_processing_days = models.PositiveIntegerField(default=7, help_text="Días para procesar devolución")
    
    # Configuración de voucher (si aplica)
    voucher_expiry_days = models.PositiveIntegerField(default=365, help_text="Días de validez del voucher")
    voucher_minimum_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0, help_text="Monto mínimo para voucher")
    
    # Mensajes personalizados
    full_refund_message = models.TextField(blank=True, help_text="Mensaje para devolución completa")
    partial_refund_message = models.TextField(blank=True, help_text="Mensaje para devolución parcial")
    no_refund_message = models.TextField(blank=True, help_text="Mensaje para sin devolución")
    voucher_message = models.TextField(blank=True, help_text="Mensaje para voucher de crédito")
    
    # Configuración avanzada
    apply_to_all_room_types = models.BooleanField(default=True, help_text="Aplicar a todos los tipos de habitación")
    room_types = models.JSONField(default=list, blank=True, help_text="Tipos de habitación específicos (si no aplica a todos)")
    
    apply_to_all_channels = models.BooleanField(default=True, help_text="Aplicar a todos los canales")
    channels = models.JSONField(default=list, blank=True, help_text="Canales específicos (si no aplica a todos)")
    
    apply_to_all_seasons = models.BooleanField(default=True, help_text="Aplicar a todas las temporadas")
    seasonal_rules = models.JSONField(default=list, blank=True, help_text="Reglas específicas por temporada")
    
    # Metadatos
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(get_user_model(), on_delete=models.SET_NULL, null=True, blank=True)
    
    class Meta:
        verbose_name = "Política de Devolución"
        verbose_name_plural = "Políticas de Devolución"
        ordering = ['-is_default', '-is_active', 'name']
        constraints = [
            models.UniqueConstraint(fields=["hotel", "name"], name="uniq_refund_policy_hotel_name"),
        ]
        indexes = [
            models.Index(fields=['hotel', 'is_active']),
            models.Index(fields=['is_default']),
        ]
    
    def __str__(self):
        return f"{self.hotel.name} - {self.name}"
    
    @staticmethod
    def resolve_for_hotel(hotel: Hotel):
        """Obtiene la política de devolución activa para un hotel"""
        policy = RefundPolicy.objects.filter(
            hotel=hotel, 
            is_active=True, 
            is_default=True
        ).first()
        if policy:
            return policy
        return RefundPolicy.objects.filter(
            hotel=hotel, 
            is_active=True
        ).order_by('-id').first()
    
    def get_refund_rules(self, check_in_date, room_type=None, channel=None):
        """
        Obtiene las reglas de devolución aplicables para una reserva específica
        """
        from datetime import datetime, timedelta
        
        # Calcular tiempo hasta el check-in
        now = datetime.now().date()
        time_until_checkin = (check_in_date - now).total_seconds()
        
        # Convertir a la unidad configurada
        if self.full_refund_unit == 'hours':
            full_refund_seconds = self.full_refund_time * 3600
        elif self.full_refund_unit == 'days':
            full_refund_seconds = self.full_refund_time * 86400
        else:  # weeks
            full_refund_seconds = self.full_refund_time * 604800
        
        if self.partial_refund_unit == 'hours':
            partial_refund_seconds = self.partial_refund_time * 3600
        elif self.partial_refund_unit == 'days':
            partial_refund_seconds = self.partial_refund_time * 86400
        else:  # weeks
            partial_refund_seconds = self.partial_refund_time * 604800
        
        if self.no_refund_unit == 'hours':
            no_refund_seconds = self.no_refund_time * 3600
        elif self.no_refund_unit == 'days':
            no_refund_seconds = self.no_refund_time * 86400
        else:  # weeks
            no_refund_seconds = self.no_refund_time * 604800
        
        # Determinar el tipo de devolución
        if time_until_checkin >= full_refund_seconds:
            return {
                'type': 'full',
                'refund_percentage': 100,
                'refund_method': self.refund_method,
                'processing_days': self.refund_processing_days,
                'message': self.full_refund_message or f"Devolución completa hasta {self.full_refund_time} {self.full_refund_unit} antes del check-in"
            }
        elif time_until_checkin >= partial_refund_seconds:
            return {
                'type': 'partial',
                'refund_percentage': float(self.partial_refund_percentage),
                'refund_method': self.refund_method,
                'processing_days': self.refund_processing_days,
                'message': self.partial_refund_message or f"Devolución del {self.partial_refund_percentage}% hasta {self.partial_refund_time} {self.partial_refund_unit} antes del check-in"
            }
        else:
            return {
                'type': 'none',
                'refund_percentage': 0,
                'refund_method': self.refund_method,
                'processing_days': self.refund_processing_days,
                'message': self.no_refund_message or f"Sin devolución después de {self.no_refund_time} {self.no_refund_unit} antes del check-in"
            }


class RefundStatus(models.TextChoices):
    PENDING = "pending", "Pendiente"
    PROCESSING = "processing", "Procesando"
    COMPLETED = "completed", "Completado"
    FAILED = "failed", "Fallido"
    CANCELLED = "cancelled", "Cancelado"


class RefundReason(models.TextChoices):
    CANCELLATION = "cancellation", "Cancelación de Reserva"
    PARTIAL_CANCELLATION = "partial_cancellation", "Cancelación Parcial"
    OVERPAYMENT = "overpayment", "Sobrepago"
    DISCOUNT_APPLIED = "discount_applied", "Descuento Aplicado"
    ADMIN_ADJUSTMENT = "admin_adjustment", "Ajuste Administrativo"
    CUSTOMER_REQUEST = "customer_request", "Solicitud del Cliente"
    SYSTEM_ERROR = "system_error", "Error del Sistema"


class Refund(models.Model):
    """
    Modelo para manejar reembolsos explícitos
    Rastrea el flujo financiero de devoluciones de dinero
    """
    reservation = models.ForeignKey(
        Reservation, 
        on_delete=models.CASCADE, 
        related_name="refunds",
        help_text="Reserva asociada al reembolso"
    )
    payment = models.ForeignKey(
        'reservations.Payment', 
        on_delete=models.CASCADE, 
        related_name="refunds",
        help_text="Pago original que se está reembolsando"
    )
    amount = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        help_text="Monto del reembolso"
    )
    reason = models.CharField(
        max_length=30, 
        choices=RefundReason.choices,
        help_text="Razón del reembolso"
    )
    status = models.CharField(
        max_length=20, 
        choices=RefundStatus.choices, 
        default=RefundStatus.PENDING,
        help_text="Estado del reembolso"
    )
    refund_method = models.CharField(
        max_length=30,
        help_text="Método de reembolso (cash, bank_transfer, credit_card, etc.)"
    )
    processing_days = models.PositiveIntegerField(
        default=7,
        help_text="Días estimados para procesar el reembolso"
    )
    external_reference = models.CharField(
        max_length=200,
        blank=True,
        null=True,
        help_text="Referencia externa del reembolso (ej: ID de Mercado Pago)"
    )
    notes = models.TextField(
        blank=True,
        null=True,
        help_text="Notas adicionales sobre el reembolso"
    )
    processed_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Fecha y hora cuando se completó el reembolso"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        get_user_model(), 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        help_text="Usuario que creó el reembolso"
    )

    class Meta:
        verbose_name = "Reembolso"
        verbose_name_plural = "Reembolsos"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['reservation', 'status']),
            models.Index(fields=['status', 'created_at']),
            models.Index(fields=['payment']),
        ]

    def __str__(self):
        return f"Reembolso {self.id} - {self.reservation.display_name} - ${self.amount}"

    def mark_as_processing(self):
        """Marca el reembolso como en procesamiento"""
        self.status = RefundStatus.PROCESSING
        self.save(update_fields=['status', 'updated_at'])

    def mark_as_completed(self, external_reference=None):
        """Marca el reembolso como completado"""
        from django.utils import timezone
        self.status = RefundStatus.COMPLETED
        self.processed_at = timezone.now()
        if external_reference:
            self.external_reference = external_reference
        self.save(update_fields=['status', 'processed_at', 'external_reference', 'updated_at'])

    def mark_as_failed(self, notes=None):
        """Marca el reembolso como fallido"""
        self.status = RefundStatus.FAILED
        if notes:
            self.notes = notes
        self.save(update_fields=['status', 'notes', 'updated_at'])

    def cancel(self, notes=None):
        """Cancela el reembolso"""
        self.status = RefundStatus.CANCELLED
        if notes:
            self.notes = notes
        self.save(update_fields=['status', 'notes', 'updated_at'])

    @property
    def is_pending(self):
        return self.status == RefundStatus.PENDING

    @property
    def is_processing(self):
        return self.status == RefundStatus.PROCESSING

    @property
    def is_completed(self):
        return self.status == RefundStatus.COMPLETED

    @property
    def is_failed(self):
        return self.status == RefundStatus.FAILED

    @property
    def is_cancelled(self):
        return self.status == RefundStatus.CANCELLED