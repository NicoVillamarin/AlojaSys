from datetime import datetime, timedelta, date

from django.http import HttpResponse, HttpResponseForbidden
from django.shortcuts import get_object_or_404
from django.utils import timezone

from icalendar import Calendar, Event

from rest_framework import viewsets, permissions, status, decorators
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response

from apps.core.models import Hotel
from apps.rooms.models import Room
from apps.reservations.models import Reservation, ReservationStatus, ReservationChannel
from .models import (
    OtaConfig, OtaProvider, OtaRoomMapping, OtaSyncJob, OtaSyncLog,
    OtaRoomTypeMapping, OtaRatePlanMapping,
)
from .serializers import (
    OtaConfigSerializer,
    OtaRoomMappingSerializer,
    OtaSyncJobSerializer,
    OtaSyncLogSerializer,
    OtaRoomTypeMappingSerializer,
    OtaRatePlanMappingSerializer,
)
from .tasks import import_ics_for_mapping_task, push_ari_for_hotel_task
from apps.payments.services.webhook_security import WebhookSecurityService
from .services.ota_reservation_service import OtaReservationService, PaymentInfo
from django.conf import settings
import os
from decimal import Decimal


def _validate_ical_token_for_hotel(hotel_id: int, token: str) -> bool:
    if not token:
        return False
    return OtaConfig.objects.filter(
        hotel_id=hotel_id,
        provider=OtaProvider.ICAL,
        is_active=True,
        ical_out_token=token,
    ).exists()


def _build_calendar(name: str) -> Calendar:
    cal = Calendar()
    cal.add("prodid", "-//AlojaSys//ICS Export//ES")
    cal.add("version", "2.0")
    cal.add("X-WR-CALNAME", name)
    return cal


def _add_reservation_event(cal: Calendar, reservation: Reservation) -> None:
    event = Event()
    # All-day event (iCal estándar): DTEND es no-inclusivo.
    # Para reservas hoteleras, el evento cubre [check_in, check_out) → DTEND = check_out.
    dt_start = datetime.combine(reservation.check_in, datetime.min.time())
    dt_end = datetime.combine(reservation.check_out, datetime.min.time())

    event.add("uid", f"alojasys-reservation-{reservation.id}@alojasys")
    event.add("summary", f"RES-{reservation.id} | {reservation.room.name}")
    event.add("dtstart", dt_start.date())
    event.add("dtend", dt_end.date())
    event.add("description", f"Hotel: {reservation.hotel.name}")
    cal.add_component(event)


def ical_export_hotel(request, hotel_id: int):
    token = request.GET.get("token")
    if not _validate_ical_token_for_hotel(hotel_id, token):
        return HttpResponseForbidden("Invalid token")

    hotel = get_object_or_404(Hotel, id=hotel_id)

    cal = _build_calendar(f"AlojaSys - {hotel.name}")

    # Exportamos reservas confirmadas y pendientes (bloquean inventario)
    qs = Reservation.objects.filter(
        hotel=hotel,
        status__in=[ReservationStatus.CONFIRMED, ReservationStatus.PENDING],
    ).select_related("room")

    for r in qs:
        _add_reservation_event(cal, r)

    data = cal.to_ical()
    response = HttpResponse(data, content_type="text/calendar; charset=utf-8")
    response["Content-Disposition"] = f'attachment; filename="hotel_{hotel_id}.ics"'
    return response


def ical_export_room(request, room_id: int):
    room = get_object_or_404(Room, id=room_id)
    token = request.GET.get("token")
    if not _validate_ical_token_for_hotel(room.hotel_id, token):
        return HttpResponseForbidden("Invalid token")

    # Verificar si hay mapeos activos con sync_direction que permita export
    mappings = OtaRoomMapping.objects.filter(
        room=room,
        provider=OtaProvider.ICAL,
        is_active=True,
    )
    # Si hay mapeos específicos, verificar sync_direction
    if mappings.exists():
        has_export = False
        for m in mappings:
            if m.sync_direction in [OtaRoomMapping.SyncDirection.EXPORT, OtaRoomMapping.SyncDirection.BOTH]:
                has_export = True
                # Actualizar last_synced al exportar
                if m.last_synced is None or m.last_synced < timezone.now() - timedelta(minutes=1):
                    m.last_synced = timezone.now()
                    m.save(update_fields=["last_synced"])
                break
        if not has_export:
            return HttpResponseForbidden("Export not allowed for this room mapping (sync_direction)")

    cal = _build_calendar(f"AlojaSys - {room.hotel.name} - {room.name}")

    qs = Reservation.objects.filter(
        room=room,
        status__in=[ReservationStatus.CONFIRMED, ReservationStatus.PENDING],
    ).select_related("hotel", "room")

    for r in qs:
        _add_reservation_event(cal, r)

    data = cal.to_ical()
    response = HttpResponse(data, content_type="text/calendar; charset=utf-8")
    response["Content-Disposition"] = f'attachment; filename="room_{room_id}.ics"'
    return response


class OtaConfigViewSet(viewsets.ModelViewSet):
    queryset = OtaConfig.objects.select_related("hotel").all()
    serializer_class = OtaConfigSerializer
    permission_classes = [permissions.AllowAny]


class OtaRoomMappingViewSet(viewsets.ModelViewSet):
    queryset = OtaRoomMapping.objects.select_related("hotel", "room").all()
    serializer_class = OtaRoomMappingSerializer
    permission_classes = [permissions.AllowAny]

    def perform_create(self, serializer):
        """Crea un mapeo validando duplicados."""
        room = serializer.validated_data["room"]
        provider = serializer.validated_data["provider"]
        
        # Verificar si ya existe un mapeo activo para esta room+provider
        existing = OtaRoomMapping.objects.filter(
            room=room,
            provider=provider,
            is_active=True,
        )
        
        if existing.exists():
            from rest_framework.exceptions import ValidationError
            raise ValidationError(
                {
                    "non_field_errors": [
                        f"Ya existe un mapeo activo para la habitación {room.name} con el proveedor {provider}. "
                        "Desactiva el mapeo existente o usa PUT/PATCH para actualizarlo."
                    ]
                }
            )
        
        serializer.save()

    def perform_update(self, serializer):
        """Actualiza un mapeo validando duplicados."""
        room = serializer.validated_data.get("room") or serializer.instance.room
        provider = serializer.validated_data.get("provider") or serializer.instance.provider
        
        # Verificar si ya existe otro mapeo activo para esta room+provider
        existing = OtaRoomMapping.objects.filter(
            room=room,
            provider=provider,
            is_active=True,
        ).exclude(id=serializer.instance.id)
        
        if existing.exists():
            from rest_framework.exceptions import ValidationError
            raise ValidationError(
                {
                    "non_field_errors": [
                        f"Ya existe otro mapeo activo para la habitación {room.name} con el proveedor {provider}."
                    ]
                }
            )
        
        serializer.save()

    @decorators.action(detail=True, methods=["post"], url_path="import_now")
    def import_now(self, request, pk=None):
        mapping = self.get_object()
        # Crear job RUNNING inmediatamente para feedback instantáneo
        job = OtaSyncJob.objects.create(
            hotel=mapping.hotel,
            provider=OtaProvider.ICAL,
            job_type=OtaSyncJob.JobType.IMPORT_ICS,
            status=OtaSyncJob.JobStatus.RUNNING,
            stats={"mapping_id": mapping.id},
        )
        # Disparar task async que actualizará el job
        import_ics_for_mapping_task.delay(mapping.id, job.id)
        return Response({"success": True, "mapping_id": mapping.id, "job_id": job.id}, status=status.HTTP_202_ACCEPTED)


class OtaSyncJobViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = OtaSyncJob.objects.select_related("hotel").order_by("-started_at")
    serializer_class = OtaSyncJobSerializer
    permission_classes = [permissions.AllowAny]


class OtaSyncLogViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = OtaSyncLog.objects.select_related("job", "job__hotel").order_by("-created_at")
    serializer_class = OtaSyncLogSerializer
    permission_classes = [permissions.AllowAny]
    
    def get_queryset(self):
        """Permitir filtros por hotel, provider o level."""
        queryset = super().get_queryset()
        
        # Filtro por hotel
        hotel_id = self.request.query_params.get("hotel")
        if hotel_id:
            queryset = queryset.filter(job__hotel_id=hotel_id)
        
        # Filtro por provider
        provider = self.request.query_params.get("provider")
        if provider:
            queryset = queryset.filter(job__provider=provider)
        
        # Filtro por level
        level = self.request.query_params.get("level")
        if level:
            queryset = queryset.filter(level=level)
        
        return queryset


class OtaRoomTypeMappingViewSet(viewsets.ModelViewSet):
    queryset = OtaRoomTypeMapping.objects.select_related("hotel").all()
    serializer_class = OtaRoomTypeMappingSerializer
    permission_classes = [permissions.AllowAny]


class OtaRatePlanMappingViewSet(viewsets.ModelViewSet):
    queryset = OtaRatePlanMapping.objects.select_related("hotel").all()
    serializer_class = OtaRatePlanMappingSerializer
    permission_classes = [permissions.AllowAny]


@decorators.api_view(["POST"])
@decorators.permission_classes([permissions.AllowAny])
def push_ari(request):
    hotel_id = int(request.data.get("hotel"))
    provider = request.data.get("provider") or OtaProvider.BOOKING
    date_from = request.data.get("date_from")
    date_to = request.data.get("date_to")
    push_ari_for_hotel_task.delay(hotel_id, provider, date_from, date_to)
    return Response({"success": True, "queued": True}, status=status.HTTP_202_ACCEPTED)


# ===== Webhooks OTA (Booking / Airbnb) =====

def _get_webhook_secret_for_provider(provider: str) -> str:
    if provider == OtaProvider.BOOKING:
        return os.environ.get("BOOKING_WEBHOOK_SECRET", os.environ.get("OTAS_WEBHOOK_SECRET", ""))
    if provider == OtaProvider.AIRBNB:
        return os.environ.get("AIRBNB_WEBHOOK_SECRET", os.environ.get("OTAS_WEBHOOK_SECRET", ""))
    return os.environ.get("OTAS_WEBHOOK_SECRET", "")


def _parse_iso_date(value) -> date | None:
    if not value:
        return None
    try:
        if isinstance(value, str):
            return datetime.fromisoformat(value[:10]).date()
        if isinstance(value, datetime):
            return value.date()
        if isinstance(value, date):
            return value
    except Exception:
        return None
    return None


def _provider_to_channel(provider: str) -> str:
    return {
        OtaProvider.BOOKING: ReservationChannel.BOOKING,
        OtaProvider.EXPEDIA: ReservationChannel.EXPEDIA,
        OtaProvider.AIRBNB: ReservationChannel.AIRBNB,
    }.get(provider, ReservationChannel.OTHER)


def _process_reservation_webhook(provider: str, request) -> dict:
    secret = _get_webhook_secret_for_provider(provider)
    if not WebhookSecurityService.verify_webhook_signature(request, secret):
        WebhookSecurityService.log_webhook_security_event(
            event_type="hmac_failed",
            details={"provider": provider}
        )
        return {"ok": False, "status": "invalid_signature"}

    data = request.data if hasattr(request, "data") else {}
    notification_id = request.headers.get("X-Event-Id") or data.get("event_id") or data.get("id")
    external_res_id = data.get("reservation_id") or data.get("external_id") or data.get("id")

    # Verificar idempotencia solo por notification_id (event_id), no por external_res_id
    # porque una misma reserva puede recibir múltiples eventos (creación, actualización, etc.)
    if notification_id and WebhookSecurityService.is_notification_processed(notification_id, None):
        WebhookSecurityService.log_webhook_security_event(
            event_type="duplicate_detected",
            notification_id=notification_id,
            external_reference=external_res_id,
            details={"provider": provider}
        )
        return {"ok": True, "status": "duplicate"}

    hotel_id = data.get("hotel_id") or data.get("property_id")
    ota_room_id = data.get("ota_room_id") or data.get("room_id")
    room_id = data.get("pms_room_id") or data.get("room")
    check_in = _parse_iso_date(data.get("check_in"))
    check_out = _parse_iso_date(data.get("check_out"))
    guests = int(data.get("guests") or 1)
    notes = data.get("notes") or ""

    mapping = None
    hotel = None
    room = None

    if ota_room_id:
        mapping = (
            OtaRoomMapping.objects.select_related("hotel", "room")
            .filter(provider=provider, external_id=str(ota_room_id), is_active=True)
            .first()
        )
        if mapping:
            hotel = mapping.hotel
            room = mapping.room

    if not room and room_id:
        try:
            room = Room.objects.get(id=room_id)
            hotel = room.hotel
        except Room.DoesNotExist:
            pass

    if not hotel and hotel_id:
        hotel = Hotel.objects.filter(id=hotel_id).first()

    job = OtaSyncJob.objects.create(
        hotel=hotel,
        provider=provider,
        job_type=OtaSyncJob.JobType.PULL_RESERVATIONS,
        status=OtaSyncJob.JobStatus.RUNNING,
        stats={"webhook": True, "provider": provider},
    )

    try:
        if not (hotel and room and external_res_id and check_in and check_out):
            OtaSyncLog.objects.create(
                job=job,
                level=OtaSyncLog.Level.WARNING,
                message="WEBHOOK_INCOMPLETE",
                payload={
                    "hotel_id": getattr(hotel, "id", None),
                    "room_id": getattr(room, "id", None),
                    "external_id": external_res_id,
                    "check_in": str(check_in) if check_in else None,
                    "check_out": str(check_out) if check_out else None,
                    "provider": provider,
                },
            )
            job.status = OtaSyncJob.JobStatus.SUCCESS
            job.save(update_fields=["status"]) 
            if notification_id:
                WebhookSecurityService.mark_notification_processed(notification_id, None)
            return {"ok": True, "status": "accepted_noop"}

        channel = _provider_to_channel(provider)

        # Construir guests_data (principal y adicionales)
        guest_name = request.data.get('guest_name', f'Huésped {provider}')
        guest_email = request.data.get('guest_email', '')
        guests_data = [{
            "name": guest_name,
            "email": guest_email or f"{guest_name.lower().replace(' ', '.')}@example.com",
            "is_primary": True,
            "source": "webhook",
            "provider": provider
        }]
        for i in range(2, guests + 1):
            guests_data.append({
                "name": f"Huésped {i}",
                "email": f"guest{i}@example.com",
                "is_primary": False,
                "source": "webhook",
                "provider": provider
            })

        # PaymentInfo desde payload (si viene). Por defecto, HOTEL collect.
        paid_by_val = request.data.get('paid_by')  # 'ota' | 'hotel'
        payment_type = request.data.get('payment_source')  # 'ota_payout' | 'ota_vcc' | ...
        payment_info = None
        if paid_by_val:
            payment_info = PaymentInfo(
                paid_by=paid_by_val,
                payment_source=payment_type,
                provider=provider,
                external_reference=request.data.get('payment_tx_id') or request.data.get('external_payment_id'),
                currency=request.data.get('currency'),
                gross_amount=_to_float(request.data.get('gross_amount')),
                commission_amount=_to_float(request.data.get('commission_amount')),
                net_amount=_to_float(request.data.get('net_amount')),
                activation_date=_parse_iso_date(request.data.get('activation_date')),
                payout_date=_parse_iso_date(request.data.get('payout_date')),
            )

        # Upsert tolerante
        # Obtener nombre legible del provider para notificaciones
        provider_name = None
        try:
            provider_name = OtaProvider(provider).label
        except (ValueError, KeyError):
            provider_name = provider.title()  # Fallback a título del string
        
        result = OtaReservationService.upsert_reservation(
            hotel=hotel,
            room=room,
            external_id=str(external_res_id),
            channel=channel,
            check_in=check_in,
            check_out=check_out,
            guests=guests,
            guests_data=guests_data,
            notes=f"Webhook {provider}: {notes}" if notes else f"Webhook {provider}",
            payment_info=payment_info,
            provider_name=provider_name,
        )

        # Asegurar noches y totales consistentes tras el upsert OTA
        try:
            from apps.reservations.models import Reservation
            from apps.reservations.services.pricing import generate_nights_for_reservation, recalc_reservation_totals
            res_obj = Reservation.objects.get(id=result.get("reservation_id"))
            generate_nights_for_reservation(res_obj)
            recalc_reservation_totals(res_obj)
        except Exception:
            pass

        # Logs según resultado
        if result.get("created"):
            OtaSyncLog.objects.create(
                job=job,
                level=OtaSyncLog.Level.INFO,
                message="WEBHOOK_RESERVATION_CREATED",
                payload={
                    "reservation_id": result.get("reservation_id"),
                    "external_id": external_res_id,
                    "provider": provider,
                    "overbooking": result.get("overbooking"),
                    "paid_by": result.get("paid_by"),
                },
            )
        else:
            OtaSyncLog.objects.create(
                job=job,
                level=OtaSyncLog.Level.INFO,
                message="WEBHOOK_RESERVATION_UPDATED",
                payload={
                    "reservation_id": result.get("reservation_id"),
                    "external_id": external_res_id,
                    "provider": provider,
                    "overbooking": result.get("overbooking"),
                    "paid_by": result.get("paid_by"),
                },
            )

        job.status = OtaSyncJob.JobStatus.SUCCESS
        job.save(update_fields=["status"])
        # Marcar notification_id como procesado (no external_res_id, para permitir actualizaciones)
        if notification_id:
            WebhookSecurityService.mark_notification_processed(notification_id, None)
        return {"ok": True, "status": "processed"}

    except Exception as e:
        OtaSyncLog.objects.create(
            job=job,
            level=OtaSyncLog.Level.ERROR,
            message="WEBHOOK_ERROR",
            payload={"error": str(e), "provider": provider},
        )
        job.status = OtaSyncJob.JobStatus.FAILED
        job.error_message = str(e)
        job.save(update_fields=["status", "error_message"])
        return {"ok": False, "status": "error", "error": str(e)}


@api_view(["POST"])
@permission_classes([permissions.AllowAny])
def booking_webhook(request):
    result = _process_reservation_webhook(OtaProvider.BOOKING, request)
    http_status = status.HTTP_200_OK if result.get("ok") else status.HTTP_400_BAD_REQUEST
    return Response(result, status=http_status)


@api_view(["POST"])
@permission_classes([permissions.AllowAny])
def airbnb_webhook(request):
    result = _process_reservation_webhook(OtaProvider.AIRBNB, request)
    http_status = status.HTTP_200_OK if result.get("ok") else status.HTTP_400_BAD_REQUEST
    return Response(result, status=http_status)


# ===== Webhooks Smoobu (Channel Manager) =====

def _get_smoobu_webhook_token() -> str:
    return os.environ.get("SMOOBU_WEBHOOK_TOKEN", os.environ.get("OTAS_WEBHOOK_TOKEN", ""))


def _verify_smoobu_webhook_token(request) -> bool:
    """
    Smoobu no documenta firma HMAC en webhooks.
    Validamos por token propio (query ?token=... o header X-Webhook-Token).
    En DEBUG permitimos sin token para facilitar desarrollo.
    """
    token_required = _get_smoobu_webhook_token()
    if not token_required:
        return True if settings.DEBUG else True  # si no configuraste token, no bloqueamos
    provided = request.query_params.get("token") or request.headers.get("X-Webhook-Token") or request.headers.get("X-Token")
    return bool(provided) and str(provided) == str(token_required)


def _parse_smoobu_date(value: str | None) -> date | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(str(value)[:10]).date()
    except Exception:
        return None


def _map_smoobu_channel_to_internal(channel_name: str | None) -> str:
    name = (channel_name or "").lower()
    if "booking" in name:
        return ReservationChannel.BOOKING
    if "airbnb" in name:
        return ReservationChannel.AIRBNB
    if "expedia" in name:
        return ReservationChannel.EXPEDIA
    return ReservationChannel.OTHER


@api_view(["POST"])
@permission_classes([permissions.AllowAny])
def smoobu_webhook(request):
    if not _verify_smoobu_webhook_token(request):
        return Response({"ok": False, "status": "invalid_token"}, status=status.HTTP_403_FORBIDDEN)

    payload = request.data if hasattr(request, "data") else {}
    action = payload.get("action")
    data = payload.get("data") or {}

    # Construir notification_id para idempotencia (Smoobu no provee event_id explícito en docs)
    smoobu_res_id = data.get("id")
    modified = data.get("modifiedAt") or data.get("modified-at") or data.get("modified_at") or data.get("created-at")
    notification_id = f"smoobu:{action}:{smoobu_res_id}:{modified}" if (action and smoobu_res_id) else None

    if notification_id and WebhookSecurityService.is_notification_processed(notification_id, None):
        return Response({"ok": True, "status": "duplicate"}, status=status.HTTP_200_OK)

    # Resolver apartment -> room mapping
    apartment = data.get("apartment") or {}
    apartment_id = (apartment.get("id") if isinstance(apartment, dict) else None) or data.get("apartmentId")
    if not apartment_id:
        if notification_id:
            WebhookSecurityService.mark_notification_processed(notification_id, None)
        return Response({"ok": True, "status": "accepted_noop"}, status=status.HTTP_200_OK)

    mapping = (
        OtaRoomMapping.objects.select_related("hotel", "room")
        .filter(provider=OtaProvider.SMOOBU, external_id=str(apartment_id), is_active=True)
        .first()
    )

    job = OtaSyncJob.objects.create(
        hotel=getattr(mapping, "hotel", None),
        provider=OtaProvider.SMOOBU,
        job_type=OtaSyncJob.JobType.PULL_RESERVATIONS,
        status=OtaSyncJob.JobStatus.RUNNING,
        stats={"webhook": True, "provider": OtaProvider.SMOOBU},
    )

    try:
        if not (mapping and mapping.hotel and mapping.room and smoobu_res_id):
            OtaSyncLog.objects.create(
                job=job,
                level=OtaSyncLog.Level.WARNING,
                message="SMOOBU_WEBHOOK_INCOMPLETE",
                payload={"apartment_id": apartment_id, "smoobu_id": smoobu_res_id, "action": action},
            )
            job.status = OtaSyncJob.JobStatus.SUCCESS
            job.save(update_fields=["status"])
            if notification_id:
                WebhookSecurityService.mark_notification_processed(notification_id, None)
            return Response({"ok": True, "status": "accepted_noop"}, status=status.HTTP_200_OK)

        channel_name = None
        chan = data.get("channel") or {}
        if isinstance(chan, dict):
            channel_name = chan.get("name")
        channel = _map_smoobu_channel_to_internal(channel_name)

        external_id = f"smoobu:{smoobu_res_id}"
        check_in = _parse_smoobu_date(data.get("arrival") or data.get("arrivalDate"))
        check_out = _parse_smoobu_date(data.get("departure") or data.get("departureDate"))

        # Cancelación / borrado
        if action in ("cancelReservation", "deleteReservation"):
            # intentar por channel + fallback a cualquier channel
            qs = Reservation.objects.filter(hotel=mapping.hotel, external_id=external_id)
            if channel:
                qs = qs.filter(channel=channel)
            res = qs.order_by("-id").first()
            if res:
                res.status = ReservationStatus.CANCELLED
                res.save(update_fields=["status"])
                OtaSyncLog.objects.create(
                    job=job,
                    level=OtaSyncLog.Level.INFO,
                    message="SMOOBU_RESERVATION_CANCELLED",
                    payload={"reservation_id": res.id, "external_id": external_id, "channel": channel},
                )
            job.status = OtaSyncJob.JobStatus.SUCCESS
            job.save(update_fields=["status"])
            if notification_id:
                WebhookSecurityService.mark_notification_processed(notification_id, None)
            return Response({"ok": True, "status": "processed"}, status=status.HTTP_200_OK)

        if not (check_in and check_out):
            OtaSyncLog.objects.create(
                job=job,
                level=OtaSyncLog.Level.WARNING,
                message="SMOOBU_WEBHOOK_MISSING_DATES",
                payload={"external_id": external_id, "action": action},
            )
            job.status = OtaSyncJob.JobStatus.SUCCESS
            job.save(update_fields=["status"])
            if notification_id:
                WebhookSecurityService.mark_notification_processed(notification_id, None)
            return Response({"ok": True, "status": "accepted_noop"}, status=status.HTTP_200_OK)

        adults = int(data.get("adults") or 0)
        children = int(data.get("children") or 0)
        guests = max(adults + children, 1)

        guest_name = data.get("guest-name") or data.get("guest_name") or data.get("guestName") or data.get("firstname") or "Huésped Smoobu"
        email = data.get("email") or ""
        guests_data = [{
            "name": guest_name,
            "email": email or f"{guest_name.lower().replace(' ', '.')}@example.com",
            "is_primary": True,
            "source": "smoobu",
            "provider": "smoobu",
            "channel_name": channel_name,
        }]

        result = OtaReservationService.upsert_reservation(
            hotel=mapping.hotel,
            room=mapping.room,
            external_id=external_id,
            channel=channel,
            check_in=check_in,
            check_out=check_out,
            guests=guests,
            guests_data=guests_data,
            notes=f"Webhook Smoobu (canal: {channel_name})",
            provider_name=OtaProvider.SMOOBU.label,
        )

        OtaSyncLog.objects.create(
            job=job,
            level=OtaSyncLog.Level.INFO,
            message="SMOOBU_WEBHOOK_RESERVATION_UPSERTED",
            payload={
                "reservation_id": result.get("reservation_id"),
                "created": result.get("created"),
                "external_id": external_id,
                "channel": channel,
            },
        )

        job.status = OtaSyncJob.JobStatus.SUCCESS
        job.save(update_fields=["status"])
        if notification_id:
            WebhookSecurityService.mark_notification_processed(notification_id, None)
        return Response({"ok": True, "status": "processed"}, status=status.HTTP_200_OK)
    except Exception as e:
        OtaSyncLog.objects.create(
            job=job,
            level=OtaSyncLog.Level.ERROR,
            message="SMOOBU_WEBHOOK_ERROR",
            payload={"error": str(e), "action": action},
        )
        job.status = OtaSyncJob.JobStatus.FAILED
        job.error_message = str(e)
        job.save(update_fields=["status", "error_message"])
        return Response({"ok": False, "status": "error", "error": str(e)}, status=status.HTTP_400_BAD_REQUEST)