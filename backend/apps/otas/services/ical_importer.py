from datetime import date, datetime, timedelta

import requests
from icalendar import Calendar

from django.db import transaction
from django.utils import timezone

from apps.reservations.models import RoomBlock, RoomBlockType
from ..models import OtaRoomMapping, OtaImportedEvent, OtaProvider, OtaSyncJob, OtaSyncLog


def _to_date(value) -> date:
    if hasattr(value, "dt"):
        value = value.dt
    if isinstance(value, datetime):
        return value.date()
    return value


def _normalize_range(start: date, end: date) -> tuple[date, date]:
    # Asegurar rango válido: end > start
    if end <= start:
        end = start + timedelta(days=1)
    return start, end


@transaction.atomic
def import_ics_for_room_mapping(mapping_id: int, job: OtaSyncJob | None = None) -> dict:
    mapping = OtaRoomMapping.objects.select_related("hotel", "room").get(id=mapping_id)
    # Respetar sync_direction: si es "export" solo, no importar
    if not mapping.is_active or not mapping.ical_in_url:
        return {"processed": 0, "created": 0, "updated": 0, "skipped": 0}
    if mapping.sync_direction == OtaRoomMapping.SyncDirection.EXPORT:
        return {"processed": 0, "created": 0, "updated": 0, "skipped": 0, "reason": "sync_direction is export only"}

    stats = {"processed": 0, "created": 0, "updated": 0, "skipped": 0}

    if job:
        OtaSyncLog.objects.create(
            job=job,
            level=OtaSyncLog.Level.INFO,
            message="IMPORT_STARTED",
            payload={"mapping_id": mapping.id, "url": mapping.ical_in_url},
        )

    try:
        resp = requests.get(mapping.ical_in_url, timeout=20)
        resp.raise_for_status()
    except Exception as e:
        if job:
            OtaSyncLog.objects.create(job=job, level=OtaSyncLog.Level.ERROR, message="Error descargando ICS", payload={"error": str(e), "url": mapping.ical_in_url})
        return stats

    cal = Calendar.from_ical(resp.content)

    for component in cal.walk("VEVENT"):
        stats["processed"] += 1

        uid = str(component.get("uid")) if component.get("uid") else None
        dtstart = _to_date(component.get("dtstart").dt) if component.get("dtstart") else None
        dtend = _to_date(component.get("dtend").dt) if component.get("dtend") else None
        summary = str(component.get("summary")) if component.get("summary") else None

        if not uid or not dtstart or not dtend:
            stats["skipped"] += 1
            continue

        start, end = _normalize_range(dtstart, dtend)

        imported, created = OtaImportedEvent.objects.get_or_create(
            hotel=mapping.hotel,
            room=mapping.room,
            provider=OtaProvider.ICAL,
            uid=uid,
            defaults={
                "dtstart": start,
                "dtend": end,
                "source_url": mapping.ical_in_url,
                "summary": summary,
            },
        )

        if not created:
            changed = False
            if imported.dtstart != start or imported.dtend != end or imported.summary != summary:
                imported.dtstart = start
                imported.dtend = end
                imported.summary = summary
                changed = True
            if imported.source_url != mapping.ical_in_url:
                imported.source_url = mapping.ical_in_url
                changed = True
            if changed:
                imported.save(update_fields=["dtstart", "dtend", "summary", "source_url", "last_seen"])
                stats["updated"] += 1
            else:
                stats["skipped"] += 1
        else:
            stats["created"] += 1

        # Crear/asegurar RoomBlock (bloqueo HOLD)
        # Nota: RoomBlock requiere end_date > start_date
        start, end = _normalize_range(start, end)
        RoomBlock.objects.update_or_create(
            hotel=mapping.hotel,
            room=mapping.room,
            start_date=start,
            end_date=end,
            defaults={
                "block_type": RoomBlockType.HOLD,
                "reason": f"OTA iCal UID {uid}",
                "is_active": True,
            },
        )

    if job:
        job.stats = {**(job.stats or {}), **stats}
        job.save(update_fields=["stats"])
        OtaSyncLog.objects.create(
            job=job,
            level=OtaSyncLog.Level.INFO,
            message="IMPORT_COMPLETED",
            payload={"mapping_id": mapping.id, **stats},
        )

    # Actualizar last_synced si hubo procesamiento exitoso
    if stats["processed"] > 0:
        mapping.last_synced = timezone.now()
        mapping.save(update_fields=["last_synced"])

    return stats

