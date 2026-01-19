"""
Servicio de sincronización iCal para OTAs.

Centraliza la lógica de importación y exportación de reservas mediante archivos iCal (.ics).
"""
from datetime import date, datetime, timedelta
from typing import Dict, Any, Optional

import requests
from icalendar import Calendar, Event

from django.db import transaction
from django.utils import timezone
from django.conf import settings

from apps.reservations.models import Reservation, ReservationStatus, ReservationChannel, RoomBlock, RoomBlockType
from apps.notifications.services import NotificationService
from ..models import (
    OtaRoomMapping,
    OtaImportedEvent,
    OtaSyncJob,
    OtaSyncLog,
    OtaProvider,
)


class ICALSyncService:
    """Servicio para sincronizar reservas mediante iCal."""

    @staticmethod
    def _to_date(value) -> date:
        """Convierte un valor de iCalendar a date."""
        if hasattr(value, "dt"):
            value = value.dt
        if isinstance(value, datetime):
            return value.date()
        return value

    @staticmethod
    def _normalize_range(start: date, end: date) -> tuple[date, date]:
        """Asegura que el rango sea válido: end > start."""
        if end <= start:
            end = start + timedelta(days=1)
        return start, end

    @staticmethod
    @transaction.atomic
    def import_reservations(ota_room_mapping: OtaRoomMapping, job: Optional[OtaSyncJob] = None) -> Dict[str, Any]:
        """
        Importa reservas desde un feed iCal.

        Args:
            ota_room_mapping: Mapeo de habitación OTA con URL iCal configurada
            job: Job de sincronización opcional para registrar logs

        Returns:
            Dict con estadísticas: {processed, created, updated, skipped, errors}
        """
        stats = {"processed": 0, "created": 0, "updated": 0, "skipped": 0, "errors": 0, "cancelled": 0}
        run_started_at = timezone.now()

        # Verificar condiciones previas
        if not ota_room_mapping.is_active or not ota_room_mapping.ical_in_url:
            reason = "mapping not active or no ical_in_url"
            if job:
                OtaSyncLog.objects.create(
                    job=job,
                    level=OtaSyncLog.Level.WARNING,
                    message="IMPORT_SKIPPED",
                    payload={"mapping_id": ota_room_mapping.id, "reason": reason},
                )
            return {**stats, "reason": reason}

        # Verificar sync_direction
        if ota_room_mapping.sync_direction not in [
            OtaRoomMapping.SyncDirection.IMPORT,
            OtaRoomMapping.SyncDirection.BOTH,
        ]:
            reason = f"sync_direction is {ota_room_mapping.sync_direction}, not allowing import"
            if job:
                OtaSyncLog.objects.create(
                    job=job,
                    level=OtaSyncLog.Level.INFO,
                    message="IMPORT_SKIPPED",
                    payload={"mapping_id": ota_room_mapping.id, "reason": reason},
                )
            return {**stats, "reason": reason}

        # Registrar inicio
        if job:
            OtaSyncLog.objects.create(
                job=job,
                level=OtaSyncLog.Level.INFO,
                message="IMPORT_STARTED",
                payload={"mapping_id": ota_room_mapping.id, "url": ota_room_mapping.ical_in_url},
            )

        # Descargar archivo iCal
        try:
            resp = requests.get(ota_room_mapping.ical_in_url, timeout=20)
            resp.raise_for_status()
        except Exception as e:
            error_msg = f"Error descargando ICS: {str(e)}"
            stats["errors"] += 1
            if job:
                OtaSyncLog.objects.create(
                    job=job,
                    level=OtaSyncLog.Level.ERROR,
                    message="IMPORT_ERROR",
                    payload={"error": str(e), "url": ota_room_mapping.ical_in_url},
                )
            return stats

        # Parsear calendario
        try:
            cal = Calendar.from_ical(resp.content)
        except Exception as e:
            error_msg = f"Error parseando ICS: {str(e)}"
            stats["errors"] += 1
            if job:
                OtaSyncLog.objects.create(
                    job=job,
                    level=OtaSyncLog.Level.ERROR,
                    message="IMPORT_ERROR",
                    payload={"error": str(e)},
                )
            return stats

        # Procesar eventos VEVENT
        seen_uids: set[str] = set()
        for component in cal.walk("VEVENT"):
            stats["processed"] += 1

            uid = str(component.get("uid")) if component.get("uid") else None
            dtstart = component.get("dtstart")
            dtend = component.get("dtend")
            summary = str(component.get("summary")) if component.get("summary") else None
            ical_status = str(component.get("status") or "").strip().lower()  # e.g. CANCELLED

            if not uid or not dtstart or not dtend:
                stats["skipped"] += 1
                if job:
                    OtaSyncLog.objects.create(
                        job=job,
                        level=OtaSyncLog.Level.WARNING,
                        message="EVENT_SKIPPED",
                        payload={
                            "reason": "missing uid, dtstart or dtend",
                            "uid": uid,
                            "has_dtstart": bool(dtstart),
                            "has_dtend": bool(dtend),
                        },
                    )
                continue

            seen_uids.add(uid)

            # Normalizar fechas
            start_date = ICALSyncService._to_date(dtstart.dt) if dtstart else None
            end_date = ICALSyncService._to_date(dtend.dt) if dtend else None

            if not start_date or not end_date:
                stats["skipped"] += 1
                continue

            start_date, end_date = ICALSyncService._normalize_range(start_date, end_date)

            # Persistir / refrescar tracking del evento importado (por provider real, no siempre "ical")
            try:
                imported_event, created_ie = OtaImportedEvent.objects.get_or_create(
                    hotel=ota_room_mapping.hotel,
                    room=ota_room_mapping.room,
                    provider=ota_room_mapping.provider,
                    uid=uid,
                    defaults={
                        "dtstart": start_date,
                        "dtend": end_date,
                        "source_url": ota_room_mapping.ical_in_url,
                        "summary": summary,
                    },
                )
                if not created_ie:
                    changed_ie = False
                    if imported_event.dtstart != start_date or imported_event.dtend != end_date:
                        imported_event.dtstart = start_date
                        imported_event.dtend = end_date
                        changed_ie = True
                    if imported_event.source_url != ota_room_mapping.ical_in_url:
                        imported_event.source_url = ota_room_mapping.ical_in_url
                        changed_ie = True
                    if imported_event.summary != summary:
                        imported_event.summary = summary
                        changed_ie = True
                    if changed_ie:
                        imported_event.save(update_fields=["dtstart", "dtend", "source_url", "summary", "last_seen"])
                    else:
                        # Aunque no cambie nada, refrescar last_seen para poder detectar "desaparecidos"
                        OtaImportedEvent.objects.filter(pk=imported_event.pk).update(last_seen=run_started_at)
                # created_ie ya tiene last_seen set por auto_now=True
            except Exception:
                # No romper import por fallas de tracking
                pass

            # Determinar si se debe crear Reservation o RoomBlock
            # Por defecto: Booking/Airbnb/Expedia crean Reservation, ICAL genérico puede crear RoomBlock
            # Para ICAL, podemos crear RoomBlock si no necesitamos rastrear como reserva visible
            create_reservation = ota_room_mapping.provider in [
                OtaProvider.BOOKING,
                OtaProvider.AIRBNB,
                OtaProvider.EXPEDIA,
            ]
            
            # Si es ICAL, por defecto también creamos Reservation (comportamiento actual)
            # Pero se puede cambiar para crear RoomBlock si es necesario
            if ota_room_mapping.provider == OtaProvider.ICAL:
                create_reservation = True  # Cambiar a False si se quiere usar RoomBlock para ICAL genérico
            
            # Mapear provider a channel para Reservations
            channel_map = {
                OtaProvider.ICAL: ReservationChannel.OTHER,
                OtaProvider.BOOKING: ReservationChannel.BOOKING,
                OtaProvider.AIRBNB: ReservationChannel.AIRBNB,
                OtaProvider.EXPEDIA: ReservationChannel.EXPEDIA,
            }
            channel = channel_map.get(ota_room_mapping.provider, ReservationChannel.OTHER)
            
            # Mapear provider a "source" para logging (equivalente al provider)
            source_map = {
                OtaProvider.ICAL: "ical",
                OtaProvider.BOOKING: "booking",
                OtaProvider.AIRBNB: "airbnb",
                OtaProvider.EXPEDIA: "expedia",
            }
            source = source_map.get(ota_room_mapping.provider, "unknown")

            # Procesar según tipo: Reservation o RoomBlock
            try:
                if create_reservation:
                    # ===== LÓGICA PARA RESERVATION =====
                    # Buscar si existe una reserva con el mismo external_id y channel en el hotel
                    reservation = Reservation.objects.filter(
                        hotel=ota_room_mapping.hotel,
                        external_id=uid,
                        channel=channel,
                    ).first()

                    # Si el VEVENT viene CANCELLED, cancelar la reserva si existe y no está cerrada.
                    if ical_status in ("cancelled", "canceled"):
                        if reservation and reservation.status in [ReservationStatus.PENDING, ReservationStatus.CONFIRMED]:
                            reservation.status = ReservationStatus.CANCELLED
                            reservation.notes = (reservation.notes or "") + f"\nCancelada desde {ota_room_mapping.provider} iCal (STATUS:CANCELLED)."
                            reservation.save(skip_clean=True)
                            stats["cancelled"] += 1
                            if job:
                                OtaSyncLog.objects.create(
                                    job=job,
                                    level=OtaSyncLog.Level.INFO,
                                    message="RESERVATION_CANCELLED",
                                    payload={
                                        "reservation_id": reservation.id,
                                        "external_id": uid,
                                        "source": source,
                                        "channel": channel,
                                        "provider": ota_room_mapping.provider,
                                        "reason": "ical_status_cancelled",
                                        "status": "success",
                                    },
                                )
                        else:
                            stats["skipped"] += 1
                        continue

                    if reservation:
                        # Actualizar reserva existente
                        changed = False
                        if reservation.check_in != start_date or reservation.check_out != end_date:
                            reservation.check_in = start_date
                            reservation.check_out = end_date
                            changed = True
                        if reservation.room_id != ota_room_mapping.room_id:
                            reservation.room = ota_room_mapping.room
                            changed = True
                        if reservation.status != ReservationStatus.CONFIRMED and reservation.status != ReservationStatus.CANCELLED:
                            reservation.status = ReservationStatus.CONFIRMED
                            changed = True
                        if summary and (not reservation.notes or summary not in reservation.notes):
                            reservation.notes = f"Importado desde {ota_room_mapping.provider} iCal: {summary or ''}"
                            changed = True

                        if changed:
                            # Saltar validación de solapamiento para reservas importadas desde OTA
                            # porque pueden tener fechas que se solapan con otras reservas del PMS
                            reservation.save(skip_clean=True)
                            stats["updated"] += 1
                            if job:
                                OtaSyncLog.objects.create(
                                    job=job,
                                    level=OtaSyncLog.Level.INFO,
                                    message="RESERVATION_UPDATED",
                                    payload={
                                        "reservation_id": reservation.id,
                                        "external_id": uid,
                                        "source": source,
                                        "channel": channel,
                                        "check_in": start_date.isoformat(),
                                        "check_out": end_date.isoformat(),
                                        "room_id": ota_room_mapping.room_id,
                                        "provider": ota_room_mapping.provider,
                                        "status": "success",
                                    },
                                )
                        else:
                            stats["skipped"] += 1
                            if job:
                                OtaSyncLog.objects.create(
                                    job=job,
                                    level=OtaSyncLog.Level.INFO,
                                    message="RESERVATION_NO_CHANGES",
                                    payload={
                                        "reservation_id": reservation.id,
                                        "external_id": uid,
                                        "source": source,
                                        "status": "skipped",
                                    },
                                )
                    else:
                        # Crear nueva reserva
                        # Nota: Al crear, puede haber conflictos de solapamiento con otras reservas
                        # En ese caso, registramos el error pero continuamos
                        try:
                            # Obtener política de cancelación para el hotel
                            from apps.payments.models import CancellationPolicy
                            cancellation_policy = CancellationPolicy.resolve_for_hotel(ota_room_mapping.hotel)
                            
                            # Extraer nombre del huésped del summary si es posible
                            guest_name = summary or f"Huésped {ota_room_mapping.provider}"
                            # Intentar extraer nombre del summary si tiene formato "Reserva - Nombre" o "Reserva- Nombre"
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
                            
                            # Preparar guests_data completo
                            guests_data = [{
                                "name": guest_name,
                                "email": f"{guest_name.lower().replace(' ', '.')}@example.com",
                                "is_primary": True,
                                "source": source,  # "ical", "booking", "airbnb", etc.
                            }]
                            
                            # Proveer valores mínimos para pasar validaciones y guardar con skip_clean
                            reservation = Reservation(
                                hotel=ota_room_mapping.hotel,
                                room=ota_room_mapping.room,
                                external_id=uid,  # UID del evento iCal como external_id
                                channel=channel,  # Channel según provider (booking, expedia, other)
                                check_in=start_date,
                                check_out=end_date,
                                # iCal no modela “pendiente/confirmada” como un PMS, pero el evento representa
                                # una ocupación real (bloquea inventario). Para evitar confusión operativa y
                                # efectos colaterales (tareas automáticas sobre PENDING), la marcamos CONFIRMED.
                                status=ReservationStatus.CONFIRMED,
                                guests=1,
                                guests_data=guests_data,
                                notes=f"Importado desde {ota_room_mapping.provider} iCal: {summary or ''}",
                                applied_cancellation_policy=cancellation_policy,  # Aplicar política si existe
                                # Campos agregados para compatibilidad con columnas NOT NULL
                                overbooking_flag=False,
                            )
                            reservation.save(skip_clean=True)
                            
                            # Generar noches y calcular totales para que la reserva esté completa
                            from apps.reservations.services.pricing import generate_nights_for_reservation, recalc_reservation_totals
                            generate_nights_for_reservation(reservation)
                            recalc_reservation_totals(reservation)
                            
                            # Verificar si hay overbooking
                            active_status = [
                                ReservationStatus.PENDING,
                                ReservationStatus.CONFIRMED,
                                ReservationStatus.CHECK_IN,
                            ]
                            has_overlap = Reservation.objects.filter(
                                hotel=reservation.hotel,
                                room=reservation.room,
                                status__in=active_status,
                                check_in__lt=reservation.check_out,
                                check_out__gt=reservation.check_in,
                            ).exclude(pk=reservation.pk).exists()
                            
                            if has_overlap and not reservation.overbooking_flag:
                                reservation.overbooking_flag = True
                                reservation.save(update_fields=["overbooking_flag"])
                            
                            # Crear notificación para nueva reserva OTA
                            try:
                                provider_name = OtaProvider(ota_room_mapping.provider).label
                                NotificationService.create_ota_reservation_notification(
                                    provider_name=provider_name,
                                    reservation_code=f"RES-{reservation.id}",
                                    room_name=ota_room_mapping.room.name or f"Habitación {ota_room_mapping.room.number}",
                                    check_in_date=start_date.strftime("%d/%m/%Y"),
                                    check_out_date=end_date.strftime("%d/%m/%Y"),
                                    guest_name=guest_name,
                                    hotel_id=ota_room_mapping.hotel.id,
                                    reservation_id=reservation.id,
                                    external_id=uid,
                                    overbooking=has_overlap
                                )
                            except Exception as notif_error:
                                import logging
                                logger = logging.getLogger(__name__)
                                logger.warning(f"Error al crear notificación para reserva OTA {reservation.id}: {notif_error}")
                            
                            stats["created"] += 1
                            if job:
                                OtaSyncLog.objects.create(
                                    job=job,
                                    level=OtaSyncLog.Level.INFO,
                                    message="RESERVATION_CREATED",
                                    payload={
                                        "reservation_id": reservation.id,
                                        "external_id": uid,
                                        "source": source,
                                        "channel": channel,
                                        "check_in": start_date.isoformat(),
                                        "check_out": end_date.isoformat(),
                                        "room_id": ota_room_mapping.room_id,
                                        "provider": ota_room_mapping.provider,
                                        "status": "success",
                                    },
                                )
                        except Exception as create_error:
                            # Si falla por validación de solapamiento, registrar pero continuar
                            stats["errors"] += 1
                            if job:
                                OtaSyncLog.objects.create(
                                    job=job,
                                    level=OtaSyncLog.Level.WARNING,
                                    message="RESERVATION_CONFLICT",
                                    payload={
                                        "external_id": uid,
                                        "source": source,
                                        "error": str(create_error),
                                        "check_in": start_date.isoformat(),
                                        "check_out": end_date.isoformat(),
                                        "room_id": ota_room_mapping.room_id,
                                        "provider": ota_room_mapping.provider,
                                        "status": "error",
                                    },
                                )
                else:
                    # ===== LÓGICA PARA ROOMBLOCK (cuando no se requiere reserva visible) =====
                    # Buscar si existe un bloqueo con el mismo external_id almacenado en reason
                    # (usamos reason para almacenar el external_id ya que RoomBlock no tiene external_id)
                    existing_block = RoomBlock.objects.filter(
                        hotel=ota_room_mapping.hotel,
                        room=ota_room_mapping.room,
                        reason__icontains=f"external_id:{uid}",
                        is_active=True,
                    ).first()
                    
                    if existing_block:
                        # Actualizar bloqueo existente
                        changed = False
                        if existing_block.start_date != start_date or existing_block.end_date != end_date:
                            existing_block.start_date = start_date
                            existing_block.end_date = end_date
                            changed = True
                        if summary and (not existing_block.reason or summary not in existing_block.reason):
                            existing_block.reason = f"external_id:{uid} - {summary or 'Importado desde OTA'}"
                            changed = True
                        
                        if changed:
                            existing_block.save()
                            stats["updated"] += 1
                            if job:
                                OtaSyncLog.objects.create(
                                    job=job,
                                    level=OtaSyncLog.Level.INFO,
                                    message="ROOMBLOCK_UPDATED",
                                    payload={
                                        "block_id": existing_block.id,
                                        "external_id": uid,
                                        "source": source,
                                        "start_date": start_date.isoformat(),
                                        "end_date": end_date.isoformat(),
                                        "room_id": ota_room_mapping.room_id,
                                        "provider": ota_room_mapping.provider,
                                        "status": "success",
                                    },
                                )
                        else:
                            stats["skipped"] += 1
                            if job:
                                OtaSyncLog.objects.create(
                                    job=job,
                                    level=OtaSyncLog.Level.INFO,
                                    message="ROOMBLOCK_NO_CHANGES",
                                    payload={
                                        "block_id": existing_block.id,
                                        "external_id": uid,
                                        "source": source,
                                        "status": "skipped",
                                    },
                                )
                    else:
                        # Crear nuevo bloqueo
                        try:
                            room_block = RoomBlock.objects.create(
                                hotel=ota_room_mapping.hotel,
                                room=ota_room_mapping.room,
                                start_date=start_date,
                                end_date=end_date,
                                block_type=RoomBlockType.HOLD,
                                reason=f"external_id:{uid} - {summary or 'Importado desde OTA iCal'}",  # Almacenar UID en reason
                                is_active=True,
                            )
                            stats["created"] += 1
                            if job:
                                OtaSyncLog.objects.create(
                                    job=job,
                                    level=OtaSyncLog.Level.INFO,
                                    message="ROOMBLOCK_CREATED",
                                    payload={
                                        "block_id": room_block.id,
                                        "external_id": uid,
                                        "source": source,
                                        "start_date": start_date.isoformat(),
                                        "end_date": end_date.isoformat(),
                                        "room_id": ota_room_mapping.room_id,
                                        "provider": ota_room_mapping.provider,
                                        "status": "success",
                                    },
                                )
                        except Exception as create_error:
                            stats["errors"] += 1
                            if job:
                                OtaSyncLog.objects.create(
                                    job=job,
                                    level=OtaSyncLog.Level.ERROR,
                                    message="ROOMBLOCK_ERROR",
                                    payload={
                                        "external_id": uid,
                                        "source": source,
                                        "error": str(create_error),
                                        "check_in": start_date.isoformat(),
                                        "check_out": end_date.isoformat(),
                                        "room_id": ota_room_mapping.room_id,
                                        "provider": ota_room_mapping.provider,
                                        "status": "error",
                                    },
                                )

            except Exception as e:
                stats["errors"] += 1
                if job:
                    OtaSyncLog.objects.create(
                        job=job,
                        level=OtaSyncLog.Level.ERROR,
                        message="IMPORT_ERROR",
                        payload={
                            "external_id": uid,
                            "source": source,
                            "error": str(e),
                            "check_in": start_date.isoformat() if start_date else None,
                            "check_out": end_date.isoformat() if end_date else None,
                            "room_id": ota_room_mapping.room_id,
                            "provider": ota_room_mapping.provider,
                            "create_reservation": create_reservation,
                            "status": "error",
                        },
                    )

        # Cancelaciones por "evento desaparecido del feed":
        # Si un UID ya existía para esta fuente (source_url) y no apareció en esta corrida,
        # lo marcamos como cancelado (solo reservas futuras/activas).
        try:
            if ota_room_mapping.ical_in_url:
                disappeared = (
                    OtaImportedEvent.objects.filter(
                        hotel=ota_room_mapping.hotel,
                        room=ota_room_mapping.room,
                        provider=ota_room_mapping.provider,
                        source_url=ota_room_mapping.ical_in_url,
                        last_seen__lt=run_started_at,
                    )
                )
                today = timezone.localdate()
                for ev in disappeared.iterator():
                    if ev.uid in seen_uids:
                        continue
                    # Cancelar solo si la reserva está activa y aún no pasó (ev.dtend >= hoy)
                    if ev.dtend and ev.dtend < today:
                        continue
                    r = Reservation.objects.filter(
                        hotel=ota_room_mapping.hotel,
                        external_id=ev.uid,
                        channel=channel_map.get(ota_room_mapping.provider, ReservationChannel.OTHER),
                    ).first()
                    if not r:
                        continue
                    if r.status not in [ReservationStatus.PENDING, ReservationStatus.CONFIRMED]:
                        continue
                    r.status = ReservationStatus.CANCELLED
                    r.notes = (r.notes or "") + f"\nCancelada desde {ota_room_mapping.provider} iCal (evento ya no está en el feed)."
                    r.save(skip_clean=True)
                    stats["cancelled"] += 1
                    if job:
                        OtaSyncLog.objects.create(
                            job=job,
                            level=OtaSyncLog.Level.INFO,
                            message="RESERVATION_CANCELLED",
                            payload={
                                "reservation_id": r.id,
                                "external_id": ev.uid,
                                "provider": ota_room_mapping.provider,
                                "reason": "event_disappeared",
                                "status": "success",
                            },
                        )
        except Exception:
            # No romper import por fallas al detectar desaparecidos
            pass

        # Actualizar last_synced si hubo procesamiento exitoso
        if stats["processed"] > 0 or stats["created"] > 0 or stats["updated"] > 0:
            ota_room_mapping.last_synced = timezone.now()
            ota_room_mapping.save(update_fields=["last_synced"])

        # Registrar finalización
        if job:
            job.stats = {**(job.stats or {}), **stats}
            job.save(update_fields=["stats"])
            OtaSyncLog.objects.create(
                job=job,
                level=OtaSyncLog.Level.INFO,
                message="IMPORT_COMPLETED",
                payload={"mapping_id": ota_room_mapping.id, **stats},
            )

        return stats

    @staticmethod
    @transaction.atomic
    def export_reservations(ota_room_mapping: OtaRoomMapping, job: Optional[OtaSyncJob] = None) -> Dict[str, Any]:
        """
        Exporta reservas a formato iCal.

        Nota: Esta función prepara los datos para export. La generación real del .ics
        se hace en las vistas (ical_export_room) que sirven el archivo bajo demanda.

        Args:
            ota_room_mapping: Mapeo de habitación OTA
            job: Job de sincronización opcional para registrar logs

        Returns:
            Dict con estadísticas: {processed, exported}
        """
        stats = {"processed": 0, "exported": 0}

        # Verificar condiciones previas
        if not ota_room_mapping.is_active:
            reason = "mapping not active"
            if job:
                OtaSyncLog.objects.create(
                    job=job,
                    level=OtaSyncLog.Level.WARNING,
                    message="EXPORT_SKIPPED",
                    payload={"mapping_id": ota_room_mapping.id, "reason": reason},
                )
            return {**stats, "reason": reason}

        # Verificar sync_direction
        if ota_room_mapping.sync_direction not in [
            OtaRoomMapping.SyncDirection.EXPORT,
            OtaRoomMapping.SyncDirection.BOTH,
        ]:
            reason = f"sync_direction is {ota_room_mapping.sync_direction}, not allowing export"
            if job:
                OtaSyncLog.objects.create(
                    job=job,
                    level=OtaSyncLog.Level.INFO,
                    message="EXPORT_SKIPPED",
                    payload={"mapping_id": ota_room_mapping.id, "reason": reason},
                )
            return {**stats, "reason": reason}

        # Registrar inicio
        if job:
            OtaSyncLog.objects.create(
                job=job,
                level=OtaSyncLog.Level.INFO,
                message="EXPORT_STARTED",
                payload={"mapping_id": ota_room_mapping.id, "room_id": ota_room_mapping.room_id},
            )

        # Obtener reservas confirmadas para esta habitación
        reservations = Reservation.objects.filter(
            hotel=ota_room_mapping.hotel,
            room=ota_room_mapping.room,
            status=ReservationStatus.CONFIRMED,
        ).select_related("room", "hotel")

        stats["processed"] = reservations.count()

        # Nota: La generación real del .ics se hace en las vistas bajo demanda.
        # Aquí solo contamos las reservas que estarían disponibles para export.
        # El archivo .ics se sirve desde /api/otas/ical/room/{room_id}.ics?token={token}

        # Actualizar last_synced
        ota_room_mapping.last_synced = timezone.now()
        ota_room_mapping.save(update_fields=["last_synced"])

        stats["exported"] = stats["processed"]

        # Registrar finalización
        if job:
            job.stats = {**(job.stats or {}), **stats}
            job.save(update_fields=["stats"])
            OtaSyncLog.objects.create(
                job=job,
                level=OtaSyncLog.Level.INFO,
                message="EXPORT_COMPLETED",
                payload={"mapping_id": ota_room_mapping.id, **stats},
            )

        return stats

    @staticmethod
    def schedule_sync() -> Dict[str, Any]:
        """
        Ejecuta sincronización (import/export) para todos los mapeos activos.

        Returns:
            Dict con estadísticas generales: {total_mappings, import_success, import_errors, export_success, export_errors}
        """
        stats = {
            "total_mappings": 0,
            "import_success": 0,
            "import_errors": 0,
            "export_success": 0,
            "export_errors": 0,
        }

        # Obtener todos los mapeos activos
        mappings = OtaRoomMapping.objects.select_related("hotel", "room").filter(is_active=True)

        for mapping in mappings:
            stats["total_mappings"] += 1

            # Import si corresponde
            if mapping.sync_direction in [
                OtaRoomMapping.SyncDirection.IMPORT,
                OtaRoomMapping.SyncDirection.BOTH,
            ] and mapping.ical_in_url:
                try:
                    job = OtaSyncJob.objects.create(
                        hotel=mapping.hotel,
                        provider=mapping.provider,
                        job_type=OtaSyncJob.JobType.IMPORT_ICS,
                        status=OtaSyncJob.JobStatus.RUNNING,
                        stats={"mapping_id": mapping.id},
                    )
                    result = ICALSyncService.import_reservations(mapping, job=job)
                    job.status = OtaSyncJob.JobStatus.SUCCESS if result.get("errors", 0) == 0 else OtaSyncJob.JobStatus.FAILED
                    job.finished_at = timezone.now()
                    job.save(update_fields=["status", "finished_at", "stats"])

                    if result.get("errors", 0) == 0:
                        stats["import_success"] += 1
                    else:
                        stats["import_errors"] += 1

                except Exception as e:
                    stats["import_errors"] += 1
                    if job:
                        job.status = OtaSyncJob.JobStatus.FAILED
                        job.error_message = str(e)
                        job.finished_at = timezone.now()
                        job.save(update_fields=["status", "error_message", "finished_at"])
                        OtaSyncLog.objects.create(
                            job=job,
                            level=OtaSyncLog.Level.ERROR,
                            message="SCHEDULE_IMPORT_ERROR",
                            payload={"mapping_id": mapping.id, "error": str(e)},
                        )

            # Export si corresponde
            if mapping.sync_direction in [
                OtaRoomMapping.SyncDirection.EXPORT,
                OtaRoomMapping.SyncDirection.BOTH,
            ]:
                try:
                    job = OtaSyncJob.objects.create(
                        hotel=mapping.hotel,
                        provider=mapping.provider,
                        job_type=OtaSyncJob.JobType.EXPORT_ICS,
                        status=OtaSyncJob.JobStatus.RUNNING,
                        stats={"mapping_id": mapping.id},
                    )
                    result = ICALSyncService.export_reservations(mapping, job=job)
                    job.status = OtaSyncJob.JobStatus.SUCCESS
                    job.finished_at = timezone.now()
                    job.save(update_fields=["status", "finished_at", "stats"])

                    stats["export_success"] += 1

                except Exception as e:
                    stats["export_errors"] += 1
                    if job:
                        job.status = OtaSyncJob.JobStatus.FAILED
                        job.error_message = str(e)
                        job.finished_at = timezone.now()
                        job.save(update_fields=["status", "error_message", "finished_at"])
                        OtaSyncLog.objects.create(
                            job=job,
                            level=OtaSyncLog.Level.ERROR,
                            message="SCHEDULE_EXPORT_ERROR",
                            payload={"mapping_id": mapping.id, "error": str(e)},
                        )

        return stats

