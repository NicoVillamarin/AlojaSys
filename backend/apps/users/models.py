from django.db import models
from django.contrib.auth.models import User


class UserProfile(models.Model):
    """
    Perfil de usuario extendido que permite asignar múltiples hoteles
    a un usuario para que pueda operar en ellos.
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile")
    enterprise = models.ForeignKey("enterprises.Enterprise", on_delete=models.CASCADE, related_name="user_profiles", null=True, blank=True, help_text="Empresa principal del usuario")
    hotels = models.ManyToManyField("core.Hotel", related_name="user_profiles", blank=True)
    phone = models.CharField(max_length=50, blank=True)
    position = models.CharField(max_length=100, blank=True, verbose_name="Cargo")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Perfil de Usuario"
        verbose_name_plural = "Perfiles de Usuario"

    def __str__(self):
        return f"{self.user.get_full_name() or self.user.username} - {self.position or 'Sin cargo'}"
