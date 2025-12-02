from django.db import models
from django.db.models import Q
from django.utils import timezone


class ChatbotProviderAccount(models.Model):
    class Provider(models.TextChoices):
        META_CLOUD = "meta_cloud", "Meta WhatsApp Cloud API"
        TWILIO = "twilio", "Twilio"
        OTHER = "other", "Otro"

    name = models.CharField(max_length=120, help_text="Nombre interno de la cuenta/proveedor")
    provider = models.CharField(max_length=30, choices=Provider.choices)
    phone_number = models.CharField(max_length=30, help_text="Número de WhatsApp asignado (E.164)")
    business_id = models.CharField(
        max_length=64,
        blank=True,
        help_text="Business ID (Meta) u otro identificador requerido"
    )
    phone_number_id = models.CharField(
        max_length=64,
        blank=True,
        help_text="Phone Number ID (Meta) u otro identificador interno"
    )
    api_token = models.CharField(max_length=512, help_text="Token/API key para enviar mensajes")
    metadata = models.JSONField(default=dict, blank=True)
    is_active = models.BooleanField(default=True)
    is_managed = models.BooleanField(
        default=True,
        help_text="Indica si la cuenta es administrada por AlojaSys"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]
        indexes = [
            models.Index(fields=["provider", "is_active"]),
            models.Index(fields=["phone_number"]),
        ]
        verbose_name = "Cuenta de Proveedor WhatsApp"
        verbose_name_plural = "Cuentas de Proveedores WhatsApp"

    def __str__(self) -> str:
        status = "Activa" if self.is_active else "Inactiva"
        return f"{self.name} ({self.get_provider_display()} - {status})"


class ChatSession(models.Model):
    class State(models.TextChoices):
        ASKING_CHECKIN = "asking_checkin", "Solicitando check-in"
        ASKING_CHECKOUT = "asking_checkout", "Solicitando check-out"
        ASKING_GUESTS = "asking_guests", "Solicitando cantidad de huéspedes"
        ASKING_GUEST_NAME = "asking_guest_name", "Solicitando nombre del huésped"
        ASKING_GUEST_EMAIL = "asking_guest_email", "Solicitando email del huésped"
        CONFIRMATION = "confirmation", "Esperando confirmación"
        COMPLETED = "completed", "Completada"
        ABANDONED = "abandoned", "Abandonada"

    hotel = models.ForeignKey(
        "core.Hotel",
        on_delete=models.CASCADE,
        related_name="chatbot_sessions"
    )
    guest_phone = models.CharField(max_length=32, help_text="Teléfono del huésped en formato E.164")
    guest_name = models.CharField(max_length=120, blank=True)
    guest_email = models.EmailField(blank=True)
    state = models.CharField(
        max_length=40,
        choices=State.choices,
        default=State.ASKING_CHECKIN
    )
    context = models.JSONField(default=dict, blank=True)
    language = models.CharField(max_length=10, default="es")
    last_message_at = models.DateTimeField(default=timezone.now)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-updated_at"]
        indexes = [
            models.Index(fields=["hotel", "guest_phone"]),
            models.Index(fields=["is_active", "updated_at"]),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=["hotel", "guest_phone"],
                condition=Q(is_active=True),
                name="unique_active_chatbot_session_per_guest"
            )
        ]
        verbose_name = "Sesión de Chatbot"
        verbose_name_plural = "Sesiones de Chatbot"

    def __str__(self) -> str:
        return f"{self.hotel.name} - {self.guest_phone} ({self.state})"

    def mark_abandoned(self):
        self.is_active = False
        self.state = self.State.ABANDONED
        self.save(update_fields=["is_active", "state", "updated_at"])

