from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone
from datetime import timedelta

from apps.otas.models import OtaSyncJob, OtaProvider, OtaSyncLog
from apps.core.models import Hotel
from apps.otas.services.ari_publisher import pull_reservations_for_hotel


class Command(BaseCommand):
    help = "Dispara un PULL de reservas para un hotel/proveedor y muestra el job y sus logs"

    def add_arguments(self, parser):
        parser.add_argument("--hotel-id", type=int, required=True)
        parser.add_argument("--provider", type=str, default=OtaProvider.BOOKING)
        parser.add_argument("--minutes", type=int, default=10)

    def handle(self, *args, **opts):
        hotel_id = opts["hotel_id"]
        provider = opts["provider"]
        minutes = int(opts["minutes"]) if opts["minutes"] else 10

        try:
            hotel = Hotel.objects.get(id=hotel_id)
        except Hotel.DoesNotExist:
            raise CommandError(f"Hotel id={hotel_id} no existe")

        since = timezone.now() - timedelta(minutes=minutes)

        job = OtaSyncJob.objects.create(
            hotel=hotel,
            provider=provider,
            job_type=OtaSyncJob.JobType.PULL_RESERVATIONS,
            status=OtaSyncJob.JobStatus.RUNNING,
            stats={},
        )

        stats = pull_reservations_for_hotel(job, hotel_id, provider, since)
        job.status = OtaSyncJob.JobStatus.SUCCESS
        job.stats = stats
        job.save(update_fields=["status", "stats", "finished_at"])

        self.stdout.write(self.style.SUCCESS(f"JOB {job.id} STATUS: {job.status} | STATS: {job.stats}"))

        logs = list(OtaSyncLog.objects.filter(job=job).order_by("created_at").values("level", "message", "payload", "created_at"))
        if not logs:
            self.stdout.write("(sin logs)")
            return

        self.stdout.write(self.style.MIGRATE_HEADING("Logs:"))
        for l in logs:
            created = l["created_at"].strftime("%H:%M:%S") if l.get("created_at") else ""
            self.stdout.write(f"[{created}] {l['level'].upper()} {l['message']} :: {l.get('payload')}")


