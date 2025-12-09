from django.db import models


class Enterprise(models.Model):
    class PlanType(models.TextChoices):
        BASIC = "basic", "Básico"
        MEDIUM = "medium", "Medio"
        FULL = "full", "Full"
        CUSTOM = "custom", "Custom"

    name = models.CharField(max_length=150, unique=True)
    legal_name = models.CharField(max_length=200, blank=True)
    tax_id = models.CharField(max_length=50, blank=True)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=50, blank=True)
    address = models.CharField(max_length=200, blank=True)
    country = models.ForeignKey(
        "locations.Country",
        on_delete=models.PROTECT,
        related_name="enterprises",
        null=True,
        blank=True,
    )
    state = models.ForeignKey(
        "locations.State",
        on_delete=models.PROTECT,
        related_name="enterprises",
        null=True,
        blank=True,
    )
    city = models.ForeignKey(
        "locations.City",
        on_delete=models.PROTECT,
        related_name="enterprises",
        null=True,
        blank=True,
    )
    plan_type = models.CharField(
        max_length=20,
        choices=PlanType.choices,
        default=PlanType.BASIC,
        help_text="Plan comercial contratado que determina el conjunto base de funcionalidades.",
    )
    enabled_features = models.JSONField(
        default=dict,
        blank=True,
        help_text=(
            "Overrides de funcionalidades por empresa. "
            "Se combinan con los defaults del plan para habilitar/deshabilitar módulos."
        ),
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Empresa"
        verbose_name_plural = "Empresas"

    def __str__(self) -> str:
        return self.name

