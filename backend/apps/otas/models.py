from django.db import models
from django.utils import timezone

from apps.core.models import Hotel
from apps.rooms.models import Room

class OtaProvider(models.TextChoices):
    ICAL = "ical", "iCal"
    BOOKING = "booking", "Booking"
    AIRBNB = "airbnb", "Airbnb"
    EXPEDIA = "expedia", "Expedia"
    GOOGLE = "google", "Google Calendar"
    OTHER = "other", "Otro"

class OtaConfig(models.Model):
    hotel = models.ForeignKey(Hotel, on_delete=models.CASCADE, related_name="ota_configs")
    provider = models.CharField(max_length=255, choices=OtaProvider.choices)
    is_active = models.BooleanField(default=True)
    label = models.CharField(max_length=120, blank=True, null=True)

    # Para export ICS autenticado (token compartido por hotel/proveedor)
    ical_out_token = models.CharField(max_length=64, blank=True, null=True)

    # Credenciales y parámetros del proveedor (polimórfico)
    credentials = models.JSONField(default=dict, blank=True)

    # ---- Booking: credenciales y parámetros comunes ----
    booking_hotel_id = models.CharField(max_length=64, blank=True, null=True)
    booking_client_id = models.CharField(max_length=120, blank=True, null=True)
    booking_client_secret = models.CharField(max_length=120, blank=True, null=True)
    booking_base_url = models.URLField(blank=True, null=True)
    class BookingMode(models.TextChoices):
        TEST = "test", "Test"
        PROD = "prod", "Prod"
    booking_mode = models.CharField(max_length=8, choices=BookingMode.choices, default=BookingMode.TEST)

    # ---- Airbnb: credenciales y parámetros comunes ----
    airbnb_account_id = models.CharField(max_length=64, blank=True, null=True)
    airbnb_client_id = models.CharField(max_length=120, blank=True, null=True)
    airbnb_client_secret = models.CharField(max_length=120, blank=True, null=True)
    airbnb_base_url = models.URLField(blank=True, null=True)
    class AirbnbMode(models.TextChoices):
        TEST = "test", "Test"
        PROD = "prod", "Prod"
    airbnb_mode = models.CharField(max_length=8, choices=AirbnbMode.choices, default=AirbnbMode.TEST)

    # Verificación de configuración (base_url válido)
    verified = models.BooleanField(
        default=False,
        help_text="Indica si la configuración base_url es válida y está verificada"
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = [('hotel', 'provider')]
        indexes = [
            models.Index(fields=['hotel', 'provider']),
        ]
    
    def __str__(self) -> str:
        return f"OTA Config - {self.hotel.name} - {self.provider}"

class OtaRoomMapping(models.Model):
    class SyncDirection(models.TextChoices):
        IMPORT = "import", "Import"
        EXPORT = "export", "Export"
        BOTH = "both", "Both"

    hotel = models.ForeignKey(Hotel, on_delete=models.CASCADE, related_name="ota_room_mappings")
    room = models.ForeignKey(Room, on_delete=models.CASCADE, related_name="ota_mappings")
    provider = models.CharField(max_length=20, choices=OtaProvider.choices)

    # Identificador externo de la habitacion (Cuando aplique)
    external_id = models.CharField(max_length=120, blank=True, null=True)

    # URL de ICS de entrada (pull) para esta habitacion
    ical_in_url = models.URLField(blank=True, null=True)

    # Dirección de sincronización
    sync_direction = models.CharField(max_length=10, choices=SyncDirection.choices, default=SyncDirection.BOTH)

    # Última sincronización exitosa
    last_synced = models.DateTimeField(null=True, blank=True)

    # Google Calendar Webhooks (opcional)
    google_watch_channel_id = models.CharField(max_length=120, blank=True, null=True)
    google_resource_id = models.CharField(max_length=120, blank=True, null=True)
    google_watch_expiration = models.DateTimeField(blank=True, null=True)
    google_webhook_token = models.CharField(max_length=64, blank=True, null=True)
    google_sync_token = models.CharField(max_length=255, blank=True, null=True)

    # Estado del mapeo
    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta: 
        unique_together = [('room', 'provider')]
        indexes = [
            models.Index(fields=['hotel', 'provider']),
            models.Index(fields=['room', 'provider']),
        ]
    
    def __str__(self) -> str:
        return f"OTA Room Mapping - {self.room.name} - {self.provider}"

class OtaSyncJob(models.Model):
    class JobType(models.TextChoices):
        IMPORT_ICS = "import_ics", "Import ICS"
        EXPORT_ICS = "export_ics", "Export ICS"
        PUSH_ARI = "push_ari", "Push ARI"
        PULL_RESERVATIONS = "pull_reservations", "Pull Reservations"

    class JobStatus(models.TextChoices):
        PENDING = "pending", "Pending"
        RUNNING = "running", "Running"
        SUCCESS = "success", "Success"
        FAILED = "failed", "Failed"

    hotel = models.ForeignKey(Hotel, on_delete=models.CASCADE, related_name="ota_sync_jobs", null=True, blank=True)
    provider = models.CharField(max_length=20, choices=OtaProvider.choices)
    job_type = models.CharField(max_length=30, choices=JobType.choices)
    status = models.CharField(max_length=20, choices=JobStatus.choices, default=JobStatus.PENDING)

    started_at = models.DateTimeField(default=timezone.now)
    finished_at = models.DateTimeField(blank=True, null=True)

    stats = models.JSONField(default=dict, blank=True)
    error_message = models.TextField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=["provider", "job_type", "status"]),
            models.Index(fields=["started_at"]),
        ]

    def __str__(self) -> str:
        return f"{self.provider} {self.job_type} [{self.status}]"

class OtaSyncLog(models.Model):
    class Level(models.TextChoices):
        INFO = "info", "Info"
        WARNING = "warning", "Warning"
        ERROR = "error", "Error"

    job = models.ForeignKey(OtaSyncJob, on_delete=models.CASCADE, related_name="logs")
    level = models.CharField(max_length=20, choices=Level.choices, default=Level.INFO)
    message = models.TextField()
    payload = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=["level", "created_at"]),
        ]

    def __str__(self) -> str:
        return f"Log {self.level} - {self.created_at:%Y-%m-%d %H:%M:%S}"


class OtaImportedEvent(models.Model):
    """Eventos importados desde feeds ICS para idempotencia y auditoría."""
    hotel = models.ForeignKey(Hotel, on_delete=models.CASCADE, related_name="ota_imported_events")
    room = models.ForeignKey(Room, on_delete=models.CASCADE, related_name="ota_imported_events")
    provider = models.CharField(max_length=20, choices=OtaProvider.choices, default=OtaProvider.ICAL)

    uid = models.CharField(max_length=255)
    dtstart = models.DateField()
    dtend = models.DateField()
    source_url = models.URLField(blank=True, null=True)
    last_seen = models.DateTimeField(auto_now=True)
    summary = models.CharField(max_length=255, blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = [("room", "provider", "uid")]
        indexes = [
            models.Index(fields=["hotel", "room"]),
            models.Index(fields=["provider"]),
        ]

    def __str__(self) -> str:
        return f"{self.provider}:{self.uid} {self.dtstart}->{self.dtend}"


class OtaRoomTypeMapping(models.Model):
    """Mapea tipos de habitación del PMS con códigos de la OTA."""
    hotel = models.ForeignKey(Hotel, on_delete=models.CASCADE, related_name="ota_room_type_mappings")
    provider = models.CharField(max_length=20, choices=OtaProvider.choices)
    room_type_code = models.CharField(max_length=60, help_text="Código interno del PMS (ej: DOUBLE)")
    provider_code = models.CharField(max_length=120, help_text="Código en la OTA")
    name = models.CharField(max_length=120, blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = [("hotel", "provider", "room_type_code")]
        indexes = [
            models.Index(fields=["hotel", "provider"]),
        ]

    def __str__(self) -> str:
        return f"{self.hotel_id}:{self.provider}:{self.room_type_code}->{self.provider_code}"


class OtaRatePlanMapping(models.Model):
    """Mapea planes de tarifa del PMS con IDs/códigos de la OTA."""
    hotel = models.ForeignKey(Hotel, on_delete=models.CASCADE, related_name="ota_rate_plan_mappings")
    provider = models.CharField(max_length=20, choices=OtaProvider.choices)
    rate_plan_code = models.CharField(max_length=60, help_text="Código interno PMS (ej: STANDARD)")
    provider_code = models.CharField(max_length=120, help_text="Código en la OTA")
    currency = models.CharField(max_length=3, default="ARS")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = [("hotel", "provider", "rate_plan_code")]
        indexes = [
            models.Index(fields=["hotel", "provider"]),
        ]

    def __str__(self) -> str:
        return f"{self.hotel_id}:{self.provider}:{self.rate_plan_code}->{self.provider_code}"