from django.db import models
from datetime import time
from django.core.exceptions import ValidationError


class Hotel(models.Model):
    name = models.CharField(max_length=120, unique=True)
    legal_name = models.CharField(max_length=200, blank=True)
    tax_id = models.CharField(max_length=50, blank=True)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=50, blank=True)
    address = models.CharField(max_length=200, blank=True)
    city = models.ForeignKey("locations.City", on_delete=models.PROTECT, related_name="hotels", null=True, blank=True)
    timezone = models.CharField(max_length=60, default="America/Argentina/Buenos_Aires")
    check_in_time = models.TimeField(default=time(15, 0))
    check_out_time = models.TimeField(default=time(11, 0))
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Hotel"
        verbose_name_plural = "Hoteles"

    def __str__(self) -> str:
        return self.name
    
    def clean(self):
        if self.check_in_time == self.check_out_time:
            raise ValidationError("check_in_time y check_out_time no pueden ser iguales.")