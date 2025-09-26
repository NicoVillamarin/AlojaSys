from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from apps.core.models import Hotel
from apps.rooms.models import Room, RoomType, RoomStatus
from decimal import Decimal
import random


class Command(BaseCommand):
    help = "Genera habitaciones de ejemplo para un hotel dado."

    def add_arguments(self, parser):
        parser.add_argument("hotel_id", type=int, help="ID del hotel destino")
        parser.add_argument("--count", type=int, default=20, help="Cantidad de habitaciones a crear (default: 20)")
        parser.add_argument("--prefix", type=str, default="HAB", help="Prefijo del nombre de habitación")

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
        room_types_weighted = [
            RoomType.SINGLE,
            RoomType.SINGLE,
            RoomType.DOUBLE,
            RoomType.DOUBLE,
            RoomType.TRIPLE,
            RoomType.SUITE,
        ]

        created = 0
        skipped = 0

        # Determinar punto de partida de numeración para evitar colisiones
        existing_numbers = set(Room.objects.filter(hotel=hotel).values_list("number", flat=True))
        next_number = 101
        while next_number in existing_numbers:
            next_number += 1

        for i in range(count):
            floor = random.choice(floors)
            room_type = random.choice(room_types_weighted)

            # Numeración coherente: planta * 100 + índice
            if next_number < floor * 100:
                next_number = floor * 100 + 1

            number = next_number
            next_number += 1

            capacity_by_type = {
                RoomType.SINGLE: 1,
                RoomType.DOUBLE: 2,
                RoomType.TRIPLE: 3,
                RoomType.SUITE: 2,
            }
            base_price_by_type = {
                RoomType.SINGLE: Decimal("50.00"),
                RoomType.DOUBLE: Decimal("80.00"),
                RoomType.TRIPLE: Decimal("110.00"),
                RoomType.SUITE: Decimal("180.00"),
            }

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
