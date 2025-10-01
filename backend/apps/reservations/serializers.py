from rest_framework import serializers
from django.utils import timezone
from django.db import transaction
from .models import Reservation, ReservationStatus, ReservationCharge, Payment, ChannelCommission
from apps.rooms.models import RoomStatus

class ReservationSerializer(serializers.ModelSerializer):
    hotel_name = serializers.CharField(source="hotel.name", read_only=True)
    room_name = serializers.CharField(source="room.name", read_only=True)
    room_data = serializers.SerializerMethodField()  # Datos completos de la habitación
    guest_name = serializers.CharField(read_only=True)  # Propiedad del modelo
    guest_email = serializers.CharField(read_only=True)  # Propiedad del modelo
    display_name = serializers.CharField(read_only=True)

    class Meta:
        model = Reservation
        fields = [
            "id", "hotel", "hotel_name", "room", "room_name", "room_data",
            "guest_name", "guest_email", "guests", "guests_data",
            "check_in", "check_out", "status", "total_price", "notes",
            "channel",
            "display_name", "created_at", "updated_at",
        ]
        read_only_fields = ["id", "total_price", "created_at", "updated_at", "guest_name", "guest_email", "room_data", "display_name"]

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
            instance = Reservation(**validated_data)
            instance.full_clean()
            instance.save()
            return instance

    def update(self, instance, validated_data):
        with transaction.atomic():
            for key, value in validated_data.items():
                setattr(instance, key, value)
            instance.full_clean()
            instance.save()
            return instance

class ReservationChargeSerializer(serializers.ModelSerializer):
    class Meta:
        model = ReservationCharge
        fields = ['id', 'date', 'description', 'amount']

class PaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payment
        fields = ['id', 'date', 'method', 'amount']

class ChannelCommissionSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChannelCommission
        fields = ['id', 'channel', 'rate_percent', 'amount']
