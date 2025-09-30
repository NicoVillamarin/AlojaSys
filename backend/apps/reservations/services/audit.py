from decimal import Decimal
from django.db.models import Sum
from apps.reservations.models import Reservation

def _to_str_money(val) -> str:
    d = Decimal(str(val or 0)).quantize(Decimal('0.01'))
    return format(d, 'f')

def build_snapshot(reservation: Reservation) -> dict:
    nights_total = reservation.nights.aggregate(s=Sum('total_night'))['s'] or Decimal('0.00')
    charges_total = reservation.charges.aggregate(s=Sum('amount'))['s'] or Decimal('0.00')
    payments_total = reservation.payments.aggregate(s=Sum('amount'))['s'] or Decimal('0.00')
    return {
        "id": reservation.id,
        "hotel_id": reservation.hotel_id,
        "room_id": reservation.room_id,
        "check_in": str(reservation.check_in),
        "check_out": str(reservation.check_out),
        "guests": reservation.guests,
        "status": reservation.status,
        "channel": reservation.channel,
        "totals": {
            "nights_total": _to_str_money(nights_total),
            "charges_total": _to_str_money(charges_total),
            "payments_total": _to_str_money(payments_total),
            "total_price": _to_str_money(reservation.total_price or 0),
        },
    }

def build_diff(old_obj: Reservation | None, new_obj: Reservation, fields: list[str]) -> dict:
    if old_obj is None:
        return {}
    diff = {}
    for f in fields:
        old = getattr(old_obj, f, None)
        new = getattr(new_obj, f, None)
        if str(old) != str(new):
            diff[f] = {
                "old": str(old) if old is not None else None,
                "new": str(new) if new is not None else None,
            }
    return diff