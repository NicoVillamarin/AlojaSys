from django.db import models
from django.conf import settings
from django.utils import timezone


class TaskType(models.TextChoices):
    CHECKOUT = "checkout", "Salida"
    DAILY = "daily", "Diaria"
    MAINTENANCE = "maintenance", "Mantenimiento"


class TaskStatus(models.TextChoices):
    PENDING = "pending", "Pendiente"
    IN_PROGRESS = "in_progress", "En proceso"
    COMPLETED = "completed", "Completada"
    CANCELLED = "cancelled", "Cancelada"


class CleaningStaff(models.Model):
    hotel = models.ForeignKey("core.Hotel", on_delete=models.CASCADE, related_name="cleaning_staff")
    first_name = models.CharField(max_length=120)
    last_name = models.CharField(max_length=120, blank=True, null=True)
    zone = models.CharField(max_length=120, blank=True, null=True)
    is_active = models.BooleanField(default=True)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        help_text="Usuario del sistema asociado (opcional)",
        related_name="cleaning_profile",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Personal de limpieza"
        verbose_name_plural = "Personal de limpieza"
        indexes = [
            models.Index(fields=["hotel"]),
            models.Index(fields=["is_active"]),
        ]
        permissions = [
            ("access_housekeeping", "Puede acceder al módulo de housekeeping"),
            ("manage_all_tasks", "Puede gestionar todas las tareas de housekeeping"),
        ]

    def __str__(self) -> str:
        return f"{self.first_name} {self.last_name or ''}".strip()


class HousekeepingTask(models.Model):
    hotel = models.ForeignKey("core.Hotel", on_delete=models.CASCADE, related_name="housekeeping_tasks")
    room = models.ForeignKey("rooms.Room", on_delete=models.CASCADE, related_name="housekeeping_tasks")
    task_type = models.CharField(max_length=20, choices=TaskType.choices, default=TaskType.DAILY)
    status = models.CharField(max_length=20, choices=TaskStatus.choices, default=TaskStatus.PENDING)
    assigned_to = models.ForeignKey(
        CleaningStaff, on_delete=models.SET_NULL, blank=True, null=True, related_name="tasks"
    )
    notes = models.TextField(blank=True, null=True)
    priority = models.IntegerField(default=0)
    zone = models.CharField(max_length=120, blank=True, null=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, blank=True, null=True, related_name="created_hk_tasks"
    )
    started_at = models.DateTimeField(blank=True, null=True)
    completed_at = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-priority", "created_at"]
        verbose_name = "Tarea de limpieza"
        verbose_name_plural = "Tareas de limpieza"
        indexes = [
            models.Index(fields=["hotel"]),
            models.Index(fields=["room"]),
            models.Index(fields=["status"]),
            models.Index(fields=["task_type"]),
        ]
        permissions = [
            ("access_housekeeping", "Puede acceder al módulo de housekeeping"),
            ("manage_all_tasks", "Puede gestionar todas las tareas de housekeeping"),
        ]

    def __str__(self) -> str:
        return f"{self.get_task_type_display()} - {self.room.name} ({self.get_status_display()})"


class HousekeepingConfig(models.Model):
    """
    Configuración de housekeeping por hotel.
    Usamos un modelo dedicado (en lugar de JSON en Hotel) siguiendo patrones existentes (OTAs/Payments).
    """
    hotel = models.OneToOneField("core.Hotel", on_delete=models.CASCADE, related_name="housekeeping_config")
    # Generación y asignación
    enable_auto_assign = models.BooleanField(default=True)
    create_daily_tasks = models.BooleanField(default=True)
    daily_generation_time = models.TimeField(default=timezone.datetime(2000, 1, 1, 7, 0).time())
    # Reglas de servicio
    skip_service_on_checkin = models.BooleanField(default=True)
    skip_service_on_checkout = models.BooleanField(default=True)
    linens_every_n_nights = models.PositiveIntegerField(default=3)
    towels_every_n_nights = models.PositiveIntegerField(default=1)
    # Ventanas
    morning_window_start = models.TimeField(null=True, blank=True, default=timezone.datetime(2000, 1, 1, 9, 0).time())
    morning_window_end = models.TimeField(null=True, blank=True, default=timezone.datetime(2000, 1, 1, 13, 0).time())
    afternoon_window_start = models.TimeField(null=True, blank=True, default=timezone.datetime(2000, 1, 1, 13, 0).time())
    afternoon_window_end = models.TimeField(null=True, blank=True, default=timezone.datetime(2000, 1, 1, 18, 0).time())
    quiet_hours_start = models.TimeField(null=True, blank=True)
    quiet_hours_end = models.TimeField(null=True, blank=True)
    # Asignación
    prefer_by_zone = models.BooleanField(default=True)
    rebalance_every_minutes = models.PositiveIntegerField(default=5)
    # Prioridades
    checkout_priority = models.PositiveIntegerField(default=2)
    daily_priority = models.PositiveIntegerField(default=1)
    # Duraciones estimadas (minutos) por tipo y tipo de habitación
    durations = models.JSONField(default=dict, blank=True)
    # Alertas
    alert_checkout_unstarted_minutes = models.PositiveIntegerField(default=30)
    # Metadatos
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Configuración de Housekeeping"
        verbose_name_plural = "Configuraciones de Housekeeping"
        indexes = [
            models.Index(fields=["hotel"]),
        ]

    def __str__(self) -> str:
        return f"HousekeepingConfig({self.hotel.name})"

