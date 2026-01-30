from rest_framework import serializers
from django.db.models import Sum
from django.utils import timezone
from django.db import transaction
from django.core.exceptions import ValidationError
from datetime import date
from .models import Reservation, ReservationStatus, ReservationCharge, Payment, ChannelCommission, ReservationChannel
from apps.rooms.models import RoomStatus, Room
from apps.core.models import Hotel

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
    channel_display = serializers.SerializerMethodField()
    is_ota = serializers.SerializerMethodField()
    paid_by = serializers.CharField(read_only=True)
    overbooking_flag = serializers.BooleanField(read_only=True)
    pricing_currency_code = serializers.CharField(source="pricing_currency.code", read_only=True)

    class Meta:
        model = Reservation
        fields = [
            "id", "hotel", "hotel_name", "room", "room_name", "room_data",
            "guest_name", "guest_email", "guests", "guests_data",
            "group_code",
            "check_in", "check_out", "status", "total_price", "balance_due", "total_paid", "notes",
            "channel", "channel_display", "is_ota", "paid_by", "overbooking_flag",
            "promotion_code", "voucher_code", "applied_cancellation_policy", "applied_cancellation_policy_name",
            "price_source", "pricing_currency", "pricing_currency_code",
            "display_name", "created_at", "updated_at",
        ]
        read_only_fields = [
            "id",
            "total_price",
            "balance_due",
            "total_paid",
            "created_at",
            "updated_at",
            "guest_name",
            "guest_email",
            "room_data",
            "display_name",
            "pricing_currency",
            "pricing_currency_code",
        ]

    @staticmethod
    def _infer_channel_label_from_guests_data(obj) -> str | None:
        """
        Para reservas que entran vía Smoobu, intentamos inferir el canal real
        (Booking/Airbnb/Expedia) desde metadata en guests_data.
        """
        try:
            guests_data = obj.guests_data or []
            if not isinstance(guests_data, list) or not guests_data:
                return None
            primary = next((g for g in guests_data if isinstance(g, dict) and g.get("is_primary") is True), None)
            if not primary:
                primary = guests_data[0] if isinstance(guests_data[0], dict) else None
            if not primary:
                return None
            channel_name = (primary.get("channel_name") or primary.get("provider_channel") or "") if isinstance(primary, dict) else ""
            channel_name = str(channel_name).lower()
            if "booking" in channel_name:
                return "Booking"
            if "airbnb" in channel_name:
                return "Airbnb"
            if "expedia" in channel_name:
                return "Expedia"
        except Exception:
            return None
        return None

    def get_channel_display(self, obj):
        """
        Display del canal para UI.

        - Por defecto usa el label del enum (`get_channel_display()`).
        - Si la reserva entró vía Smoobu (external_id prefijo `smoobu:`), mostramos:
          "Booking - Smoobu", "Airbnb - Smoobu", etc.
        """
        base = obj.get_channel_display() if hasattr(obj, "get_channel_display") else str(getattr(obj, "channel", "") or "")
        external_id = str(getattr(obj, "external_id", "") or "")
        if external_id.startswith("smoobu:"):
            # Si quedó como "Otro", intentamos inferir el canal real desde metadata.
            if base.lower() in ("otro", "other"):
                inferred = self._infer_channel_label_from_guests_data(obj)
                if inferred:
                    base = inferred
            return f"{base} - Smoobu"
        return base

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
            "base_currency": getattr(obj.room, "base_currency_id", None),
            "base_currency_code": getattr(getattr(obj.room, "base_currency", None), "code", None),
            "extra_guest_fee": float(obj.room.extra_guest_fee),
            "secondary_price": float(obj.room.secondary_price) if getattr(obj.room, "secondary_price", None) is not None else None,
            "secondary_currency": getattr(obj.room, "secondary_currency_id", None),
            "secondary_currency_code": getattr(getattr(obj.room, "secondary_currency", None), "code", None),
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

            # Normalización de canal/origen
            # - Si no hay external_id y el payload NO especificó canal, usar DIRECT
            # - Si hay external_id y el canal viene como DIRECT, forzar OTHER (reservas OTA)
            if not instance.external_id:
                if "channel" not in validated_data:
                    instance.channel = ReservationChannel.DIRECT
            else:
                if instance.channel == ReservationChannel.DIRECT:
                    instance.channel = ReservationChannel.OTHER
            
            # Validar disponibilidad en OTAs antes de confirmar (solo para reservas sin external_id)
            if not instance.external_id and instance.room_id and instance.check_in and instance.check_out:
                from apps.otas.services.availability_checker import OtaAvailabilityChecker
                from django.core.exceptions import ValidationError
                
                # Solo validar si es una reserva que se va a confirmar (CONFIRMED o PENDING que luego se confirmará)
                # No validar para reservas importadas desde OTAs (external_id)
                strict_mode = validated_data.get('status') == ReservationStatus.CONFIRMED
                
                is_valid, warnings = OtaAvailabilityChecker.validate_before_confirmation(
                    room=instance.room,
                    check_in=instance.check_in,
                    check_out=instance.check_out,
                    exclude_reservation_id=None,
                    strict=strict_mode
                )
                
                if not is_valid:
                    # En modo estricto, rechazar la reserva
                    error_msg = "La habitación no está disponible en las OTAs. " + "; ".join(warnings)
                    raise ValidationError(error_msg)
                elif warnings and strict_mode:
                    # Si hay advertencias en modo estricto, incluirlas en las notas
                    if not instance.notes:
                        instance.notes = ""
                    instance.notes += f"\n[OTA Check] {'; '.join(warnings)}"
            
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
                
                # Validar disponibilidad en OTAs antes de confirmar (solo para reservas sin external_id)
                if not instance.external_id and instance.room_id and instance.check_in and instance.check_out:
                    from apps.otas.services.availability_checker import OtaAvailabilityChecker
                    
                    # Obtener fechas actualizadas si se están modificando
                    check_in = validated_data.get('check_in', instance.check_in)
                    check_out = validated_data.get('check_out', instance.check_out)
                    
                    is_valid, warnings = OtaAvailabilityChecker.validate_before_confirmation(
                        room=instance.room,
                        check_in=check_in,
                        check_out=check_out,
                        exclude_reservation_id=instance.id,
                        strict=True  # En modo estricto al confirmar
                    )
                    
                    if not is_valid:
                        error_msg = "La habitación no está disponible en las OTAs. " + "; ".join(warnings)
                        raise ValidationError(error_msg)
                    elif warnings:
                        # Agregar advertencias a las notas
                        if not instance.notes:
                            instance.notes = ""
                        instance.notes += f"\n[OTA Check al confirmar] {'; '.join(warnings)}"
                
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
            
            # Normalización de canal/origen en update
            external_id_final = validated_data.get('external_id', instance.external_id)
            # Aplicar el resto de campos excepto 'channel' (lo normalizamos luego)
            for key, value in validated_data.items():
                if key == 'channel':
                    continue
                setattr(instance, key, value)

            if not external_id_final:
                instance.channel = ReservationChannel.DIRECT
            else:
                # Si viene DIRECT por error, forzar a OTHER como seguro por defecto
                new_channel = validated_data.get('channel', instance.channel)
                if new_channel == ReservationChannel.DIRECT:
                    new_channel = ReservationChannel.OTHER
                instance.channel = new_channel
            instance.full_clean()
            instance.save()
            return instance

    def get_is_ota(self, obj):
        return bool(obj.external_id)

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


class MultiRoomReservationRoomSerializer(serializers.Serializer):
    """
    Datos específicos de cada habitación dentro de una reserva multi-habitación.
    """
    room = serializers.PrimaryKeyRelatedField(queryset=Room.objects.all())
    guests = serializers.IntegerField(min_value=1)
    guests_data = serializers.ListField(
        child=serializers.DictField(),
        required=False
    )
    promotion_code = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    voucher_code = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    notes = serializers.CharField(required=False, allow_blank=True, allow_null=True)


class MultiRoomReservationCreateSerializer(serializers.Serializer):
    """
    Serializer de entrada para crear una reserva multi-habitación.

    Crea internamente varias instancias de `Reservation`, una por habitación,
    compartiendo hotel, fechas y canal, y reutilizando toda la lógica de
    validación/pricing existente del serializer de una sola reserva.
    """
    hotel = serializers.PrimaryKeyRelatedField(queryset=Hotel.objects.all())
    check_in = serializers.DateField()
    check_out = serializers.DateField()
    status = serializers.ChoiceField(choices=ReservationStatus.choices, required=False)
    channel = serializers.ChoiceField(choices=ReservationChannel.choices, required=False)
    external_id = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    notes = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    promotion_code = serializers.CharField(required=False, allow_blank=True, allow_null=True, help_text="Código de promoción a nivel de grupo (se aplica a todas las habitaciones si no tienen uno específico)")
    voucher_code = serializers.CharField(required=False, allow_blank=True, allow_null=True, help_text="Código de voucher a nivel de grupo (se aplica a todas las habitaciones si no tienen uno específico)")
    group_code = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    rooms = MultiRoomReservationRoomSerializer(many=True)

class ReservationChargeSerializer(serializers.ModelSerializer):
    class Meta:
        model = ReservationCharge
        fields = ['id', 'date', 'description', 'amount']

class PaymentSerializer(serializers.ModelSerializer):
    receipt_pdf_url = serializers.URLField(read_only=True, allow_null=True)
    receipt_number = serializers.CharField(read_only=True, allow_null=True)
    
    class Meta:
        model = Payment
        fields = ['id', 'date', 'method', 'amount', 'currency', 'terminal_id', 'batch_number', 'status', 'notes', 'is_deposit', 'metadata', 'receipt_pdf_url', 'receipt_number']

class ChannelCommissionSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChannelCommission
        fields = ['id', 'channel', 'rate_percent', 'amount']
