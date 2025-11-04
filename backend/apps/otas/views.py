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
    # All-day event [DTEND no-inclusivo → sumar 1 día]
    dt_start = datetime.combine(reservation.check_in, datetime.min.time())
    dt_end = datetime.combine(reservation.check_out + timedelta(days=1), datetime.min.time())

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
        reservation = (
            Reservation.objects.filter(hotel=hotel, external_id=str(external_res_id), channel=channel)
            .first()
        )

        if reservation:
            changed = False
            if reservation.room_id != room.id:
                reservation.room = room
                changed = True
            if reservation.check_in != check_in or reservation.check_out != check_out:
                reservation.check_in = check_in
                reservation.check_out = check_out
                changed = True
            if reservation.status != ReservationStatus.CONFIRMED:
                reservation.status = ReservationStatus.CONFIRMED
                changed = True
            if notes:
                reservation.notes = (reservation.notes or "") + f"\nWebhook {provider}: {notes}"
                changed = True
            if changed:
                reservation.save(skip_clean=True)
                OtaSyncLog.objects.create(
                    job=job,
                    level=OtaSyncLog.Level.INFO,
                    message="WEBHOOK_RESERVATION_UPDATED",
                    payload={
                        "reservation_id": reservation.id,
                        "external_id": external_res_id,
                        "provider": provider,
                        "status": "success",
                    },
                )
            else:
                OtaSyncLog.objects.create(
                    job=job,
                    level=OtaSyncLog.Level.INFO,
                    message="WEBHOOK_RESERVATION_NO_CHANGES",
                    payload={"external_id": external_res_id, "provider": provider},
                )
        else:
            # Obtener política de cancelación para el hotel
            from apps.payments.models import CancellationPolicy
            cancellation_policy = CancellationPolicy.resolve_for_hotel(hotel)
            
            # Preparar guests_data completo (al menos con nombre si viene en el payload)
            guest_name = request.data.get('guest_name', f'Huésped {provider}')
            guest_email = request.data.get('guest_email', '')
            guests_data = [{
                "name": guest_name,
                "email": guest_email or f"{guest_name.lower().replace(' ', '.')}@example.com",
                "is_primary": True,
                "source": "webhook",
                "provider": provider
            }]
            # Agregar huéspedes adicionales si hay más de 1
            for i in range(2, guests + 1):
                guests_data.append({
                    "name": f"Huésped {i}",
                    "email": f"guest{i}@example.com",
                    "is_primary": False,
                    "source": "webhook",
                    "provider": provider
                })
            
            # Crear instancia sin guardar primero para poder usar skip_clean=True
            reservation = Reservation(
                hotel=hotel,
                room=room,
                external_id=str(external_res_id),
                channel=channel,
                check_in=check_in,
                check_out=check_out,
                status=ReservationStatus.CONFIRMED,
                guests=guests,
                guests_data=guests_data,
                notes=f"Creada por webhook {provider}",
                applied_cancellation_policy=cancellation_policy,  # Aplicar política si existe
            )
            # Guardar saltando validaciones (reservas desde OTAs pueden tener restricciones diferentes)
            reservation.save(skip_clean=True)
            
            # Generar noches y calcular totales para que la reserva esté completa
            from apps.reservations.services.pricing import generate_nights_for_reservation, recalc_reservation_totals
            generate_nights_for_reservation(reservation)
            recalc_reservation_totals(reservation)
            OtaSyncLog.objects.create(
                job=job,
                level=OtaSyncLog.Level.INFO,
                message="WEBHOOK_RESERVATION_CREATED",
                payload={
                    "reservation_id": reservation.id,
                    "external_id": external_res_id,
                    "provider": provider,
                    "status": "success",
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