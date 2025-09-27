from rest_framework import serializers
from django.utils import timezone
from django.db import transaction
from .models import Reservation, ReservationStatus
from apps.rooms.models import RoomStatus

class ReservationSerializer(serializers.ModelSerializer):
    hotel_name = serializers.CharField(source="hotel.name", read_only=True)
    room_name = serializers.CharField(source="room.name", read_only=True)

    class Meta:
        model = Reservation
        fields = [
            "id", "hotel", "hotel_name", "room", "room_name",
            "guest_name", "guest_email", "guests",
            "check_in", "check_out", "status", "total_price", "notes",
            "created_at", "updated_at",
        ]
        read_only_fields = ["id", "total_price", "created_at", "updated_at"]

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
