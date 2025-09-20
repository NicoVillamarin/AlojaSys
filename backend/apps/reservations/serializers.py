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
            "guest_name", "guest_email",
            "check_in", "check_out", "status", "total_price", "notes",
            "created_at", "updated_at",
        ]
        read_only_fields = ["id", "total_price", "created_at", "updated_at"]

    def create(self, validated_data):
        with transaction.atomic():
            instance = Reservation(**validated_data)
            instance.full_clean()
            instance.save()
            self._maybe_auto_check_in(instance)
            if instance.status == ReservationStatus.CHECK_IN:
                instance.save(update_fields=["status"])
            return instance

    def update(self, instance, validated_data):
        with transaction.atomic():
            for key, value in validated_data.items():
                setattr(instance, key, value)
            instance.full_clean()
            instance.save()
            self._maybe_auto_check_in(instance)
            if instance.status == ReservationStatus.CHECK_IN:
                instance.save(update_fields=["status"])
            return instance

    def _maybe_auto_check_in(self, instance: Reservation) -> None:
        """Auto check-in si la reserva está confirmada y activa hoy.
        No hace nada para fechas futuras o si ya está en check_in.
        """
        today = timezone.localdate()
        if (
            instance.status == ReservationStatus.CONFIRMED
            and instance.check_in <= today < instance.check_out
        ):
            if instance.status != ReservationStatus.CHECK_IN:
                instance.status = ReservationStatus.CHECK_IN
            if instance.room.status != RoomStatus.OCCUPIED:
                instance.room.status = RoomStatus.OCCUPIED
                instance.room.save(update_fields=["status"])