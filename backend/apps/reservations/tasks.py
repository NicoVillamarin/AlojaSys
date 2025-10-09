from datetime import date
from django.db import transaction
from django.utils import timezone
from celery import shared_task
from django.db.utils import ProgrammingError, OperationalError
from apps.reservations.models import Reservation, ReservationStatus
from apps.core.models import Hotel
from apps.rooms.models import RoomStatus

@shared_task(bind=True, autoretry_for=(ProgrammingError, OperationalError), retry_backoff=5, retry_jitter=True, retry_kwargs={"max_retries": 5})
def sync_room_occupancy_for_today(self):
    today = timezone.localdate() if timezone.is_aware(timezone.now()) else date.today()

    with transaction.atomic():
        checkin_qs = Reservation.objects.select_related("room", "hotel").filter(
            status__in=[ReservationStatus.CONFIRMED, ReservationStatus.CHECK_IN],
            check_in__lte=today,
            check_out__gt=today,
        )
        for res in checkin_qs:
            # Respetar la configuración del hotel: si auto_check_in_enabled es False, no marcar automáticamente
            if not getattr(res.hotel, "auto_check_in_enabled", False):
                continue
            if res.status != ReservationStatus.CHECK_IN:
                res.status = ReservationStatus.CHECK_IN
                res.save(update_fields=["status"])
            if res.room.status != RoomStatus.OCCUPIED:
                res.room.status = RoomStatus.OCCUPIED
                res.room.save(update_fields=["status"])

    with transaction.atomic():
        checkout_qs = Reservation.objects.select_related("room").filter(
            status=ReservationStatus.CHECK_IN,
            check_out__lte=today,
        )
        for res in checkout_qs:
            res.status = ReservationStatus.CHECK_OUT
            res.save(update_fields=["status"])

            overlapping_active = Reservation.objects.filter(
                room=res.room,
                status__in=[ReservationStatus.PENDING, ReservationStatus.CONFIRMED, ReservationStatus.CHECK_IN],
                check_in__lt=today,
                check_out__gt=today,
            ).exists()
            if not overlapping_active and res.room.status != RoomStatus.AVAILABLE:
                res.room.status = RoomStatus.AVAILABLE
                res.room.save(update_fields=["status"])