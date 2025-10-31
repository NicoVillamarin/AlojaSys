from celery import shared_task
from django.db import transaction

from .models import OtaRoomMapping, OtaSyncJob, OtaProvider
from .services.ical_importer import import_ics_for_room_mapping
from .services.ari_publisher import push_ari_for_hotel
from datetime import date, timedelta


@shared_task(bind=True)
def import_all_ics(self):
    """Importa ICS para todos los mapeos activos con URL configurada."""
    mappings = OtaRoomMapping.objects.select_related("hotel", "room").filter(
        provider=OtaProvider.ICAL,
        is_active=True,
    ).exclude(ical_in_url__isnull=True).exclude(ical_in_url="")

    total = 0
    for m in mappings:
        job = OtaSyncJob.objects.create(
            hotel=m.hotel,
            provider=OtaProvider.ICAL,
            job_type=OtaSyncJob.JobType.IMPORT_ICS,
            status=OtaSyncJob.JobStatus.RUNNING,
            stats={"mapping_id": m.id},
        )
        try:
            stats = import_ics_for_room_mapping(m.id, job=job)
            job.status = OtaSyncJob.JobStatus.SUCCESS
            job.stats = {**(job.stats or {}), **(stats or {})}
        except Exception as e:
            job.status = OtaSyncJob.JobStatus.FAILED
            job.error_message = str(e)
        finally:
            job.save(update_fields=["status", "stats", "error_message", "finished_at"])
        total += 1

    return {"processed_mappings": total}


@shared_task(bind=True)
def import_ics_for_mapping_task(self, mapping_id: int, job_id: int | None = None):
    if job_id:
        job = OtaSyncJob.objects.get(id=job_id)
    else:
        job = OtaSyncJob.objects.create(
            provider=OtaProvider.ICAL,
            job_type=OtaSyncJob.JobType.IMPORT_ICS,
            status=OtaSyncJob.JobStatus.RUNNING,
            stats={"mapping_id": mapping_id},
        )
    try:
        stats = import_ics_for_room_mapping(mapping_id, job=job)
        job.status = OtaSyncJob.JobStatus.SUCCESS
        job.stats = {**(job.stats or {}), **(stats or {})}
    except Exception as e:
        job.status = OtaSyncJob.JobStatus.FAILED
        job.error_message = str(e)
    finally:
        job.save(update_fields=["status", "stats", "error_message", "finished_at"])
    return job.stats or {}


@shared_task(bind=True)
def push_ari_for_hotel_task(self, hotel_id: int, provider: str, date_from_str: str, date_to_str: str):
    df = date.fromisoformat(date_from_str)
    dt = date.fromisoformat(date_to_str)
    job = OtaSyncJob.objects.create(
        hotel_id=hotel_id,
        provider=provider,
        job_type=OtaSyncJob.JobType.PUSH_ARI,
        status=OtaSyncJob.JobStatus.RUNNING,
        stats={"hotel_id": hotel_id, "provider": provider, "date_from": date_from_str, "date_to": date_to_str},
    )
    try:
        stats = push_ari_for_hotel(job, hotel_id, provider, df, dt)
        job.status = OtaSyncJob.JobStatus.SUCCESS
        job.stats = stats
    except Exception as e:
        job.status = OtaSyncJob.JobStatus.FAILED
        job.error_message = str(e)
    finally:
        job.save(update_fields=["status", "stats", "error_message", "finished_at"])
    return job.stats or {}


