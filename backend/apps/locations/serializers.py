from rest_framework import serializers
from .models import Country, State, City

class CountrySerializer(serializers.ModelSerializer):
    class Meta:
        model = Country
        fields = [
            "id",
            "name",
            "code2",
            "code3",
            "phone_code",
            "currency_code",
            "timezone",
            "default_check_in_time",
            "default_check_out_time",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]

class StateSerializer(serializers.ModelSerializer):
    country_name = serializers.CharField(source="country.name", read_only=True)
    country_code2 = serializers.CharField(source="country.code2", read_only=True)
    class Meta:
        model = State
        fields = ["id", "name", "code", "country", "country_name", "country_code2", "created_at", "updated_at"]
        read_only_fields = ["id", "created_at", "updated_at"]

class CitySerializer(serializers.ModelSerializer):
    state_name = serializers.CharField(source="state.name", read_only=True)
    country_code2 = serializers.CharField(source="state.country.code2", read_only=True)
    class Meta:
        model = City
        fields = ["id", "name", "state", "state_name", "country_code2", "lat", "lng", "postal_code", "created_at", "updated_at"]
        read_only_fields = ["id", "created_at", "updated_at"]