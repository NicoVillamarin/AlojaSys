from decimal import Decimal
from datetime import timedelta, date
from apps.reservations.models import ReservationNight

def compute_nightly_rate(room, guests) -> dict:
    base = room.base_price or Decimal('0.00')
    included = room.capacity or 1
    extra_guests = max((guests or 1) - included, 0)
    extra = (room.extra_guest_fee or Decimal('0.00')) * Decimal(extra_guests)

    return {
        'base_rate': base,
        'extra_guest_fee': extra,
        'discount': Decimal('0.00'),
        'tax': Decimal('0.00'),
        'total_night': (base + extra).quantize(Decimal('0.01')),
    }

def generate_nights_for_reservation(reservation):
    ReservationNight.objects.filter(reservation=reservation).delete()
    current = reservation.check_in
    while current < reservation.check_out:
        parts = compute_nightly_rate(reservation.room, reservation.guests)
        ReservationNight.objects.create(
            reservation=reservation,
            hotel=reservation.hotel,
            room=reservation.room,
            date=current,
            **parts,
        )
        current += timedelta(days=1)

def recalc_reservation_totals(reservation):
    from django.db.models import Sum
    nights_total = reservation.nights.aggregate(s=Sum('total_night'))['s'] or Decimal('0.00')
    charges_total = reservation.charges.aggregate(s=Sum('amount'))['s'] or Decimal('0.00')
    total = (nights_total + charges_total).quantize(Decimal('0.01'))
    # Evitar disparar post_save de nuevo para no entrar en recursión
    type(reservation).objects.filter(pk=reservation.pk).update(total_price=total)