from rest_framework import serializers
from .models import Room
from django.utils import timezone

class RoomSerializer(serializers.ModelSerializer):
    hotel_name = serializers.CharField(source="hotel.name", read_only=True)
    current_reservation = serializers.SerializerMethodField()
    current_guests = serializers.SerializerMethodField()
    future_reservations = serializers.SerializerMethodField()

    class Meta:
        model = Room
        fields = [
            "id",
            "hotel", 
            "hotel_name", 
            "name",
            "number", 
            "floor",
            "room_type", 
            "capacity", 
            "max_capacity", 
            "extra_guest_fee", 
            "base_price", 
            "status",
            "is_active", 
            "description", 
            "created_at", 
            "updated_at",
            "current_reservation", 
            "current_guests",
            "future_reservations",
        ]
        
        read_only_fields = [
            "id", 
            "created_at", 
            "updated_at", 
            "current_reservation", 
            "current_guests",
            "future_reservations"
        ]

    def get_future_reservations(self, obj):
        today = timezone.localdate()
        qs = (obj.reservations
              .filter(check_out__gt=today)
              .order_by("check_in")
              .values("id", "status", "guest_name", "check_in", "check_out")
        )
        return list(qs)

    def get_current_reservation(self, obj):
        today = timezone.localdate()
        # Consideramos ocupación si la reserva está confirmada o en check-in
        active_status = ["confirmed", "check_in"]
        res = (obj.reservations
               .filter(check_in__lte=today, check_out__gt=today, status__in=active_status)
               .order_by("-status")
               .values("id", "status", "guest_name", "check_in", "check_out")
               .first())
        return res

    def get_current_guests(self, obj):
        today = timezone.localdate()
        # Consideramos ocupación si la reserva está confirmada o en check-in
        active_status = ["confirmed", "check_in"]
        reservation = (obj.reservations
                      .filter(check_in__lte=today, check_out__gt=today, status__in=active_status)
                      .first())
        
        if reservation:
            # Retornar el número real de huéspedes de la reserva
            return reservation.guests
        return 0