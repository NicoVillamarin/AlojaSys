from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from apps.core.models import Hotel
from apps.rooms.models import Room, RoomType, RoomStatus
from decimal import Decimal
import random


class Command(BaseCommand):
    help = "Borra todas las habitaciones y crea 30 habitaciones completas para cada hotel (SIN tocar reservas)."

    def add_arguments(self, parser):
        parser.add_argument("--confirm", action="store_true", help="Confirma que quieres borrar todas las habitaciones")
        parser.add_argument("--count", type=int, default=30, help="Cantidad de habitaciones por hotel (default: 30)")

    @transaction.atomic
    def handle(self, *args, **options):
        if not options["confirm"]:
            self.stdout.write(
                self.style.WARNING(
                    "⚠️  ADVERTENCIA: Este comando borrará TODAS las habitaciones.\n"
                    "Las reservas NO se verán afectadas.\n"
                    "Usa --confirm para proceder."
                )
            )
            return

        count = options["count"]
        
        # 1. Borrar todas las habitaciones
        self.stdout.write("🗑️  Borrando todas las habitaciones...")
        rooms_deleted = Room.objects.all().delete()[0]
        self.stdout.write(f"   ✅ {rooms_deleted} habitaciones eliminadas")
        
        # 2. Obtener los hoteles
        hotels = Hotel.objects.filter(is_active=True)
        if not hotels.exists():
            raise CommandError("No hay hoteles activos en el sistema")
        
        self.stdout.write(f"🏨 Encontrados {hotels.count()} hoteles activos")
        
        # 3. Crear habitaciones para cada hotel
        total_created = 0
        
        for hotel in hotels:
            self.stdout.write(f"\n🏨 Procesando hotel: {hotel.name} (ID: {hotel.id})")
            created = self._create_rooms_for_hotel(hotel, count)
            total_created += created
            self.stdout.write(f"   ✅ {created} habitaciones creadas para {hotel.name}")
        
        self.stdout.write(
            self.style.SUCCESS(
                f"\n🎉 Proceso completado exitosamente!\n"
                f"   • {rooms_deleted} habitaciones eliminadas\n"
                f"   • {total_created} nuevas habitaciones creadas\n"
                f"   • Las reservas se mantuvieron intactas"
            )
        )

    def _create_rooms_for_hotel(self, hotel, count):
        """Crea habitaciones completas para un hotel específico"""
        created = 0
        
        # Distribución de tipos de habitación
        room_types_distribution = [
            (RoomType.SINGLE, 0.3),    # 30% individuales
            (RoomType.DOUBLE, 0.4),    # 40% dobles
            (RoomType.TRIPLE, 0.2),    # 20% triples
            (RoomType.SUITE, 0.1),     # 10% suites
        ]
        
        # Configuración por tipo de habitación
        room_config = {
            RoomType.SINGLE: {
                "capacity": 1,
                "max_capacity": 2,
                "base_price": Decimal("50.00"),
                "extra_guest_fee": Decimal("15.00"),
                "description": "Habitación individual con cama simple, ideal para viajeros de negocios"
            },
            RoomType.DOUBLE: {
                "capacity": 2,
                "max_capacity": 3,
                "base_price": Decimal("80.00"),
                "extra_guest_fee": Decimal("20.00"),
                "description": "Habitación doble con cama matrimonial, perfecta para parejas"
            },
            RoomType.TRIPLE: {
                "capacity": 3,
                "max_capacity": 4,
                "base_price": Decimal("110.00"),
                "extra_guest_fee": Decimal("25.00"),
                "description": "Habitación triple con múltiples camas, ideal para familias pequeñas"
            },
            RoomType.SUITE: {
                "capacity": 2,
                "max_capacity": 4,
                "base_price": Decimal("180.00"),
                "extra_guest_fee": Decimal("30.00"),
                "description": "Suite de lujo con sala de estar separada y amenities premium"
            }
        }
        
        # Distribución de pisos
        floors_distribution = [1, 1, 1, 1, 2, 2, 2, 3, 3, 4, 5, 6]
        
        # Determinar punto de partida de numeración
        next_number = 101
        
        for i in range(count):
            # Seleccionar tipo de habitación según distribución
            room_type = self._weighted_choice(room_types_distribution)
            floor = random.choice(floors_distribution)
            
            # Asegurar numeración coherente por piso
            if next_number < floor * 100:
                next_number = floor * 100 + 1
            
            number = next_number
            next_number += 1
            
            # Configuración de la habitación
            config = room_config[room_type]
            
            # Crear nombre único incluyendo el ID del hotel
            name = f"HAB-{hotel.id}-{number}"
            
            # Crear la habitación con todos los campos
            room = Room.objects.create(
                name=name,
                hotel=hotel,
                floor=floor,
                room_type=room_type,
                number=number,
                description=config["description"],
                base_price=config["base_price"],
                capacity=config["capacity"],
                max_capacity=config["max_capacity"],
                extra_guest_fee=config["extra_guest_fee"],
                status=RoomStatus.AVAILABLE,
                is_active=True
            )
            
            created += 1
            
            # Log cada 10 habitaciones
            if created % 10 == 0:
                self.stdout.write(f"   📝 {created}/{count} habitaciones creadas...")
        
        return created

    def _weighted_choice(self, choices):
        """Selecciona un elemento basado en pesos"""
        total = sum(weight for _, weight in choices)
        r = random.uniform(0, total)
        upto = 0
        for choice, weight in choices:
            if upto + weight >= r:
                return choice
            upto += weight
        return choices[-1][0]  # fallback
