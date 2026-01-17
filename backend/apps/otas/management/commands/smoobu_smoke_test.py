from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone
from datetime import timedelta

import requests

from apps.core.models import Hotel
from apps.rooms.models import Room
from apps.otas.models import OtaConfig, OtaProvider, OtaRoomMapping, OtaSyncJob
from apps.otas.services.ari_publisher import pull_reservations_for_hotel


class Command(BaseCommand):
    help = "Smoke test Smoobu: configura api key + mapeo y ejecuta pull de reservas"

    def add_arguments(self, parser):
        parser.add_argument("--hotel-id", type=int, required=True)
        parser.add_argument("--room-id", type=int, required=True)
        parser.add_argument("--apartment-id", type=str, required=True, help="ID del apartment en Smoobu a mapear con la habitación")
        parser.add_argument("--api-key", type=str, required=False, help="Api-Key de Smoobu (si se omite, usa el guardado en OtaConfig.credentials)")
        parser.add_argument("--base-url", type=str, default="https://login.smoobu.com", help="Base URL Smoobu (default: https://login.smoobu.com)")
        parser.add_argument("--since-minutes", type=int, default=60 * 24 * 7, help="Ventana de cambios a consultar (default: 7 días)")

    def handle(self, *args, **opts):
        hotel_id = opts["hotel_id"]
        room_id = opts["room_id"]
        apartment_id = str(opts["apartment_id"])
        api_key = opts.get("api_key")
        base_url = str(opts.get("base_url") or "https://login.smoobu.com").rstrip("/")
        since_minutes = int(opts.get("since_minutes") or (60 * 24 * 7))

        try:
            hotel = Hotel.objects.get(id=hotel_id)
            room = Room.objects.get(id=room_id)
        except Hotel.DoesNotExist:
            raise CommandError(f"Hotel id={hotel_id} no existe")
        except Room.DoesNotExist:
            raise CommandError(f"Room id={room_id} no existe")

        self.stdout.write(self.style.SUCCESS(f"Hotel: {hotel.name} | Room: {room.name} | Apartment: {apartment_id}"))

        cfg, _ = OtaConfig.objects.get_or_create(
            hotel=hotel,
            provider=OtaProvider.SMOOBU,
            defaults={"is_active": True, "credentials": {}},
        )
        cfg.is_active = True
        creds = dict(cfg.credentials or {})
        creds["base_url"] = base_url
        if api_key:
            creds["api_key"] = api_key
        cfg.credentials = creds
        cfg.save(update_fields=["is_active", "credentials"])

        if not (cfg.credentials or {}).get("api_key"):
            raise CommandError("Falta Api-Key. Pasá --api-key o cargalo en OtaConfig.credentials.api_key")

        self.stdout.write(self.style.SUCCESS("Config Smoobu OK (api_key presente)"))

        # Verificación simple contra /api/me (si está disponible)
        try:
            r = requests.get(
                f"{base_url}/api/me",
                headers={"Api-Key": (cfg.credentials or {}).get("api_key")},
                timeout=15,
            )
            self.stdout.write(f"GET /api/me -> HTTP {r.status_code}")
        except Exception as e:
            self.stdout.write(self.style.WARNING(f"No se pudo consultar /api/me: {e}"))

        mapping, _ = OtaRoomMapping.objects.get_or_create(
            hotel=hotel,
            room=room,
            provider=OtaProvider.SMOOBU,
            defaults={"external_id": apartment_id, "is_active": True},
        )
        mapping.external_id = apartment_id
        mapping.is_active = True
        mapping.save(update_fields=["external_id", "is_active"])
        self.stdout.write(self.style.SUCCESS(f"Mapping Smoobu OK: room={room.id} -> apartment={apartment_id}"))

        since = timezone.now() - timedelta(minutes=since_minutes)
        job = OtaSyncJob.objects.create(
            hotel=hotel,
            provider=OtaProvider.SMOOBU,
            job_type=OtaSyncJob.JobType.PULL_RESERVATIONS,
            status=OtaSyncJob.JobStatus.RUNNING,
            stats={"hotel_id": hotel.id, "provider": OtaProvider.SMOOBU, "since": since.isoformat(), "trigger": "command"},
        )
        stats = pull_reservations_for_hotel(job, hotel.id, OtaProvider.SMOOBU, since)
        job.status = OtaSyncJob.JobStatus.SUCCESS
        job.stats = stats
        job.finished_at = timezone.now()
        job.save(update_fields=["status", "stats", "finished_at"])

        self.stdout.write(self.style.SUCCESS(f"PULL SMOOBU OK: {stats}"))
        self.stdout.write(self.style.SUCCESS("Smoobu smoke test completado"))

