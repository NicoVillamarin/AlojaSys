from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from apps.core.models import Hotel
from apps.rooms.models import Room, RoomStatus
from decimal import Decimal
import random


class Command(BaseCommand):
    help = "Genera habitaciones de ejemplo para un hotel dado."

    def add_arguments(self, parser):
        parser.add_argument("hotel_id", type=int, help="ID del hotel destino")
        parser.add_argument("--count", type=int, default=20, help="Cantidad de habitaciones a crear (default: 20)")
        parser.add_argument("--prefix", type=str, default="HAB", help="Prefijo del nombre de habitación")
        parser.add_argument("--ars", action="store_true", help="Usar precios típicos de Argentina (ARS)")

    @transaction.atomic
    def handle(self, hotel_id: int, *args, **options):
        try:
            hotel = Hotel.objects.get(pk=hotel_id)
        except Hotel.DoesNotExist:
            raise CommandError(f"Hotel {hotel_id} no existe")

        count = options["count"]
        prefix = options["prefix"].upper()

        # Definición de plantas y tipos, con distribución básica
        floors = [1, 1, 1, 2, 2, 2, 3, 3, 4, 5]
        single = "single"
        double = "double"
        triple = "triple"
        suite = "suite"
        room_types_weighted = [
            single,
            single,
            double,
            double,
            triple,
            suite,
        ]

        created = 0
        skipped = 0

        # Determinar punto de partida de numeración para evitar colisiones
        existing_numbers = set(Room.objects.filter(hotel=hotel).values_list("number", flat=True))
        next_number = 101
        while next_number in existing_numbers:
            next_number += 1

        # Configuración de capacidades y precios (opcional ARS)
        capacity_by_type = {
            single: 1,
            double: 2,
            triple: 3,
            suite: 2,
        }
        if options.get("ars"):
            # Valores típicos en ARS (ajustables)
            base_price_by_type = {
                single: Decimal("40000.00"),
                double: Decimal("65000.00"),
                triple: Decimal("90000.00"),
                suite: Decimal("150000.00"),
            }
        else:
            base_price_by_type = {
                single: Decimal("50.00"),
                double: Decimal("80.00"),
                triple: Decimal("110.00"),
                suite: Decimal("180.00"),
            }

        for i in range(count):
            floor = random.choice(floors)
            room_type = random.choice(room_types_weighted)

            # Numeración coherente: planta * 100 + índice
            if next_number < floor * 100:
                next_number = floor * 100 + 1

            number = next_number
            next_number += 1

            name = f"{prefix}-{number}"

            if Room.objects.filter(hotel=hotel, number=number).exists() or Room.objects.filter(name=name).exists():
                skipped += 1
                continue

            Room.objects.create(
                name=name,
                hotel=hotel,
                floor=floor,
                room_type=room_type,
                number=number,
                description=f"Habitación {room_type} en piso {floor}",
                base_price=base_price_by_type[room_type],
                capacity=capacity_by_type[room_type],
                status=RoomStatus.AVAILABLE,
                is_active=True,
            )
            created += 1

        self.stdout.write(self.style.SUCCESS(f"Hotel {hotel_id}: creadas {created}, saltadas {skipped}"))
