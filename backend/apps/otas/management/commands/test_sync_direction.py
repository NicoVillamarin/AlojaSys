from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta

from apps.core.models import Hotel
from apps.rooms.models import Room
from apps.otas.models import OtaRoomMapping, OtaProvider, OtaSyncJob
from apps.otas.services.ical_importer import import_ics_for_room_mapping


class Command(BaseCommand):
    help = "Prueba sync_direction y last_synced en OtaRoomMapping"

    def add_arguments(self, parser):
        parser.add_argument("--hotel-id", type=int, default=1)
        parser.add_argument("--room-id", type=int, default=1)

    def handle(self, *args, **opts):
        hotel_id = opts["hotel_id"]
        room_id = opts["room_id"]

        try:
            hotel = Hotel.objects.get(id=hotel_id)
            room = Room.objects.get(id=room_id)
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error: {e}"))
            return

        self.stdout.write(self.style.SUCCESS(f"\n🧪 TEST: sync_direction y last_synced"))
        self.stdout.write(f"Hotel: {hotel.name} | Room: {room.name}\n")

        # Crear/obtener mapeo de prueba
        mapping, created = OtaRoomMapping.objects.get_or_create(
            hotel=hotel,
            room=room,
            provider=OtaProvider.ICAL,
            defaults={
                "ical_in_url": "https://httpbin.org/get",  # URL dummy para pruebas
                "sync_direction": OtaRoomMapping.SyncDirection.BOTH,
                "is_active": True,
            }
        )
        self.stdout.write(f"Mapping ID: {mapping.id} ({'CREADO' if created else 'EXISTENTE'})")
        self.stdout.write(f"sync_direction: {mapping.sync_direction}")
        self.stdout.write(f"last_synced ANTES: {mapping.last_synced or 'Nunca'}\n")

        # Test 1: Verificar que sync_direction se puede cambiar
        self.stdout.write(self.style.WARNING("📝 Test 1: Cambiar sync_direction"))
        for direction in ["both", "import", "export"]:
            mapping.sync_direction = direction
            mapping.save()
            self.stdout.write(f"  ✓ Cambiado a '{direction}': {mapping.sync_direction == direction}")

        # Resetear a BOTH para pruebas siguientes
        mapping.sync_direction = OtaRoomMapping.SyncDirection.BOTH
        mapping.save()

        # Test 2: Import con sync_direction=IMPORT
        self.stdout.write(self.style.WARNING("\n📥 Test 2: Import con sync_direction=IMPORT"))
        mapping.sync_direction = OtaRoomMapping.SyncDirection.IMPORT
        mapping.save()
        job = OtaSyncJob.objects.create(
            hotel=hotel,
            provider=OtaProvider.ICAL,
            job_type=OtaSyncJob.JobType.IMPORT_ICS,
            status=OtaSyncJob.JobStatus.RUNNING,
            stats={"mapping_id": mapping.id},
        )
        try:
            stats = import_ics_for_room_mapping(mapping.id, job=job)
            mapping.refresh_from_db()
            self.stdout.write(f"  ✓ Stats: {stats}")
            self.stdout.write(f"  ✓ last_synced DESPUÉS: {mapping.last_synced or 'No actualizado'}")
            self.stdout.write(f"  ✓ sync_direction respetado: {mapping.sync_direction == 'import'}")
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"  ✗ Error: {e}"))

        # Test 3: Import con sync_direction=EXPORT (no debería importar)
        self.stdout.write(self.style.WARNING("\n📤 Test 3: Intentar import con sync_direction=EXPORT (debe fallar)"))
        mapping.sync_direction = OtaRoomMapping.SyncDirection.EXPORT
        mapping.save()
        old_last_synced = mapping.last_synced
        job2 = OtaSyncJob.objects.create(
            hotel=hotel,
            provider=OtaProvider.ICAL,
            job_type=OtaSyncJob.JobType.IMPORT_ICS,
            status=OtaSyncJob.JobStatus.RUNNING,
            stats={"mapping_id": mapping.id},
        )
        try:
            stats = import_ics_for_room_mapping(mapping.id, job=job2)
            mapping.refresh_from_db()
            self.stdout.write(f"  ✓ Stats: {stats}")
            self.stdout.write(f"  ✓ Debe tener processed=0: {stats.get('processed', -1) == 0}")
            self.stdout.write(f"  ✓ last_synced NO cambió: {mapping.last_synced == old_last_synced}")
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"  ✗ Error: {e}"))

        # Test 4: Verificar serializer
        self.stdout.write(self.style.WARNING("\n📋 Test 4: Verificar serializer incluye campos"))
        from apps.otas.serializers import OtaRoomMappingSerializer
        serializer = OtaRoomMappingSerializer(mapping)
        data = serializer.data
        has_sync_dir = "sync_direction" in data
        has_last_synced = "last_synced" in data
        self.stdout.write(f"  ✓ sync_direction en serializer: {has_sync_dir}")
        self.stdout.write(f"  ✓ last_synced en serializer: {has_last_synced}")
        if has_sync_dir:
            self.stdout.write(f"  ✓ Valor sync_direction: {data['sync_direction']}")

        self.stdout.write(self.style.SUCCESS("\n✅ Tests completados"))

