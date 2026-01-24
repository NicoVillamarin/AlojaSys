from __future__ import annotations

from datetime import date, datetime, timedelta
from typing import Any, Dict, Optional

from django.db import transaction
from django.utils import timezone

from apps.reservations.models import Reservation, ReservationStatus, ReservationChannel
from apps.otas.models import OtaRoomMapping, OtaSyncJob, OtaSyncLog, OtaProvider, OtaImportedEvent
from apps.notifications.services import NotificationService
from .ota_reservation_service import OtaReservationService

# Lazy import para evitar errores si no están instaladas las dependencias de Google
try:
    from ..adapters.google_calendar_adapter import list_events, watch_calendar, insert_event, update_event, delete_event, get_calendar
    GOOGLE_AVAILABLE = True
except ImportError:
    GOOGLE_AVAILABLE = False
    list_events = None
    watch_calendar = None
    insert_event = None
    update_event = None
    delete_event = None
    get_calendar = None


def _event_dates(google_event: Dict[str, Any]) -> tuple[date, date]:
    """Convierte start/end de Google a fechas de check-in/check-out.

    Preferencia: interpretar eventos all‑day como "noches" del PMS.
    Esto significa que si en Google marcás 25–26 (dos días), en el PMS
    será check-in=25 y check-out=26 (1 noche). Google envía end exclusivo
    para all‑day, por lo que restamos 1 día.
    """
    from datetime import timedelta

    def _to_date(d: Dict[str, str]) -> date:
        if 'date' in d:  # all-day event
            return date.fromisoformat(d['date'])
        # dateTime with timezone
        return datetime.fromisoformat(d['dateTime'].replace('Z', '+00:00')).date()

    start_is_date = 'date' in google_event['start']
    end_is_date = 'date' in google_event['end']

    start = _to_date(google_event['start'])
    end = _to_date(google_event['end'])

    # Ajuste para all‑day: Google usa end exclusivo → restar 1 día
    if start_is_date and end_is_date:
        end = end - timedelta(days=1)

    return start, end


@transaction.atomic
def import_events_for_mapping(mapping: OtaRoomMapping, job: Optional[OtaSyncJob] = None) -> Dict[str, Any]:
    """Importa eventos de Google Calendar como reservas del PMS.

    mapping.external_id debe contener el Calendar ID.
    OtaConfig.credentials debe contener `service_account_json` con las credenciales.
    """
    if not GOOGLE_AVAILABLE:
        return {"processed": 0, "created": 0, "updated": 0, "errors": 1, "reason": "google_api_not_installed"}
    
    stats: Dict[str, Any] = {"processed": 0, "created": 0, "updated": 0, "errors": 0}

    # Obtener credenciales desde OtaConfig del hotel/proveedor
    ota_config = mapping.hotel.ota_configs.filter(provider=OtaProvider.GOOGLE, is_active=True).first()
    if not ota_config:
        return {**stats, "reason": "no_active_google_config"}

    creds_container = ota_config.credentials or {}
    # Aceptar dos formatos: {"service_account_json": {...}} o el JSON de SA plano
    if isinstance(creds_container, dict) and "service_account_json" in creds_container:
        creds = creds_container.get("service_account_json")
    else:
        creds = creds_container  # asumir que ya es el JSON de la service account
    # Validación mínima
    if not isinstance(creds, dict) or creds.get("type") != "service_account":
        return {**stats, "reason": "missing_or_invalid_service_account_json"}

    calendar_id = mapping.external_id
    if not calendar_id:
        return {**stats, "reason": "missing_calendar_id_in_mapping"}

    # Listar eventos (full o incremental con syncToken)
    try:
        if mapping.google_sync_token:
            events = list_events(creds, calendar_id, sync_token=mapping.google_sync_token)
        else:
            events = list_events(creds, calendar_id)
    except Exception as e:
        stats["errors"] += 1
        if job:
            OtaSyncLog.objects.create(job=job, level=OtaSyncLog.Level.ERROR, message="GOOGLE_IMPORT_ERROR", payload={"error": str(e)})
        return stats

    seen_uids: set[str] = set()

    for ev in events.get('items', []):
        # Manejar eventos cancelados (Google envía status=cancelled y sin start/end)
        if ev.get('status') == 'cancelled':
            uid = ev.get('id')
            if uid:
                seen_uids.add(uid)
                try:
                    res = Reservation.objects.filter(hotel=mapping.hotel, room=mapping.room, external_id=uid).first()
                    if res and res.status != ReservationStatus.CANCELLED:
                        res.status = ReservationStatus.CANCELLED
                        res.notes = (res.notes or "") + "\nCancelada por Google Calendar (evento eliminado)."
                        res.save(update_fields=["status", "notes"], skip_clean=True)
                        if job:
                            OtaSyncLog.objects.create(
                                job=job,
                                level=OtaSyncLog.Level.INFO,
                                message="GOOGLE_EVENT_DELETED_CANCELLED",
                                payload={"external_id": uid, "reservation_id": res.id},
                            )
                    # Borrar tracking si existe
                    OtaImportedEvent.objects.filter(hotel=mapping.hotel, room=mapping.room, provider=OtaProvider.GOOGLE, uid=uid).delete()
                except Exception as e:
                    if job:
                        OtaSyncLog.objects.create(job=job, level=OtaSyncLog.Level.ERROR, message="GOOGLE_EVENT_DELETE_ERROR", payload={"uid": uid, "error": str(e)})
            continue
        # Si el evento fue creado por AlojaSys (extendedProperties.private.alojasys_reservation_id), no importar para evitar duplicados
        try:
            ext_priv = ev.get('extendedProperties', {}).get('private', {})
            if ext_priv.get('alojasys_reservation_id'):
                # Skip: evento originado en el PMS
                seen_uids.add(ev.get('id') or '')
                continue
        except Exception:
            pass

        # Solo eventos con fechas
        if 'start' not in ev or 'end' not in ev:
            continue

        stats['processed'] += 1
        uid = ev.get('id')
        if not uid:
            continue
        seen_uids.add(uid)
        summary = ev.get('summary') or ''

        # Si la descripción indica una reserva creada por AlojaSys, no importar
        desc = ev.get('description') or ''
        if 'AlojaSys Reservation #' in desc:
            seen_uids.add(uid)
            continue
        check_in, check_out = _event_dates(ev)

        # Extraer nombre del huésped del summary (similar a iCal)
        guest_name = summary or "Google Guest"
        if summary:
            # Si tiene formato "Reserva - Nombre" o "Reserva- Nombre", extraer el nombre
            if ' - ' in summary:
                parts = summary.split(' - ', 1)
                if len(parts) > 1 and parts[0].strip().lower().startswith('reserva'):
                    guest_name = parts[1].strip()  # Tomar la parte después de "Reserva - "
                else:
                    guest_name = parts[0].strip()  # Si no empieza con "Reserva", tomar la primera parte
            elif '-' in summary and not summary.startswith('-'):
                # Formato "Reserva-Nombre" (sin espacio)
                parts = summary.split('-', 1)
                if len(parts) > 1 and parts[0].strip().lower().startswith('reserva'):
                    guest_name = parts[1].strip()  # Tomar la parte después de "Reserva-"
                else:
                    guest_name = summary  # Si no empieza con "Reserva", usar el summary completo
            else:
                guest_name = summary  # Si no tiene separador, usar el summary completo

        # Upsert de reserva (reutiliza canal OTHER para Google)
        try:
            result = OtaReservationService.upsert_reservation(
                hotel=mapping.hotel,
                room=mapping.room,
                external_id=uid,
                channel=ReservationChannel.OTHER,
                check_in=check_in,
                check_out=check_out,
                guests=1,
                guests_data=[{"name": guest_name, "email": "", "is_primary": True}],
                notes=f"Importado desde Google Calendar: {summary}",
                payment_info=None,
                auto_confirm=False,
                provider_name=OtaProvider.GOOGLE.label,  # "Google Calendar"
            )
            # Registrar/actualizar evento importado para detectar eliminaciones futuras
            imported, created = OtaImportedEvent.objects.get_or_create(
                hotel=mapping.hotel,
                room=mapping.room,
                provider=OtaProvider.GOOGLE,
                uid=uid,
                defaults={
                    "dtstart": check_in,
                    "dtend": check_out,
                    "source_url": f"google://{mapping.external_id}",
                    "summary": summary,
                },
            )
            if not created:
                changed = False
                if imported.dtstart != check_in or imported.dtend != check_out or imported.summary != summary:
                    imported.dtstart = check_in
                    imported.dtend = check_out
                    imported.summary = summary
                    changed = True
                if imported.source_url != f"google://{mapping.external_id}":
                    imported.source_url = f"google://{mapping.external_id}"
                    changed = True
                if changed:
                    imported.save(update_fields=["dtstart", "dtend", "summary", "source_url", "last_seen"])
            if result.get("created"):
                stats['created'] += 1
            else:
                stats['updated'] += 1

            # Notificación: si no fue "created" pero el evento importado sí es nuevo, notificar
            # (caso: ya existía una reserva con ese external_id pero es la primera vez que vemos este UID de Google)
            if (not result.get("created")) and created:
                try:
                    NotificationService.create_ota_reservation_notification(
                        provider_name=OtaProvider.GOOGLE.label,
                        reservation_code=f"RES-{{}}".format(
                            Reservation.objects.filter(
                                hotel=mapping.hotel, room=mapping.room, external_id=uid
                            ).values_list('id', flat=True).first() or "?"
                        ),
                        room_name=mapping.room.name or f"Habitación {mapping.room.number}",
                        check_in_date=check_in.strftime("%d/%m/%Y"),
                        check_out_date=check_out.strftime("%d/%m/%Y"),
                        guest_name=guest_name,
                        hotel_id=mapping.hotel.id,
                        reservation_id=Reservation.objects.filter(
                            hotel=mapping.hotel, room=mapping.room, external_id=uid
                        ).values_list('id', flat=True).first(),
                        external_id=uid,
                        overbooking=False,
                    )
                except Exception:
                    pass
        except Exception as e:
            stats['errors'] += 1
            if job:
                OtaSyncLog.objects.create(
                    job=job,
                    level=OtaSyncLog.Level.ERROR,
                    message="GOOGLE_EVENT_IMPORT_ERROR",
                    payload={"event_id": uid, "error": str(e)},
                )

    # Detectar eventos eliminados en Google y cancelar la reserva asociada (para modo full sync)
    try:
        existing = OtaImportedEvent.objects.filter(
            hotel=mapping.hotel,
            room=mapping.room,
            provider=OtaProvider.GOOGLE,
        )
        for imp in existing:
            if imp.uid not in seen_uids:
                try:
                    res = Reservation.objects.filter(
                        hotel=mapping.hotel,
                        room=mapping.room,
                        external_id=imp.uid,
                    ).first()
                    if res and res.status != ReservationStatus.CANCELLED:
                        res.status = ReservationStatus.CANCELLED
                        res.notes = (res.notes or "") + "\nCancelada por Google Calendar (evento eliminado)."
                        res.save(update_fields=["status", "notes"], skip_clean=True)
                        if job:
                            OtaSyncLog.objects.create(
                                job=job,
                                level=OtaSyncLog.Level.INFO,
                                message="GOOGLE_EVENT_DELETED_CANCELLED",
                                payload={"external_id": imp.uid, "reservation_id": res.id},
                            )
                    imp.delete()
                except Exception as e:
                    if job:
                        OtaSyncLog.objects.create(
                            job=job,
                            level=OtaSyncLog.Level.ERROR,
                            message="GOOGLE_EVENT_DELETE_ERROR",
                            payload={"uid": imp.uid, "error": str(e)},
                        )
    except Exception as e:
        if job:
            OtaSyncLog.objects.create(job=job, level=OtaSyncLog.Level.ERROR, message="GOOGLE_DELETE_SCAN_ERROR", payload={"error": str(e)})

    # Salvaguarda adicional: cancelar reservas importadas desde Google cuyo external_id ya no aparece
    try:
        missing_reservations = Reservation.objects.filter(
            hotel=mapping.hotel,
            room=mapping.room,
            channel=ReservationChannel.OTHER,
            external_id__isnull=False,
            notes__icontains="Google Calendar",
        ).exclude(external_id__in=list(seen_uids))

        for res in missing_reservations:
            if res.status != ReservationStatus.CANCELLED:
                res.status = ReservationStatus.CANCELLED
                res.notes = (res.notes or "") + "\nCancelada por Google Calendar (evento eliminado - fallback)."
                res.save(update_fields=["status", "notes"], skip_clean=True)
                if job:
                    OtaSyncLog.objects.create(
                        job=job,
                        level=OtaSyncLog.Level.INFO,
                        message="GOOGLE_EVENT_DELETED_CANCELLED_FALLBACK",
                        payload={"external_id": res.external_id, "reservation_id": res.id},
                    )
    except Exception as e:
        if job:
            OtaSyncLog.objects.create(job=job, level=OtaSyncLog.Level.ERROR, message="GOOGLE_DELETE_FALLBACK_ERROR", payload={"error": str(e)})

    # Actualizar last_synced
    mapping.last_synced = timezone.now()
    mapping.save(update_fields=["last_synced"])

    if job:
        OtaSyncLog.objects.create(job=job, level=OtaSyncLog.Level.INFO, message="GOOGLE_IMPORT_COMPLETED", payload={**stats})

    # Guardar nextSyncToken si existe (para incremental en siguientes corridas)
    try:
        next_token = events.get('nextSyncToken')
        if next_token:
            mapping.google_sync_token = next_token
            mapping.save(update_fields=["google_sync_token"])
    except Exception:
        pass

    return stats


def enable_webhook_watch(mapping: OtaRoomMapping, base_callback_url: str) -> Dict[str, Any]:
    """Habilita un canal de watch (webhook) para un mapping de Google.

    base_callback_url: ej. https://tu-dominio.com (sin slash final)
    """
    if not GOOGLE_AVAILABLE:
        return {"status": "error", "reason": "google_api_not_installed"}

    ota_config = mapping.hotel.ota_configs.filter(provider=OtaProvider.GOOGLE, is_active=True).first()
    if not ota_config:
        return {"status": "error", "reason": "no_active_google_config"}

    creds_container = ota_config.credentials or {}
    if isinstance(creds_container, dict) and "service_account_json" in creds_container:
        creds = creds_container.get("service_account_json")
    else:
        creds = creds_container
    if not isinstance(creds, dict) or creds.get("type") != "service_account":
        return {"status": "error", "reason": "missing_or_invalid_service_account_json"}

    import uuid
    from django.utils import timezone

    channel_id = str(uuid.uuid4())
    token = str(uuid.uuid4()).replace("-", "")[:32]
    address = f"{base_callback_url}/api/otas/google/webhooks/notify/"

    resp = watch_calendar(creds, mapping.external_id, address, channel_id, token)
    resource_id = resp.get("resourceId")
    expiration_ms = resp.get("expiration")
    expiration_dt = None
    if expiration_ms:
        try:
            expiration_dt = timezone.datetime.fromtimestamp(int(expiration_ms) / 1000, tz=timezone.utc)
        except Exception:
            expiration_dt = None

    mapping.google_watch_channel_id = channel_id
    mapping.google_resource_id = resource_id
    mapping.google_watch_expiration = expiration_dt
    mapping.google_webhook_token = token
    mapping.save(update_fields=[
        "google_watch_channel_id",
        "google_resource_id",
        "google_watch_expiration",
        "google_webhook_token",
    ])

    return {"status": "ok", "channel_id": channel_id, "resource_id": resource_id, "expiration": expiration_ms}


def export_reservation_to_google(reservation: Reservation) -> Dict[str, Any]:
    """Exporta una reserva a Google Calendar (crea/actualiza evento).
    
    Busca mapeos activos de Google para la habitación y exporta la reserva.
    """
    import logging
    logger = logging.getLogger(__name__)
    
    if not GOOGLE_AVAILABLE:
        logger.warning(f"Reservation {reservation.id}: Google API not installed")
        return {"status": "error", "reason": "google_api_not_installed"}
    
    # Solo exportar reservas confirmadas
    if reservation.status != ReservationStatus.CONFIRMED:
        logger.debug(f"Reservation {reservation.id}: Status is {reservation.status}, skipping export")
        return {"status": "skipped", "reason": "reservation_not_confirmed"}
    
    # Buscar mapeos Google activos para esta habitación con export habilitado
    mappings = OtaRoomMapping.objects.filter(
        hotel=reservation.hotel,
        room=reservation.room,
        provider=OtaProvider.GOOGLE,
        is_active=True,
        sync_direction__in=[OtaRoomMapping.SyncDirection.EXPORT, OtaRoomMapping.SyncDirection.BOTH],
    ).exclude(external_id__isnull=True).exclude(external_id="")
    
    if not mappings.exists():
        logger.warning(f"Reservation {reservation.id}: No Google mappings found for room {reservation.room_id} with EXPORT/BOTH direction")
        return {"status": "skipped", "reason": "no_google_mappings"}
    
    # Obtener credenciales desde OtaConfig
    ota_config = reservation.hotel.ota_configs.filter(provider=OtaProvider.GOOGLE, is_active=True).first()
    if not ota_config:
        return {"status": "error", "reason": "no_active_google_config"}
    
    creds_container = ota_config.credentials or {}
    if isinstance(creds_container, dict) and "service_account_json" in creds_container:
        creds = creds_container.get("service_account_json")
    else:
        creds = creds_container
    if not isinstance(creds, dict) or creds.get("type") != "service_account":
        return {"status": "error", "reason": "missing_or_invalid_service_account_json"}
    
    results = []

    def _find_existing_event_id(calendar_id: str) -> str | None:
        """Busca si ya existe un evento en el calendario para esta reserva.
        Criterio: extendedProperties.private.alojasys_reservation_id == reservation.id
        Fallback: description contiene "AlojaSys Reservation #<id>".
        """
        try:
            time_min = reservation.check_in - timedelta(days=2)
            time_max = reservation.check_out + timedelta(days=2)
            evs = list_events(creds, calendar_id, time_min=time_min, time_max=time_max)
            for ev in evs.get('items', []):
                ext_priv = (ev.get('extendedProperties') or {}).get('private') or {}
                if str(ext_priv.get('alojasys_reservation_id')) == str(reservation.id):
                    return ev.get('id')
                if ('description' in ev) and (f"AlojaSys Reservation #{reservation.id}" in (ev.get('description') or '')):
                    return ev.get('id')
        except Exception:
            return None
        return None
    for mapping in mappings:
        calendar_id = mapping.external_id
        if not calendar_id:
            continue
        
        # Verificar acceso al calendario antes de intentar crear eventos
        try:
            get_calendar(creds, calendar_id)
            logger.debug(f"Reservation {reservation.id}: Calendar {calendar_id} is accessible")
        except Exception as cal_error:
            error_msg = str(cal_error)
            if "404" in error_msg or "notFound" in error_msg:
                logger.error(f"Reservation {reservation.id}: Calendar {calendar_id} not found or Service Account lacks access. Make sure the calendar is shared with the Service Account email.")
                results.append({"mapping_id": mapping.id, "action": "error", "error": f"Calendar not accessible: {error_msg}"})
                continue
            else:
                logger.warning(f"Reservation {reservation.id}: Could not verify calendar access: {error_msg}, proceeding anyway")
        
        # Nombre del huésped
        guest_name = "Huésped"
        if reservation.guests_data:
            primary = next((g for g in reservation.guests_data if g.get("is_primary")), reservation.guests_data[0])
            guest_name = primary.get("name", "Huésped")
        
        # Crear cuerpo del evento
        event_body = {
            "summary": f"Reserva - {guest_name}",
            "description": f"AlojaSys Reservation #{reservation.id}\nHabitación: {reservation.room.name}\nHotel: {reservation.hotel.name}",
            "start": {
                "date": reservation.check_in.isoformat(),
                "timeZone": "America/Argentina/Buenos_Aires",
            },
            "end": {
                # Google Calendar (all-day) usa end EXCLUSIVO.
                # En hotelería, nuestro rango ya es [check_in, check_out) → el día de check_out NO ocupa noche.
                # Por lo tanto, el end.date correcto es exactamente check_out (sin +1),
                # para permitir back-to-back (salida 24, entrada 24).
                "date": reservation.check_out.isoformat(),
                "timeZone": "America/Argentina/Buenos_Aires",
            },
            "extendedProperties": {
                "private": {
                    "alojasys_reservation_id": str(reservation.id),
                }
            },
        }
        
        # Buscar si ya existe un evento para esta reserva (idempotencia)
        google_event_id = _find_existing_event_id(calendar_id)
        
        try:
            if google_event_id:
                # Actualizar evento existente
                event_id = google_event_id.replace('google_', '')
                logger.info(f"Reservation {reservation.id}: Updating Google Calendar event {event_id} in calendar {calendar_id}")
                update_event(creds, calendar_id, event_id, event_body)
                results.append({"mapping_id": mapping.id, "action": "updated", "event_id": event_id})
            else:
                # Crear nuevo evento
                logger.info(f"Reservation {reservation.id}: Creating Google Calendar event in calendar {calendar_id}")
                created_event = insert_event(creds, calendar_id, event_body)
                event_id = created_event.get('id')
                logger.info(f"Reservation {reservation.id}: Created Google Calendar event {event_id}")
                # Registrar en OtaImportedEvent para seguimiento (sin tocar external_id para no violar validación de canal DIRECT)
                try:
                    OtaImportedEvent.objects.update_or_create(
                        hotel=reservation.hotel,
                        room=reservation.room,
                        provider=OtaProvider.GOOGLE,
                        uid=event_id,
                        defaults={
                            "dtstart": reservation.check_in,
                            "dtend": reservation.check_out,
                            "summary": event_body.get("summary"),
                            "source_url": f"google://{calendar_id}",
                        },
                    )
                except Exception:
                    pass
                results.append({"mapping_id": mapping.id, "action": "created", "event_id": event_id})
        except Exception as e:
            error_msg = str(e)
            # Mensaje más claro para errores comunes
            if "404" in error_msg or "notFound" in error_msg or "Not Found" in error_msg:
                error_msg = f"Calendar not found or Service Account lacks write permissions. Calendar ID: {calendar_id}. Make sure the Service Account email has 'Make changes to events' permission."
            elif "403" in error_msg or "Forbidden" in error_msg:
                error_msg = f"Access denied. Service Account needs 'Make changes to events' permission on calendar {calendar_id}."
            logger.error(f"Reservation {reservation.id}: Error creating/updating Google Calendar event: {error_msg}", exc_info=True)
            results.append({"mapping_id": mapping.id, "action": "error", "error": error_msg})
    
    return {"status": "ok", "results": results}


def delete_reservation_from_google(reservation: Reservation) -> Dict[str, Any]:
    """Elimina un evento de Google Calendar cuando se cancela una reserva."""
    if not GOOGLE_AVAILABLE:
        return {"status": "error", "reason": "google_api_not_installed"}
    
    # Buscar event_id en external_id
    if not reservation.external_id or not reservation.external_id.startswith('google_'):
        return {"status": "skipped", "reason": "no_google_event_id"}
    
    event_id = reservation.external_id.replace('google_', '')
    
    # Buscar mapeos Google activos
    mappings = OtaRoomMapping.objects.filter(
        hotel=reservation.hotel,
        room=reservation.room,
        provider=OtaProvider.GOOGLE,
        is_active=True,
    ).exclude(external_id__isnull=True).exclude(external_id="")
    
    if not mappings.exists():
        return {"status": "skipped", "reason": "no_google_mappings"}
    
    ota_config = reservation.hotel.ota_configs.filter(provider=OtaProvider.GOOGLE, is_active=True).first()
    if not ota_config:
        return {"status": "error", "reason": "no_active_google_config"}
    
    creds_container = ota_config.credentials or {}
    if isinstance(creds_container, dict) and "service_account_json" in creds_container:
        creds = creds_container.get("service_account_json")
    else:
        creds = creds_container
    if not isinstance(creds, dict) or creds.get("type") != "service_account":
        return {"status": "error", "reason": "missing_or_invalid_service_account_json"}
    
    results = []
    for mapping in mappings:
        calendar_id = mapping.external_id
        try:
            delete_event(creds, calendar_id, event_id)
            results.append({"mapping_id": mapping.id, "action": "deleted"})
        except Exception as e:
            # Si el evento ya no existe, está bien
            if "not found" in str(e).lower() or "404" in str(e):
                results.append({"mapping_id": mapping.id, "action": "already_deleted"})
            else:
                results.append({"mapping_id": mapping.id, "action": "error", "error": str(e)})
    
    return {"status": "ok", "results": results}

