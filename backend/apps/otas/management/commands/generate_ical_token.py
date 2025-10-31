from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from apps.core.models import Hotel
from apps.rooms.models import Room
from apps.otas.models import OtaConfig, OtaProvider

import secrets


class Command(BaseCommand):
    help = "Genera (o muestra) el token iCal para un hotel y lista URLs ICS"

    def add_arguments(self, parser):
        parser.add_argument(
            "--hotel-id",
            type=int,
            required=True,
            help="ID del hotel para generar/mostrar token iCal",
        )
        parser.add_argument(
            "--base-url",
            type=str,
            default="http://localhost:8000",
            help="Base URL para imprimir URLs completas (default: http://localhost:8000)",
        )
        parser.add_argument(
            "--show-rooms",
            action="store_true",
            help="Muestra también URLs ICS por habitación (muestra hasta 5)",
        )

    @transaction.atomic
    def handle(self, *args, **options):
        hotel_id = options["hotel_id"]
        base_url = options["base_url"].rstrip("/")
        show_rooms = options["show_rooms"]

        try:
            hotel = Hotel.objects.get(id=hotel_id)
        except Hotel.DoesNotExist:
            raise CommandError(f"Hotel con id={hotel_id} no existe")

        cfg, _ = OtaConfig.objects.get_or_create(
            hotel=hotel,
            provider=OtaProvider.ICAL,
            defaults={"is_active": True},
        )

        if not cfg.ical_out_token:
            cfg.ical_out_token = secrets.token_urlsafe(24)
            cfg.is_active = True
            cfg.save(update_fields=["ical_out_token", "is_active"])

        token = cfg.ical_out_token

        hotel_path = f"/api/otas/ical/hotel/{hotel.id}.ics?token={token}"
        self.stdout.write(self.style.SUCCESS("Token iCal generado/activo:"))
        self.stdout.write(f"  HOTEL_ID: {hotel.id}")
        self.stdout.write(f"  TOKEN   : {token}")
        self.stdout.write("")
        self.stdout.write(self.style.SUCCESS("URL ICS por hotel:"))
        self.stdout.write(f"  {base_url}{hotel_path}")

        if show_rooms:
            self.stdout.write("")
            self.stdout.write(self.style.SUCCESS("URLs ICS por habitación (hasta 5):"))
            rooms = Room.objects.filter(hotel=hotel).order_by("id").values("id", "name")[:5]
            if not rooms:
                self.stdout.write("  (El hotel no tiene habitaciones registradas)")
            for r in rooms:
                room_path = f"/api/otas/ical/room/{r['id']}.ics?token={token}"
                self.stdout.write(f"  - {r['name']} (ID {r['id']}): {base_url}{room_path}")

        self.stdout.write("")
        self.stdout.write(self.style.SUCCESS("Listo. Copiá la URL y probá en el navegador o con curl."))


