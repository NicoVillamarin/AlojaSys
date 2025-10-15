from datetime import date, datetime
from zoneinfo import ZoneInfo
from django.db import transaction
from django.utils import timezone
from celery import shared_task
from django.db.utils import ProgrammingError, OperationalError
from apps.reservations.models import Reservation, ReservationStatus
from apps.core.models import Hotel
from apps.rooms.models import RoomStatus, Room

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
        # Procesar checkout automático basado en horario del hotel (usando zona horaria del hotel)
        # Obtener todas las reservas que deberían hacer checkout hoy (fecha basada en TZ del servidor)
        checkout_reservations = Reservation.objects.select_related("room", "hotel").filter(
            status=ReservationStatus.CHECK_IN,
            check_out=today,
        )

        for res in checkout_reservations:
            # Hora actual en la zona horaria configurada del hotel
            try:
                hotel_tz = ZoneInfo(res.hotel.timezone) if res.hotel and res.hotel.timezone else None
            except Exception:
                hotel_tz = None

            aware_now = timezone.now()
            local_now = timezone.localtime(aware_now, hotel_tz) if hotel_tz else aware_now
            current_time_local = local_now.time()

            # Verificar si ya pasó la hora de checkout del hotel (en hora local del hotel)
            hotel_checkout_time = res.hotel.check_out_time
            if current_time_local >= hotel_checkout_time:
                # Realizar checkout automático
                res.status = ReservationStatus.CHECK_OUT
                res.save(update_fields=["status"])

                # Liberar la habitación
                if res.room.status == RoomStatus.OCCUPIED:
                    res.room.status = RoomStatus.AVAILABLE
                    res.room.save(update_fields=["status"])

                print(
                    f"✅ Checkout automático realizado para reserva {res.id} - {res.room.name} (hora local {current_time_local}, tz={res.hotel.timezone})"
                )

    with transaction.atomic():
        # Actualizar el estado de las habitaciones basándose en reservas activas
        all_rooms = Room.objects.filter(is_active=True)
        for room in all_rooms:
            # Verificar si hay reservas activas para esta habitación hoy
            # (dentro del rango de fechas de la reserva)
            active_reservations = Reservation.objects.filter(
                room=room,
                status__in=[ReservationStatus.PENDING, ReservationStatus.CONFIRMED, ReservationStatus.CHECK_IN],
                check_in__lte=today,
                check_out__gt=today,
            ).exists()
            
            # Si no hay reservas activas en el rango de fechas, verificar si hay una reserva en CHECK_IN
            # que aún no haya hecho checkout manual (incluso si ya pasó la fecha de checkout)
            if not active_reservations:
                active_reservations = Reservation.objects.filter(
                    room=room,
                    status=ReservationStatus.CHECK_IN,
                    check_in__lte=today,
                ).exists()
            
            # También verificar si hay una reserva confirmada que comienza hoy
            if not active_reservations:
                active_reservations = Reservation.objects.filter(
                    room=room,
                    status=ReservationStatus.CONFIRMED,
                    check_in=today,
                ).exists()
            
            # Solo marcar como disponible si NO hay reservas activas
            if not active_reservations and room.status != RoomStatus.AVAILABLE:
                room.status = RoomStatus.AVAILABLE
                room.save(update_fields=["status"])
            elif active_reservations and room.status != RoomStatus.OCCUPIED:
                room.status = RoomStatus.OCCUPIED
                room.save(update_fields=["status"])


@shared_task(bind=True, autoretry_for=(ProgrammingError, OperationalError), retry_backoff=5, retry_jitter=True, retry_kwargs={"max_retries": 5})
def process_automatic_checkouts(self):
    """
    Tarea para procesar checkouts automáticos basados en el horario configurado en cada hotel.
    Esta tarea debe ejecutarse cada hora para verificar si hay reservas que deben hacer checkout.
    """
    today = timezone.localdate() if timezone.is_aware(timezone.now()) else date.today()
    
    print("🕐 Procesando checkouts automáticos - evaluando por hotel en su zona horaria")
    
    # Obtener todas las reservas que deberían hacer checkout hoy y están en CHECK_IN
    checkout_reservations = Reservation.objects.select_related("room", "hotel").filter(
        status=ReservationStatus.CHECK_IN,
        check_out=today,
    )
    
    processed_count = 0
    
    for res in checkout_reservations:
        # Hora actual en la zona horaria del hotel
        try:
            hotel_tz = ZoneInfo(res.hotel.timezone) if res.hotel and res.hotel.timezone else None
        except Exception:
            hotel_tz = None

        aware_now = timezone.now()
        local_now = timezone.localtime(aware_now, hotel_tz) if hotel_tz else aware_now
        current_time_local = local_now.time()

        # Verificar si ya pasó la hora de checkout del hotel
        hotel_checkout_time = res.hotel.check_out_time

        print(
            f"📋 Reserva {res.id} - Hotel: {res.hotel.name} - TZ: {res.hotel.timezone} - Ahora local: {current_time_local} - Checkout configurado: {hotel_checkout_time}"
        )

        if current_time_local >= hotel_checkout_time:
            try:
                with transaction.atomic():
                    # Realizar checkout automático
                    res.status = ReservationStatus.CHECK_OUT
                    res.save(update_fields=["status"])
                    
                    # Liberar la habitación
                    if res.room.status == RoomStatus.OCCUPIED:
                        res.room.status = RoomStatus.AVAILABLE
                        res.room.save(update_fields=["status"])
                    
                    processed_count += 1
                    print(f"✅ Checkout automático realizado para reserva {res.id} - {res.room.name} - Hotel: {res.hotel.name}")
                    
            except Exception as e:
                print(f"❌ Error procesando checkout automático para reserva {res.id}: {e}")
        else:
            print(f"⏳ Reserva {res.id} - Aún no es hora de checkout (falta {hotel_checkout_time})")
    
    print(f"📊 Procesamiento completado: {processed_count} checkouts automáticos realizados")
    return f"Procesados {processed_count} checkouts automáticos"