from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.invoicing.models import AfipConfig
from apps.invoicing.services.afip_auth_service import AfipAuthService, AfipAuthError


class Command(BaseCommand):
    help = "Obtiene y persiste un TA (token/sign) de AFIP usando Zeep"

    def add_arguments(self, parser):
        parser.add_argument('--hotel-id', type=int, default=None, help='ID de hotel (opcional)')

    def handle(self, *args, **options):
        hotel_id = options.get('hotel_id')
        cfg_qs = AfipConfig.objects.all()
        if hotel_id:
            cfg_qs = cfg_qs.filter(hotel_id=hotel_id)
        cfg = cfg_qs.first()
        if not cfg:
            self.stderr.write(self.style.ERROR('No hay AfipConfig configurado'))
            return

        self.stdout.write(f"Usando AfipConfig #{cfg.id} (hotel={cfg.hotel_id}, env={cfg.environment})")

        # Usar el cliente por requests para capturar el primer 200 y persistir inmediatamente
        service = AfipAuthService(cfg)
        try:
            token, sign = service.get_token_and_sign()
            self.stdout.write(self.style.SUCCESS(f"OK TA obtenido. Token len={len(token)} Sign len={len(sign)}"))
            return
        except AfipAuthError as e:
            self.stderr.write(self.style.ERROR(f"AFIP WSAA error: {e}"))
            return
        except Exception as e:
            self.stderr.write(self.style.ERROR(f"Error inesperado: {e}"))
            return


