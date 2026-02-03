from decimal import Decimal

from django.conf import settings
from django.db import models
from django.utils import timezone

from apps.core.models import Hotel


class CashSessionStatus(models.TextChoices):
    OPEN = "open", "Abierta"
    CLOSED = "closed", "Cerrada"
    CANCELLED = "cancelled", "Anulada"


class CashMovementType(models.TextChoices):
    IN = "in", "Ingreso"
    OUT = "out", "Egreso"


class CashSession(models.Model):
    """
    Sesión de caja (apertura/cierre).

    Nota: El "esperado" se calcula dinámicamente en base a:
    - opening_amount
    - pagos en efectivo (Payment.method='cash') dentro del rango opened_at..closed_at
    - movimientos manuales (CashMovement)
    """

    hotel = models.ForeignKey(Hotel, on_delete=models.CASCADE, related_name="cash_sessions")

    status = models.CharField(
        max_length=12, choices=CashSessionStatus.choices, default=CashSessionStatus.OPEN
    )

    currency = models.CharField(max_length=3, default="ARS")

    opened_at = models.DateTimeField(default=timezone.now)
    opened_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="cash_sessions_opened",
    )
    opening_amount = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))

    closed_at = models.DateTimeField(null=True, blank=True)
    closed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="cash_sessions_closed",
    )
    closing_amount = models.DecimalField(
        max_digits=12, decimal_places=2, null=True, blank=True, help_text="Efectivo contado al cierre"
    )

    expected_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Efectivo esperado calculado al momento de cerrar (snapshot)",
    )
    difference_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Diferencia: closing_amount - expected_amount",
    )

    notes = models.TextField(blank=True, default="")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Sesión de caja"
        verbose_name_plural = "Sesiones de caja"
        ordering = ["-opened_at"]
        indexes = [
            models.Index(fields=["hotel", "status"]),
            models.Index(fields=["hotel", "opened_at"]),
            models.Index(fields=["hotel", "currency", "opened_at"]),
        ]
        permissions = [
            ("open_cashsession", "Puede abrir caja"),
            ("close_cashsession", "Puede cerrar caja"),
            ("view_cashbox_reports", "Puede ver reportes de caja"),
        ]

    def __str__(self) -> str:
        return f"Caja {self.hotel_id} {self.opened_at:%Y-%m-%d %H:%M} ({self.get_status_display()})"


class CashMovement(models.Model):
    session = models.ForeignKey(CashSession, on_delete=models.CASCADE, related_name="movements")
    hotel = models.ForeignKey(Hotel, on_delete=models.CASCADE, related_name="cash_movements")

    movement_type = models.CharField(max_length=8, choices=CashMovementType.choices)
    currency = models.CharField(max_length=3, default="ARS")
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    description = models.CharField(max_length=255, blank=True, default="")

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="cash_movements_created",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Movimiento de caja"
        verbose_name_plural = "Movimientos de caja"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["hotel", "created_at"]),
            models.Index(fields=["session", "created_at"]),
            models.Index(fields=["hotel", "currency", "created_at"]),
        ]

    def __str__(self) -> str:
        return f"{self.get_movement_type_display()} {self.amount} {self.currency}"

