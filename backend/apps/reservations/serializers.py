from rest_framework import serializers
from django.db.models import Sum
from django.utils import timezone
from django.db import transaction
from django.core.exceptions import ValidationError
from datetime import date
from .models import Reservation, ReservationStatus, ReservationCharge, Payment, ChannelCommission
from apps.rooms.models import RoomStatus

class ReservationSerializer(serializers.ModelSerializer):
    hotel_name = serializers.CharField(source="hotel.name", read_only=True)
    room_name = serializers.CharField(source="room.name", read_only=True)
    room_data = serializers.SerializerMethodField()  # Datos completos de la habitación
    guest_name = serializers.CharField(read_only=True)  # Propiedad del modelo
    guest_email = serializers.CharField(read_only=True)  # Propiedad del modelo
    display_name = serializers.CharField(read_only=True)
    total_price = serializers.SerializerMethodField()
    balance_due = serializers.SerializerMethodField()
    total_paid = serializers.SerializerMethodField()
    applied_cancellation_policy_name = serializers.CharField(
        source="applied_cancellation_policy.name", 
        read_only=True
    )

    class Meta:
        model = Reservation
        fields = [
            "id", "hotel", "hotel_name", "room", "room_name", "room_data",
            "guest_name", "guest_email", "guests", "guests_data",
            "check_in", "check_out", "status", "total_price", "balance_due", "total_paid", "notes",
            "channel", "promotion_code", "voucher_code", "applied_cancellation_policy", "applied_cancellation_policy_name",
            "display_name", "created_at", "updated_at",
        ]
        read_only_fields = ["id", "total_price", "balance_due", "total_paid", "created_at", "updated_at", "guest_name", "guest_email", "room_data", "display_name"]

    def get_room_data(self, obj):
        """Devuelve los datos completos de la habitación"""
        if not obj.room:
            return None
        
        return {
            "id": obj.room.id,
            "name": obj.room.name,
            "number": obj.room.number,
            "floor": obj.room.floor,
            "room_type": obj.room.room_type,
            "capacity": obj.room.capacity,
            "max_capacity": obj.room.max_capacity,
            "base_price": float(obj.room.base_price),
            "extra_guest_fee": float(obj.room.extra_guest_fee),
            "description": obj.room.description,
            "status": obj.room.status,
            "is_active": obj.room.is_active,
        }

    def create(self, validated_data):
        with transaction.atomic():
            # Asignar política de cancelación vigente al momento de crear la reserva
            if 'applied_cancellation_policy' not in validated_data:
                from apps.payments.models import CancellationPolicy
                hotel = validated_data.get('hotel')
                if hotel:
                    cancellation_policy = CancellationPolicy.resolve_for_hotel(hotel)
                    if cancellation_policy:
                        validated_data['applied_cancellation_policy'] = cancellation_policy
            
            instance = Reservation(**validated_data)
            instance.full_clean()
            instance.save()
            return instance

    def update(self, instance, validated_data):
        with transaction.atomic():
            # Validar que no se pueda confirmar una reserva con check_in anterior a la fecha actual
            if 'status' in validated_data and validated_data['status'] == ReservationStatus.CONFIRMED:
                today = date.today()
                if instance.check_in < today:
                    raise ValidationError({
                        'status': 'No se puede confirmar una reserva con fecha de check-in anterior a la fecha actual.'
                    })
                
                # Guardar snapshot de la política de cancelación al confirmar la reserva
                if instance.applied_cancellation_policy and not instance.applied_cancellation_snapshot:
                    policy = instance.applied_cancellation_policy
                    instance.applied_cancellation_snapshot = {
                        'policy_id': policy.id,
                        'name': policy.name,
                        'free_cancellation_time': policy.free_cancellation_time,
                        'free_cancellation_unit': policy.free_cancellation_unit,
                        'partial_time': policy.partial_refund_time,
                        'partial_percentage': float(policy.partial_refund_percentage),
                        'no_cancellation_time': policy.no_refund_time,
                        'no_cancellation_unit': policy.no_refund_unit,
                        'fee_type': policy.cancellation_fee_type,
                        'fee_value': float(policy.cancellation_fee_value),
                        'auto_refund_on_cancel': policy.auto_refund_on_cancel,
                        'allow_cancellation_after_checkin': policy.allow_cancellation_after_checkin,
                        'allow_cancellation_after_checkout': policy.allow_cancellation_after_checkout,
                        'allow_cancellation_no_show': policy.allow_cancellation_no_show,
                        'allow_cancellation_early_checkout': policy.allow_cancellation_early_checkout,
                        'snapshot_created_at': timezone.now().isoformat()
                    }
            
            for key, value in validated_data.items():
                setattr(instance, key, value)
            instance.full_clean()
            instance.save()
            return instance

    def get_total_price(self, obj):
        nights_sum = obj.nights.aggregate(s=Sum('total_night'))['s']
        if nights_sum is not None:
            return nights_sum
        return obj.total_price

    def get_balance_due(self, obj):
        """Calcula el saldo pendiente de la reserva"""
        from apps.payments.services.payment_calculator import calculate_balance_due
        balance_info = calculate_balance_due(obj)
        return float(balance_info['balance_due'])

    def get_total_paid(self, obj):
        """Calcula el total pagado de la reserva"""
        from apps.payments.services.payment_calculator import calculate_balance_due
        balance_info = calculate_balance_due(obj)
        return float(balance_info['total_paid'])

class ReservationChargeSerializer(serializers.ModelSerializer):
    class Meta:
        model = ReservationCharge
        fields = ['id', 'date', 'description', 'amount']

class PaymentSerializer(serializers.ModelSerializer):
    receipt_pdf_url = serializers.URLField(read_only=True, allow_null=True)
    
    class Meta:
        model = Payment
        fields = ['id', 'date', 'method', 'amount', 'terminal_id', 'batch_number', 'status', 'notes', 'is_deposit', 'metadata', 'receipt_pdf_url']

class ChannelCommissionSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChannelCommission
        fields = ['id', 'channel', 'rate_percent', 'amount']
