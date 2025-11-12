from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from apps.core.models import Hotel
from apps.rooms.models import Room, RoomType, RoomStatus, CleaningStatus
from decimal import Decimal, InvalidOperation
import json
import os


class Command(BaseCommand):
    help = "Carga habitaciones desde un archivo JSON para un hotel específico."

    def add_arguments(self, parser):
        parser.add_argument(
            "hotel_id",
            type=int,
            help="ID del hotel destino"
        )
        parser.add_argument(
            "json_file",
            type=str,
            help="Ruta al archivo JSON con las habitaciones"
        )
        parser.add_argument(
            "--update",
            action="store_true",
            help="Actualizar habitaciones existentes si ya existen (por nombre)"
        )
        parser.add_argument(
            "--skip-existing",
            action="store_true",
            help="Saltar habitaciones que ya existen (por nombre)"
        )

    def validate_room_data(self, data, index):
        """Valida los datos de una habitación"""
        required_fields = ['name', 'floor', 'room_type', 'number', 'base_price']
        for field in required_fields:
            if field not in data:
                raise CommandError(f"Habitación {index}: falta el campo requerido '{field}'")
        
        # Validar room_type
        valid_types = [choice[0] for choice in RoomType.choices]
        if data['room_type'] not in valid_types:
            raise CommandError(
                f"Habitación {index}: room_type '{data['room_type']}' inválido. "
                f"Opciones: {', '.join(valid_types)}"
            )
        
        # Validar status si se proporciona
        if 'status' in data:
            valid_statuses = [choice[0] for choice in RoomStatus.choices]
            if data['status'] not in valid_statuses:
                raise CommandError(
                    f"Habitación {index}: status '{data['status']}' inválido. "
                    f"Opciones: {', '.join(valid_statuses)}"
                )
        
        # Validar cleaning_status si se proporciona
        if 'cleaning_status' in data:
            valid_cleaning = [choice[0] for choice in CleaningStatus.choices]
            if data['cleaning_status'] not in valid_cleaning:
                raise CommandError(
                    f"Habitación {index}: cleaning_status '{data['cleaning_status']}' inválido. "
                    f"Opciones: {', '.join(valid_cleaning)}"
                )
        
        # Validar precios
        try:
            base_price = Decimal(str(data['base_price']))
            if base_price < 0:
                raise CommandError(f"Habitación {index}: base_price no puede ser negativo")
            data['base_price'] = base_price
        except (InvalidOperation, ValueError):
            raise CommandError(f"Habitación {index}: base_price debe ser un número válido")
        
        if 'extra_guest_fee' in data:
            try:
                extra_fee = Decimal(str(data['extra_guest_fee']))
                if extra_fee < 0:
                    raise CommandError(f"Habitación {index}: extra_guest_fee no puede ser negativo")
                data['extra_guest_fee'] = extra_fee
            except (InvalidOperation, ValueError):
                raise CommandError(f"Habitación {index}: extra_guest_fee debe ser un número válido")
        
        # Valores por defecto
        data.setdefault('capacity', 1)
        data.setdefault('max_capacity', data.get('capacity', 1))
        data.setdefault('extra_guest_fee', Decimal('0.00'))
        data.setdefault('status', RoomStatus.AVAILABLE)
        data.setdefault('cleaning_status', CleaningStatus.CLEAN)
        data.setdefault('description', '')
        data.setdefault('is_active', True)
        
        return data

    @transaction.atomic
    def handle(self, hotel_id, json_file, *args, **options):
        # Validar hotel
        try:
            hotel = Hotel.objects.get(pk=hotel_id)
        except Hotel.DoesNotExist:
            raise CommandError(f"Hotel {hotel_id} no existe")

        # Validar archivo
        if not os.path.exists(json_file):
            raise CommandError(f"Archivo no encontrado: {json_file}")

        # Leer JSON
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                rooms_data = json.load(f)
        except json.JSONDecodeError as e:
            raise CommandError(f"Error al parsear JSON: {e}")
        except Exception as e:
            raise CommandError(f"Error al leer archivo: {e}")

        if not isinstance(rooms_data, list):
            raise CommandError("El JSON debe ser un array de habitaciones")

        # Procesar habitaciones
        created = 0
        updated = 0
        skipped = 0
        errors = []

        for index, room_data in enumerate(rooms_data, start=1):
            try:
                # Validar datos
                room_data = self.validate_room_data(room_data, index)
                
                name = room_data['name']
                number = room_data['number']
                
                # Verificar si ya existe
                existing_room = Room.objects.filter(hotel=hotel, name=name).first()
                
                if existing_room:
                    if options.get('skip_existing'):
                        skipped += 1
                        self.stdout.write(
                            self.style.WARNING(f"  [{index}] Saltando '{name}' (ya existe)")
                        )
                        continue
                    elif options.get('update'):
                        # Actualizar habitación existente
                        for key, value in room_data.items():
                            if key not in ['name', 'hotel']:  # No actualizar nombre ni hotel
                                setattr(existing_room, key, value)
                        existing_room.save()
                        updated += 1
                        self.stdout.write(
                            self.style.SUCCESS(f"  [{index}] Actualizada '{name}'")
                        )
                        continue
                    else:
                        errors.append(f"  [{index}] Habitación '{name}' ya existe. Usa --update o --skip-existing")
                        continue
                
                # Verificar número único en el hotel
                if Room.objects.filter(hotel=hotel, number=number).exists():
                    errors.append(f"  [{index}] Número {number} ya existe en el hotel")
                    continue
                
                # Crear habitación
                Room.objects.create(
                    hotel=hotel,
                    **{k: v for k, v in room_data.items() if k != 'hotel'}
                )
                created += 1
                self.stdout.write(
                    self.style.SUCCESS(f"  [{index}] Creada '{name}' (Piso {room_data['floor']}, {room_data['room_type']})")
                )
                
            except Exception as e:
                errors.append(f"  [{index}] Error: {str(e)}")
                continue

        # Resumen
        self.stdout.write("\n" + "="*50)
        self.stdout.write(self.style.SUCCESS(f"✅ Resumen:"))
        self.stdout.write(f"   Creadas: {created}")
        if updated > 0:
            self.stdout.write(f"   Actualizadas: {updated}")
        if skipped > 0:
            self.stdout.write(f"   Saltadas: {skipped}")
        if errors:
            self.stdout.write(self.style.ERROR(f"   Errores: {len(errors)}"))
            self.stdout.write("\n" + self.style.ERROR("Errores encontrados:"))
            for error in errors:
                self.stdout.write(self.style.ERROR(error))
        self.stdout.write("="*50)

