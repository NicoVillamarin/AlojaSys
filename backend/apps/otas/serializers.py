from rest_framework import serializers
from django.core.exceptions import ValidationError
from urllib.parse import urlparse

from .models import (
    OtaConfig,
    OtaRoomMapping,
    OtaSyncJob,
    OtaSyncLog,
    OtaRoomTypeMapping,
    OtaRatePlanMapping,
    OtaProvider,
)


def _mask_sensitive_value(value: str | None, visible_chars: int = 4) -> str | None:
    """Enmascara un valor sensible mostrando solo los primeros caracteres."""
    if not value or len(value) <= visible_chars:
        return "****" if value else None
    return f"{value[:visible_chars]}{'*' * max(8, len(value) - visible_chars)}"


class OtaConfigSerializer(serializers.ModelSerializer):
    hotel_name = serializers.CharField(source="hotel.name", read_only=True)
    
    # Campos enmascarados para lectura (siempre visibles)
    ical_out_token_masked = serializers.SerializerMethodField()
    booking_client_secret_masked = serializers.SerializerMethodField()
    airbnb_client_secret_masked = serializers.SerializerMethodField()
    
    # Campos originales: writable para actualizar, pero enmascarados en lectura
    ical_out_token = serializers.CharField(required=False, allow_null=True, allow_blank=True)
    booking_client_secret = serializers.CharField(write_only=True, required=False, allow_null=True, allow_blank=True)
    airbnb_client_secret = serializers.CharField(write_only=True, required=False, allow_null=True, allow_blank=True)
    
    def __init__(self, *args, **kwargs):
        """Permite incluir token real solo cuando se solicita explícitamente."""
        super().__init__(*args, **kwargs)
        # Por defecto, no exponer el token real
        self._include_real_token = kwargs.get('context', {}).get('include_real_token', False)

    def get_ical_out_token_masked(self, obj) -> str | None:
        """Retorna el token iCal enmascarado para lectura."""
        return _mask_sensitive_value(obj.ical_out_token)

    def get_booking_client_secret_masked(self, obj) -> str | None:
        """Retorna el secret de Booking enmascarado para lectura."""
        return _mask_sensitive_value(obj.booking_client_secret)

    def get_airbnb_client_secret_masked(self, obj) -> str | None:
        """Retorna el secret de Airbnb enmascarado para lectura."""
        return _mask_sensitive_value(obj.airbnb_client_secret)
    
    # URLs completas de iCal (para evitar exponer token real)
    ical_hotel_url = serializers.SerializerMethodField()
    ical_room_urls = serializers.SerializerMethodField()
    
    def get_ical_hotel_url(self, obj) -> str | None:
        """Retorna la URL completa del iCal del hotel."""
        if not obj.ical_out_token or not obj.hotel_id:
            return None
        request = self.context.get('request')
        if request:
            base_url = f"{request.scheme}://{request.get_host()}"
            return f"{base_url}/api/otas/ical/hotel/{obj.hotel_id}.ics?token={obj.ical_out_token}"
        return None
    
    def get_ical_room_urls(self, obj) -> list:
        """Retorna las URLs completas de iCal por habitación (si aplica)."""
        # Por ahora retornamos lista vacía, se puede expandir si es necesario
        return []
    
    def to_representation(self, instance):
        """Enmascara tokens/secrets en la respuesta."""
        data = super().to_representation(instance)
        # Enmascarar ical_out_token en la respuesta (a menos que se solicite explícitamente)
        if 'ical_out_token' in data and data['ical_out_token']:
            if not self._include_real_token:
                data['ical_out_token'] = _mask_sensitive_value(instance.ical_out_token)
        return data

    def validate_booking_base_url(self, value: str | None) -> str | None:
        """Valida que booking_base_url contenga un dominio permitido."""
        if not value:
            return value
        
        # Dominios permitidos para Booking
        allowed_domains = ['booking.com', 'httpbin.org']  # httpbin.org para testing
        
        try:
            parsed = urlparse(value)
            domain = parsed.netloc.lower().replace('www.', '')
            
            # Verificar que el dominio esté en la lista permitida
            if not any(allowed in domain for allowed in allowed_domains):
                raise ValidationError(
                    f"El dominio '{domain}' no está permitido. "
                    f"Dominios permitidos: {', '.join(allowed_domains)}"
                )
        except Exception as e:
            raise ValidationError(f"URL inválida: {str(e)}")
        
        return value

    def validate_airbnb_base_url(self, value: str | None) -> str | None:
        """Valida que airbnb_base_url contenga un dominio permitido."""
        if not value:
            return value
        
        # Dominios permitidos para Airbnb
        allowed_domains = ['airbnb.com', 'httpbin.org']  # httpbin.org para testing
        
        try:
            parsed = urlparse(value)
            domain = parsed.netloc.lower().replace('www.', '')
            
            # Verificar que el dominio esté en la lista permitida
            if not any(allowed in domain for allowed in allowed_domains):
                raise ValidationError(
                    f"El dominio '{domain}' no está permitido. "
                    f"Dominios permitidos: {', '.join(allowed_domains)}"
                )
        except Exception as e:
            raise ValidationError(f"URL inválida: {str(e)}")
        
        return value

    def validate(self, attrs):
        """Valida la configuración completa y actualiza el campo verified."""
        # Ignorar verified si viene en attrs (lo calculamos automáticamente)
        attrs.pop('verified', None)
        
        # Validar base_url según provider
        provider = attrs.get('provider', self.instance.provider if self.instance else None)
        
        if provider == OtaProvider.BOOKING:
            base_url = attrs.get('booking_base_url')
            if base_url is None and self.instance:
                base_url = self.instance.booking_base_url
            
            # Verificar dominio permitido
            if base_url:
                try:
                    parsed = urlparse(base_url)
                    domain = parsed.netloc.lower().replace('www.', '')
                    if any(allowed in domain for allowed in ['booking.com', 'httpbin.org']):
                        attrs['verified'] = True
                    else:
                        attrs['verified'] = False
                except Exception:
                    attrs['verified'] = False
            else:
                attrs['verified'] = False
                
        elif provider == OtaProvider.AIRBNB:
            base_url = attrs.get('airbnb_base_url')
            if base_url is None and self.instance:
                base_url = self.instance.airbnb_base_url
            
            # Verificar dominio permitido
            if base_url:
                try:
                    parsed = urlparse(base_url)
                    domain = parsed.netloc.lower().replace('www.', '')
                    if any(allowed in domain for allowed in ['airbnb.com', 'httpbin.org']):
                        attrs['verified'] = True
                    else:
                        attrs['verified'] = False
                except Exception:
                    attrs['verified'] = False
            else:
                attrs['verified'] = False
        else:
            # Para ICAL y otros providers, verified=False por defecto
            attrs['verified'] = False
        
        return attrs

    class Meta:
        model = OtaConfig
        fields = [
            "id", "hotel", "hotel_name", "provider", "is_active", "label",
            # Tokens/secrets enmascarados (read-only para visualización)
            "ical_out_token_masked",
            "booking_client_secret_masked",
            "airbnb_client_secret_masked",
            # Tokens/secrets: ical_out_token siempre enmascarado en lectura, writable para actualizar
            # booking_client_secret y airbnb_client_secret solo writable (no se retornan en lectura)
            "ical_out_token",
            "booking_client_secret",
            "airbnb_client_secret",
            # URLs completas de iCal (para uso del frontend)
            "ical_hotel_url",
            "ical_room_urls",
            # Otros campos
            "credentials",
            # Booking fields
            "booking_hotel_id", "booking_client_id",
            "booking_base_url", "booking_mode",
            # Airbnb fields
            "airbnb_account_id", "airbnb_client_id",
            "airbnb_base_url", "airbnb_mode",
            # Verificación (calculado automáticamente)
            "verified",
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
            "external_id", "ical_in_url", "sync_direction", "last_synced",
            "is_active", "created_at", "updated_at",
        ]
        read_only_fields = ["created_at", "updated_at", "last_synced"]


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