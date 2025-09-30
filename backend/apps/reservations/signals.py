from django.db.models.signals import post_save
from django.dispatch import receiver
from apps.reservations.models import Reservation
from .services.pricing import generate_nights_for_reservation, recalc_reservation_totals
from django.conf import settings
from .models import Reservation, ReservationCharge, ChannelCommission

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

def reservation_post_save(sender, instance: Reservation, created, **kwargs):
    if not instance.check_in or not instance.check_out or not instance.room_id:
        return
    generate_nights_for_reservation(instance)
    recalc_reservation_totals(instance)
    upsert_channel_commission(instance)