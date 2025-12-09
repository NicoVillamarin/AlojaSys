from rest_framework import serializers

from .models import Enterprise
from .features import get_effective_features


class EnterpriseSerializer(serializers.ModelSerializer):
    city_name = serializers.SerializerMethodField(read_only=True)
    state_name = serializers.SerializerMethodField(read_only=True)
    country_code2 = serializers.SerializerMethodField(read_only=True)
    plan_features = serializers.SerializerMethodField(read_only=True)

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
            "plan_type",
            "enabled_features",
            "plan_features",
            "is_active",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]

    def to_internal_value(self, data):
        # Normalizar strings vacíos a null para FKs opcionales
        if isinstance(data, dict):
            data = data.copy()
            for key in ("country", "state", "city"):
                if data.get(key) == "":
                    data[key] = None
        return super().to_internal_value(data)

    def validate(self, attrs):
        """
        Si viene city, forzar coherencia: state y country se derivan de city.
        Si no viene city pero viene state, derivar country desde state.
        """
        city = attrs.get("city")
        state = attrs.get("state")
        if city is not None:
            try:
                # city, state y country son instancias; asignamos consistentes
                attrs["state"] = city.state if hasattr(city, "state") else None
                attrs["country"] = city.state.country if hasattr(city, "state") and hasattr(city.state, "country") else None
            except Exception:
                pass
        elif state is not None:
            try:
                attrs["country"] = state.country if hasattr(state, "country") else None
            except Exception:
                pass
        return attrs

    def get_plan_features(self, obj: Enterprise):
        """
        Devuelve los features efectivos que tiene la empresa según su plan
        y overrides. Útil para que el frontend pueda ocultar/mostrar módulos.
        """
        return get_effective_features(obj)

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


