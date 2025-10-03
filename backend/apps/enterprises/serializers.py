from rest_framework import serializers
from .models import Enterprise


class EnterpriseSerializer(serializers.ModelSerializer):
    city_name = serializers.SerializerMethodField(read_only=True)
    state_name = serializers.SerializerMethodField(read_only=True)
    country_code2 = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Enterprise
        fields = [
            "id",
            "name",
            "legal_name",
            "tax_id",
            "email",
            "phone",
            "address",
            "country",
            "state",
            "city",
            "city_name",
            "state_name",
            "country_code2",
            "is_active",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]

    def get_city_name(self, obj):
        try:
            return obj.city.name if obj.city else ""
        except Exception:
            return ""

    def get_state_name(self, obj):
        try:
            return obj.city.state.name if obj.city and obj.city.state else ""
        except Exception:
            return ""

    def get_country_code2(self, obj):
        try:
            return obj.city.state.country.code2 if obj.city and obj.city.state and obj.city.state.country else ""
        except Exception:
            return ""


