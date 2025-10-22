from rest_framework import serializers
from .models import Hotel

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
        fields = ["id", "enterprise", "enterprise_name", "name", "legal_name", "tax_id", "check_in_time", "check_out_time", "auto_check_in_enabled", "auto_no_show_enabled", "email", "phone",
                  "address", "country", "state", "city", "city_name", "state_name", "country_code2",
                  "logo", "logo_url", "logo_base64", "logo_filename", "is_active", "created_at", "updated_at"]
        read_only_fields = ["id", "created_at", "updated_at"]
    
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


 