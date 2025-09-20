from django.apps import AppConfig

class ReservationsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.reservations'
    verbose_name = 'Reservas'

    def ready(self):
        # Si necesitas signals:
        # from . import signals
        pass