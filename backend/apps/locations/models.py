from django.db import models
from django.core.exceptions import ValidationError
from zoneinfo import ZoneInfo

class Country(models.Model):
    code2 = models.CharField(max_length=2, unique=True)   # ISO-3166-1 alpha-2 (ej: AR)
    code3 = models.CharField(max_length=3, unique=True)   # ISO-3166-1 alpha-3 (ej: ARG)
    name = models.CharField(max_length=120, unique=True)
    phone_code = models.CharField(max_length=6, blank=True)
    currency_code = models.CharField(max_length=3, blank=True)
    timezone = models.CharField(max_length=60, blank=True, default="")
    default_check_in_time = models.TimeField(blank=True, null=True)
    default_check_out_time = models.TimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "País"
        verbose_name_plural = "Países"

    def __str__(self) -> str:
        return f"{self.name} ({self.code2})"

    def clean(self):
        # Validar que la zona horaria (si se provee) sea IANA válida
        if self.timezone:
            try:
                ZoneInfo(self.timezone)
            except Exception:
                raise ValidationError({"timezone": "Zona horaria inválida. Use un identificador IANA válido (ej: America/Argentina/Buenos_Aires)."})


class State(models.Model):
    country = models.ForeignKey(Country, on_delete=models.CASCADE, related_name="states")
    code = models.CharField(max_length=10, blank=True)  # ISO-3166-2 i aplica
    name = models.CharField(max_length=120)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Provincia/Estado"
        verbose_name_plural = "Provincias/Estados"
        constraints = [
            models.UniqueConstraint(fields=["country", "name"], name="uniq_state_country_name"),
        ]
        indexes = [
            models.Index(fields=["country"]),
        ]

    def __str__(self) -> str:
        return f"{self.name} - {self.country.code2}"


class City(models.Model):
    state = models.ForeignKey(State, on_delete=models.CASCADE, related_name="cities")
    name = models.CharField(max_length=120)
    postal_code = models.CharField(max_length=20, blank=True, null=True)
    lat = models.DecimalField(max_digits=9, decimal_places=6, blank=True, null=True)
    lng = models.DecimalField(max_digits=9, decimal_places=6, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Ciudad"
        verbose_name_plural = "Ciudades"
        constraints = [
            models.UniqueConstraint(fields=["state", "name"], name="uniq_city_state_name"),
        ]
        indexes = [
            models.Index(fields=["state"]),
        ]

    def __str__(self) -> str:
        return f"{self.name} - {self.state.name}"