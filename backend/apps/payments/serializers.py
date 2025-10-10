from rest_framework import serializers
from .models import PaymentMethod, PaymentPolicy


class PaymentMethodSerializer(serializers.ModelSerializer):
    class Meta:
        model = PaymentMethod
        fields = ["id", "code", "name", "is_active", "created_at", "updated_at"]


class PaymentPolicySerializer(serializers.ModelSerializer):
    hotel_name = serializers.CharField(source="hotel.name", read_only=True)
    methods = serializers.PrimaryKeyRelatedField(many=True, queryset=PaymentMethod.objects.all(), required=False)

    class Meta:
        model = PaymentPolicy
        fields = [
            "id", "hotel", "hotel_name", "name", "is_active", "is_default",
            "allow_deposit", "deposit_type", "deposit_value", "deposit_due", "deposit_days_before",
            "balance_due", "methods",
            "created_at", "updated_at",
        ]

    def validate(self, data):
        # Validar que hotel y name estén presentes
        if not data.get('hotel'):
            raise serializers.ValidationError({'hotel': 'Este campo es requerido.'})
        if not data.get('name'):
            raise serializers.ValidationError({'name': 'Este campo es requerido.'})
        
        # Validar que solo una política sea default por hotel
        if data.get('is_default', False):
            hotel = data.get('hotel')
            if hotel:
                existing_default = PaymentPolicy.objects.filter(
                    hotel=hotel,
                    is_default=True
                ).exclude(id=self.instance.id if self.instance else None)
                if existing_default.exists():
                    raise serializers.ValidationError(
                        {'is_default': 'Ya existe una política de pago por defecto para este hotel'}
                    )
        
        return data


