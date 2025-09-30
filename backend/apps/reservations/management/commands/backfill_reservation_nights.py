from django.core.management.base import BaseCommand
from apps.reservations.models import Reservation
from apps.reservations.services.pricing import generate_nights_for_reservation, recalc_reservation_totals

class Command(BaseCommand):
    help = "Genera ReservationNight para las reservas existentes"

    def add_arguments(self, parser):
        parser.add_argument('--reservation-id', type=int)
        parser.add_argument('--hotel-id', type=int)

    def handle(self, *args, **opts):
        qs = Reservation.objects.all()
        if opts.get('reservation-id'):
            qs = qs.filter(id=opts['reservation-id'])
        if opts.get('hotel-id'):
            qs = qs.filter(hotel_id=opts['hotel-id'])
        count = 0
        for r in qs.iterator():
            generate_nights_for_reservation(r)
            recalc_reservation_totals(r)
            count += 1
        self.stdout.write(self.style.SUCCESS(f"✅ {count} reservas procesadas"))