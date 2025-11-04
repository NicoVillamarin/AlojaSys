"""
Management command para simular una reserva de Airbnb.

Este script crea una reserva como si viniera de Airbnb, simulando
el proceso completo de importación desde una OTA.

Uso:
    python manage.py simulate_airbnb_reservation --hotel 1 --room 1
    python manage.py simulate_airbnb_reservation --hotel 1 --room 1 --check-in 2024-12-25 --nights 3 --guests 2 --guest-name "Juan Pérez"
"""

from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone
from django.db import transaction
from datetime import date, timedelta
from apps.core.models import Hotel
from apps.rooms.models import Room
from apps.reservations.models import Reservation, ReservationStatus, ReservationChannel
from apps.reservations.services.pricing import generate_nights_for_reservation, recalc_reservation_totals
from apps.payments.models import CancellationPolicy
from apps.otas.models import OtaProvider, OtaSyncJob, OtaSyncLog
import random


class Command(BaseCommand):
    help = 'Simula una reserva de Airbnb creando una Reservation con external_id y channel=OTHER'

    def add_arguments(self, parser):
        parser.add_argument(
            '--hotel',
            type=int,
            required=True,
            help='ID del hotel para la reserva'
        )
        parser.add_argument(
            '--room',
            type=int,
            required=True,
            help='ID de la habitación para la reserva'
        )
        parser.add_argument(
            '--check-in',
            type=str,
            help='Fecha de check-in (YYYY-MM-DD). Por defecto: mañana'
        )
        parser.add_argument(
            '--nights',
            type=int,
            default=2,
            help='Número de noches (por defecto: 2)'
        )
        parser.add_argument(
            '--guests',
            type=int,
            default=1,
            help='Número de huéspedes (por defecto: 1)'
        )
        parser.add_argument(
            '--guest-name',
            type=str,
            help='Nombre del huésped (por defecto: "Huésped Airbnb")'
        )
        parser.add_argument(
            '--external-id',
            type=str,
            help='ID externo de Airbnb (por defecto: se genera automáticamente)'
        )
        parser.add_argument(
            '--create-job',
            action='store_true',
            help='Crear también un OtaSyncJob y OtaSyncLog para simular el proceso completo'
        )

    def handle(self, *args, **options):
        hotel_id = options['hotel']
        room_id = options['room']
        # Manejar argumento con guión (--check-in) que se convierte a check_in
        check_in_str = options.get('check_in') or options.get('check-in')
        nights = options['nights']
        guests = options['guests']
        # Manejar argumento con guión (--guest-name) que se convierte a guest_name
        guest_name = options.get('guest_name') or options.get('guest-name') or 'Huésped Airbnb'
        external_id = options.get('external_id') or options.get('external-id') or f"airbnb-{random.randint(100000, 999999)}"
        create_job = options.get('create_job', False)

        # Validar hotel
        try:
            hotel = Hotel.objects.get(id=hotel_id)
        except Hotel.DoesNotExist:
            raise CommandError(f'Hotel con ID {hotel_id} no existe.')

        # Validar habitación
        try:
            room = Room.objects.get(id=room_id, hotel=hotel)
        except Room.DoesNotExist:
            raise CommandError(f'Habitación con ID {room_id} no existe en el hotel {hotel.name}.')

        # Validar capacidad de la habitación
        max_capacity = room.max_capacity if room.max_capacity else 1
        if guests > max_capacity:
            self.stdout.write(
                self.style.WARNING(
                    f'⚠️  La habitación {room.name} tiene capacidad máxima de {max_capacity} huéspedes. '
                    f'Se usará {max_capacity} en lugar de {guests}.'
                )
            )
            guests = max_capacity
        
        # Validar que haya al menos 1 huésped
        if guests < 1:
            guests = 1
            self.stdout.write(
                self.style.WARNING(
                    '⚠️  Se ajustó el número de huéspedes a 1 (mínimo requerido).'
                )
            )

        # Calcular fechas
        if check_in_str:
            try:
                check_in = date.fromisoformat(check_in_str)
            except ValueError:
                raise CommandError(f'Fecha de check-in inválida: {check_in_str}. Use formato YYYY-MM-DD.')
        else:
            check_in = date.today() + timedelta(days=1)  # Mañana por defecto

        if check_in < date.today():
            raise CommandError(f'La fecha de check-in ({check_in}) no puede ser en el pasado.')

        check_out = check_in + timedelta(days=nights)

        # Obtener política de cancelación para el hotel
        cancellation_policy = CancellationPolicy.resolve_for_hotel(hotel)
        if not cancellation_policy:
            self.stdout.write(
                self.style.WARNING(
                    f'⚠️  No hay política de cancelación configurada para el hotel {hotel.name}. '
                    f'La reserva se creará sin política (no se podrá cancelar desde el sistema).'
                )
            )

        # Preparar guests_data completo
        # Limpiar nombre del huésped para el email
        guest_email_base = guest_name.lower().strip().replace(' ', '.').replace("'", "").replace('"', '')
        if not guest_email_base:
            guest_email_base = "huesped"
        
        guests_data = [{
            "name": guest_name,
            "email": f"{guest_email_base}@example.com",  # Email simulado
            "is_primary": True,
            "source": "airbnb"
        }]
        # Agregar huéspedes adicionales si hay más de 1
        for i in range(2, guests + 1):
            guests_data.append({
                "name": f"Huésped {i}",
                "email": f"guest{i}@example.com",
                "is_primary": False,
                "source": "airbnb"
            })

        with transaction.atomic():
            # Verificar si ya existe una reserva con este external_id
            existing = Reservation.objects.filter(
                external_id=external_id,
                channel=ReservationChannel.AIRBNB
            ).first()

            if existing:
                self.stdout.write(
                    self.style.WARNING(
                        f'⚠️  Ya existe una reserva con external_id="{external_id}" (ID: {existing.id}). '
                        f'Se actualizará la reserva existente.'
                    )
                )
                reservation = existing
                reservation.check_in = check_in
                reservation.check_out = check_out
                reservation.guests = guests
                reservation.guests_data = guests_data
                reservation.notes = f"Reserva simulada desde Airbnb (actualizada: {timezone.now().isoformat()})"
                
                # Aplicar política de cancelación si no tiene
                if cancellation_policy and not reservation.applied_cancellation_policy:
                    reservation.applied_cancellation_policy = cancellation_policy
                
                reservation.save(skip_clean=True)
                
                # Eliminar noches existentes antes de regenerar
                from apps.reservations.models import ReservationNight
                ReservationNight.objects.filter(reservation=reservation).delete()
                
                # Recalcular noches y totales
                try:
                    generate_nights_for_reservation(reservation)
                    recalc_reservation_totals(reservation)
                    reservation.refresh_from_db()
                except Exception as e:
                    self.stdout.write(
                        self.style.WARNING(
                            f'⚠️  Error al calcular noches/totales: {str(e)}. '
                            f'La reserva se creó pero puede no tener precio calculado.'
                        )
                    )
                
                self.stdout.write(
                    self.style.SUCCESS(f'✅ Reserva actualizada: ID {reservation.id}')
                )
            else:
                # Crear nueva reserva
                reservation = Reservation(
                    hotel=hotel,
                    room=room,
                    external_id=external_id,
                    channel=ReservationChannel.AIRBNB,  # Airbnb tiene su propio canal
                    check_in=check_in,
                    check_out=check_out,
                    status=ReservationStatus.CONFIRMED,
                    guests=guests,
                    guests_data=guests_data,
                    notes=f"Reserva simulada desde Airbnb (creada: {timezone.now().isoformat()})",
                    applied_cancellation_policy=cancellation_policy,  # Aplicar política si existe
                )
                # Guardar saltando validaciones (como haría un webhook real)
                reservation.save(skip_clean=True)
                
                # Generar noches y calcular totales
                try:
                    generate_nights_for_reservation(reservation)
                    recalc_reservation_totals(reservation)
                    reservation.refresh_from_db()
                except Exception as e:
                    self.stdout.write(
                        self.style.WARNING(
                            f'⚠️  Error al calcular noches/totales: {str(e)}. '
                            f'La reserva se creó pero puede no tener precio calculado.'
                        )
                    )
                
                self.stdout.write(
                    self.style.SUCCESS(f'✅ Reserva creada: ID {reservation.id}')
                )

        # Crear OtaSyncJob y OtaSyncLog si se solicita
        if create_job:
            job = OtaSyncJob.objects.create(
                hotel=hotel,
                provider=OtaProvider.AIRBNB,
                job_type=OtaSyncJob.JobType.PULL_RESERVATIONS,
                status=OtaSyncJob.JobStatus.SUCCESS,
                stats={
                    "simulated": True,
                    "source": "management_command",
                    "provider": "airbnb",
                },
            )
            OtaSyncLog.objects.create(
                job=job,
                level=OtaSyncLog.Level.INFO,
                message="RESERVATION_CREATED",
                payload={
                    "reservation_id": reservation.id,
                    "external_id": external_id,
                    "source": "airbnb",
                    "channel": "other",
                    "check_in": check_in.isoformat(),
                    "check_out": check_out.isoformat(),
                    "room_id": room.id,
                    "provider": "airbnb",
                    "status": "success",
                    "simulated": True,
                },
            )
            self.stdout.write(
                self.style.SUCCESS(f'✅ OtaSyncJob y OtaSyncLog creados (Job ID: {job.id})')
            )

        # Refrescar reserva para obtener datos actualizados
        reservation.refresh_from_db()
        
        # Mostrar resumen
        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS('=' * 60))
        self.stdout.write(self.style.SUCCESS('Resumen de la reserva simulada:'))
        self.stdout.write(self.style.SUCCESS('=' * 60))
        self.stdout.write(f'  ID de Reserva: {reservation.id}')
        self.stdout.write(f'  External ID (Airbnb): {reservation.external_id}')
        self.stdout.write(f'  Canal: {reservation.get_channel_display()} ({reservation.channel})')
        self.stdout.write(f'  Hotel: {hotel.name}')
        self.stdout.write(f'  Habitación: {room.name}')
        self.stdout.write(f'  Check-in: {reservation.check_in}')
        self.stdout.write(f'  Check-out: {reservation.check_out}')
        self.stdout.write(f'  Noches: {nights}')
        self.stdout.write(f'  Huéspedes: {reservation.guests}')
        self.stdout.write(f'  Estado: {reservation.get_status_display()}')
        
        # Mostrar información de huéspedes
        guest_name_display = reservation.guest_name or 'N/A'
        guest_email_display = reservation.guest_email or 'N/A'
        self.stdout.write(f'  Nombre del huésped: {guest_name_display}')
        self.stdout.write(f'  Email del huésped: {guest_email_display}')
        
        # Mostrar precio
        total_price_display = f'${reservation.total_price:.2f}' if reservation.total_price else '$0.00'
        self.stdout.write(f'  Precio total: {total_price_display}')
        
        # Mostrar política de cancelación
        if reservation.applied_cancellation_policy:
            self.stdout.write(f'  Política de cancelación: {reservation.applied_cancellation_policy.name} ✅')
        else:
            self.stdout.write(self.style.WARNING('  ⚠️  Política de cancelación: No aplicada'))
        
        self.stdout.write(self.style.SUCCESS('=' * 60))
        self.stdout.write('')
        
        # Mensaje final
        if reservation.applied_cancellation_policy and reservation.total_price:
            self.stdout.write(
                self.style.SUCCESS(
                    f'✅ La reserva está completa y lista para usar. Aparecerá en la gestión de reservas '
                    f'con el badge de canal "Otro" y podrá cancelarse desde el sistema.'
                )
            )
        elif not reservation.applied_cancellation_policy:
            self.stdout.write(
                self.style.WARNING(
                    f'⚠️  La reserva se creó pero NO tiene política de cancelación. '
                    f'No se podrá cancelar desde el sistema hasta que se asigne una política.'
                )
            )
        else:
            self.stdout.write(
                self.style.SUCCESS(
                    f'✅ La reserva se creó correctamente. Verifica que tenga precio calculado.'
                )
            )

