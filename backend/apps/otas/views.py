from datetime import datetime, timedelta

from django.http import HttpResponse, HttpResponseForbidden
from django.shortcuts import get_object_or_404

from icalendar import Calendar, Event

from rest_framework import viewsets, permissions, status, decorators
from rest_framework.response import Response

from apps.core.models import Hotel
from apps.rooms.models import Room
from apps.reservations.models import Reservation, ReservationStatus
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
    queryset = OtaSyncLog.objects.select_related("job").order_by("-created_at")
    serializer_class = OtaSyncLogSerializer
    permission_classes = [permissions.AllowAny]


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