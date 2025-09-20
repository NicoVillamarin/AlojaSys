from rest_framework import serializers
from .models import Hotel

class HotelSerializer(serializers.ModelSerializer):
    city_name = serializers.CharField(source="city.name", read_only=True)
    state_name = serializers.CharField(source="city.state.name", read_only=True)
    country_code2 = serializers.CharField(source="city.state.country.code2", read_only=True)
    class Meta:
        model = Hotel
        fields = ["id", "name", "legal_name", "tax_id", "check_in_time", "check_out_time", "email", "phone",
                  "address", "city", "city_name", "state_name", "country_code2",
                  "is_active", "created_at", "updated_at"]
        read_only_fields = ["id", "created_at", "updated_at"]