from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone
from datetime import timedelta

from apps.otas.models import OtaSyncJob, OtaProvider, OtaSyncLog
from apps.core.models import Hotel
from apps.otas.services.ari_publisher import push_ari_for_hotel


class Command(BaseCommand):
    help = "Dispara un PUSH ARI para un hotel/proveedor y muestra el job y sus logs"

    def add_arguments(self, parser):
        parser.add_argument("--hotel-id", type=int, required=True)
        parser.add_argument("--provider", type=str, default=OtaProvider.BOOKING)
        parser.add_argument("--days", type=int, default=7)

    def handle(self, *args, **opts):
        hotel_id = opts["hotel_id"]
        provider = opts["provider"]
        days = int(opts["days"]) if opts["days"] else 7

        try:
            hotel = Hotel.objects.get(id=hotel_id)
        except Hotel.DoesNotExist:
            raise CommandError(f"Hotel id={hotel_id} no existe")

        today = timezone.now().date()
        date_from = today + timedelta(days=1)
        date_to = today + timedelta(days=days)

        self.stdout.write(self.style.WARNING(
            f"PUSH ARI → hotel={hotel.name} ({hotel_id}) provider={provider} rango={date_from}..{date_to}"
        ))

        job = OtaSyncJob.objects.create(
            hotel=hotel,
            provider=provider,
            job_type=OtaSyncJob.JobType.PUSH_ARI,
            status=OtaSyncJob.JobStatus.RUNNING,
            stats={},
        )

        stats = push_ari_for_hotel(job, hotel_id, provider, date_from, date_to)
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


