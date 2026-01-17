from celery import shared_task
from django.db import transaction

from .models import OtaRoomMapping, OtaSyncJob, OtaProvider, OtaSyncLog
from .services.ical_importer import import_ics_for_room_mapping  # Mantener para compatibilidad
from .services.ical_sync_service import ICALSyncService
from .services.ari_publisher import push_ari_for_hotel, pull_reservations_for_hotel

# Lazy import para Google Calendar (opcional)
try:
    from .services.google_sync_service import import_events_for_mapping as google_import_events
    GOOGLE_AVAILABLE = True
except ImportError:
    GOOGLE_AVAILABLE = False
    google_import_events = None
from .models import OtaConfig
from django.utils import timezone
from datetime import date, timedelta
import os, json
import redis
from .services.smoobu_sync_service import SmoobuSyncService


@shared_task(bind=True)
def import_all_ics(self):
    """Importa ICS para todos los mapeos activos con URL configurada usando ICALSyncService."""
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
            stats = ICALSyncService.import_reservations(m, job=job)
            job.status = OtaSyncJob.JobStatus.SUCCESS if stats.get("errors", 0) == 0 else OtaSyncJob.JobStatus.FAILED
            job.finished_at = timezone.now()
            job.save(update_fields=["status", "stats", "finished_at"])
        except Exception as e:
            job.status = OtaSyncJob.JobStatus.FAILED
            job.error_message = str(e)
            job.finished_at = timezone.now()
            job.save(update_fields=["status", "error_message", "finished_at"])
        total += 1

    return {"processed_mappings": total}


@shared_task(bind=True)
def schedule_ical_sync(self):
    """Ejecuta sincronización programada de iCal (import/export) para todos los mapeos activos."""
    stats = ICALSyncService.schedule_sync()
    return stats


@shared_task(bind=True)
def import_all_google(self):
    """Importa eventos para todos los mapeos con provider=GOOGLE."""
    if not GOOGLE_AVAILABLE:
        return {"processed_mappings": 0, "error": "google_api_not_installed"}
    
    mappings = OtaRoomMapping.objects.select_related("hotel", "room").filter(
        provider=OtaProvider.GOOGLE,
        is_active=True,
    ).exclude(external_id__isnull=True).exclude(external_id="")

    total = 0
    for m in mappings:
        job = OtaSyncJob.objects.create(
            hotel=m.hotel,
            provider=OtaProvider.GOOGLE,
            job_type=OtaSyncJob.JobType.IMPORT_ICS,
            status=OtaSyncJob.JobStatus.RUNNING,
            stats={"mapping_id": m.id},
        )
        try:
            stats = google_import_events(m, job=job)
            job.status = OtaSyncJob.JobStatus.SUCCESS if stats.get("errors", 0) == 0 else OtaSyncJob.JobStatus.FAILED
            job.finished_at = timezone.now()
            job.save(update_fields=["status", "stats", "finished_at"])
            # Publicar evento para refrescar UI si éxito
            if job.status == OtaSyncJob.JobStatus.SUCCESS:
                try:
                    redis_host = os.environ.get("REDIS_HOST", "redis")
                    r = redis.Redis(host=redis_host, port=6379, db=0)
                    payload = json.dumps({"type": "reservations_updated", "hotel_id": m.hotel_id, "provider": "google"})
                    r.publish("otas:events", payload)
                    r.publish(f"otas:events:{m.hotel_id}", payload)
                except Exception:
                    pass
        except Exception as e:
            job.status = OtaSyncJob.JobStatus.FAILED
            job.error_message = str(e)
            job.finished_at = timezone.now()
            job.save(update_fields=["status", "error_message", "finished_at"])
        total += 1

    return {"processed_mappings": total}

@shared_task(bind=True)
def import_google_for_mapping_task(self, mapping_id: int):
    """Importa eventos para un mapeo específico (usado por webhooks)."""
    if not GOOGLE_AVAILABLE:
        return {}
    mapping = OtaRoomMapping.objects.select_related("hotel", "room").get(id=mapping_id)
    job = OtaSyncJob.objects.create(
        hotel=mapping.hotel,
        provider=OtaProvider.GOOGLE,
        job_type=OtaSyncJob.JobType.IMPORT_ICS,
        status=OtaSyncJob.JobStatus.RUNNING,
        stats={"mapping_id": mapping_id, "trigger": "webhook"},
    )
    try:
        stats = google_import_events(mapping, job=job)
        job.status = OtaSyncJob.JobStatus.SUCCESS if stats.get("errors", 0) == 0 else OtaSyncJob.JobStatus.FAILED
        job.finished_at = timezone.now()
        job.save(update_fields=["status", "stats", "finished_at"])
    except Exception as e:
        job.status = OtaSyncJob.JobStatus.FAILED
        job.error_message = str(e)
        job.finished_at = timezone.now()
        job.save(update_fields=["status", "error_message", "finished_at"])
    return job.stats or {}

@shared_task(bind=True)
def import_ics_for_mapping_task(self, mapping_id: int, job_id: int | None = None):
    """Importa iCal para un mapeo específico usando ICALSyncService."""
    if job_id:
        job = OtaSyncJob.objects.get(id=job_id)
    else:
        mapping = OtaRoomMapping.objects.select_related("hotel").get(id=mapping_id)
        job = OtaSyncJob.objects.create(
            hotel=mapping.hotel,
            provider=OtaProvider.ICAL,
            job_type=OtaSyncJob.JobType.IMPORT_ICS,
            status=OtaSyncJob.JobStatus.RUNNING,
            stats={"mapping_id": mapping_id},
        )
        # Registrar inicio de sincronización en log (solo si creamos el job)
        OtaSyncLog.objects.create(
            job=job,
            level=OtaSyncLog.Level.INFO,
            message="IMPORT_ICS_STARTED",
            payload={
                "mapping_id": mapping_id,
                "hotel_id": mapping.hotel_id,
                "provider": OtaProvider.ICAL,
                "trigger": "task",
            },
        )
    try:
        mapping = OtaRoomMapping.objects.select_related("hotel", "room").get(id=mapping_id)
        stats = ICALSyncService.import_reservations(mapping, job=job)
        job.status = OtaSyncJob.JobStatus.SUCCESS if stats.get("errors", 0) == 0 else OtaSyncJob.JobStatus.FAILED
        job.finished_at = timezone.now()
        job.save(update_fields=["status", "stats", "finished_at"])
        if job.status == OtaSyncJob.JobStatus.SUCCESS:
            try:
                redis_host = os.environ.get("REDIS_HOST", "redis")
                r = redis.Redis(host=redis_host, port=6379, db=0)
                payload = json.dumps({"type": "reservations_updated", "hotel_id": mapping.hotel_id, "provider": "ical"})
                r.publish("otas:events", payload)
                r.publish(f"otas:events:{mapping.hotel_id}", payload)
            except Exception:
                pass
        
        # Registrar finalización (el ICALSyncService ya registra IMPORT_COMPLETED, pero agregamos uno adicional aquí para consistencia)
        if stats.get("errors", 0) == 0:
            OtaSyncLog.objects.create(
                job=job,
                level=OtaSyncLog.Level.INFO,
                message="IMPORT_ICS_TASK_COMPLETED",
                payload={
                    "mapping_id": mapping_id,
                    "stats": stats,
                    "status": "success",
                },
            )
    except Exception as e:
        import traceback
        job.status = OtaSyncJob.JobStatus.FAILED
        job.error_message = str(e)
        job.finished_at = timezone.now()
        job.save(update_fields=["status", "error_message", "finished_at"])
        
        # Registrar error en log con detalles completos
        OtaSyncLog.objects.create(
            job=job,
            level=OtaSyncLog.Level.ERROR,
            message="IMPORT_ICS_TASK_ERROR",
            payload={
                "mapping_id": mapping_id,
                "error": str(e),
                "error_type": type(e).__name__,
                "traceback": traceback.format_exc(),
                "timestamp": timezone.now().isoformat(),
            },
        )
    return job.stats or {}


@shared_task(bind=True)
def push_ari_for_hotel_task(self, hotel_id: int, provider: str, date_from_str: str, date_to_str: str, job_id: int | None = None):
    df = date.fromisoformat(date_from_str)
    dt = date.fromisoformat(date_to_str)
    
    # Si no hay job_id, crear uno nuevo (llamada directa desde task)
    if job_id:
        try:
            job = OtaSyncJob.objects.get(id=job_id)
        except OtaSyncJob.DoesNotExist:
            # Si el job aún no es visible (race condition antes de commit), crear uno de respaldo
            job = OtaSyncJob.objects.create(
                hotel_id=hotel_id,
                provider=provider,
                job_type=OtaSyncJob.JobType.PUSH_ARI,
                status=OtaSyncJob.JobStatus.RUNNING,
                stats={
                    "hotel_id": hotel_id,
                    "provider": provider,
                    "date_from": date_from_str,
                    "date_to": date_to_str,
                    "fallback": "job_not_found",
                },
            )
            OtaSyncLog.objects.create(
                job=job,
                level=OtaSyncLog.Level.WARNING,
                message="PUSH_ARI_JOB_MISSING_CREATED",
                payload={
                    "hotel_id": hotel_id,
                    "provider": provider,
                    "date_from": date_from_str,
                    "date_to": date_to_str,
                    "note": "Original job_id no encontrado; creado job de respaldo",
                },
            )
    else:
        job = OtaSyncJob.objects.create(
            hotel_id=hotel_id,
            provider=provider,
            job_type=OtaSyncJob.JobType.PUSH_ARI,
            status=OtaSyncJob.JobStatus.RUNNING,
            stats={"hotel_id": hotel_id, "provider": provider, "date_from": date_from_str, "date_to": date_to_str},
        )
        
        # Registrar inicio de sincronización en log (solo si creamos el job aquí)
        OtaSyncLog.objects.create(
            job=job,
            level=OtaSyncLog.Level.INFO,
            message="PUSH_ARI_STARTED",
            payload={
                "hotel_id": hotel_id,
                "provider": provider,
                "date_from": date_from_str,
                "date_to": date_to_str,
                "trigger": "task",
            },
        )
    
    try:
        stats = push_ari_for_hotel(job, hotel_id, provider, df, dt)
        job.status = OtaSyncJob.JobStatus.SUCCESS
        job.stats = stats
        job.finished_at = timezone.now()
        
        # Registrar éxito en log
        OtaSyncLog.objects.create(
            job=job,
            level=OtaSyncLog.Level.INFO,
            message="PUSH_ARI_COMPLETED",
            payload={
                "hotel_id": hotel_id,
                "provider": provider,
                "stats": stats,
                "status": "success",
            },
        )
    except Exception as e:
        import traceback
        job.status = OtaSyncJob.JobStatus.FAILED
        job.error_message = str(e)
        job.finished_at = timezone.now()
        
        # Registrar error en log con detalles completos
        OtaSyncLog.objects.create(
            job=job,
            level=OtaSyncLog.Level.ERROR,
            message="PUSH_ARI_ERROR",
            payload={
                "hotel_id": hotel_id,
                "provider": provider,
                "error": str(e),
                "error_type": type(e).__name__,
                "traceback": traceback.format_exc(),
                "timestamp": timezone.now().isoformat(),
            },
        )
    finally:
        job.save(update_fields=["status", "stats", "error_message", "finished_at"])
    return job.stats or {}


# PULL RESERVATIONS
@shared_task(bind=True)
def pull_reservations_for_hotel_task(self, hotel_id: int, provider: str, since_iso: str | None = None):
    since = timezone.now() - timedelta(minutes=10) if not since_iso else timezone.datetime.fromisoformat(since_iso)
    job = OtaSyncJob.objects.create(
        hotel_id=hotel_id,
        provider=provider,
        job_type=OtaSyncJob.JobType.PULL_RESERVATIONS,
        status=OtaSyncJob.JobStatus.RUNNING,
        stats={"hotel_id": hotel_id, "provider": provider, "since": since.isoformat()},
    )
    
    # Registrar inicio de sincronización en log
    OtaSyncLog.objects.create(
        job=job,
        level=OtaSyncLog.Level.INFO,
        message="PULL_RES_STARTED",
        payload={
            "hotel_id": hotel_id,
            "provider": provider,
            "since": since.isoformat(),
            "trigger": "task",
        },
    )
    
    try:
        stats = pull_reservations_for_hotel(job, hotel_id, provider, since)
        job.status = OtaSyncJob.JobStatus.SUCCESS
        job.stats = stats
        job.finished_at = timezone.now()
        
        # Registrar éxito en log
        OtaSyncLog.objects.create(
            job=job,
            level=OtaSyncLog.Level.INFO,
            message="PULL_RES_COMPLETED",
            payload={
                "hotel_id": hotel_id,
                "provider": provider,
                "stats": stats,
                "status": "success",
            },
        )
    except Exception as e:
        import traceback
        job.status = OtaSyncJob.JobStatus.FAILED
        job.error_message = str(e)
        job.finished_at = timezone.now()
        
        # Registrar error en log con detalles completos
        OtaSyncLog.objects.create(
            job=job,
            level=OtaSyncLog.Level.ERROR,
            message="PULL_RES_ERROR",
            payload={
                "hotel_id": hotel_id,
                "provider": provider,
                "error": str(e),
                "error_type": type(e).__name__,
                "traceback": traceback.format_exc(),
                "timestamp": timezone.now().isoformat(),
            },
        )
    finally:
        job.save(update_fields=["status", "stats", "error_message", "finished_at"])
    return job.stats or {}


@shared_task(bind=True)
def pull_reservations_all_hotels_task(self):
    configs = OtaConfig.objects.filter(is_active=True, provider__in=[OtaProvider.BOOKING, OtaProvider.AIRBNB]).values("hotel_id", "provider").distinct()
    total = 0
    for cfg in configs:
        pull_reservations_for_hotel_task.delay(cfg["hotel_id"], cfg["provider"], None)
        total += 1
    return {"scheduled": total}


# ===== SMOOBU (push) =====
@shared_task(bind=True)
def sync_smoobu_for_hotel_task(self, hotel_id: int, days_ahead: int = 90, job_id: int | None = None):
    """
    Empuja bloqueos (y opcionalmente rates) desde AlojaSys hacia Smoobu para un hotel.
    """
    if job_id:
        try:
            job = OtaSyncJob.objects.get(id=job_id)
        except OtaSyncJob.DoesNotExist:
            job = OtaSyncJob.objects.create(
                hotel_id=hotel_id,
                provider=OtaProvider.SMOOBU,
                job_type=OtaSyncJob.JobType.SYNC_SMOOBU,
                status=OtaSyncJob.JobStatus.RUNNING,
                stats={"hotel_id": hotel_id, "provider": OtaProvider.SMOOBU, "days_ahead": days_ahead, "fallback": "job_not_found"},
            )
    else:
        job = OtaSyncJob.objects.create(
            hotel_id=hotel_id,
            provider=OtaProvider.SMOOBU,
            job_type=OtaSyncJob.JobType.SYNC_SMOOBU,
            status=OtaSyncJob.JobStatus.RUNNING,
            stats={"hotel_id": hotel_id, "provider": OtaProvider.SMOOBU, "days_ahead": days_ahead},
        )

    OtaSyncLog.objects.create(
        job=job,
        level=OtaSyncLog.Level.INFO,
        message="SMOOBU_SYNC_STARTED",
        payload={"hotel_id": hotel_id, "days_ahead": days_ahead, "trigger": "task"},
    )

    try:
        result = SmoobuSyncService.sync_hotel(int(hotel_id), days_ahead=int(days_ahead))
        job.status = OtaSyncJob.JobStatus.SUCCESS if result.get("status") == "ok" else OtaSyncJob.JobStatus.FAILED
        job.stats = {**(job.stats or {}), **result}
        job.finished_at = timezone.now()
        OtaSyncLog.objects.create(
            job=job,
            level=OtaSyncLog.Level.INFO if job.status == OtaSyncJob.JobStatus.SUCCESS else OtaSyncLog.Level.WARNING,
            message="SMOOBU_SYNC_COMPLETED",
            payload={"hotel_id": hotel_id, "result": result},
        )
    except Exception as e:
        import traceback
        job.status = OtaSyncJob.JobStatus.FAILED
        job.error_message = str(e)
        job.finished_at = timezone.now()
        OtaSyncLog.objects.create(
            job=job,
            level=OtaSyncLog.Level.ERROR,
            message="SMOOBU_SYNC_ERROR",
            payload={"hotel_id": hotel_id, "error": str(e), "traceback": traceback.format_exc()},
        )
    finally:
        job.save(update_fields=["status", "stats", "error_message", "finished_at"])
    return job.stats or {}

