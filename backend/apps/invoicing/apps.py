from django.apps import AppConfig


class InvoicingConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.invoicing'
    verbose_name = 'Facturación Electrónica'
    
    def ready(self):
        """Configuración inicial de la aplicación"""
        # Importar señales si las hay
        try:
            import apps.invoicing.signals
        except ImportError:
            pass
