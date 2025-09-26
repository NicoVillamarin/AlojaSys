from django.db import models


class Enterprise(models.Model):
    name = models.CharField(max_length=150, unique=True)
    legal_name = models.CharField(max_length=200, blank=True)
    tax_id = models.CharField(max_length=50, blank=True)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=50, blank=True)
    address = models.CharField(max_length=200, blank=True)
    country = models.ForeignKey("locations.Country", on_delete=models.PROTECT, related_name="enterprises", null=True, blank=True)
    state = models.ForeignKey("locations.State", on_delete=models.PROTECT, related_name="enterprises", null=True, blank=True)
    city = models.ForeignKey("locations.City", on_delete=models.PROTECT, related_name="enterprises", null=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Empresa"
        verbose_name_plural = "Empresas"

    def __str__(self) -> str:
        return self.name


