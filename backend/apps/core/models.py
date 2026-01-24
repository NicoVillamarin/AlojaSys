from django.db import models
from datetime import time
from django.core.exceptions import ValidationError
from django.core.files.storage import default_storage


class Hotel(models.Model):
    enterprise = models.ForeignKey("enterprises.Enterprise", on_delete=models.PROTECT, related_name="hotels", null=True, blank=True)
    name = models.CharField(max_length=120, unique=True)
    legal_name = models.CharField(max_length=200, blank=True)
    tax_id = models.CharField(max_length=50, blank=True)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=50, blank=True)
    address = models.CharField(max_length=200, blank=True)
    country = models.ForeignKey("locations.Country", on_delete=models.PROTECT, related_name="hotels", null=True, blank=True)
    state = models.ForeignKey("locations.State", on_delete=models.PROTECT, related_name="hotels", null=True, blank=True)
    city = models.ForeignKey("locations.City", on_delete=models.PROTECT, related_name="hotels", null=True, blank=True)
    class WhatsappProvider(models.TextChoices):
        META_CLOUD = "meta_cloud", "Meta WhatsApp Cloud API"
        TWILIO = "twilio", "Twilio"
        OTHER = "other", "Otro"

    whatsapp_enabled = models.BooleanField(
        default=False,
        help_text="Habilita la captura automática de reservas vía WhatsApp"
    )
    whatsapp_phone = models.CharField(
        max_length=30,
        blank=True,
        help_text="Número oficial de WhatsApp del hotel (formato E.164)"
    )
    whatsapp_provider = models.CharField(
        max_length=30,
        choices=WhatsappProvider.choices,
        blank=True,
        help_text="Proveedor directo si el hotel trae su propia cuenta"
    )
    whatsapp_business_id = models.CharField(
        max_length=64,
        blank=True,
        help_text="Business ID (Meta) u otro identificador requerido por el proveedor"
    )
    whatsapp_phone_number_id = models.CharField(
        max_length=64,
        blank=True,
        help_text="Phone Number ID (Meta) u otro ID interno del número"
    )
    whatsapp_api_token = models.CharField(
        max_length=512,
        blank=True,
        help_text="Token/API Key del proveedor (almacenamiento básico, considerar cifrado)"
    )
    whatsapp_provider_account = models.ForeignKey(
        "chatbot.ChatbotProviderAccount",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="hotels",
        help_text="Cuenta administrada por AlojaSys para usar un número compartido"
    )
    timezone = models.CharField(max_length=60, default="America/Argentina/Buenos_Aires")
    check_in_time = models.TimeField(default=time(15, 0))
    check_out_time = models.TimeField(default=time(11, 0))
    auto_check_in_enabled = models.BooleanField(default=False)
    auto_check_out_enabled = models.BooleanField(default=True, help_text="Habilita el check-out automático de reservas")
    auto_no_show_enabled = models.BooleanField(default=False, help_text="Habilita el marcado automático de reservas como no-show")
    logo = models.ImageField(
        upload_to='hotels/logos/%Y/%m/%d/',
        blank=True,
        null=True,
        help_text="Logo del hotel"
    )
    guest_card_policies = models.TextField(
        blank=True,
        null=True,
        help_text="Políticas y horarios que aparecen en la ficha del pasajero (texto libre, se imprime al final de la ficha)"
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Hotel"
        verbose_name_plural = "Hoteles"
        permissions = [
            # Django crea automáticamente: add_hotel, change_hotel, delete_hotel, view_hotel
            # Puedes agregar permisos personalizados aquí si necesitas:
            # ("manage_hotel", "Puede gestionar configuración del hotel"),
        ]

    def __str__(self) -> str:
        return self.name
    
    @property
    def logo_url(self):
        """Obtiene la URL completa del logo del hotel"""
        if self.logo:
            return self.logo.url
        return None
    
    def clean(self):
        if self.check_in_time == self.check_out_time:
            raise ValidationError("check_in_time y check_out_time no pueden ser iguales.")
        if self.whatsapp_enabled and not self.whatsapp_phone:
            raise ValidationError({
                "whatsapp_phone": "Debes configurar el número de WhatsApp si habilitás este canal."
            })
        if self.whatsapp_enabled:
            has_shared_account = bool(self.whatsapp_provider_account_id)
            has_custom_credentials = all([
                self.whatsapp_provider,
                self.whatsapp_api_token,
                self.whatsapp_phone_number_id,
            ])
            if not (has_shared_account or has_custom_credentials):
                raise ValidationError(
                    "Configura una cuenta compartida o provee proveedor/token/phone_number_id para WhatsApp."
                )

    def save(self, *args, **kwargs):
        # Si el hotel tiene país definido y no tiene timezone/horarios seteados explícitamente,
        # tomar valores por defecto del país.
        if self.country_id:
            try:
                from apps.locations.models import Country
                country = Country.objects.filter(id=self.country_id).only(
                    "timezone", "default_check_in_time", "default_check_out_time"
                ).first()
                if country:
                    if (not self.timezone) and country.timezone:
                        self.timezone = country.timezone
                    if (not self.check_in_time) and country.default_check_in_time:
                        self.check_in_time = country.default_check_in_time
                    if (not self.check_out_time) and country.default_check_out_time:
                        self.check_out_time = country.default_check_out_time
            except Exception:
                # En caso de migraciones iniciales u otros contextos, no bloquear el guardado
                pass
        super().save(*args, **kwargs)