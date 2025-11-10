from django.core.management.base import BaseCommand
from apps.reservations.models import Reservation
from apps.otas.services.google_sync_service import export_reservation_to_google


class Command(BaseCommand):
    help = 'Prueba exportar una reserva a Google Calendar'

    def add_arguments(self, parser):
        parser.add_argument('reservation_id', type=int, help='ID de la reserva a exportar')

    def handle(self, *args, **options):
        reservation_id = options['reservation_id']
        
        try:
            reservation = Reservation.objects.get(id=reservation_id)
        except Reservation.DoesNotExist:
            self.stdout.write(self.style.ERROR(f'Reserva {reservation_id} no encontrada'))
            return
        
        self.stdout.write(f'Probando exportar reserva #{reservation.id} a Google Calendar...')
        self.stdout.write(f'  Hotel: {reservation.hotel.name}')
        self.stdout.write(f'  Habitación: {reservation.room.name}')
        self.stdout.write(f'  Estado: {reservation.status}')
        self.stdout.write(f'  Check-in: {reservation.check_in}')
        self.stdout.write(f'  Check-out: {reservation.check_out}')
        
        result = export_reservation_to_google(reservation)
        
        self.stdout.write(f'\nResultado: {result.get("status")}')
        if result.get("reason"):
            self.stdout.write(self.style.WARNING(f'Razón: {result.get("reason")}'))
        if result.get("results"):
            for r in result.get("results", []):
                if r.get("action") == "created":
                    self.stdout.write(self.style.SUCCESS(f'✓ Evento creado: {r.get("event_id")}'))
                elif r.get("action") == "updated":
                    self.stdout.write(self.style.SUCCESS(f'✓ Evento actualizado: {r.get("event_id")}'))
                elif r.get("action") == "error":
                    self.stdout.write(self.style.ERROR(f'✗ Error: {r.get("error")}'))

