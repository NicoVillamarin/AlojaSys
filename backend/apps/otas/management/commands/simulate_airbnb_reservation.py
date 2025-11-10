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
from apps.otas.services.ota_reservation_service import OtaReservationService, PaymentInfo
from apps.reservations.models import Payment
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
        parser.add_argument(
            '--paid-by-ota',
            action='store_true',
            help='Marcar la reserva como pagada por OTA (default: hotel)'
        )
        parser.add_argument(
            '--payment-source',
            type=str,
            choices=['ota_payout', 'ota_vcc'],
            default='ota_payout',
            help='Tipo de pago OTA: ota_payout (payout) o ota_vcc (tarjeta virtual)'
        )
        parser.add_argument(
            '--gross-amount',
            type=float,
            help='Monto bruto pagado por el huésped a la OTA'
        )
        parser.add_argument(
            '--commission-amount',
            type=float,
            help='Comisión de la OTA (por defecto: 15%% del monto bruto)'
        )
        parser.add_argument(
            '--payout-date',
            type=str,
            help='Fecha estimada de payout OTA (YYYY-MM-DD). Por defecto: check-in + 7 días'
        )
        parser.add_argument(
            '--currency',
            type=str,
            default='ARS',
            help='Moneda (default: ARS)'
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
        paid_by_ota = options.get('paid_by_ota', False)
        payment_source = options.get('payment_source', 'ota_payout')
        gross_amount = options.get('gross_amount')
        commission_amount = options.get('commission_amount')
        payout_date_str = options.get('payout_date')
        currency = options.get('currency', 'ARS')

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

        # Preparar PaymentInfo si se solicita pago OTA
        payment_info = None
        if paid_by_ota:
            # Calcular montos si no se proporcionaron
            if gross_amount is None:
                # Estimar monto bruto basado en precio de la habitación (si ya está calculado)
                # Por ahora usamos un valor por defecto
                gross_amount = 100000.0  # Valor por defecto
                self.stdout.write(
                    self.style.WARNING(
                        f'⚠️  No se proporcionó --gross-amount. Usando valor por defecto: ${gross_amount:.2f}'
                    )
                )
            
            if commission_amount is None:
                # Por defecto: 15% del monto bruto
                commission_amount = gross_amount * 0.15
                self.stdout.write(
                    self.style.SUCCESS(
                        f'💰 Comisión calculada automáticamente (15%%): ${commission_amount:.2f}'
                    )
                )
            
            net_amount = gross_amount - commission_amount
            
            # Calcular fecha de payout si no se proporciona
            payout_date = None
            if payout_date_str:
                try:
                    payout_date = date.fromisoformat(payout_date_str)
                except ValueError:
                    self.stdout.write(
                        self.style.WARNING(
                            f'⚠️  Fecha de payout inválida: {payout_date_str}. Usando fecha por defecto.'
                        )
                    )
                    payout_date = check_in + timedelta(days=7)
            else:
                payout_date = check_in + timedelta(days=7)
            
            payment_info = PaymentInfo(
                paid_by="ota",
                payment_source=payment_source,
                provider="airbnb",
                external_reference=f"AB_TX_{external_id}",
                currency=currency,
                gross_amount=gross_amount,
                commission_amount=commission_amount,
                net_amount=net_amount,
                payout_date=payout_date,
            )

        # Usar OtaReservationService para crear/actualizar con soporte de pagos OTA
        with transaction.atomic():
            result = OtaReservationService.upsert_reservation(
                hotel=hotel,
                room=room,
                external_id=external_id,
                channel=ReservationChannel.AIRBNB,
                check_in=check_in,
                check_out=check_out,
                guests=guests,
                guests_data=guests_data,
                notes=f"Reserva simulada desde Airbnb (creada: {timezone.now().isoformat()})",
                payment_info=payment_info,
            )
            
            reservation = Reservation.objects.get(id=result['reservation_id'])
            
            # Aplicar política de cancelación si no tiene
            if cancellation_policy and not reservation.applied_cancellation_policy:
                reservation.applied_cancellation_policy = cancellation_policy
                reservation.save(update_fields=["applied_cancellation_policy"])
            
            # Generar noches y calcular totales si no existen
            from apps.reservations.models import ReservationNight
            if not reservation.nights.exists():
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
            
            if result['created']:
                self.stdout.write(
                    self.style.SUCCESS(f'✅ Reserva creada: ID {reservation.id}')
                )
            else:
                self.stdout.write(
                    self.style.SUCCESS(f'✅ Reserva actualizada: ID {reservation.id}')
                )
            
            if result.get('overbooking'):
                self.stdout.write(
                    self.style.WARNING(
                        f'⚠️  Overbooking detectado: hay otras reservas activas que se superponen.'
                    )
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
        
        # Mostrar información de pago OTA
        if reservation.paid_by:
            paid_by_display = reservation.get_paid_by_display() if hasattr(reservation, 'get_paid_by_display') else reservation.paid_by
            self.stdout.write(f'  Origen de pago: {paid_by_display}')
            
            if reservation.paid_by == Reservation.PaidBy.OTA:
                # Buscar el Payment asociado
                payment = Payment.objects.filter(
                    reservation=reservation,
                    payment_source__in=['ota_payout', 'ota_vcc']
                ).first()
                
                if payment:
                    self.stdout.write(f'  💳 Pago OTA registrado:')
                    self.stdout.write(f'     - Tipo: {payment.get_payment_source_display() if hasattr(payment, "get_payment_source_display") else payment.payment_source}')
                    self.stdout.write(f'     - Bruto: ${payment.gross_amount:.2f}')
                    self.stdout.write(f'     - Comisión: ${payment.commission_amount:.2f}')
                    self.stdout.write(f'     - Neto: ${payment.net_amount:.2f}')
                    self.stdout.write(f'     - Estado: {payment.status}')
                    if payment.payout_date:
                        self.stdout.write(f'     - Payout estimado: {payment.payout_date}')
                    if payment.external_reference:
                        self.stdout.write(f'     - Ref. externa: {payment.external_reference}')
                else:
                    self.stdout.write(self.style.WARNING('     ⚠️  No se encontró Payment asociado'))
        
        # Mostrar overbooking flag
        if reservation.overbooking_flag:
            self.stdout.write(self.style.WARNING('  ⚠️  Overbooking: Sí (hay otras reservas que se superponen)'))
        
        # Mostrar política de cancelación
        if reservation.applied_cancellation_policy:
            self.stdout.write(f'  Política de cancelación: {reservation.applied_cancellation_policy.name} ✅')
        else:
            self.stdout.write(self.style.WARNING('  ⚠️  Política de cancelación: No aplicada'))
        
        self.stdout.write(self.style.SUCCESS('=' * 60))
        self.stdout.write('')
        
        # Mensaje final
        payment_status_msg = ""
        if reservation.paid_by == Reservation.PaidBy.OTA:
            payment_status_msg = " y aparece como 'Pagada por OTA' en el frontend"
        
        if reservation.applied_cancellation_policy and reservation.total_price:
            self.stdout.write(
                self.style.SUCCESS(
                    f'✅ La reserva está completa y lista para usar. Aparecerá en la gestión de reservas '
                    f'con el badge de canal "Airbnb"{payment_status_msg} y podrá cancelarse desde el sistema.'
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
        
        if paid_by_ota:
            self.stdout.write(
                self.style.SUCCESS(
                    f'\n💡 La reserva está marcada como pagada por OTA. '
                    f'Verifica en el frontend que aparezca el badge "Pagada por OTA" y '
                    f'que el Payment esté en estado "pending_settlement" para conciliación.'
                )
            )

