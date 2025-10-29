from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import AfipConfig, Invoice, InvoiceItem, InvoiceType, InvoiceStatus, TaxCondition, AfipEnvironment

User = get_user_model()


class AfipConfigSerializer(serializers.ModelSerializer):
    """Serializer para configuración AFIP"""
    hotel_name = serializers.CharField(source='hotel.name', read_only=True)
    environment_display = serializers.CharField(source='get_environment_display', read_only=True)
    tax_condition_display = serializers.CharField(source='get_tax_condition_display', read_only=True)
    
    class Meta:
        model = AfipConfig
        fields = [
            'id', 'hotel', 'hotel_name', 'cuit', 'tax_condition', 'tax_condition_display',
            'point_of_sale', 'certificate_path', 'private_key_path', 'environment',
            'environment_display', 'is_active', 'last_invoice_number', 'last_cae_date',
            'afip_token', 'afip_sign', 'afip_token_generation', 'afip_token_expiration',
            'created_at', 'updated_at', 'created_by'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'last_invoice_number', 'last_cae_date', 'afip_token', 'afip_sign', 'afip_token_generation', 'afip_token_expiration']
    
    def validate_cuit(self, value):
        """Validar CUIT"""
        if not value.isdigit() or len(value) != 11:
            raise serializers.ValidationError("El CUIT debe tener exactamente 11 dígitos")
        return value
    
    def validate_point_of_sale(self, value):
        """Validar punto de venta"""
        if value < 1 or value > 9999:
            raise serializers.ValidationError("El punto de venta debe estar entre 1 y 9999")
        return value


class InvoiceItemSerializer(serializers.ModelSerializer):
    """Serializer para items de factura"""
    
    class Meta:
        model = InvoiceItem
        fields = [
            'id', 'description', 'quantity', 'unit_price', 'subtotal',
            'vat_rate', 'vat_amount', 'total', 'afip_code'
        ]
        read_only_fields = ['id', 'subtotal', 'vat_amount', 'total']


class InvoiceSerializer(serializers.ModelSerializer):
    """Serializer para facturas"""
    hotel_name = serializers.CharField(source='hotel.name', read_only=True)
    reservation_display = serializers.CharField(source='reservation.display_name', read_only=True)
    type_display = serializers.CharField(source='get_type_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    client_tax_condition_display = serializers.CharField(source='get_client_tax_condition_display', read_only=True)
    pdf_url = serializers.SerializerMethodField()
    is_approved = serializers.BooleanField(read_only=True)
    is_expired = serializers.BooleanField(read_only=True)
    can_be_resent = serializers.BooleanField(read_only=True)
    items = InvoiceItemSerializer(many=True, read_only=True)
    
    class Meta:
        model = Invoice
        fields = [
            'id', 'reservation', 'reservation_display', 'payment', 'hotel', 'hotel_name',
            'type', 'type_display', 'number', 'issue_date', 'cae', 'cae_expiration',
            'total', 'vat_amount', 'net_amount', 'currency', 'status', 'status_display',
            'pdf_file', 'pdf_url', 'afip_response', 'client_name', 'client_document_type',
            'client_document_number', 'client_tax_condition', 'client_tax_condition_display',
            'client_address', 'retry_count', 'last_error', 'sent_to_afip_at', 'approved_at',
            'is_approved', 'is_expired', 'can_be_resent', 'items', 'created_at', 'updated_at',
            'created_by'
        ]
        read_only_fields = [
            'id', 'number', 'cae', 'cae_expiration', 'pdf_url', 'is_approved',
            'is_expired', 'can_be_resent', 'retry_count', 'last_error',
            'sent_to_afip_at', 'approved_at', 'created_at', 'updated_at'
        ]
    
    def get_pdf_url(self, obj):
        """Obtener URL del PDF"""
        return obj.get_pdf_url()
    
    def validate_total(self, value):
        """Validar total positivo"""
        if value <= 0:
            raise serializers.ValidationError("El total debe ser mayor a 0")
        return value
    
    def validate_issue_date(self, value):
        """Validar fecha de emisión no futura"""
        from django.utils import timezone
        if value > timezone.now().date():
            raise serializers.ValidationError("La fecha de emisión no puede ser futura")
        return value


class CreateInvoiceFromReservationSerializer(serializers.Serializer):
    """Serializer para crear factura desde reserva"""
    reservation_id = serializers.IntegerField()
    invoice_type = serializers.ChoiceField(choices=InvoiceType.choices)
    client_name = serializers.CharField(max_length=200)
    # Debe almacenar el código AFIP de 2 dígitos (p.ej. DNI = "96")
    client_document_type = serializers.CharField(max_length=2, default="96")
    client_document_number = serializers.CharField(max_length=20)
    client_tax_condition = serializers.ChoiceField(choices=TaxCondition.choices, default=TaxCondition.CONSUMIDOR_FINAL)
    client_address = serializers.CharField(required=False, allow_blank=True)
    issue_date = serializers.DateField(required=False)
    items = InvoiceItemSerializer(many=True, required=False)

    def validate_client_document_type(self, value: str) -> str:
        """Acepta etiquetas ("DNI", "CUIT", etc.) y mapea al código AFIP de 2 dígitos.
        Si ya viene un código válido de 2 caracteres, lo retorna tal cual.
        """
        if value is None:
            return "96"

        value_str = str(value).strip().upper()

        # Si ya es un código de 2 chars, devolverlo tal cual
        if len(value_str) == 2:
            return value_str

        label_to_code = {
            "DNI": "96",
            "CUIT": "80",
            "CUIL": "86",
            "PASAPORTE": "94",
            "PASSPORT": "94",
            "OTRO": "99",
            "OTHER": "99",
        }

        return label_to_code.get(value_str, "96")
    
    def validate_reservation_id(self, value):
        """Validar que la reserva existe"""
        from apps.reservations.models import Reservation
        try:
            reservation = Reservation.objects.get(id=value)
            # Verificar si el hotel tiene configuración AFIP
            # afip_config es una relación one-to-one, no un QuerySet
            try:
                afip_config = reservation.hotel.afip_config
                if not afip_config:
                    raise serializers.ValidationError("El hotel no tiene configuración AFIP")
            except:
                raise serializers.ValidationError("El hotel no tiene configuración AFIP")
            return value
        except Reservation.DoesNotExist:
            raise serializers.ValidationError("La reserva no existe")


class SendInvoiceToAfipSerializer(serializers.Serializer):
    """Serializer para enviar factura a AFIP"""
    force_send = serializers.BooleanField(default=False, help_text="Forzar envío aunque ya esté enviada")


class RetryFailedInvoiceSerializer(serializers.Serializer):
    """Serializer para reintentar factura fallida"""
    reason = serializers.CharField(required=False, allow_blank=True, help_text="Motivo del reintento")


class CancelInvoiceSerializer(serializers.Serializer):
    """Serializer para cancelar factura"""
    reason = serializers.CharField(required=True, help_text="Motivo de la cancelación")


class InvoiceSummarySerializer(serializers.Serializer):
    """Serializer para resumen de facturas"""
    total_invoices = serializers.IntegerField()
    approved_invoices = serializers.IntegerField()
    pending_invoices = serializers.IntegerField()
    error_invoices = serializers.IntegerField()
    total_amount = serializers.DecimalField(max_digits=12, decimal_places=2)
    approved_amount = serializers.DecimalField(max_digits=12, decimal_places=2)
    pending_amount = serializers.DecimalField(max_digits=12, decimal_places=2)
    error_amount = serializers.DecimalField(max_digits=12, decimal_places=2)
    invoices_by_type = serializers.DictField()
    invoices_by_status = serializers.DictField()


class AfipStatusSerializer(serializers.Serializer):
    """Serializer para estado de AFIP"""
    is_available = serializers.BooleanField()
    last_connection = serializers.DateTimeField()
    environment = serializers.CharField()
    service_status = serializers.CharField()
    last_error = serializers.CharField(required=False, allow_null=True)


class InjectTASerializer(serializers.Serializer):
    """Serializer para inyectar manualmente un TA válido en AfipConfig"""
    token = serializers.CharField(max_length=10000)
    sign = serializers.CharField(max_length=10000)
    generation_time = serializers.DateTimeField(required=False)
    expiration_time = serializers.DateTimeField(required=False)


class GenerateInvoiceFromPaymentSerializer(serializers.Serializer):
    """Serializer para generar factura desde pago"""
    customer_name = serializers.CharField(max_length=255, required=False)
    customer_document_type = serializers.ChoiceField(
        choices=[('DNI', 'DNI'), ('CUIT', 'CUIT'), ('CUIL', 'CUIL'), ('PASAPORTE', 'PASAPORTE')],
        required=False
    )
    customer_document_number = serializers.CharField(max_length=20, required=False)
    customer_address = serializers.CharField(max_length=500, required=False)
    customer_city = serializers.CharField(max_length=100, required=False)
    customer_postal_code = serializers.CharField(max_length=20, required=False)
    customer_country = serializers.CharField(max_length=100, required=False, default='Argentina')
    issue_date = serializers.DateField(required=False)
    send_to_afip = serializers.BooleanField(default=False)
    items = InvoiceItemSerializer(many=True, required=False)
    reference_payments = serializers.ListField(
        child=serializers.IntegerField(),
        required=False,
        help_text="Lista de IDs de pagos a incluir en la factura (señas + pago final)"
    )
    
    def validate_customer_document_number(self, value):
        """Validar número de documento"""
        if value and not value.isdigit():
            raise serializers.ValidationError("El número de documento debe contener solo dígitos")
        return value
    
    def validate_reference_payments(self, value):
        """Validar que los pagos de referencia existan y pertenezcan a la misma reserva"""
        if not value:
            return value
            
        from apps.reservations.models import Payment
        payments = Payment.objects.filter(id__in=value)
        
        if len(payments) != len(value):
            raise serializers.ValidationError("Algunos pagos de referencia no existen")
        
        # Verificar que todos los pagos pertenezcan a la misma reserva
        reservation_ids = set(payment.reservation_id for payment in payments)
        if len(reservation_ids) > 1:
            raise serializers.ValidationError("Todos los pagos deben pertenecer a la misma reserva")
        
        return value


class CreateCreditNoteSerializer(serializers.Serializer):
    """Serializer para crear nota de crédito"""
    total = serializers.DecimalField(max_digits=10, decimal_places=2)
    net_amount = serializers.DecimalField(max_digits=10, decimal_places=2)
    vat_amount = serializers.DecimalField(max_digits=10, decimal_places=2)
    issue_date = serializers.DateField(required=False)
    reason = serializers.CharField(max_length=500, required=False)
    items = InvoiceItemSerializer(many=True, required=True)
    
    def validate(self, data):
        """Validar que los totales coincidan"""
        total = data['total']
        net_amount = data['net_amount']
        vat_amount = data['vat_amount']
        
        if abs(total - (net_amount + vat_amount)) > 0.01:  # Tolerancia de 1 centavo
            raise serializers.ValidationError("El total debe ser igual a la suma del neto y el IVA")
        
        return data
