from django.apps import AppConfig

class OtasConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.otas'
    verbose_name = 'OTAs'

    def ready(self):
        # Registra señales para automatización ARI
        from apps.otas import signals  # noqa: F401