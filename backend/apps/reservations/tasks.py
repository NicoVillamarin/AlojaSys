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


@shared_task(bind=True, autoretry_for=(ProgrammingError, OperationalError), retry_backoff=5, retry_jitter=True, retry_kwargs={"max_retries": 5})
def auto_cancel_expired_reservations(self):
    """
    Cancela automáticamente reservas pendientes que no han pagado el adelanto
    dentro del tiempo configurado en la política de pago
    """
    from apps.payments.services.payment_calculator import calculate_balance_due
    from apps.payments.models import PaymentPolicy
    from apps.reservations.models import ReservationChangeLog, ReservationChangeEvent
    
    today = timezone.localdate() if timezone.is_aware(timezone.now()) else date.today()
    processed_count = 0
    cancelled_count = 0
    
    print(f"🔄 Iniciando auto-cancelación de reservas vencidas - Fecha: {today}")
    
    # Obtener reservas pendientes
    pending_reservations = Reservation.objects.select_related("hotel", "room").filter(
        status=ReservationStatus.PENDING
    )
    
    for reservation in pending_reservations:
        try:
            # Obtener política de pago del hotel
            payment_policy = PaymentPolicy.resolve_for_hotel(reservation.hotel)
            
            if not payment_policy:
                print(f"⚠️ Reserva {reservation.id} - No hay política de pago configurada para el hotel {reservation.hotel.name}")
                continue
            
            # Calcular información de pago
            balance_info = calculate_balance_due(reservation)
            deposit_due_date = balance_info.get('deposit_due_date')
            
            if not deposit_due_date:
                print(f"⚠️ Reserva {reservation.id} - No se pudo calcular fecha de vencimiento del adelanto")
                continue
            
            # Verificar auto-cancelación por días desde creación
            days_since_creation = (today - reservation.created_at.date()).days
            should_auto_cancel = (
                payment_policy.auto_cancel_enabled and 
                days_since_creation >= payment_policy.auto_cancel_days
            )
            
            # Verificar si la fecha de vencimiento del adelanto ya pasó
            deposit_expired = deposit_due_date < today
            
            if should_auto_cancel or deposit_expired:
                reason = "días desde creación" if should_auto_cancel else "adelanto vencido"
                print(f"⏰ Reserva {reservation.id} - Cancelación por {reason} (días: {days_since_creation}, vencimiento: {deposit_due_date})")
                
                # Cancelar la reserva
                with transaction.atomic():
                    reservation.status = ReservationStatus.CANCELLED
                    reservation.save(update_fields=["status"])
                    
                    # Liberar la habitación
                    if reservation.room:
                        reservation.room.status = RoomStatus.AVAILABLE
                        reservation.room.save(update_fields=["status"])
                    
                    # Registrar log de cancelación automática
                    ReservationChangeLog.objects.create(
                        reservation=reservation,
                        event_type=ReservationChangeEvent.CANCEL,
                        changed_by=None,  # Sistema automático
                        message=f"Reserva cancelada automáticamente por {reason}. Días desde creación: {days_since_creation}, Fecha de vencimiento: {deposit_due_date}",
                        metadata={
                            'auto_cancellation': True,
                            'reason': 'days_since_creation' if should_auto_cancel else 'deposit_expired',
                            'days_since_creation': days_since_creation,
                            'deposit_due_date': deposit_due_date.isoformat(),
                            'payment_policy_id': payment_policy.id,
                            'payment_policy_name': payment_policy.name,
                            'auto_cancel_days': payment_policy.auto_cancel_days,
                            'auto_cancel_enabled': payment_policy.auto_cancel_enabled
                        }
                    )
                    
                    cancelled_count += 1
                    print(f"❌ Reserva {reservation.id} cancelada automáticamente - Hotel: {reservation.hotel.name} - Habitación: {reservation.room.name if reservation.room else 'N/A'}")
            
            else:
                days_remaining = (deposit_due_date - today).days
                days_until_auto_cancel = payment_policy.auto_cancel_days - days_since_creation
                print(f"✅ Reserva {reservation.id} - Adelanto vence en {days_remaining} días ({deposit_due_date}), Auto-cancelación en {days_until_auto_cancel} días")
            
            processed_count += 1
            
        except Exception as e:
            print(f"❌ Error procesando auto-cancelación para reserva {reservation.id}: {e}")
    
    print(f"📊 Auto-cancelación completada: {processed_count} reservas procesadas, {cancelled_count} canceladas")
    return f"Procesadas {processed_count} reservas, {cancelled_count} canceladas automáticamente"

@shared_task(bind=True, autoretry_for=(ProgrammingError, OperationalError), retry_backoff=5, retry_jitter=True, retry_kwargs={"max_retries": 5})
def auto_mark_no_show_daily(self):
    """
    Tarea Celery que marca automáticamente las reservas confirmadas vencidas como no-show
    Solo procesa hoteles que tienen auto_no_show_enabled=True
    """
    from apps.reservations.models import ReservationStatusChange
    
    today = timezone.now().date()
    processed_count = 0
    no_show_count = 0
    
    print(f"🚀 Iniciando auto no-show para {today}")
    
    # Obtener hoteles que tienen auto no-show habilitado
    hotels_with_auto_no_show = Hotel.objects.filter(
        auto_no_show_enabled=True,
        is_active=True
    )
    
    if not hotels_with_auto_no_show.exists():
        print("ℹ️ No hay hoteles con auto no-show habilitado")
        return "No hay hoteles con auto no-show habilitado"
    
    print(f"🏨 Procesando {hotels_with_auto_no_show.count()} hoteles con auto no-show habilitado")
    
    for hotel in hotels_with_auto_no_show:
        try:
            # Buscar reservas confirmadas con check-in pasado para este hotel
            expired_reservations = Reservation.objects.filter(
                hotel=hotel,
                status='confirmed',
                check_in__lt=today
            )
            
            hotel_processed = 0
            hotel_no_show = 0
            
            for reservation in expired_reservations:
                try:
                    # Cambiar estado a no_show
                    reservation.status = 'no_show'
                    reservation.save(update_fields=['status'])
                    
                    # Registrar el cambio de estado
                    ReservationStatusChange.objects.create(
                        reservation=reservation,
                        from_status='confirmed',
                        to_status='no_show',
                        changed_by=None,  # Sistema automático
                        notes='Auto no-show: check-in date passed'
                    )
                    
                    hotel_no_show += 1
                    no_show_count += 1
                    print(f"  ✅ Hotel {hotel.name}: Reserva {reservation.id} marcada como no-show")
                    
                except Exception as e:
                    print(f"  ❌ Error procesando reserva {reservation.id} en hotel {hotel.name}: {e}")
                
                hotel_processed += 1
                processed_count += 1
            
            if hotel_processed > 0:
                print(f"🏨 Hotel {hotel.name}: {hotel_processed} reservas procesadas, {hotel_no_show} marcadas como no-show")
                
        except Exception as e:
            print(f"❌ Error procesando hotel {hotel.name}: {e}")
    
    print(f"📊 Auto no-show completado: {processed_count} reservas procesadas, {no_show_count} marcadas como no-show")
    return f"Procesadas {processed_count} reservas, {no_show_count} marcadas como no-show"


@shared_task(bind=True, autoretry_for=(ProgrammingError, OperationalError), retry_backoff=5, retry_jitter=True, retry_kwargs={"max_retries": 5})
def auto_cancel_expired_pending_reservations(self):
    """
    Cancela automáticamente reservas PENDING que ya pasaron su fecha de check-in
    Estas reservas no pagaron el depósito y ya no pueden hacer check-in
    """
    from apps.reservations.models import ReservationStatusChange
    
    today = timezone.now().date()
    processed_count = 0
    cancelled_count = 0
    
    print(f"🔄 Iniciando cancelación automática de reservas PENDING vencidas - Fecha: {today}")
    
    # Buscar reservas PENDING con check-in pasado
    expired_pending_reservations = Reservation.objects.select_related("hotel", "room").filter(
        status=ReservationStatus.PENDING,
        check_in__lt=today
    )
    
    if not expired_pending_reservations.exists():
        print("ℹ️ No hay reservas PENDING vencidas para cancelar")
        return "No hay reservas PENDING vencidas para cancelar"
    
    print(f"📋 Encontradas {expired_pending_reservations.count()} reservas PENDING vencidas")
    
    for reservation in expired_pending_reservations:
        try:
            with transaction.atomic():
                # Cambiar estado a CANCELLED
                reservation.status = ReservationStatus.CANCELLED
                reservation.save(update_fields=['status'])
                
                # Liberar la habitación
                if reservation.room:
                    reservation.room.status = RoomStatus.AVAILABLE
                    reservation.room.save(update_fields=['status'])
                
                # Registrar el cambio de estado
                ReservationStatusChange.objects.create(
                    reservation=reservation,
                    from_status='pending',
                    to_status='cancelled',
                    changed_by=None,  # Sistema automático
                    notes='Auto-cancelación: fecha de check-in vencida sin pago del depósito'
                )
                
                cancelled_count += 1
                print(f"❌ Reserva {reservation.id} cancelada automáticamente - Hotel: {reservation.hotel.name} - Habitación: {reservation.room.name if reservation.room else 'N/A'} - Check-in vencido: {reservation.check_in}")
                
        except Exception as e:
            print(f"❌ Error cancelando reserva PENDING {reservation.id}: {e}")
        
        processed_count += 1
    
    print(f"📊 Cancelación automática de PENDING completada: {processed_count} reservas procesadas, {cancelled_count} canceladas")
    return f"Procesadas {processed_count} reservas PENDING, {cancelled_count} canceladas automáticamente"