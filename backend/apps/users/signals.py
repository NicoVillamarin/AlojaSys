from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from .models import UserProfile


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """
    Signal para crear automáticamente un UserProfile cuando se crea un User.
    Útil para usuarios creados desde el admin de Django o desde createsuperuser.
    """
    if created:
        # Verificar si ya tiene perfil (por si acaso)
        if not hasattr(instance, 'profile'):
            UserProfile.objects.create(
                user=instance,
                position='Administrador' if instance.is_superuser else '',
                is_active=instance.is_active
            )


@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    """
    Asegurar que el perfil exista y se guarde cuando el usuario se actualiza.
    """
    if hasattr(instance, 'profile'):
        instance.profile.save()


