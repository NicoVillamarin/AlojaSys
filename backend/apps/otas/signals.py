from __future__ import annotations

from datetime import timedelta, date

from django.db.models.signals import post_save, post_delete
from django.db import transaction
from django.dispatch import receiver
from django.core.cache import cache
from django.utils import timezone

from apps.reservations.models import Reservation
from .models import OtaConfig, OtaProvider, OtaSyncJob, OtaSyncLog
from .tasks import push_ari_for_hotel_task


def _queue_push_ari_for_hotel(hotel_id: int, provider: str, days_ahead: int = 30, trigger_info: dict = None) -> None:
    # Evitar tormenta de eventos: coalescer por 60s
    throttle_key = f"otas:ari:throttle:{hotel_id}:{provider}"
    if cache.get(throttle_key):
        return
    cache.set(throttle_key, True, timeout=60)

    today = date.today()
    df = today
    dt = today + timedelta(days=days_ahead)
    
    # Crear job de sincronización para auditoría
    job = OtaSyncJob.objects.create(
        hotel_id=hotel_id,
        provider=provider,
        job_type=OtaSyncJob.JobType.PUSH_ARI,
        status=OtaSyncJob.JobStatus.RUNNING,
        stats={
            "hotel_id": hotel_id,
            "provider": provider,
            "date_from": df.isoformat(),
            "date_to": dt.isoformat(),
            "trigger": "signal",
            **(trigger_info or {}),
        },
    )
    
    # Registrar inicio de sincronización desde signal en log
    OtaSyncLog.objects.create(
        job=job,
        level=OtaSyncLog.Level.INFO,
        message="PUSH_ARI_STARTED",
        payload={
            "hotel_id": hotel_id,
            "provider": provider,
            "date_from": df.isoformat(),
            "date_to": dt.isoformat(),
            "trigger": "signal",
            "trigger_info": trigger_info or {},
            "timestamp": timezone.now().isoformat(),
        },
    )
    
    # Enviar job_id a la task solo tras el commit para evitar race conditions
    transaction.on_commit(lambda: push_ari_for_hotel_task.delay(
        hotel_id, provider, df.isoformat(), dt.isoformat(), job_id=job.id
    ))


def _enqueue_for_active_providers(hotel_id: int, trigger_info: dict = None) -> None:
    providers = list(
        OtaConfig.objects.filter(hotel_id=hotel_id, is_active=True, provider__in=[OtaProvider.BOOKING, OtaProvider.AIRBNB])
        .values_list("provider", flat=True)
    )
    for p in providers:
        _queue_push_ari_for_hotel(hotel_id, p, trigger_info=trigger_info)


@receiver(post_save, sender=Reservation)
def reservation_saved(sender, instance: Reservation, **kwargs):
    if not instance.hotel_id:
        return
    
    # Información del trigger para auditoría
    trigger_info = {
        "action": "reservation_saved",
        "reservation_id": instance.id,
        "reservation_status": instance.status,
        "reservation_channel": instance.channel,
        "check_in": instance.check_in.isoformat() if instance.check_in else None,
        "check_out": instance.check_out.isoformat() if instance.check_out else None,
        "created": kwargs.get("created", False),
    }
    
    _enqueue_for_active_providers(instance.hotel_id, trigger_info=trigger_info)


@receiver(post_delete, sender=Reservation)
def reservation_deleted(sender, instance: Reservation, **kwargs):
    if not instance.hotel_id:
        return
    
    # Información del trigger para auditoría
    trigger_info = {
        "action": "reservation_deleted",
        "reservation_id": instance.id,
        "reservation_status": instance.status,
        "reservation_channel": instance.channel,
        "check_in": instance.check_in.isoformat() if instance.check_in else None,
        "check_out": instance.check_out.isoformat() if instance.check_out else None,
    }
    
    _enqueue_for_active_providers(instance.hotel_id, trigger_info=trigger_info)


