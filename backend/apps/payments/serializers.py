from rest_framework import serializers
from .models import PaymentMethod, PaymentPolicy, CancellationPolicy, RefundPolicy, Refund, RefundStatus, RefundReason, PaymentGatewayConfig, RefundVoucher, RefundVoucherStatus


class PaymentMethodSerializer(serializers.ModelSerializer):
    class Meta:
        model = PaymentMethod
        fields = ["id", "code", "name", "is_active", "created_at", "updated_at"]


class PaymentPolicySerializer(serializers.ModelSerializer):
    hotel_name = serializers.CharField(source="hotel.name", read_only=True)
    methods = serializers.PrimaryKeyRelatedField(many=True, queryset=PaymentMethod.objects.all(), required=False)

    class Meta:
        model = PaymentPolicy
        fields = [
            "id", "hotel", "hotel_name", "name", "is_active", "is_default",
            "allow_deposit", "deposit_type", "deposit_value", "deposit_due", "deposit_days_before",
            "balance_due", "auto_cancel_enabled", "auto_cancel_days", "methods",
            "created_at", "updated_at",
        ]

    def validate(self, data):
        # Solo validar campos que están presentes en la data
        if 'hotel' in data:
            hotel_value = data.get('hotel')
            if not hotel_value and hotel_value != 0:  # Permitir 0 como ID válido
                raise serializers.ValidationError({'hotel': 'Este campo es requerido.'})
        
        if 'name' in data and not data.get('name'):
            raise serializers.ValidationError({'name': 'Este campo es requerido.'})
        
        # Validar que solo una política sea default por hotel
        if data.get('is_default', False):
            hotel = data.get('hotel')
            if hotel:
                existing_default = PaymentPolicy.objects.filter(
                    hotel=hotel,
                    is_default=True
                ).exclude(id=self.instance.id if self.instance else None)
                if existing_default.exists():
                    raise serializers.ValidationError(
                        {'is_default': 'Ya existe una política de pago por defecto para este hotel'}
                    )
        
        return data


class CancellationPolicySerializer(serializers.ModelSerializer):
    """Serializer para políticas de cancelación"""
    hotel_name = serializers.CharField(source="hotel.name", read_only=True)
    created_by_name = serializers.CharField(source="created_by.get_full_name", read_only=True)
    
    # Campos calculados para mostrar reglas
    cancellation_rules = serializers.SerializerMethodField()
    
    class Meta:
        model = CancellationPolicy
        fields = [
            "id", "hotel", "hotel_name", "name", "is_active", "is_default",
            "free_cancellation_time", "free_cancellation_unit",
            "partial_refund_time", "partial_refund_unit", "partial_refund_percentage",
            "no_refund_time", "no_refund_unit",
            "cancellation_fee_type", "cancellation_fee_value",
            "allow_cancellation_after_checkin", "allow_cancellation_after_checkout",
            "allow_cancellation_no_show", "allow_cancellation_early_checkout",
            "auto_refund_on_cancel",
            "free_cancellation_message", "partial_cancellation_message",
            "no_cancellation_message", "cancellation_fee_message",
            "apply_to_all_room_types", "room_types",
            "apply_to_all_channels", "channels",
            "apply_to_all_seasons", "seasonal_rules",
            "created_at", "updated_at", "created_by", "created_by_name",
            "cancellation_rules"
        ]
        read_only_fields = ["created_at", "updated_at", "created_by"]
    
    def get_cancellation_rules(self, obj):
        """Obtiene las reglas de cancelación para mostrar en la UI"""
        from datetime import date, timedelta
        
        # Simular una fecha de check-in para mostrar las reglas
        check_in_date = date.today() + timedelta(days=7)  # 7 días en el futuro
        return obj.get_cancellation_rules(check_in_date)
    
    def validate(self, data):
        # Validar solo campos presentes para soportar PATCH parcial
        if 'hotel' in data:
            hotel_value = data.get('hotel')
            if hotel_value is None or hotel_value == '':
                raise serializers.ValidationError({'hotel': 'Este campo es requerido.'})
        if 'name' in data and not data.get('name'):
            raise serializers.ValidationError({'name': 'Este campo es requerido.'})

        # Resolver hotel efectivo (dato nuevo o el de la instancia) para reglas de unicidad
        effective_hotel = data.get('hotel')
        if effective_hotel is None and self.instance is not None:
            effective_hotel = self.instance.hotel

        # Validar que solo una política sea default por hotel
        if data.get('is_default', False) and effective_hotel:
            existing_default = CancellationPolicy.objects.filter(
                hotel=effective_hotel,
                is_default=True
            ).exclude(id=self.instance.id if self.instance else None)
            if existing_default.exists():
                raise serializers.ValidationError(
                    {'is_default': 'Ya existe una política de cancelación por defecto para este hotel'}
                )
        
        # Validar tiempos de cancelación (deben ser progresivos: free < partial < no_refund)
        free_time = data.get('free_cancellation_time', 0)
        partial_time = data.get('partial_refund_time', 0)
        no_refund_time = data.get('no_refund_time', 0)
        free_unit = data.get('free_cancellation_unit', 'hours')
        partial_unit = data.get('partial_refund_unit', 'hours')
        no_refund_unit = data.get('no_refund_unit', 'hours')
        
        # Convertir todo a horas para comparar
        def convert_to_hours(time, unit):
            if unit == 'hours':
                return time
            elif unit == 'days':
                return time * 24
            elif unit == 'weeks':
                return time * 24 * 7
            return time
        
        free_hours = convert_to_hours(free_time, free_unit) if free_time > 0 else 0
        partial_hours = convert_to_hours(partial_time, partial_unit) if partial_time > 0 else 0
        no_refund_hours = convert_to_hours(no_refund_time, no_refund_unit) if no_refund_time > 0 else 0
        
        if free_hours > 0 and partial_hours > 0 and free_hours <= partial_hours:
            raise serializers.ValidationError(
                {'free_cancellation_time': 'El tiempo de cancelación gratuita debe ser mayor al tiempo de devolución parcial'}
            )
        
        if partial_hours > 0 and no_refund_hours > 0 and partial_hours <= no_refund_hours:
            raise serializers.ValidationError(
                {'partial_refund_time': 'El tiempo de devolución parcial debe ser mayor al tiempo de sin devolución'}
            )
        
        return data


class CancellationPolicyCreateSerializer(serializers.ModelSerializer):
    """Serializer para crear políticas de cancelación con valores por defecto"""
    
    class Meta:
        model = CancellationPolicy
        fields = [
            "hotel", "name", "is_active", "is_default",
            "free_cancellation_time", "free_cancellation_unit",
            "partial_refund_time", "partial_refund_unit", "partial_refund_percentage",
            "no_refund_time", "no_refund_unit",
            "cancellation_fee_type", "cancellation_fee_value",
            "allow_cancellation_after_checkin", "allow_cancellation_after_checkout",
            "allow_cancellation_no_show", "allow_cancellation_early_checkout",
            "free_cancellation_message", "partial_cancellation_message",
            "no_cancellation_message", "cancellation_fee_message",
            "apply_to_all_room_types", "room_types",
            "apply_to_all_channels", "channels",
            "apply_to_all_seasons", "seasonal_rules"
        ]
    
    def create(self, validated_data):
        # Establecer el usuario que crea la política
        validated_data['created_by'] = self.context['request'].user
        return super().create(validated_data)




class RefundPolicySerializer(serializers.ModelSerializer):
    """Serializer para políticas de devolución"""
    hotel_name = serializers.CharField(source="hotel.name", read_only=True)
    created_by_name = serializers.CharField(source="created_by.get_full_name", read_only=True)
    
    # Campos calculados para mostrar reglas
    refund_rules = serializers.SerializerMethodField()
    
    class Meta:
        model = RefundPolicy
        fields = [
            "id", "hotel", "hotel_name", "name", "is_active", "is_default",
            "full_refund_time", "full_refund_unit",
            "partial_refund_time", "partial_refund_unit", "partial_refund_percentage",
            "no_refund_time", "no_refund_unit",
            "refund_method", "refund_processing_days",
            "voucher_expiry_days", "voucher_minimum_amount",
            "full_refund_message", "partial_refund_message",
            "no_refund_message", "voucher_message",
            "apply_to_all_room_types", "room_types",
            "apply_to_all_channels", "channels",
            "apply_to_all_seasons", "seasonal_rules",
            "created_at", "updated_at", "created_by", "created_by_name",
            "refund_rules"
        ]
        read_only_fields = ["created_at", "updated_at", "created_by"]
    
    def get_refund_rules(self, obj):
        """Obtiene las reglas de devolución para mostrar en la UI"""
        from datetime import date, timedelta
        
        # Simular una fecha de check-in para mostrar las reglas
        check_in_date = date.today() + timedelta(days=7)  # 7 días en el futuro
        return obj.get_refund_rules(check_in_date)
    
    def validate(self, data):
        # Validar solo campos presentes para soportar PATCH parcial
        if 'hotel' in data:
            hotel_value = data.get('hotel')
            if hotel_value is None or hotel_value == '':
                raise serializers.ValidationError({'hotel': 'Este campo es requerido.'})
        if 'name' in data and not data.get('name'):
            raise serializers.ValidationError({'name': 'Este campo es requerido.'})

        # Resolver hotel efectivo (dato nuevo o el de la instancia) para reglas de unicidad
        effective_hotel = data.get('hotel')
        if effective_hotel is None and self.instance is not None:
            effective_hotel = self.instance.hotel

        # Validar que solo una política sea default por hotel
        if data.get('is_default', False) and effective_hotel:
            existing_default = RefundPolicy.objects.filter(
                hotel=effective_hotel,
                is_default=True
            ).exclude(id=self.instance.id if self.instance else None)
            if existing_default.exists():
                raise serializers.ValidationError(
                    {'is_default': 'Ya existe una política de devolución por defecto para este hotel'}
                )
        
        # Validar tiempos de devolución (deben ser progresivos)
        full_time = data.get('full_refund_time', 0)
        partial_time = data.get('partial_refund_time', 0)
        no_refund_time = data.get('no_refund_time', 0)
        
        if full_time > 0 and partial_time > 0 and full_time <= partial_time:
            raise serializers.ValidationError(
                {'full_refund_time': 'El tiempo de devolución completa debe ser mayor al tiempo de devolución parcial'}
            )
        
        if partial_time > 0 and no_refund_time > 0 and partial_time <= no_refund_time:
            raise serializers.ValidationError(
                {'partial_refund_time': 'El tiempo de devolución parcial debe ser mayor al tiempo de sin devolución'}
            )
        
        return data


class RefundPolicyCreateSerializer(serializers.ModelSerializer):
    """Serializer para crear políticas de devolución con valores por defecto"""
    
    class Meta:
        model = RefundPolicy
        fields = [
            "hotel", "name", "is_active", "is_default",
            "full_refund_time", "full_refund_unit",
            "partial_refund_time", "partial_refund_unit", "partial_refund_percentage",
            "no_refund_time", "no_refund_unit",
            "refund_method", "refund_processing_days",
            "voucher_expiry_days", "voucher_minimum_amount",
            "full_refund_message", "partial_refund_message",
            "no_refund_message", "voucher_message",
            "apply_to_all_room_types", "room_types",
            "apply_to_all_channels", "channels",
            "apply_to_all_seasons", "seasonal_rules"
        ]
    
    def create(self, validated_data):
        # Establecer el usuario que crea la política
        validated_data['created_by'] = self.context['request'].user
        return super().create(validated_data)


class RefundVoucherSerializer(serializers.ModelSerializer):
    """Serializer para vouchers de reembolso"""
    hotel_name = serializers.CharField(source="hotel.name", read_only=True)
    created_by_name = serializers.CharField(source="created_by.get_full_name", read_only=True)
    used_by_name = serializers.CharField(source="used_by.get_full_name", read_only=True)
    status_display = serializers.CharField(source="get_status_display", read_only=True)
    original_refund_id = serializers.IntegerField(source="original_refund.id", read_only=True)
    used_in_reservation_id = serializers.IntegerField(source="used_in_reservation.id", read_only=True)
    is_expired = serializers.SerializerMethodField()
    can_be_used = serializers.SerializerMethodField()
    
    class Meta:
        model = RefundVoucher
        fields = [
            "id", "code", "amount", "remaining_amount", "expiry_date", "status", "status_display",
            "hotel", "hotel_name", "original_refund", "original_refund_id",
            "used_in_reservation", "used_in_reservation_id", "used_at", "used_by", "used_by_name",
            "created_at", "updated_at", "created_by", "created_by_name", "notes",
            "is_expired", "can_be_used"
        ]
        read_only_fields = ["created_at", "updated_at", "code", "remaining_amount"]
    
    def get_is_expired(self, obj):
        return obj.is_expired()
    
    def get_can_be_used(self, obj):
        return obj.can_be_used()
    
    def validate_amount(self, value):
        if value <= 0:
            raise serializers.ValidationError("El monto del voucher debe ser mayor a 0")
        return value
    
    def validate_expiry_date(self, value):
        from django.utils import timezone
        if value <= timezone.now():
            raise serializers.ValidationError("La fecha de expiración debe ser futura")
        return value


class RefundVoucherCreateSerializer(serializers.ModelSerializer):
    """Serializer para crear vouchers de reembolso"""
    
    class Meta:
        model = RefundVoucher
        fields = [
            "id", "amount", "expiry_date", "hotel", "original_refund", "notes"
        ]
        read_only_fields = ["id"]
    
    def create(self, validated_data):
        # Establecer el usuario que crea el voucher
        validated_data['created_by'] = self.context['request'].user
        return super().create(validated_data)


class RefundVoucherUseSerializer(serializers.Serializer):
    """Serializer para usar un voucher en una reserva"""
    voucher_code = serializers.CharField(max_length=50)
    amount = serializers.DecimalField(max_digits=12, decimal_places=2)
    reservation_id = serializers.IntegerField()
    
    def validate_amount(self, value):
        if value <= 0:
            raise serializers.ValidationError("El monto debe ser mayor a 0")
        return value
    
    def validate_voucher_code(self, value):
        try:
            voucher = RefundVoucher.objects.get(code=value)
            if not voucher.can_be_used():
                raise serializers.ValidationError("El voucher no puede ser usado")
        except RefundVoucher.DoesNotExist:
            raise serializers.ValidationError("Voucher no encontrado")
        return value


class RefundSerializer(serializers.ModelSerializer):
    """Serializer para reembolsos"""
    reservation_id = serializers.IntegerField(source="reservation.id", read_only=True)
    reservation_display_name = serializers.CharField(source="reservation.display_name", read_only=True)
    payment_method_display = serializers.CharField(source="payment.method", read_only=True)
    created_by_name = serializers.CharField(source="created_by.get_full_name", read_only=True)
    status_display = serializers.CharField(source="get_status_display", read_only=True)
    reason_display = serializers.CharField(source="get_reason_display", read_only=True)
    generated_voucher = RefundVoucherSerializer(read_only=True)
    
    class Meta:
        model = Refund
        fields = [
            "id", "reservation", "reservation_id", "reservation_display_name", "payment", "payment_method_display",
            "amount", "reason", "reason_display", "status", "status_display",
            "refund_method", "processing_days", "external_reference", "notes",
            "processed_at", "created_at", "updated_at", "created_by", "created_by_name",
            "generated_voucher"
        ]
        read_only_fields = ["created_at", "updated_at", "processed_at"]
    
    def validate_amount(self, value):
        if value <= 0:
            raise serializers.ValidationError("El monto del reembolso debe ser mayor a 0")
        return value
    
    def validate(self, data):
        # Validar que el pago pertenezca a la reserva
        if 'payment' in data and 'reservation' in data:
            if data['payment'].reservation != data['reservation']:
                raise serializers.ValidationError(
                    "El pago debe pertenecer a la reserva especificada"
                )
        return data


class RefundCreateSerializer(serializers.ModelSerializer):
    """Serializer para crear reembolsos con valores por defecto"""
    
    class Meta:
        model = Refund
        fields = [
            "reservation", "payment", "amount", "reason", "refund_method",
            "processing_days", "notes"
        ]
    
    def create(self, validated_data):
        # Establecer el usuario que crea el reembolso
        validated_data['created_by'] = self.context['request'].user
        return super().create(validated_data)


class RefundStatusUpdateSerializer(serializers.ModelSerializer):
    """Serializer para actualizar el estado de un reembolso"""
    
    class Meta:
        model = Refund
        fields = ["status", "external_reference", "notes"]
    
    def validate_status(self, value):
        # Validar transiciones de estado permitidas
        if self.instance:
            current_status = self.instance.status
            allowed_transitions = {
                RefundStatus.PENDING: [RefundStatus.PROCESSING, RefundStatus.CANCELLED],
                RefundStatus.PROCESSING: [RefundStatus.COMPLETED, RefundStatus.FAILED],
                RefundStatus.COMPLETED: [],  # No se puede cambiar
                RefundStatus.FAILED: [RefundStatus.PROCESSING],  # Se puede reintentar
                RefundStatus.CANCELLED: []  # No se puede cambiar
            }
            
            if value not in allowed_transitions.get(current_status, []):
                raise serializers.ValidationError(
                    f"No se puede cambiar el estado de {current_status} a {value}"
                )
        return value


class PaymentGatewayConfigSerializer(serializers.ModelSerializer):
    """Serializer para configuraciones de gateway de pago"""
    hotel_name = serializers.CharField(source="hotel.name", read_only=True)
    enterprise_name = serializers.CharField(source="enterprise.name", read_only=True)
    
    class Meta:
        model = PaymentGatewayConfig
        fields = [
            "id", "provider", "enterprise", "enterprise_name", "hotel", "hotel_name",
            "public_key", "access_token", "integrator_id", "is_test", "country_code",
            "currency_code", "webhook_secret", "is_active", "refund_window_days",
            "partial_refunds_allowed", "created_at", "updated_at"
        ]
        read_only_fields = ["created_at", "updated_at"]
    
    def validate(self, data):
        # Validar que refund_window_days sea >= 0 si no es None
        refund_window_days = data.get('refund_window_days')
        if refund_window_days is not None and refund_window_days < 0:
            raise serializers.ValidationError({
                'refund_window_days': 'El valor debe ser mayor o igual a 0'
            })
        
        # Validar que al menos uno de hotel o enterprise esté presente
        hotel = data.get('hotel')
        enterprise = data.get('enterprise')
        if not hotel and not enterprise:
            raise serializers.ValidationError({
                'hotel': 'Debe especificar un hotel o una empresa'
            })
        
        return data


