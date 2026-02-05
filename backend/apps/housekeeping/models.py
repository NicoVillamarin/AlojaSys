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


class Shift(models.TextChoices):
    MORNING = "morning", "Mañana"
    AFTERNOON = "afternoon", "Tarde"
    NIGHT = "night", "Noche"


class CleaningZone(models.Model):
    """
    Zona de limpieza estructurada (piso, sector, ala, etc.)
    """
    hotel = models.ForeignKey("core.Hotel", on_delete=models.CASCADE, related_name="cleaning_zones")
    name = models.CharField(max_length=120, help_text="Nombre de la zona (ej: Piso 1, Ala A)")
    description = models.TextField(blank=True, null=True)
    floor = models.IntegerField(blank=True, null=True, help_text="Piso (opcional)")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Zona de Limpieza"
        verbose_name_plural = "Zonas de Limpieza"
        unique_together = [["hotel", "name"]]
        indexes = [
            models.Index(fields=["hotel"]),
            models.Index(fields=["is_active"]),
        ]

    def __str__(self) -> str:
        return f"{self.name} ({self.hotel.name})"


class CleaningStaff(models.Model):
    hotel = models.ForeignKey("core.Hotel", on_delete=models.CASCADE, related_name="cleaning_staff")
    first_name = models.CharField(max_length=120)
    last_name = models.CharField(max_length=120, blank=True, null=True)
    zone = models.CharField(max_length=120, blank=True, null=True, help_text="Zona libre (legacy, usar cleaning_zones)")
    shift = models.CharField(
        max_length=20,
        choices=Shift.choices,
        blank=True,
        null=True,
        help_text="Turno de trabajo (mañana, tarde, noche)"
    )
    work_start_time = models.TimeField(
        blank=True,
        null=True,
        help_text="Hora de inicio del turno de trabajo (ej: 09:00)"
    )
    work_end_time = models.TimeField(
        blank=True,
        null=True,
        help_text="Hora de fin del turno de trabajo (ej: 17:00)"
    )
    cleaning_zones = models.ManyToManyField(
        CleaningZone,
        related_name="staff",
        blank=True,
        help_text="Zonas asignadas a este empleado"
    )
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
    checklist = models.ForeignKey(
        "Checklist", on_delete=models.SET_NULL, blank=True, null=True, related_name="tasks", help_text="Checklist asociado a esta tarea"
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, blank=True, null=True, related_name="created_hk_tasks"
    )
    started_at = models.DateTimeField(blank=True, null=True)
    completed_at = models.DateTimeField(blank=True, null=True)
    estimated_minutes = models.PositiveIntegerField(
        blank=True, 
        null=True, 
        help_text="Duración estimada en minutos (se calcula desde templates o configuración)"
    )
    is_overdue = models.BooleanField(
        default=False,
        help_text="Indica si la tarea está vencida (excedió su tiempo estimado)"
    )
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
    daily_for_all_rooms = models.BooleanField(
        default=False,
        help_text="Si está activo, genera tareas diarias para todas las habitaciones activas del hotel (no solo ocupadas).",
    )
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
    # Modo de uso
    use_checklists = models.BooleanField(
        default=True,
        help_text="Si está activo, las tareas usarán checklists detallados. Si está desactivado, solo se usará descripción general."
    )
    # Prioridades
    checkout_priority = models.PositiveIntegerField(default=2)
    daily_priority = models.PositiveIntegerField(default=1)
    # Duraciones estimadas (minutos) por tipo y tipo de habitación
    durations = models.JSONField(default=dict, blank=True)
    # Alertas
    alert_checkout_unstarted_minutes = models.PositiveIntegerField(default=30)
    # Vencimiento de tareas
    max_task_duration_minutes = models.PositiveIntegerField(
        default=120,
        help_text="Tiempo máximo en minutos para una tarea en progreso antes de marcarla como vencida"
    )
    auto_complete_overdue = models.BooleanField(
        default=False,
        help_text="Si está activo, completa automáticamente las tareas vencidas después del tiempo máximo"
    )
    overdue_grace_minutes = models.PositiveIntegerField(
        default=30,
        help_text="Minutos adicionales después del tiempo máximo antes de auto-completar (solo si auto_complete_overdue está activo)"
    )
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


class TaskTemplate(models.Model):
    """
    Plantilla de tareas estándar por tipo de habitación.
    Define qué tareas se esperan para cada tipo de habitación.
    """
    hotel = models.ForeignKey("core.Hotel", on_delete=models.CASCADE, related_name="task_templates")
    room_type = models.CharField(
        max_length=20,
        help_text="Tipo de habitación (single, double, triple, suite)"
    )
    task_type = models.CharField(max_length=20, choices=TaskType.choices, default=TaskType.DAILY)
    name = models.CharField(max_length=255, help_text="Nombre de la tarea (ej: Cambio de sábanas, Reposición minibar)")
    description = models.TextField(blank=True, null=True)
    estimated_minutes = models.PositiveIntegerField(default=15, help_text="Duración estimada en minutos")
    is_required = models.BooleanField(default=True, help_text="Si es requerida o opcional")
    order = models.PositiveIntegerField(default=0, help_text="Orden de ejecución")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Plantilla de Tarea"
        verbose_name_plural = "Plantillas de Tareas"
        ordering = ["room_type", "task_type", "order"]
        indexes = [
            models.Index(fields=["hotel"]),
            models.Index(fields=["room_type"]),
            models.Index(fields=["task_type"]),
            models.Index(fields=["is_active"]),
        ]

    def __str__(self) -> str:
        room_type_label = self.room_type
        try:
            from apps.rooms.models import RoomType as RoomTypeModel
            rt = RoomTypeModel.objects.only("name").filter(code=self.room_type).first() if self.room_type else None
            if rt:
                room_type_label = rt.name
        except Exception:
            pass
        return f"{self.name} ({room_type_label} - {self.get_task_type_display()})"


class Checklist(models.Model):
    """
    Checklist personalizable por hotel.
    Puede estar asociado a un tipo de habitación, tipo de tarea, o ser general.
    """
    hotel = models.ForeignKey("core.Hotel", on_delete=models.CASCADE, related_name="checklists")
    name = models.CharField(max_length=255, help_text="Nombre del checklist")
    description = models.TextField(blank=True, null=True)
    room_type = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        help_text="Tipo de habitación específico (opcional)"
    )
    task_type = models.CharField(
        max_length=20,
        choices=TaskType.choices,
        blank=True,
        null=True,
        help_text="Tipo de tarea específico (opcional)"
    )
    is_default = models.BooleanField(default=False, help_text="Checklist por defecto para el hotel")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Checklist"
        verbose_name_plural = "Checklists"
        ordering = ["name"]
        indexes = [
            models.Index(fields=["hotel"]),
            models.Index(fields=["room_type"]),
            models.Index(fields=["task_type"]),
            models.Index(fields=["is_active"]),
        ]

    def __str__(self) -> str:
        return f"{self.name} ({self.hotel.name})"


class ChecklistItem(models.Model):
    """
    Item individual de un checklist.
    """
    checklist = models.ForeignKey(Checklist, on_delete=models.CASCADE, related_name="items")
    name = models.CharField(max_length=255, help_text="Nombre del item")
    description = models.TextField(blank=True, null=True)
    order = models.PositiveIntegerField(default=0, help_text="Orden de aparición")
    is_required = models.BooleanField(default=True, help_text="Si es requerido o opcional")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Item de Checklist"
        verbose_name_plural = "Items de Checklist"
        ordering = ["order"]
        indexes = [
            models.Index(fields=["checklist"]),
            models.Index(fields=["is_active"]),
        ]

    def __str__(self) -> str:
        return f"{self.name} ({self.checklist.name})"


class TaskChecklistCompletion(models.Model):
    """
    Registro de completado de items de checklist para una tarea específica.
    """
    task = models.ForeignKey(HousekeepingTask, on_delete=models.CASCADE, related_name="checklist_completions")
    checklist_item = models.ForeignKey(ChecklistItem, on_delete=models.CASCADE, related_name="completions")
    completed = models.BooleanField(default=False)
    completed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="completed_checklist_items"
    )
    completed_at = models.DateTimeField(blank=True, null=True)
    notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Completado de Item de Checklist"
        verbose_name_plural = "Completados de Items de Checklist"
        unique_together = [["task", "checklist_item"]]
        indexes = [
            models.Index(fields=["task"]),
            models.Index(fields=["checklist_item"]),
            models.Index(fields=["completed"]),
        ]

    def __str__(self) -> str:
        return f"{self.checklist_item.name} - {self.task.room.name} ({'✓' if self.completed else '✗'})"

