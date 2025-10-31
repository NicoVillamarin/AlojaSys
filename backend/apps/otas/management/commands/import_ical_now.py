from django.core.management.base import BaseCommand, CommandError

from apps.otas.models import OtaRoomMapping, OtaProvider
from apps.otas.services.ical_importer import import_ics_for_room_mapping


class Command(BaseCommand):
    help = "Importa ahora mismo el ICS para un mapping específico o para todos los mappings ICAL activos"

    def add_arguments(self, parser):
        parser.add_argument("--mapping-id", type=int, help="ID del OtaRoomMapping a importar")
        parser.add_argument("--all", action="store_true", help="Importa todos los mappings ICAL activos con URL")

    def handle(self, *args, **options):
        mapping_id = options.get("mapping_id")
        do_all = options.get("all")

        if not mapping_id and not do_all:
            raise CommandError("Debes especificar --mapping-id o --all")

        if mapping_id:
            stats = import_ics_for_room_mapping(mapping_id)
            self.stdout.write(self.style.SUCCESS(f"Importado mapping {mapping_id}: {stats}"))
            return

        qs = OtaRoomMapping.objects.filter(provider=OtaProvider.ICAL, is_active=True).exclude(ical_in_url__isnull=True).exclude(ical_in_url="")
        total = 0
        for m in qs:
            stats = import_ics_for_room_mapping(m.id)
            self.stdout.write(self.style.SUCCESS(f"Importado mapping {m.id} ({m.room.name}): {stats}"))
            total += 1
        self.stdout.write(self.style.SUCCESS(f"Listo. Procesados {total} mappings"))


