from rest_framework import serializers
from .models import Currency, Hotel


class CurrencyCodeField(serializers.SlugRelatedField):
    """
    Compatibilidad: expone/acepta `currency` como código (string) aunque en DB sea FK.
    Free-form: si el código no existe, se crea automáticamente.
    """

    def to_internal_value(self, data):
        if data is None:
            raise serializers.ValidationError("currency es requerido")
        code = str(data).strip().upper()
        if not code:
            raise serializers.ValidationError("currency es requerido")
        try:
            return Currency.objects.get(code__iexact=code)
        except Currency.DoesNotExist:
            # Modo free-form: crear al vuelo
            return Currency.objects.create(code=code, name=code)

class HotelSerializer(serializers.ModelSerializer):
    enterprise_name = serializers.CharField(source="enterprise.name", read_only=True)
    city_name = serializers.CharField(source="city.name", read_only=True)
    state_name = serializers.CharField(source="city.state.name", read_only=True)
    country_code2 = serializers.CharField(source="city.state.country.code2", read_only=True)
    logo_url = serializers.SerializerMethodField()
    logo_base64 = serializers.CharField(write_only=True, required=False)
    logo_filename = serializers.CharField(write_only=True, required=False)
    
    class Meta:
        model = Hotel
        fields = [
            "id",
            "enterprise",
            "enterprise_name",
            "name",
            "legal_name",
            "tax_id",
            "check_in_time",
            "check_out_time",
            "auto_check_in_enabled",
            "auto_check_out_enabled",
            "auto_no_show_enabled",
            "email",
            "phone",
            "address",
            "country",
            "state",
            "city",
            "city_name",
            "state_name",
            "country_code2",
            # WhatsApp config
            "whatsapp_enabled",
            "whatsapp_phone",
            "whatsapp_provider",
            "whatsapp_business_id",
            "whatsapp_phone_number_id",
            "whatsapp_api_token",
            "whatsapp_provider_account",
            # Logo / estado
            "logo",
            "logo_url",
            "logo_base64",
            "logo_filename",
            "guest_card_policies",
            "is_active",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]
        extra_kwargs = {
            "whatsapp_api_token": {"write_only": True, "required": False, "allow_blank": True},
        }

    def get_logo_url(self, obj):
        """Obtiene la URL completa del logo"""
        if obj.logo:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.logo.url)
            return obj.logo.url
        return None
    
    def create(self, validated_data):
        """Crear hotel con logo desde base64"""
        logo_base64 = validated_data.pop('logo_base64', None)
        logo_filename = validated_data.pop('logo_filename', None)
        
        hotel = super().create(validated_data)
        
        if logo_base64 and logo_filename:
            self._save_logo_from_base64(hotel, logo_base64, logo_filename)
        
        return hotel
    
    def update(self, instance, validated_data):
        """Actualizar hotel con logo desde base64"""
        logo_base64 = validated_data.pop('logo_base64', None)
        logo_filename = validated_data.pop('logo_filename', None)
        
        hotel = super().update(instance, validated_data)
        
        if logo_base64 and logo_filename:
            self._save_logo_from_base64(hotel, logo_base64, logo_filename)
        
        return hotel
    
    def _save_logo_from_base64(self, hotel, logo_base64, logo_filename):
        """Guarda el logo desde base64"""
        try:
            import base64
            from django.core.files.base import ContentFile
            
            # Decodificar base64
            if ',' in logo_base64:
                header, data = logo_base64.split(',', 1)
            else:
                data = logo_base64
            
            file_data = base64.b64decode(data)
            
            # Crear archivo
            file_obj = ContentFile(file_data, name=logo_filename)
            
            # Guardar en el campo logo
            hotel.logo.save(logo_filename, file_obj, save=True)
            
        except Exception as e:
            print(f"Error guardando logo desde base64: {e}")
            # No lanzar excepción para no romper el guardado del hotel


class CurrencySerializer(serializers.ModelSerializer):
    class Meta:
        model = Currency
        fields = [
            "id",
            "code",
            "name",
            "symbol",
            "is_active",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]

    def validate_code(self, value):
        code = str(value).strip().upper()
        if not code:
            raise serializers.ValidationError("code es requerido")
        return code
