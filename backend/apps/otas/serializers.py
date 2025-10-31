from rest_framework import serializers

from .models import (
    OtaConfig,
    OtaRoomMapping,
    OtaSyncJob,
    OtaSyncLog,
    OtaRoomTypeMapping,
    OtaRatePlanMapping,
)


class OtaConfigSerializer(serializers.ModelSerializer):
    hotel_name = serializers.CharField(source="hotel.name", read_only=True)

    class Meta:
        model = OtaConfig
        fields = [
            "id", "hotel", "hotel_name", "provider", "is_active", "label",
            "ical_out_token", "credentials",
            # Booking fields
            "booking_hotel_id", "booking_client_id", "booking_client_secret",
            "booking_base_url", "booking_mode",
            # Airbnb fields
            "airbnb_account_id", "airbnb_client_id", "airbnb_client_secret",
            "airbnb_base_url", "airbnb_mode",
            "created_at", "updated_at",
        ]
        read_only_fields = ["created_at", "updated_at"]


class OtaRoomMappingSerializer(serializers.ModelSerializer):
    hotel_name = serializers.CharField(source="hotel.name", read_only=True)
    room_name = serializers.CharField(source="room.name", read_only=True)

    class Meta:
        model = OtaRoomMapping
        fields = [
            "id", "hotel", "hotel_name", "room", "room_name", "provider",
            "external_id", "ical_in_url", "is_active", "created_at", "updated_at",
        ]
        read_only_fields = ["created_at", "updated_at"]


class OtaSyncJobSerializer(serializers.ModelSerializer):
    hotel_name = serializers.CharField(source="hotel.name", read_only=True)

    class Meta:
        model = OtaSyncJob
        fields = [
            "id", "hotel", "hotel_name", "provider", "job_type", "status",
            "started_at", "finished_at", "stats", "error_message",
        ]


class OtaSyncLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = OtaSyncLog
        fields = ["id", "job", "level", "message", "payload", "created_at"]


class OtaRoomTypeMappingSerializer(serializers.ModelSerializer):
    hotel_name = serializers.CharField(source="hotel.name", read_only=True)

    class Meta:
        model = OtaRoomTypeMapping
        fields = [
            "id", "hotel", "hotel_name", "provider", "room_type_code", "provider_code",
            "name", "is_active", "created_at", "updated_at"
        ]
        read_only_fields = ["created_at", "updated_at"]


class OtaRatePlanMappingSerializer(serializers.ModelSerializer):
    hotel_name = serializers.CharField(source="hotel.name", read_only=True)

    class Meta:
        model = OtaRatePlanMapping
        fields = [
            "id", "hotel", "hotel_name", "provider", "rate_plan_code", "provider_code",
            "currency", "is_active", "created_at", "updated_at"
        ]
        read_only_fields = ["created_at", "updated_at"]