from rest_framework import serializers
from .models import Room

class RoomSerializer(serializers.ModelSerializer):
    hotel_name = serializers.CharField(source="hotel.name", read_only=True)

    class Meta:
        model = Room
        fields = [
            "id", "hotel", "hotel_name", "name", "number", "floor",
            "room_type", "capacity", "base_price", "status",
            "is_active", "description", "created_at", "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]