from django.db import models
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.utils import timezone
from decimal import Decimal
from datetime import datetime, timedelta
import uuid

User = get_user_model()


class InvoiceType(models.TextChoices):
    """Tipos de comprobantes según AFIP"""
    FACTURA_A = "A", "Factura A (Responsable Inscripto)"
    FACTURA_B = "B", "Factura B (Consumidor Final)"
    FACTURA_C = "C", "Factura C (Exento)"
    FACTURA_E = "E", "Factura E (Exportación)"
    NOTA_CREDITO = "NC", "Nota de Crédito"
    NOTA_DEBITO = "ND", "Nota de Débito"


class InvoiceStatus(models.TextChoices):
    """Estados de la factura"""
    DRAFT = "draft", "Borrador"
    SENT = "sent", "Enviada a AFIP"
    APPROVED = "approved", "Aprobada por AFIP"
    ERROR = "error", "Error en AFIP"
    CANCELLED = "cancelled", "Cancelada"


class TaxCondition(models.TextChoices):
    """Condiciones de IVA según AFIP"""
    RESPONSABLE_INSCRIPTO = "1", "Responsable Inscripto"
    CONSUMIDOR_FINAL = "5", "Consumidor Final"
    EXENTO = "6", "Exento"
    NO_RESPONSABLE = "7", "No Responsable"
    MONOTRIBUTO = "8", "Monotributo"
    MONOTRIBUTO_SOCIAL = "9", "Monotributo Social"


class AfipEnvironment(models.TextChoices):
    """Ambientes de AFIP"""
    TEST = "test", "Testing"
    PRODUCTION = "production", "Producción"


class InvoiceMode(models.TextChoices):
    """Modos de facturación para señas"""
    RECEIPT_ONLY = "receipt_only", "Solo Recibos"
    FISCAL_ON_DEPOSIT = "fiscal_on_deposit", "Facturación en Seña"


class AfipConfig(models.Model):
    """
    Configuración de AFIP por hotel para facturación electrónica
    """
    hotel = models.OneToOneField(
        "core.Hotel", 
        on_delete=models.CASCADE, 
        related_name="afip_config",
        help_text="Hotel asociado a esta configuración"
    )
    
    # Datos fiscales del hotel
    cuit = models.CharField(
        max_length=11,
        help_text="CUIT del hotel (11 dígitos)"
    )
    tax_condition = models.CharField(
        max_length=2,
        choices=TaxCondition.choices,
        default=TaxCondition.RESPONSABLE_INSCRIPTO,
        help_text="Condición de IVA del hotel"
    )
    point_of_sale = models.PositiveIntegerField(
        default=1,
        help_text="Punto de venta AFIP (1-9999)"
    )
    
    # Configuración de certificados
    certificate_path = models.CharField(
        max_length=500,
        help_text="Ruta al certificado AFIP (.crt)"
    )
    private_key_path = models.CharField(
        max_length=500,
        help_text="Ruta a la clave privada AFIP (.key)"
    )
    
    # Ambiente y configuración
    environment = models.CharField(
        max_length=20,
        choices=AfipEnvironment.choices,
        default=AfipEnvironment.TEST,
        help_text="Ambiente de AFIP (test/production)"
    )
    
    # Token de Acceso (WSAA)
    afip_token = models.TextField(
        blank=True,
        help_text="Último Token de Acceso (WSAA)"
    )
    afip_sign = models.TextField(
        blank=True,
        help_text="Firma asociada al TA"
    )
    afip_token_generation = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Fecha/hora de generación del TA (WSAA)"
    )
    afip_token_expiration = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Fecha/hora de expiración del TA (WSAA)"
    )
    
    # Control de numeración
    last_invoice_number = models.PositiveIntegerField(
        default=0,
        help_text="Último número de factura emitido"
    )
    last_cae_date = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Fecha del último CAE emitido"
    )
    
    # Estado y configuración
    is_active = models.BooleanField(
        default=True,
        help_text="Indica si la configuración está activa"
    )
    
    # Configuración de facturación para señas
    invoice_mode = models.CharField(
        max_length=20,
        choices=InvoiceMode.choices,
        default=InvoiceMode.RECEIPT_ONLY,
        help_text="Modo de facturación para pagos parciales (señas)"
    )
    
    # Metadatos
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        help_text="Usuario que creó la configuración"
    )
    
    class Meta:
        verbose_name = "Configuración AFIP"
        verbose_name_plural = "Configuraciones AFIP"
        indexes = [
            models.Index(fields=['hotel', 'is_active']),
            models.Index(fields=['environment']),
            models.Index(fields=['afip_token_expiration']),
        ]
    
    def save(self, *args, **kwargs):
        # Si no tiene created_by y hay un usuario en el contexto, asignarlo
        if not self.created_by and hasattr(self, '_current_user'):
            self.created_by = self._current_user
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"AFIP Config - {self.hotel.name} ({self.get_environment_display()})"
    
    def clean(self):
        """Validaciones del modelo"""
        # Validar CUIT (11 dígitos)
        if self.cuit and not self.cuit.isdigit() or len(self.cuit) != 11:
            raise ValidationError({'cuit': 'El CUIT debe tener exactamente 11 dígitos'})
        
        # Validar punto de venta (1-9999)
        if self.point_of_sale < 1 or self.point_of_sale > 9999:
            raise ValidationError({'point_of_sale': 'El punto de venta debe estar entre 1 y 9999'})
    
    def get_next_invoice_number(self) -> int:
        """Obtiene el próximo número de factura"""
        return self.last_invoice_number + 1
    
    def format_invoice_number(self, invoice_number: int) -> str:
        """
        Formatea el número de factura como "0001-00001234"
        """
        point_of_sale_str = f"{self.point_of_sale:04d}"
        invoice_number_str = f"{invoice_number:08d}"
        return f"{point_of_sale_str}-{invoice_number_str}"
    
    def update_invoice_number(self, invoice_number: int):
        """Actualiza el último número de factura emitido"""
        if invoice_number > self.last_invoice_number:
            self.last_invoice_number = invoice_number
            self.last_cae_date = timezone.now()
            self.save(update_fields=['last_invoice_number', 'last_cae_date'])


class Invoice(models.Model):
    """
    Modelo principal para facturas electrónicas
    """
    # Identificadores únicos
    id = models.UUIDField(
        primary_key=True, 
        default=uuid.uuid4, 
        editable=False,
        help_text="ID único de la factura"
    )
    
    # Relaciones principales
    reservation = models.ForeignKey(
        "reservations.Reservation",
        on_delete=models.CASCADE,
        related_name="invoices",
        help_text="Reserva asociada a la factura"
    )
    payment = models.ForeignKey(
        "reservations.Payment",
        on_delete=models.CASCADE,
        related_name="invoices",
        null=True,
        blank=True,
        help_text="Pago principal asociado a la factura (para compatibilidad)"
    )
    payments_data = models.JSONField(
        default=list,
        blank=True,
        help_text="Lista de IDs de pagos asociados a esta factura (incluye señas y pagos finales)"
    )
    hotel = models.ForeignKey(
        "core.Hotel",
        on_delete=models.CASCADE,
        related_name="invoices",
        help_text="Hotel que emite la factura"
    )
    related_invoice = models.ForeignKey(
        "self",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="related_documents",
        help_text="Factura original para notas de crédito/débito"
    )
    
    # Datos de la factura
    type = models.CharField(
        max_length=2,
        choices=InvoiceType.choices,
        help_text="Tipo de comprobante según AFIP"
    )
    number = models.CharField(
        max_length=13,
        help_text="Número de factura formateado (0001-00001234)"
    )
    issue_date = models.DateField(
        help_text="Fecha de emisión de la factura"
    )
    
    # Datos del CAE (Código de Autorización Electrónico)
    cae = models.CharField(
        max_length=14,
        blank=True,
        help_text="Código de Autorización Electrónico de AFIP"
    )
    cae_expiration = models.DateField(
        null=True,
        blank=True,
        help_text="Fecha de vencimiento del CAE"
    )
    
    # Montos
    total = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        help_text="Total de la factura"
    )
    vat_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal('0.00'),
        help_text="Monto de IVA"
    )
    net_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        help_text="Monto neto (sin IVA)"
    )
    currency = models.CharField(
        max_length=3,
        default="ARS",
        help_text="Moneda de la factura"
    )
    
    # Estado y control
    status = models.CharField(
        max_length=20,
        choices=InvoiceStatus.choices,
        default=InvoiceStatus.DRAFT,
        help_text="Estado actual de la factura"
    )
    
    # Archivos y respuestas
    pdf_file = models.FileField(
        upload_to='invoices/pdf/%Y/%m/%d/',
        null=True,
        blank=True,
        help_text="Archivo PDF de la factura"
    )
    pdf_url = models.URLField(
        blank=True,
        help_text="URL del PDF en almacenamiento externo"
    )
    afip_response = models.JSONField(
        default=dict,
        blank=True,
        help_text="Respuesta completa de AFIP"
    )
    
    # Datos del cliente (snapshot al momento de la facturación)
    client_name = models.CharField(
        max_length=200,
        help_text="Nombre del cliente"
    )
    client_document_type = models.CharField(
        max_length=2,
        default="96",  # DNI por defecto
        help_text="Tipo de documento del cliente"
    )
    client_document_number = models.CharField(
        max_length=20,
        help_text="Número de documento del cliente"
    )
    client_tax_condition = models.CharField(
        max_length=2,
        choices=TaxCondition.choices,
        default=TaxCondition.CONSUMIDOR_FINAL,
        help_text="Condición de IVA del cliente"
    )
    client_address = models.TextField(
        blank=True,
        help_text="Dirección del cliente"
    )
    
    # Metadatos
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        help_text="Usuario que creó la factura"
    )
    
    # Campos adicionales para control
    retry_count = models.PositiveIntegerField(
        default=0,
        help_text="Número de intentos de envío a AFIP"
    )
    last_error = models.TextField(
        blank=True,
        help_text="Último error registrado"
    )
    sent_to_afip_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Fecha y hora de envío a AFIP"
    )
    approved_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Fecha y hora de aprobación por AFIP"
    )
    
    class Meta:
        verbose_name = "Factura"
        verbose_name_plural = "Facturas"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['hotel', 'status']),
            models.Index(fields=['reservation']),
            models.Index(fields=['type', 'issue_date']),
            models.Index(fields=['cae']),
            models.Index(fields=['number']),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=['hotel', 'number'],
                name='unique_invoice_number_per_hotel'
            ),
        ]
    
    def __str__(self):
        return f"Factura {self.number} - {self.get_type_display()} - ${self.total}"
    
    def clean(self):
        """Validaciones del modelo"""
        # Validar que el total sea positivo
        if self.total <= 0:
            raise ValidationError({'total': 'El total debe ser mayor a 0'})
        
        # Validar que net_amount + vat_amount = total (aproximadamente)
        if self.net_amount + self.vat_amount != self.total:
            # Permitir pequeñas diferencias por redondeo
            difference = abs((self.net_amount + self.vat_amount) - self.total)
            if difference > Decimal('0.01'):
                raise ValidationError({
                    'total': 'El total debe ser igual a net_amount + vat_amount'
                })
        
        # Validar fecha de emisión no futura
        if self.issue_date and self.issue_date > timezone.now().date():
            raise ValidationError({
                'issue_date': 'La fecha de emisión no puede ser futura'
            })
    
    def save(self, *args, **kwargs):
        """Override save para validaciones adicionales"""
        self.clean()
        super().save(*args, **kwargs)
    
    def get_pdf_url(self):
        """Obtiene la URL del PDF (local o externa)"""
        if self.pdf_url:
            return self.pdf_url
        elif self.pdf_file:
            return self.pdf_file.url
        return None
    
    def is_approved(self):
        """Verifica si la factura está aprobada por AFIP"""
        return self.status == InvoiceStatus.APPROVED and bool(self.cae)
    
    def is_expired(self):
        """Verifica si el CAE ha expirado"""
        if not self.cae_expiration:
            return False
        return timezone.now().date() > self.cae_expiration
    
    def can_be_resent(self):
        """Verifica si la factura puede ser reenviada a AFIP"""
        return (
            self.status in [InvoiceStatus.DRAFT, InvoiceStatus.ERROR] and
            self.retry_count < 3 and
            not self.is_expired()
        )
    
    def mark_as_sent(self):
        """Marca la factura como enviada a AFIP"""
        self.status = InvoiceStatus.SENT
        self.sent_to_afip_at = timezone.now()
        self.save(update_fields=['status', 'sent_to_afip_at', 'updated_at'])
    
    def mark_as_approved(self, cae: str, cae_expiration: str):
        """Marca la factura como aprobada por AFIP"""
        from datetime import datetime
        
        self.status = InvoiceStatus.APPROVED
        self.cae = cae
        self.cae_expiration = datetime.strptime(cae_expiration, '%Y%m%d').date()
        self.approved_at = timezone.now()
        self.last_error = ""
        self.save(update_fields=[
            'status', 'cae', 'cae_expiration', 'approved_at', 
            'last_error', 'updated_at'
        ])
    
    def mark_as_error(self, error_message: str):
        """Marca la factura como error y registra el mensaje"""
        self.status = InvoiceStatus.ERROR
        self.last_error = error_message
        self.retry_count += 1
        self.save(update_fields=['status', 'last_error', 'retry_count', 'updated_at'])


class InvoiceItem(models.Model):
    """
    Items de la factura (servicios, productos, etc.)
    """
    invoice = models.ForeignKey(
        Invoice,
        on_delete=models.CASCADE,
        related_name="items",
        help_text="Factura a la que pertenece el item"
    )
    
    # Descripción del item
    description = models.CharField(
        max_length=200,
        help_text="Descripción del item"
    )
    quantity = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('1.00'),
        help_text="Cantidad"
    )
    unit_price = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        help_text="Precio unitario"
    )
    
    # Cálculos
    subtotal = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        help_text="Subtotal (quantity * unit_price)"
    )
    vat_rate = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal('21.00'),
        help_text="Alicuota de IVA (%)"
    )
    vat_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        help_text="Monto de IVA del item"
    )
    total = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        help_text="Total del item (subtotal + vat_amount)"
    )
    
    # Códigos AFIP
    afip_code = models.CharField(
        max_length=20,
        default="1",  # Servicios por defecto
        help_text="Código de producto/servicio AFIP"
    )
    
    class Meta:
        verbose_name = "Item de Factura"
        verbose_name_plural = "Items de Factura"
        ordering = ['id']
    
    def __str__(self):
        return f"{self.description} - ${self.total}"
    
    def clean(self):
        """Validaciones del item"""
        # Calcular subtotal
        calculated_subtotal = self.quantity * self.unit_price
        if abs(self.subtotal - calculated_subtotal) > Decimal('0.01'):
            raise ValidationError({
                'subtotal': f'El subtotal debe ser {calculated_subtotal} (quantity * unit_price)'
            })
        
        # Calcular IVA
        calculated_vat = (self.subtotal * self.vat_rate / Decimal('100')).quantize(Decimal('0.01'))
        if abs(self.vat_amount - calculated_vat) > Decimal('0.01'):
            raise ValidationError({
                'vat_amount': f'El IVA debe ser {calculated_vat} (subtotal * vat_rate / 100)'
            })
        
        # Calcular total
        calculated_total = self.subtotal + self.vat_amount
        if abs(self.total - calculated_total) > Decimal('0.01'):
            raise ValidationError({
                'total': f'El total debe ser {calculated_total} (subtotal + vat_amount)'
            })
    
    def save(self, *args, **kwargs):
        """Override save para calcular automáticamente los montos"""
        # Calcular subtotal
        self.subtotal = (self.quantity * self.unit_price).quantize(Decimal('0.01'))
        
        # Calcular IVA
        self.vat_amount = (self.subtotal * self.vat_rate / Decimal('100')).quantize(Decimal('0.01'))
        
        # Calcular total
        self.total = (self.subtotal + self.vat_amount).quantize(Decimal('0.01'))
        
        super().save(*args, **kwargs)
