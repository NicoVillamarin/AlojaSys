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
    is_production = models.BooleanField(default=False, help_text="Indica si esta configuración es para producción")
    country_code = models.CharField(max_length=2, blank=True)   # ej: AR
    currency_code = models.CharField(max_length=3, blank=True)  # ej: ARS
    webhook_secret = models.CharField(max_length=200, blank=True)
    is_active = models.BooleanField(default=True)
    
    # Configuración de reembolsos
    refund_window_days = models.PositiveIntegerField(null=True, blank=True, help_text="Días límite para procesar reembolsos (null = sin límite)")
    partial_refunds_allowed = models.BooleanField(default=True, help_text="Permitir reembolsos parciales")

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

    def clean(self):
        from django.core.exceptions import ValidationError
        
        # Validar refund_window_days
        if self.refund_window_days is not None and self.refund_window_days < 0:
            raise ValidationError({'refund_window_days': 'El valor debe ser mayor o igual a 0'})
        
        # Validar que no se mezclen keys de producción con is_test=True
        if self.is_production and self.is_test:
            raise ValidationError({
                'is_production': 'No se puede marcar como producción si is_test=True',
                'is_test': 'No se puede usar is_test=True en configuración de producción'
            })
        
        # Validar que las keys de producción no sean de test
        if self.is_production:
            # Verificar que access_token no sea de test (contiene 'TEST' o es muy corto)
            if 'TEST' in self.access_token.upper() or len(self.access_token) < 20:
                raise ValidationError({
                    'access_token': 'El access_token parece ser de test. En producción debe usar keys reales.'
                })
            
            # Verificar que public_key no sea de test
            if 'TEST' in self.public_key.upper() or len(self.public_key) < 20:
                raise ValidationError({
                    'public_key': 'El public_key parece ser de test. En producción debe usar keys reales.'
                })
        
        # Validar que las keys de test no sean de producción
        if self.is_test and not self.is_production:
            # Verificar que access_token sea de test (contiene 'TEST' o es corto)
            if 'TEST' not in self.access_token.upper() and len(self.access_token) > 20:
                raise ValidationError({
                    'access_token': 'El access_token parece ser de producción. En test debe usar keys de prueba.'
                })
            
            # Verificar que public_key sea de test
            if 'TEST' not in self.public_key.upper() and len(self.public_key) > 20:
                raise ValidationError({
                    'public_key': 'El public_key parece ser de producción. En test debe usar keys de prueba.'
                })
    
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
    
    # Configuración de reembolsos automáticos
    auto_refund_on_cancel = models.BooleanField(default=False, help_text="Procesar reembolso automáticamente al cancelar")
    
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
        
        # Debug: imprimir información de cálculo
        print(f"DEBUG CancellationPolicy: check_in_date={check_in_date}, now={now}, time_until_checkin={time_until_checkin}")
        
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
        
        # Debug: imprimir valores calculados
        print(f"DEBUG CancellationPolicy: free_cancellation_seconds={free_cancellation_seconds}, partial_refund_seconds={partial_refund_seconds}, no_refund_seconds={no_refund_seconds}")
        
        # Determinar el tipo de cancelación
        # Lógica corregida: free_cancellation_time debe ser MAYOR que partial_refund_time
        if time_until_checkin >= free_cancellation_seconds:
            print(f"DEBUG CancellationPolicy: Aplicando cancelación gratuita (time_until_checkin={time_until_checkin} >= free_cancellation_seconds={free_cancellation_seconds})")
            return {
                'type': 'free',
                'fee_type': 'none',
                'fee_value': 0,
                'message': self.free_cancellation_message or f"Cancelación gratuita hasta {self.free_cancellation_time} {self.free_cancellation_unit} antes del check-in"
            }
        elif time_until_checkin >= partial_refund_seconds:
            print(f"DEBUG CancellationPolicy: Aplicando cancelación parcial (time_until_checkin={time_until_checkin} >= partial_refund_seconds={partial_refund_seconds})")
            return {
                'type': 'partial',
                'fee_type': self.cancellation_fee_type,
                'fee_value': float(self.cancellation_fee_value),
                'message': self.partial_cancellation_message or f"Cancelación con penalidad hasta {self.partial_refund_time} {self.partial_refund_unit} antes del check-in"
            }
        else:
            print(f"DEBUG CancellationPolicy: Aplicando sin cancelación (time_until_checkin={time_until_checkin} < partial_refund_seconds={partial_refund_seconds})")
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
        null=True,
        blank=True,
        help_text="Pago original que se está reembolsando"
    )
    amount = models.DecimalField(
        max_digits=12, 
        decimal_places=2,
        help_text="Monto del reembolso"
    )
    reason = models.CharField(
        max_length=30, 
        choices=RefundReason.choices,
        null=True,
        blank=True,
        help_text="Razón del reembolso"
    )
    status = models.CharField(
        max_length=20, 
        choices=RefundStatus.choices, 
        default=RefundStatus.PENDING,
        help_text="Estado del reembolso"
    )
    method = models.CharField(
        max_length=30,
        default='original_payment',
        help_text="Método de reembolso (original_payment, voucher, bank_transfer, etc.)"
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
    processed_by = models.ForeignKey(
        get_user_model(), 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name="processed_refunds",
        help_text="Usuario que procesó el reembolso"
    )
    # Campo para historial compacto (similar a ReservationChangeLog)
    history = models.JSONField(
        default=list,
        blank=True,
        help_text="Historial compacto de cambios del reembolso"
    )
    
    # URL del comprobante PDF generado
    receipt_pdf_url = models.URLField(
        blank=True, 
        null=True, 
        help_text="URL del comprobante PDF generado"
    )
    
    # Número de comprobante serio (ej: C-0001-000045)
    receipt_number = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        unique=True,
        help_text="Número de comprobante serio (ej: C-0001-000045)"
    )
    
    # Relación con voucher generado (si el método de reembolso es voucher)
    generated_voucher = models.ForeignKey(
        'RefundVoucher',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="source_refund",
        help_text="Voucher generado por este reembolso"
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
    
    def save(self, *args, **kwargs):
        """Override save para crear log automático al crear un refund"""
        is_new = self.pk is None
        
        # Generar número de comprobante si no existe
        if not self.receipt_number:
            try:
                self.receipt_number = ReceiptNumberSequence.generate_receipt_number(
                    hotel=self.reservation.hotel,
                    receipt_type=ReceiptNumberSequence.ReceiptType.REFUND  # "D"
                )
            except Exception as e:
                # Si hay error, no fallar la creación del refund
                pass
        
        super().save(*args, **kwargs)
        
        # Si es un nuevo refund, crear log de creación
        if is_new:
            from .services.refund_audit_service import RefundAuditService
            RefundAuditService.log_refund_created(self, self.created_by)
            
            # Si el refund se crea ya completado, generar automáticamente el PDF del comprobante
            if self.status == RefundStatus.COMPLETED and not self.receipt_pdf_url:
                try:
                    from .tasks import generate_payment_receipt_pdf
                    # Generar el PDF de forma asíncrona
                    generate_payment_receipt_pdf.delay(self.id, 'refund')
                    
                    # Enviar notificación sobre el comprobante generado
                    try:
                        from apps.notifications.services import NotificationService
                        
                        user_id = self.created_by_id if self.created_by_id else None
                        
                        NotificationService.create_receipt_generated_notification(
                            receipt_type='refund',
                            receipt_number=self.receipt_number or f'D-{self.id}',
                            reservation_code=f"RES-{self.reservation.id}",
                            hotel_name=self.reservation.hotel.name,
                            amount=str(self.amount),
                            hotel_id=self.reservation.hotel.id,
                            reservation_id=self.reservation.id,
                            user_id=user_id
                        )
                    except Exception as notif_error:
                        # No fallar si hay error en notificación
                        import logging
                        logger = logging.getLogger(__name__)
                        logger.error(f"Error creando notificación para refund {self.id}: {notif_error}")
                        
                except Exception as e:
                    # Si hay error generando el PDF, no fallar la creación del refund
                    import logging
                    logger = logging.getLogger(__name__)
                    logger.error(f"Error generando PDF automáticamente para refund {self.id}: {e}")

    def mark_as_processing(self, user=None):
        """Marca el reembolso como en procesamiento"""
        old_status = self.status
        self.status = RefundStatus.PROCESSING
        self.save(update_fields=['status', 'updated_at'])
        
        # Log del cambio de estado
        from .services.refund_audit_service import RefundAuditService
        RefundAuditService.log_status_change(self, old_status, self.status, user, "Iniciando procesamiento")
        RefundAuditService.log_processing_started(self, user)

    def mark_as_completed(self, external_reference=None, user=None):
        """Marca el reembolso como completado"""
        from django.utils import timezone
        old_status = self.status
        self.status = RefundStatus.COMPLETED
        self.processed_at = timezone.now()
        if user:
            self.processed_by = user
        if external_reference:
            self.external_reference = external_reference
        self.save(update_fields=['status', 'processed_at', 'processed_by', 'external_reference', 'updated_at'])
        
        # Log del cambio de estado y completado
        from .services.refund_audit_service import RefundAuditService
        RefundAuditService.log_status_change(self, old_status, self.status, user, "Procesamiento completado")
        RefundAuditService.log_processing_completed(self, external_reference, user)
        
        # Generar PDF de recibo de reembolso
        try:
            from .tasks import generate_payment_receipt_pdf, send_payment_receipt_email
            generate_payment_receipt_pdf.delay(self.id, 'refund')
            
            # Enviar notificación sobre el comprobante generado
            try:
                from apps.notifications.services import NotificationService
                
                user_id = self.created_by_id if self.created_by_id else None
                
                NotificationService.create_receipt_generated_notification(
                    receipt_type='refund',
                    receipt_number=self.receipt_number or f'D-{self.id}',
                    reservation_code=f"RES-{self.reservation.id}",
                    hotel_name=self.reservation.hotel.name,
                    amount=str(self.amount),
                    hotel_id=self.reservation.hotel.id,
                    reservation_id=self.reservation.id,
                    user_id=user_id
                )
            except Exception as notif_error:
                # No fallar si hay error en notificación
                import logging
                logger = logging.getLogger(__name__)
                logger.error(f"Error creando notificación para reembolso {self.id}: {notif_error}")
            
            # Enviar email con recibo si hay email del huésped
            if self.reservation.guests_data:
                # guests_data es una lista, buscar el huésped principal
                primary_guest = next(
                    (guest for guest in self.reservation.guests_data if guest.get('is_primary', False)), 
                    None
                )
                if not primary_guest and self.reservation.guests_data:
                    primary_guest = self.reservation.guests_data[0]
                
                if primary_guest and primary_guest.get('email'):
                    send_payment_receipt_email.delay(
                        self.id, 
                        'refund', 
                        primary_guest['email']
                    )
        except Exception as e:
            # No fallar el proceso si hay error generando PDF
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error generando PDF de reembolso {self.id}: {e}")

    def mark_as_failed(self, notes=None, user=None, error_message=None):
        """Marca el reembolso como fallido"""
        old_status = self.status
        self.status = RefundStatus.FAILED
        if notes:
            self.notes = notes
        self.save(update_fields=['status', 'notes', 'updated_at'])
        
        # Log del cambio de estado y fallo
        from .services.refund_audit_service import RefundAuditService
        RefundAuditService.log_status_change(self, old_status, self.status, user, "Procesamiento fallido")
        RefundAuditService.log_processing_failed(self, error_message or "Error no especificado", user)

    def cancel(self, notes=None, user=None):
        """Cancela el reembolso"""
        old_status = self.status
        self.status = RefundStatus.CANCELLED
        if notes:
            self.notes = notes
        self.save(update_fields=['status', 'notes', 'updated_at'])
        
        # Log del cambio de estado y cancelación
        from .services.refund_audit_service import RefundAuditService
        RefundAuditService.log_status_change(self, old_status, self.status, user, "Reembolso cancelado")
        RefundAuditService.log_refund_event(
            refund=self,
            event_type="cancelled",
            action="refund_cancelled",
            user=user,
            message=f"Reembolso cancelado" + (f" - {notes}" if notes else "")
        )

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


class RefundLogEvent(models.TextChoices):
    """Eventos que se pueden registrar en el log de refunds"""
    CREATED = "created", "Creado"
    STATUS_CHANGED = "status_changed", "Estado Cambiado"
    PROCESSING_STARTED = "processing_started", "Procesamiento Iniciado"
    PROCESSING_COMPLETED = "processing_completed", "Procesamiento Completado"
    PROCESSING_FAILED = "processing_failed", "Procesamiento Fallido"
    EXTERNAL_REFERENCE_UPDATED = "external_reference_updated", "Referencia Externa Actualizada"
    NOTES_UPDATED = "notes_updated", "Notas Actualizadas"
    CANCELLED = "cancelled", "Cancelado"
    RETRY_ATTEMPT = "retry_attempt", "Intento de Reintento"
    GATEWAY_ERROR = "gateway_error", "Error de Pasarela"
    MANUAL_INTERVENTION = "manual_intervention", "Intervención Manual"


class RefundVoucherStatus(models.TextChoices):
    """Estados de un voucher de reembolso"""
    ACTIVE = "active", "Activo"
    USED = "used", "Usado"
    EXPIRED = "expired", "Expirado"
    CANCELLED = "cancelled", "Cancelado"


class RefundVoucher(models.Model):
    """
    Voucher de reembolso reutilizable
    Permite crear vouchers que pueden ser utilizados en futuras reservas
    """
    code = models.CharField(
        max_length=50,
        unique=True,
        help_text="Código único del voucher"
    )
    amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        help_text="Monto del voucher"
    )
    expiry_date = models.DateTimeField(
        help_text="Fecha de expiración del voucher"
    )
    status = models.CharField(
        max_length=20,
        choices=RefundVoucherStatus.choices,
        default=RefundVoucherStatus.ACTIVE,
        help_text="Estado del voucher"
    )
    
    # Relaciones
    hotel = models.ForeignKey(
        Hotel,
        on_delete=models.CASCADE,
        related_name="refund_vouchers",
        help_text="Hotel que emitió el voucher"
    )
    original_refund = models.ForeignKey(
        Refund,
        on_delete=models.CASCADE,
        related_name="generated_vouchers",
        null=True,
        blank=True,
        help_text="Reembolso que generó este voucher"
    )
    used_in_reservation = models.ForeignKey(
        Reservation,
        on_delete=models.SET_NULL,
        related_name="used_vouchers",
        null=True,
        blank=True,
        help_text="Reserva donde se usó el voucher"
    )
    
    # Metadatos
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        get_user_model(),
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        help_text="Usuario que creó el voucher"
    )
    used_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Fecha y hora cuando se usó el voucher"
    )
    used_by = models.ForeignKey(
        get_user_model(),
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="used_vouchers",
        help_text="Usuario que usó el voucher"
    )
    
    # Campos adicionales
    notes = models.TextField(
        blank=True,
        null=True,
        help_text="Notas adicionales sobre el voucher"
    )
    remaining_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Monto restante del voucher (para vouchers parcialmente usados)"
    )

    class Meta:
        verbose_name = "Voucher de Reembolso"
        verbose_name_plural = "Vouchers de Reembolso"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['code']),
            models.Index(fields=['hotel', 'status']),
            models.Index(fields=['status', 'expiry_date']),
            models.Index(fields=['original_refund']),
        ]

    def __str__(self):
        return f"Voucher {self.code} - ${self.amount} - {self.get_status_display()}"

    def save(self, *args, **kwargs):
        """Override save para generar código único y validar estado"""
        if not self.code:
            self.code = self.generate_unique_code()
        
        # Si es nuevo voucher, establecer remaining_amount igual al amount
        if not self.pk and not self.remaining_amount:
            self.remaining_amount = self.amount
            
        super().save(*args, **kwargs)

    @classmethod
    def generate_unique_code(cls):
        """Genera un código único para el voucher"""
        import uuid
        import string
        import random
        
        # Generar código con formato: VCH-XXXX-XXXX
        while True:
            code = f"VCH-{''.join(random.choices(string.ascii_uppercase + string.digits, k=4))}-{''.join(random.choices(string.ascii_uppercase + string.digits, k=4))}"
            if not cls.objects.filter(code=code).exists():
                return code

    def is_expired(self):
        """Verifica si el voucher ha expirado"""
        from django.utils import timezone
        return timezone.now() > self.expiry_date

    def can_be_used(self):
        """Verifica si el voucher puede ser usado"""
        return (
            self.status == RefundVoucherStatus.ACTIVE and
            not self.is_expired() and
            self.remaining_amount and
            self.remaining_amount > 0
        )

    def use_voucher(self, amount, reservation, user=None):
        """Usa el voucher para una reserva específica"""
        if not self.can_be_used():
            raise ValueError("El voucher no puede ser usado")
        
        if amount > self.remaining_amount:
            raise ValueError("El monto solicitado excede el monto restante del voucher")
        
        from django.utils import timezone
        
        # Actualizar voucher
        self.remaining_amount -= amount
        if self.remaining_amount <= 0:
            self.status = RefundVoucherStatus.USED
            self.used_at = timezone.now()
            self.used_by = user
            self.used_in_reservation = reservation
        
        self.save(update_fields=[
            'remaining_amount', 'status', 'used_at', 'used_by', 
            'used_in_reservation', 'updated_at'
        ])
        
        return self

    def cancel_voucher(self, user=None, reason=None):
        """Cancela el voucher"""
        if self.status not in [RefundVoucherStatus.ACTIVE]:
            raise ValueError("Solo se pueden cancelar vouchers activos")
        
        self.status = RefundVoucherStatus.CANCELLED
        if reason:
            self.notes = f"{self.notes or ''}\nCancelado: {reason}".strip()
        
        self.save(update_fields=['status', 'notes', 'updated_at'])

    @property
    def is_active(self):
        return self.status == RefundVoucherStatus.ACTIVE

    @property
    def is_used(self):
        return self.status == RefundVoucherStatus.USED

    @property
    def is_cancelled(self):
        return self.status == RefundVoucherStatus.CANCELLED


class RefundLog(models.Model):
    """
    Log detallado de eventos de reembolsos para auditoría
    Similar a ReservationChangeLog pero específico para refunds
    """
    refund = models.ForeignKey(
        Refund, 
        on_delete=models.CASCADE, 
        related_name="logs",
        help_text="Reembolso asociado al log"
    )
    event_type = models.CharField(
        max_length=30, 
        choices=RefundLogEvent.choices,
        help_text="Tipo de evento registrado"
    )
    status = models.CharField(
        max_length=20, 
        choices=RefundStatus.choices,
        help_text="Estado del reembolso en este momento"
    )
    timestamp = models.DateTimeField(
        auto_now_add=True,
        help_text="Fecha y hora del evento"
    )
    user = models.ForeignKey(
        get_user_model(), 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        help_text="Usuario que realizó la acción (null = sistema)"
    )
    action = models.CharField(
        max_length=50,
        help_text="Acción específica realizada"
    )
    details = models.JSONField(
        default=dict,
        blank=True,
        help_text="Detalles adicionales del evento"
    )
    external_reference = models.CharField(
        max_length=200,
        blank=True,
        null=True,
        help_text="Referencia externa si aplica"
    )
    error_message = models.TextField(
        blank=True,
        null=True,
        help_text="Mensaje de error si aplica"
    )
    message = models.CharField(
        max_length=300,
        blank=True,
        null=True,
        help_text="Mensaje descriptivo del evento"
    )

    class Meta:
        verbose_name = "Log de Reembolso"
        verbose_name_plural = "Logs de Reembolsos"
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['refund', 'timestamp']),
            models.Index(fields=['event_type', 'timestamp']),
            models.Index(fields=['status', 'timestamp']),
        ]

    def __str__(self):
        return f"Log {self.id} - {self.refund.id} - {self.get_event_type_display()}"


# ===== CONCILIACIÓN BANCARIA =====

class ReconciliationStatus(models.TextChoices):
    """Estados de conciliación bancaria"""
    PENDING = "pending", "Pendiente"
    PROCESSING = "processing", "Procesando"
    COMPLETED = "completed", "Completada"
    FAILED = "failed", "Fallida"
    MANUAL_REVIEW = "manual_review", "Revisión Manual"


class MatchType(models.TextChoices):
    """Tipos de matching en conciliación"""
    EXACT = "exact", "Exacto"
    FUZZY = "fuzzy", "Aproximado"
    PARTIAL = "partial", "Parcial"
    MANUAL = "manual", "Manual"


class ReconciliationEventType(models.TextChoices):
    """Tipos de eventos en audit log de conciliación"""
    CSV_UPLOADED = "csv_uploaded", "CSV Subido"
    PROCESSING_STARTED = "processing_started", "Procesamiento Iniciado"
    AUTO_MATCHED = "auto_matched", "Match Automático"
    MANUAL_MATCHED = "manual_matched", "Match Manual"
    PENDING_REVIEW = "pending_review", "Pendiente de Revisión"
    UNMATCHED = "unmatched", "Sin Match"
    PARTIAL_MATCH = "partial_match", "Match Parcial"
    REVERSAL_DETECTED = "reversal_detected", "Reversión Detectada"
    PROCESSING_COMPLETED = "processing_completed", "Procesamiento Completado"
    ERROR = "error", "Error"


class BankReconciliationConfig(models.Model):
    """Configuración de conciliación bancaria por hotel"""
    hotel = models.ForeignKey(Hotel, on_delete=models.CASCADE, related_name="reconciliation_configs")
    
    # Tolerancias de matching
    exact_match_date_tolerance = models.PositiveIntegerField(default=1, help_text="Días de tolerancia para match exacto")
    fuzzy_match_amount_tolerance_percent = models.FloatField(default=0.5, help_text="Tolerancia de monto para match fuzzy (%)")
    fuzzy_match_date_tolerance = models.PositiveIntegerField(default=2, help_text="Días de tolerancia para match fuzzy")
    partial_match_amount_tolerance_percent = models.FloatField(default=1.0, help_text="Tolerancia de monto para match parcial (%)")
    partial_match_date_tolerance = models.PositiveIntegerField(default=3, help_text="Días de tolerancia para match parcial")
    
    # Umbrales de confianza
    auto_confirm_threshold = models.FloatField(default=90.0, help_text="Umbral para confirmación automática (%)")
    pending_review_threshold = models.FloatField(default=70.0, help_text="Umbral para revisión manual (%)")
    
    # Configuración de moneda
    default_currency = models.CharField(max_length=3, default="ARS")
    currency_rate = models.DecimalField(max_digits=10, decimal_places=4, null=True, blank=True, help_text="Tipo de cambio USD/ARS")
    currency_rate_date = models.DateField(null=True, blank=True, help_text="Fecha del tipo de cambio")
    
    # Notificaciones
    email_notifications = models.BooleanField(default=True)
    notification_threshold_percent = models.FloatField(default=10.0, help_text="Umbral para notificación de errores (%)")
    notification_emails = models.JSONField(default=list, help_text="Emails para notificaciones")
    
    # Configuración de archivos
    csv_encoding = models.CharField(max_length=20, default="utf-8")
    csv_separator = models.CharField(max_length=5, default=",")
    csv_columns = models.JSONField(default=list, help_text="Columnas esperadas en el CSV")
    
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['hotel']
    
    def __str__(self):
        return f"Configuración Conciliación - {self.hotel.name}"


class BankReconciliation(models.Model):
    """Conciliación bancaria principal"""
    hotel = models.ForeignKey(Hotel, on_delete=models.CASCADE, related_name="bank_reconciliations")
    reconciliation_date = models.DateField(help_text="Fecha de la conciliación")
    
    # Archivo CSV
    csv_file = models.FileField(upload_to='bank_reconciliations/%Y/%m/%d/')
    csv_filename = models.CharField(max_length=255)
    csv_file_size = models.PositiveIntegerField()
    
    # Estadísticas
    total_transactions = models.PositiveIntegerField(default=0)
    matched_transactions = models.PositiveIntegerField(default=0)
    unmatched_transactions = models.PositiveIntegerField(default=0)
    pending_review_transactions = models.PositiveIntegerField(default=0)
    error_transactions = models.PositiveIntegerField(default=0)
    
    # Estado y procesamiento
    status = models.CharField(max_length=20, choices=ReconciliationStatus.choices, default=ReconciliationStatus.PENDING)
    processing_started_at = models.DateTimeField(null=True, blank=True)
    processing_completed_at = models.DateTimeField(null=True, blank=True)
    
    # Usuario y auditoría
    created_by = models.ForeignKey(get_user_model(), on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Metadatos
    processing_notes = models.TextField(blank=True, help_text="Notas del procesamiento")
    error_details = models.JSONField(default=dict, help_text="Detalles de errores encontrados")
    
    class Meta:
        ordering = ['-reconciliation_date', '-created_at']
        indexes = [
            models.Index(fields=['hotel', 'reconciliation_date']),
            models.Index(fields=['status']),
        ]
    
    def __str__(self):
        return f"Conciliación {self.hotel.name} - {self.reconciliation_date}"
    
    @property
    def match_percentage(self):
        """Porcentaje de transacciones con match"""
        if self.total_transactions == 0:
            return 0
        return round((self.matched_transactions / self.total_transactions) * 100, 2)
    
    @property
    def needs_manual_review(self):
        """Indica si necesita revisión manual"""
        return self.pending_review_transactions > 0 or self.unmatched_transactions > 0


class BankTransaction(models.Model):
    """Transacciones individuales del CSV bancario"""
    reconciliation = models.ForeignKey(BankReconciliation, on_delete=models.CASCADE, related_name="transactions")
    
    # Datos de la transacción
    transaction_date = models.DateField()
    description = models.CharField(max_length=500)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    currency = models.CharField(max_length=3, default="ARS")
    reference = models.CharField(max_length=100, blank=True)
    
    # Estado del matching
    is_matched = models.BooleanField(default=False)
    is_reversal = models.BooleanField(default=False, help_text="Indica si es una reversión (monto negativo)")
    match_confidence = models.FloatField(null=True, blank=True, help_text="Confianza del match (0-100)")
    match_type = models.CharField(max_length=20, choices=MatchType.choices, null=True, blank=True)
    
    # Referencias al pago matchado
    matched_payment_id = models.PositiveIntegerField(null=True, blank=True)
    matched_payment_type = models.CharField(max_length=50, null=True, blank=True)
    matched_reservation_id = models.PositiveIntegerField(null=True, blank=True)
    
    # Diferencias encontradas
    amount_difference = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    date_difference_days = models.IntegerField(default=0)
    
    # Auditoría
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['transaction_date', 'amount']
        indexes = [
            models.Index(fields=['reconciliation', 'is_matched']),
            models.Index(fields=['transaction_date', 'amount']),
            models.Index(fields=['is_reversal']),
        ]
    
    def __str__(self):
        return f"Transacción {self.amount} - {self.transaction_date}"


class ReconciliationMatch(models.Model):
    """Matches entre transacciones bancarias y pagos del sistema"""
    reconciliation = models.ForeignKey(BankReconciliation, on_delete=models.CASCADE, related_name="matches")
    bank_transaction = models.ForeignKey(BankTransaction, on_delete=models.CASCADE, related_name="matches")
    
    # Referencia al pago matchado
    payment_id = models.PositiveIntegerField()
    payment_type = models.CharField(max_length=50)  # 'payment_intent', 'bank_transfer', 'payment'
    reservation_id = models.PositiveIntegerField()
    
    # Detalles del match
    match_type = models.CharField(max_length=20, choices=MatchType.choices)
    confidence_score = models.FloatField()
    amount_difference = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    date_difference_days = models.IntegerField(default=0)
    
    # Estado del match
    is_confirmed = models.BooleanField(default=False)
    is_manual = models.BooleanField(default=False)
    manual_approved_by = models.ForeignKey(get_user_model(), on_delete=models.SET_NULL, null=True, blank=True)
    manual_approved_at = models.DateTimeField(null=True, blank=True)
    manual_notes = models.TextField(blank=True)
    
    # Auditoría
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['bank_transaction', 'payment_id', 'payment_type']
        indexes = [
            models.Index(fields=['reconciliation', 'is_confirmed']),
            models.Index(fields=['payment_id', 'payment_type']),
        ]
    
    def __str__(self):
        return f"Match {self.bank_transaction.amount} - {self.payment_type}#{self.payment_id}"


class BankReconciliationLog(models.Model):
    """Log de auditoría para conciliaciones bancarias"""
    reconciliation = models.ForeignKey(BankReconciliation, on_delete=models.CASCADE, related_name="audit_logs")
    
    # Evento
    event_type = models.CharField(max_length=30, choices=ReconciliationEventType.choices)
    event_description = models.CharField(max_length=500)
    
    # Referencias
    bank_transaction_id = models.PositiveIntegerField(null=True, blank=True)
    payment_id = models.PositiveIntegerField(null=True, blank=True)
    payment_type = models.CharField(max_length=50, null=True, blank=True)
    reservation_id = models.PositiveIntegerField(null=True, blank=True)
    
    # Detalles del evento
    details = models.JSONField(default=dict)
    confidence_score = models.FloatField(null=True, blank=True)
    
    # Usuario y auditoría
    created_by = models.ForeignKey(get_user_model(), on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    # Archivo asociado
    csv_filename = models.CharField(max_length=255, blank=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['reconciliation', 'event_type']),
            models.Index(fields=['created_at']),
        ]
    
    def __str__(self):
        return f"Log {self.event_type} - {self.created_at.strftime('%Y-%m-%d %H:%M')}"


class BankTransferStatus(models.TextChoices):
    """Estados de una transferencia bancaria"""
    UPLOADED = "uploaded", "Comprobante Subido"
    PENDING_REVIEW = "pending_review", "Pendiente de Revisión"
    CONFIRMED = "confirmed", "Confirmada"
    REJECTED = "rejected", "Rechazada"
    PROCESSING = "processing", "Procesando"


class BankTransferPayment(models.Model):
    """
    Modelo para manejar transferencias bancarias con comprobantes
    Permite subir comprobantes, validar con OCR y conciliar pagos
    """
    reservation = models.ForeignKey(
        Reservation, 
        on_delete=models.CASCADE, 
        related_name="bank_transfers",
        help_text="Reserva asociada a la transferencia"
    )
    hotel = models.ForeignKey(
        Hotel, 
        on_delete=models.CASCADE, 
        related_name="bank_transfers",
        help_text="Hotel de la reserva"
    )
    
    # Datos de la transferencia
    amount = models.DecimalField(
        max_digits=12, 
        decimal_places=2,
        help_text="Monto de la transferencia"
    )
    transfer_date = models.DateField(
        help_text="Fecha de la transferencia bancaria"
    )
    cbu_iban = models.CharField(
        max_length=50,
        help_text="CBU o IBAN de la cuenta destino"
    )
    bank_name = models.CharField(
        max_length=100,
        blank=True,
        help_text="Nombre del banco (opcional)"
    )
    
    # Comprobante
    receipt_file = models.FileField(
        upload_to='bank_transfers/receipts/%Y/%m/%d/',
        help_text="Archivo del comprobante de transferencia"
    )
    receipt_filename = models.CharField(
        max_length=255,
        blank=True,
        help_text="Nombre original del archivo"
    )
    receipt_url = models.URLField(
        blank=True,
        help_text="URL completa del comprobante (Cloudinary o local)"
    )
    storage_type = models.CharField(
        max_length=20,
        choices=[
            ('local', 'Local'),
            ('cloudinary', 'Cloudinary'),
        ],
        default='local',
        help_text="Tipo de almacenamiento del archivo"
    )
    
    # Estado y validación
    status = models.CharField(
        max_length=20,
        choices=BankTransferStatus.choices,
        default=BankTransferStatus.UPLOADED,
        help_text="Estado de la transferencia"
    )
    
    # Datos extraídos por OCR
    ocr_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Monto extraído por OCR del comprobante"
    )
    ocr_cbu = models.CharField(
        max_length=50,
        blank=True,
        help_text="CBU extraído por OCR del comprobante"
    )
    ocr_confidence = models.FloatField(
        null=True,
        blank=True,
        help_text="Nivel de confianza del OCR (0-1)"
    )
    
    # Validación y conciliación
    is_amount_valid = models.BooleanField(
        null=True,
        blank=True,
        help_text="Si el monto coincide con el esperado"
    )
    is_cbu_valid = models.BooleanField(
        null=True,
        blank=True,
        help_text="Si el CBU coincide con el esperado"
    )
    validation_notes = models.TextField(
        blank=True,
        help_text="Notas de la validación"
    )
    
    # Referencias
    external_reference = models.CharField(
        max_length=200,
        blank=True,
        help_text="Referencia externa de la transferencia"
    )
    payment_reference = models.CharField(
        max_length=200,
        blank=True,
        help_text="Referencia del pago asociado"
    )
    
    # Metadatos
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        get_user_model(),
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        help_text="Usuario que subió el comprobante"
    )
    reviewed_by = models.ForeignKey(
        get_user_model(),
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="reviewed_bank_transfers",
        help_text="Usuario que revisó el comprobante"
    )
    reviewed_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Fecha de revisión"
    )
    
    # Notas adicionales
    notes = models.TextField(
        blank=True,
        help_text="Notas adicionales sobre la transferencia"
    )
    
    # Historial de cambios
    history = models.JSONField(
        default=list,
        blank=True,
        help_text="Historial de cambios de la transferencia"
    )

    class Meta:
        verbose_name = "Transferencia Bancaria"
        verbose_name_plural = "Transferencias Bancarias"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['reservation', 'status']),
            models.Index(fields=['hotel', 'status']),
            models.Index(fields=['status', 'created_at']),
            models.Index(fields=['transfer_date']),
        ]

    def __str__(self):
        return f"Transferencia {self.id} - {self.reservation.id} - ${self.amount} - {self.get_status_display()}"

    def save(self, *args, **kwargs):
        """Override save para crear log automático"""
        is_new = self.pk is None
        old_status = None
        
        if not is_new:
            try:
                old_instance = BankTransferPayment.objects.get(pk=self.pk)
                old_status = old_instance.status
            except BankTransferPayment.DoesNotExist:
                pass
        
        super().save(*args, **kwargs)
        
        # Log de creación o cambio de estado
        if is_new:
            self._log_event('created', f"Transferencia bancaria creada por ${self.amount}")
        elif old_status and old_status != self.status:
            self._log_event('status_changed', f"Estado cambiado de {old_status} a {self.status}")

    def _log_event(self, event_type, message, user=None):
        """Registra un evento en el historial"""
        from django.utils import timezone
        
        log_entry = {
            'timestamp': timezone.now().isoformat(),
            'event_type': event_type,
            'message': message,
            'user_id': user.id if user else None,
            'user_name': user.username if user else None,
        }
        
        if not self.history:
            self.history = []
        
        self.history.append(log_entry)
        
        # Actualizar solo el campo history sin triggerar save() nuevamente
        BankTransferPayment.objects.filter(pk=self.pk).update(history=self.history)

    def mark_as_pending_review(self, user=None):
        """Marca la transferencia como pendiente de revisión"""
        self.status = BankTransferStatus.PENDING_REVIEW
        self.save(update_fields=['status', 'updated_at'])
        self._log_event('status_changed', "Transferencia marcada como pendiente de revisión", user)

    def mark_as_confirmed(self, user=None, notes=""):
        """Marca la transferencia como confirmada"""
        from django.utils import timezone
        
        self.status = BankTransferStatus.CONFIRMED
        self.reviewed_by = user
        self.reviewed_at = timezone.now()
        if notes:
            self.notes = notes
        self.save(update_fields=['status', 'reviewed_by', 'reviewed_at', 'notes', 'updated_at'])
        self._log_event('confirmed', f"Transferencia confirmada{': ' + notes if notes else ''}", user)
        
        # Crear el pago asociado
        self._create_payment()

    def mark_as_rejected(self, user=None, notes=""):
        """Marca la transferencia como rechazada"""
        from django.utils import timezone
        
        self.status = BankTransferStatus.REJECTED
        self.reviewed_by = user
        self.reviewed_at = timezone.now()
        if notes:
            self.notes = notes
        self.save(update_fields=['status', 'reviewed_by', 'reviewed_at', 'notes', 'updated_at'])
        self._log_event('rejected', f"Transferencia rechazada{': ' + notes if notes else ''}", user)

    def _create_payment(self):
        """Crea el pago asociado a la transferencia confirmada"""
        from apps.reservations.models import Payment, ReservationStatus
        
        payment = Payment.objects.create(
            reservation=self.reservation,
            date=self.transfer_date,
            method='bank_transfer',
            amount=self.amount
        )
        
        self.payment_reference = f"PAY-{payment.id}"
        self.save(update_fields=['payment_reference'])
        
        # Actualizar estado de la reserva si está pendiente
        if self.reservation.status == ReservationStatus.PENDING:
            self.reservation.status = ReservationStatus.CONFIRMED
            self.reservation.save(update_fields=['status', 'updated_at'])
            
            # Log del cambio de estado de la reserva
            from apps.reservations.models import ReservationChangeLog, ReservationChangeEvent
            ReservationChangeLog.objects.create(
                reservation=self.reservation,
                event_type=ReservationChangeEvent.STATUS_CHANGED,
                changed_by=self.reviewed_by,
                message=f"Reserva confirmada automáticamente por pago de transferencia bancaria de ${self.amount}"
            )
        
        # Log del pago creado
        from apps.reservations.models import ReservationChangeLog, ReservationChangeEvent
        ReservationChangeLog.objects.create(
            reservation=self.reservation,
            event_type=ReservationChangeEvent.PAYMENT_ADDED,
            changed_by=self.reviewed_by,
            message=f"Pago por transferencia bancaria de ${self.amount} confirmado"
        )

    def validate_ocr_data(self):
        """Valida los datos extraídos por OCR"""
        # Validar monto
        if self.ocr_amount is not None:
            self.is_amount_valid = abs(float(self.amount) - float(self.ocr_amount)) <= 0.01
        
        # Validar CBU
        if self.ocr_cbu:
            self.is_cbu_valid = self.cbu_iban.upper() == self.ocr_cbu.upper()
        
        # NUEVA LÓGICA: Confirmar automáticamente por defecto
        # Solo revisión manual si hay problemas serios
        if self.ocr_amount is None and self.ocr_cbu is None:
            # Si OCR no pudo extraer nada, confirmar de todas formas
            self.status = BankTransferStatus.CONFIRMED
            self.validation_notes = "Transferencia confirmada - OCR no pudo extraer datos pero comprobante subido"
            self.is_amount_valid = True  # Asumir que es válido
            self.is_cbu_valid = True
            self._create_payment()
        elif self.is_amount_valid is False or self.is_cbu_valid is False:
            # Solo si hay datos OCR y no coinciden, revisar manualmente
            self.status = BankTransferStatus.PENDING_REVIEW
            self.validation_notes = "Datos OCR no coinciden - requiere revisión manual"
        else:
            # Confirmar automáticamente
            self.status = BankTransferStatus.CONFIRMED
            self.validation_notes = "Validación automática exitosa"
            self._create_payment()
        
        self.save(update_fields=['is_amount_valid', 'is_cbu_valid', 'status', 'validation_notes', 'updated_at'])

    @property
    def needs_manual_review(self):
        """Indica si la transferencia necesita revisión manual"""
        return (
            self.status == BankTransferStatus.PENDING_REVIEW or
            self.is_amount_valid is False or
            self.is_cbu_valid is False
        )

    @property
    def is_auto_validated(self):
        """Indica si la transferencia fue validada automáticamente"""
        return (
            self.status == BankTransferStatus.CONFIRMED and
            self.is_amount_valid and
            self.is_cbu_valid and
            not self.reviewed_by
        )


class ReceiptNumberSequence(models.Model):
    """
    Modelo para manejar la numeración secuencial de comprobantes
    Formato: PREFIJO-SERIE-NUMERO (ej: R-0001-000045)
    """
    class ReceiptType(models.TextChoices):
        DEPOSIT = "S", "Recibo de Seña"  # S-0001-000012
        PAYMENT = "P", "Recibo de Pago Total"  # P-0001-000085
        REFUND = "D", "Comprobante de Devolución"  # D-0001-000004
        CANCELLATION = "C", "Comprobante de Cancelación"  # C-0001-000012
        VOUCHER = "V", "Voucher de Crédito"
        INTERNAL = "INT", "Comprobante Interno"
    
    hotel = models.ForeignKey(
        Hotel, 
        on_delete=models.CASCADE, 
        related_name="receipt_sequences",
        help_text="Hotel al que pertenece esta secuencia"
    )
    receipt_type = models.CharField(
        max_length=10,
        choices=ReceiptType.choices,
        help_text="Tipo de comprobante"
    )
    series = models.PositiveIntegerField(
        default=1,
        help_text="Número de serie (0001-9999)"
    )
    current_number = models.PositiveIntegerField(
        default=0,
        help_text="Último número usado en esta serie"
    )
    is_active = models.BooleanField(
        default=True,
        help_text="Si esta secuencia está activa"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['hotel', 'receipt_type', 'series']
        ordering = ['hotel', 'receipt_type', 'series']
    
    def __str__(self):
        return f"{self.get_receipt_type_display()}-{self.series:04d} (Hotel: {self.hotel.name})"
    
    def get_next_number(self):
        """Obtiene el siguiente número en la secuencia"""
        self.current_number += 1
        self.save(update_fields=['current_number', 'updated_at'])
        return self.current_number
    
    def get_formatted_receipt_number(self):
        """Retorna el número de comprobante formateado: PREFIJO-SERIE-NUMERO"""
        return f"{self.receipt_type}-{self.series:04d}-{self.current_number:06d}"
    
    @classmethod
    def get_or_create_sequence(cls, hotel, receipt_type, series=1):
        """Obtiene o crea una secuencia para el hotel y tipo especificados"""
        sequence, created = cls.objects.get_or_create(
            hotel=hotel,
            receipt_type=receipt_type,
            series=series,
            defaults={'current_number': 0}
        )
        return sequence
    
    @classmethod
    def generate_receipt_number(cls, hotel, receipt_type, series=1):
        """Genera un nuevo número de comprobante"""
        sequence = cls.get_or_create_sequence(hotel, receipt_type, series)
        sequence.get_next_number()
        return sequence.get_formatted_receipt_number()