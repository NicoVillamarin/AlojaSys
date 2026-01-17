from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone
from datetime import timedelta
import os
import requests

from apps.core.models import Hotel
from apps.rooms.models import Room
from apps.otas.models import OtaProvider, OtaRoomMapping


class Command(BaseCommand):
    help = "Simula un webhook de Smoobu contra el endpoint local (new/update/cancel/delete)."

    def add_arguments(self, parser):
        parser.add_argument("--hotel-id", type=int, required=True)
        parser.add_argument("--room-id", type=int, required=True)
        parser.add_argument("--apartment-id", type=str, required=True, help="ID del apartment en Smoobu (mapeo external_id)")
        parser.add_argument("--base-url", type=str, default="http://localhost:8000", help="Base URL del backend (default: http://localhost:8000)")
        parser.add_argument(
            "--action",
            type=str,
            default="newReservation",
            choices=["newReservation", "updateReservation", "cancelReservation", "deleteReservation"],
        )
        parser.add_argument("--token", type=str, default=None, help="Token del webhook (si se omite, usa SMOOBU_WEBHOOK_TOKEN)")
        parser.add_argument("--smoobu-res-id", type=int, default=999001, help="ID de reserva Smoobu para el payload")
        parser.add_argument("--channel-name", type=str, default="Booking.com", help="Nombre del canal (Booking.com/Airbnb/...)")

    def handle(self, *args, **opts):
        hotel_id = opts["hotel_id"]
        room_id = opts["room_id"]
        apartment_id = str(opts["apartment_id"])
        base_url = str(opts["base_url"]).rstrip("/")
        action = opts["action"]
        token = opts.get("token") or os.environ.get("SMOOBU_WEBHOOK_TOKEN") or ""
        smoobu_res_id = int(opts.get("smoobu_res_id") or 999001)
        channel_name = opts.get("channel_name") or "Booking.com"

        try:
            hotel = Hotel.objects.get(id=hotel_id)
            room = Room.objects.get(id=room_id)
        except Hotel.DoesNotExist:
            raise CommandError(f"Hotel id={hotel_id} no existe")
        except Room.DoesNotExist:
            raise CommandError(f"Room id={room_id} no existe")

        # Asegurar mapeo Smoobu para que el webhook resuelva habitación
        mapping, _ = OtaRoomMapping.objects.get_or_create(
            hotel=hotel,
            room=room,
            provider=OtaProvider.SMOOBU,
            defaults={"external_id": apartment_id, "is_active": True},
        )
        mapping.external_id = apartment_id
        mapping.is_active = True
        mapping.save(update_fields=["external_id", "is_active"])

        now = timezone.now()
        arrival = (now.date() + timedelta(days=3)).isoformat()
        departure = (now.date() + timedelta(days=5)).isoformat()

        payload = {
            "action": action,
            "user": 1,
            "data": {
                "id": smoobu_res_id,
                "arrival": arrival,
                "departure": departure,
                "modifiedAt": now.strftime("%Y-%m-%d %H:%M"),
                "apartment": {"id": int(apartment_id) if apartment_id.isdigit() else apartment_id, "name": f"Apt {apartment_id}"},
                "channel": {"id": 1, "name": channel_name},
                "guest-name": "Test Smoobu",
                "email": "test@smoobu.local",
                "adults": 2,
                "children": 0,
                "price": 12345,
                "notice": "Simulación webhook",
                "is-blocked-booking": False,
            },
        }

        url = f"{base_url}/api/otas/webhooks/smoobu/"
        params = {"token": token} if token else {}

        self.stdout.write(self.style.WARNING(f"POST {url} action={action} token={'set' if bool(token) else 'EMPTY'}"))
        resp = requests.post(url, params=params, json=payload, timeout=20)
        self.stdout.write(self.style.SUCCESS(f"HTTP {resp.status_code}: {resp.text}"))

