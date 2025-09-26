from django.core.management.base import BaseCommand
from apps.enterprises.models import Enterprise
from apps.core.models import Hotel


class Command(BaseCommand):
    help = "Crea una empresa demo y la asigna a los hoteles sin empresa"

    def handle(self, *args, **options):
        enterprise, created = Enterprise.objects.get_or_create(
            name="Demo Enterprise",
            defaults={
                "legal_name": "Demo Enterprise S.A.",
                "is_active": True,
            },
        )
        if created:
            self.stdout.write(self.style.SUCCESS(f"Creada empresa demo: {enterprise.name}"))
        else:
            self.stdout.write(self.style.WARNING(f"Empresa demo ya existía: {enterprise.name}"))

        updated = Hotel.objects.filter(enterprise__isnull=True).update(enterprise=enterprise)
        self.stdout.write(self.style.SUCCESS(f"Hoteles actualizados: {updated}"))


