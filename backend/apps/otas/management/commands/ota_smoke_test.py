from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone
from datetime import timedelta, date

from apps.core.models import Hotel
from apps.rooms.models import Room
from apps.reservations.models import Reservation, ReservationStatus
from apps.otas.models import OtaConfig, OtaProvider, OtaRoomMapping, OtaSyncJob
from apps.otas.services.ical_sync_service import ICALSyncService
from apps.otas.services.ari_publisher import build_mock_ari_payload, push_ari_for_hotel

import secrets


class Command(BaseCommand):
    help = "Smoke test OTAs: iCal export/import y push ARI mock en un hotel/habitación"

    def add_arguments(self, parser):
        parser.add_argument("--hotel-id", type=int, required=True)
        parser.add_argument("--room-id", type=int, required=True)
        parser.add_argument("--base-url", type=str, default="http://backend:8000")

    def handle(self, *args, **opts):
        hotel_id = opts["hotel_id"]
        room_id = opts["room_id"]
        base_url = opts["base_url"].rstrip("/")

        try:
            hotel = Hotel.objects.get(id=hotel_id)
            room = Room.objects.get(id=room_id)
        except Hotel.DoesNotExist:
            raise CommandError(f"Hotel id={hotel_id} no existe")
        except Room.DoesNotExist:
            raise CommandError(f"Room id={room_id} no existe")

        self.stdout.write(self.style.SUCCESS(f"Hotel: {hotel.name} | Room: {room.name}"))

        # 1) Asegurar config iCal con token
        cfg, _ = OtaConfig.objects.get_or_create(hotel=hotel, provider=OtaProvider.ICAL, defaults={"is_active": True})
        if not cfg.ical_out_token:
            cfg.ical_out_token = secrets.token_urlsafe(24)
            cfg.is_active = True
            cfg.save(update_fields=["ical_out_token", "is_active"])
        self.stdout.write(f"Token iCal: {cfg.ical_out_token}")

        hotel_ics = f"{base_url}/api/otas/ical/hotel/{hotel.id}.ics?token={cfg.ical_out_token}"
        room_ics = f"{base_url}/api/otas/ical/room/{room.id}.ics?token={cfg.ical_out_token}"
        self.stdout.write(f"URL ICS hotel: {hotel_ics}")
        self.stdout.write(f"URL ICS room : {room_ics}")

        # 2) Crear reserva demo futura (para que el ICS tenga eventos)
        today = timezone.now().date()
        res = Reservation.objects.create(
            hotel=hotel,
            room=room,
            guests=1,
            guests_data=[{"name": "Smoke", "is_primary": True}],
            check_in=today + timedelta(days=2),
            check_out=today + timedelta(days=4),
            status=ReservationStatus.CONFIRMED,
            total_price=1000,
        )
        self.stdout.write(self.style.SUCCESS(f"Reserva demo creada: RES-{res.id}"))

        # 3) Asegurar mapping ICAL apuntando a su propio ICS (para la prueba)
        m, _ = OtaRoomMapping.objects.get_or_create(
            hotel=hotel, room=room, provider=OtaProvider.ICAL,
            defaults={"ical_in_url": room_ics, "is_active": True}
        )
        if not m.ical_in_url:
            m.ical_in_url = room_ics
            m.is_active = True
            m.save(update_fields=["ical_in_url", "is_active"])
        self.stdout.write(f"Mapping ICAL: id={m.id} url={m.ical_in_url}")

        # 4) Ejecutar import ICS sincronamente
        job = OtaSyncJob.objects.create(hotel=hotel, provider=OtaProvider.ICAL, job_type=OtaSyncJob.JobType.IMPORT_ICS, status=OtaSyncJob.JobStatus.RUNNING, stats={"mapping_id": m.id})
        stats = ICALSyncService.import_reservations(m, job=job)
        job.status = OtaSyncJob.JobStatus.SUCCESS
        job.stats = stats
        job.save(update_fields=["status", "stats", "finished_at"])
        self.stdout.write(self.style.SUCCESS(f"IMPORT ICS OK: {stats}"))

        # 5) ARI payload mock y push (usa mapeos si existen; si no, el payload saldrá vacío)
        df = today + timedelta(days=1)
        dt = today + timedelta(days=7)
        ari_payload = build_mock_ari_payload(hotel.id, OtaProvider.BOOKING, df, dt)
        self.stdout.write(f"ARI items a enviar: {len(ari_payload.get('items', []))}")

        job2 = OtaSyncJob.objects.create(hotel=hotel, provider=OtaProvider.BOOKING, job_type=OtaSyncJob.JobType.PUSH_ARI, status=OtaSyncJob.JobStatus.RUNNING, stats={})
        push_stats = push_ari_for_hotel(job2, hotel.id, OtaProvider.BOOKING, df, dt)
        job2.status = OtaSyncJob.JobStatus.SUCCESS
        job2.stats = push_stats
        job2.save(update_fields=["status", "stats", "finished_at"])
        self.stdout.write(self.style.SUCCESS(f"PUSH ARI OK: {push_stats}"))

        self.stdout.write(self.style.SUCCESS("Smoke test completado"))


