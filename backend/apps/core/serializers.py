from rest_framework import serializers
from .models import Hotel

class HotelSerializer(serializers.ModelSerializer):
    enterprise_name = serializers.CharField(source="enterprise.name", read_only=True)
    city_name = serializers.CharField(source="city.name", read_only=True)
    state_name = serializers.CharField(source="city.state.name", read_only=True)
    country_code2 = serializers.CharField(source="city.state.country.code2", read_only=True)
    class Meta:
        model = Hotel
        fields = ["id", "enterprise", "enterprise_name", "name", "legal_name", "tax_id", "check_in_time", "check_out_time", "auto_check_in_enabled", "email", "phone",
                  "address", "country", "state", "city", "city_name", "state_name", "country_code2",
                  "is_active", "created_at", "updated_at"]
        read_only_fields = ["id", "created_at", "updated_at"]


 