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
    avatar_image = models.ImageField(
        upload_to='users/avatars/%Y/%m/%d/',
        blank=True,
        null=True,
        help_text="Foto de perfil del usuario"
    )
    is_active = models.BooleanField(default=True)
    is_housekeeping_staff = models.BooleanField(default=False, help_text="Si está activo, el usuario es staff de limpieza con acceso limitado al módulo de housekeeping.")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Perfil de Usuario"
        verbose_name_plural = "Perfiles de Usuario"

    def __str__(self):
        return f"{self.user.get_full_name() or self.user.username} - {self.position or 'Sin cargo'}"
