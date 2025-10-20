from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
import uuid


class NotificationType(models.TextChoices):
    AUTO_CANCEL = "auto_cancel", "Auto Cancelación"
    MANUAL_CANCEL = "manual_cancel", "Cancelación Manual"
    NO_SHOW = "no_show", "No Show"
    REFUND_AUTO = "refund_auto", "Reembolso Automático"
    REFUND_FAILED = "refund_failed", "Reembolso Fallido"


class Notification(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    type = models.CharField(
        max_length=20, 
        choices=NotificationType.choices,
        help_text="Tipo de notificación"
    )
    title = models.CharField(
        max_length=200,
        help_text="Título de la notificación"
    )
    message = models.TextField(
        help_text="Mensaje detallado de la notificación"
    )
    user = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        null=True, 
        blank=True,
        help_text="Usuario destinatario (null = todos los usuarios)"
    )
    is_read = models.BooleanField(
        default=False,
        help_text="Indica si la notificación ha sido leída"
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text="Fecha y hora de creación"
    )
    
    # Campos adicionales para contexto
    hotel_id = models.PositiveIntegerField(
        null=True, 
        blank=True,
        help_text="ID del hotel relacionado"
    )
    reservation_id = models.PositiveIntegerField(
        null=True, 
        blank=True,
        help_text="ID de la reserva relacionada"
    )
    metadata = models.JSONField(
        default=dict,
        blank=True,
        help_text="Datos adicionales en formato JSON"
    )

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'is_read']),
            models.Index(fields=['type', 'created_at']),
            models.Index(fields=['hotel_id', 'created_at']),
        ]

    def __str__(self):
        return f"{self.get_type_display()}: {self.title}"

    def mark_as_read(self):
        """Marca la notificación como leída"""
        self.is_read = True
        self.save(update_fields=['is_read'])

    @classmethod
    def get_unread_count(cls, user=None):
        """Obtiene el conteo de notificaciones no leídas"""
        queryset = cls.objects.filter(is_read=False)
        if user:
            queryset = queryset.filter(user=user)
        return queryset.count()

    @classmethod
    def mark_all_as_read(cls, user=None):
        """Marca todas las notificaciones como leídas"""
        queryset = cls.objects.filter(is_read=False)
        if user:
            queryset = queryset.filter(user=user)
        return queryset.update(is_read=True)
