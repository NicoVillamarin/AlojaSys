from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from apps.reservations.models import Reservation, ReservationChangeLog, ReservationStatusChange, ReservationChangeEvent
from .services.pricing import generate_nights_for_reservation, recalc_reservation_totals
from django.conf import settings
from .models import Reservation, ReservationCharge, ChannelCommission
from .services.audit import build_snapshot, build_diff
from .middleware import get_current_user

AUDIT_FIELDS = [
    "room_id",
    "check_in",
    "check_out",
    "guests",
    "guests_data",
    "status",
    "channel",
    "notes",
]

def upsert_channel_commission(reservation: Reservation):
    from decimal import Decimal
    rates = getattr(settings, "CHANNEL_COMMISSION_RATES", {})
    rate = Decimal(str(rates.get(reservation.channel, 0)))
    amount = (reservation.total_price or Decimal('0.00')) * (rate / Decimal('100'))
    ChannelCommission.objects.update_or_create(
        reservation=reservation,
        defaults={'channel': reservation.channel, 'rate_percent': rate, 'amount': amount},
    )

@receiver(post_save, sender=Reservation)
def reservation_post_save_first(sender, instance: Reservation, created, **kwargs):
    if not instance.check_in or not instance.check_out or not instance.room_id:
        return
    generate_nights_for_reservation(instance)
    recalc_reservation_totals(instance)
    upsert_channel_commission(instance)

@receiver(pre_save, sender=Reservation)
def reservation_pre_save(sender, instance: Reservation, **kwargs):
    if instance.pk:
        try:
            instance._prev = Reservation.objects.get(pk=instance.pk)
        except Reservation.DoesNotExist:
            instance._prev = None
    else:
        instance._prev = None

@receiver(post_save, sender=Reservation)
def reservation_post_save_log(sender, instance: Reservation, created, **kwargs):
    if instance.check_in and instance.check_out and instance.room_id:
        generate_nights_for_reservation(instance)
        recalc_reservation_totals(instance)

    prev = getattr(instance, "_prev", None)
    user = get_current_user()

    if created:
        room_name = getattr(getattr(instance, "room", None), "name", "Habitación")
        msg = (
            f"Reserva #{instance.id} creada: "
            f"{instance.guest_name or 'Sin nombre'} • {room_name} • "
            f"{instance.check_in} → {instance.check_out}"
        )
        ReservationChangeLog.objects.create(
            reservation=instance,
            event_type=ReservationChangeEvent.CREATED,
            changed_by=user if user is not None else None,
            fields_changed={},
            snapshot=build_snapshot(instance),
            message=msg,
        )
        return

    changed = build_diff(prev, instance, AUDIT_FIELDS) if prev else {}
    if changed:
        ReservationChangeLog.objects.create(
            reservation=instance,
            event_type=ReservationChangeEvent.UPDATED,
            changed_by=user if user is not None else None,
            fields_changed=changed,
            snapshot=build_snapshot(instance),
            message=f"Reserva actualizada: {instance.id}",
        )
    
    if prev and prev.status != instance.status:
        ReservationStatusChange.objects.create(
            reservation=instance,
            from_status=prev.status,
            to_status=instance.status,
            changed_by=user if user is not None else None,
            notes=f"Estado actualizado: {instance.status}",
        )
        ReservationChangeLog.objects.create(
            reservation=instance,
            event_type=ReservationChangeEvent.STATUS_CHANGED,
            changed_by=user if user is not None else None,
            fields_changed={"status": {"old": prev.status, "new": instance.status}},
            snapshot=build_snapshot(instance),
        )