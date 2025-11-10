"""
Management command para simular una reserva de Booking.com.

Este script crea/actualiza una reserva como si viniera de Booking, usando
el servicio central OtaReservationService (idempotente) e incluyendo datos
de pago OTA opcionales. Dispara notificación de "Nueva reserva OTA".

Uso:
    python manage.py simulate_booking_reservation --hotel 1 --room 1
    python manage.py simulate_booking_reservation --hotel 1 --room 1 --check-in 2025-12-25 --nights 3 --guests 2 --guest-name "Juan Pérez"
    python manage.py simulate_booking_reservation --hotel 1 --room 1 --paid-by-ota --gross-amount 120000 --commission-amount 18000 --payment-source ota_payout
"""

from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone
from django.db import transaction
from datetime import date, timedelta
import random

from apps.core.models import Hotel
from apps.rooms.models import Room
from apps.reservations.models import Reservation, ReservationStatus, ReservationChannel
from apps.reservations.services.pricing import generate_nights_for_reservation, recalc_reservation_totals
from apps.payments.models import CancellationPolicy
from apps.otas.models import OtaProvider, OtaSyncJob, OtaSyncLog
from apps.otas.services.ota_reservation_service import OtaReservationService, PaymentInfo
from apps.reservations.models import Payment


class Command(BaseCommand):
    help = "Simula una reserva de Booking.com y dispara notificación OTA"

    def add_arguments(self, parser):
        parser.add_argument("--hotel", type=int, required=True, help="ID del hotel para la reserva")
        parser.add_argument("--room", type=int, required=True, help="ID de la habitación para la reserva")
        parser.add_argument("--check-in", type=str, help="Fecha de check-in (YYYY-MM-DD). Por defecto: mañana")
        parser.add_argument("--nights", type=int, default=2, help="Número de noches (por defecto: 2)")
        parser.add_argument("--guests", type=int, default=1, help="Número de huéspedes (por defecto: 1)")
        parser.add_argument("--guest-name", type=str, help='Nombre del huésped (por defecto: "Huésped Booking")')
        parser.add_argument("--external-id", type=str, help="ID externo de Booking (por defecto: random booking-XXXXXX)")
        parser.add_argument("--create-job", action="store_true", help="Crear OtaSyncJob/Log simulados")

        # Pagos OTA
        parser.add_argument("--paid-by-ota", action="store_true", help="Marcar la reserva como pagada por OTA")
        parser.add_argument("--payment-source", type=str, choices=["ota_payout", "ota_vcc"], default="ota_payout",
                            help="Tipo de pago OTA")
        parser.add_argument("--gross-amount", type=float, help="Monto bruto pagado por el huésped a la OTA")
        parser.add_argument("--commission-amount", type=float, help="Comisión de la OTA (default: 15%% del bruto)")
        parser.add_argument("--payout-date", type=str, help="Fecha estimada de payout OTA (YYYY-MM-DD)")
        parser.add_argument("--currency", type=str, default="ARS", help="Moneda (default: ARS)")

    def handle(self, *args, **options):
        hotel_id = options["hotel"]
        room_id = options["room"]
        check_in_str = options.get("check_in") or options.get("check-in")
        nights = options["nights"]
        guests = options["guests"]
        guest_name = options.get("guest_name") or options.get("guest-name") or "Huésped Booking"
        external_id = options.get("external_id") or options.get("external-id") or f"booking-{random.randint(100000, 999999)}"
        create_job = options.get("create_job", False)

        paid_by_ota = options.get("paid_by_ota", False)
        payment_source = options.get("payment_source", "ota_payout")
        gross_amount = options.get("gross_amount")
        commission_amount = options.get("commission_amount")
        payout_date_str = options.get("payout_date")
        currency = options.get("currency", "ARS")

        # Validar hotel
        try:
            hotel = Hotel.objects.get(id=hotel_id)
        except Hotel.DoesNotExist:
            raise CommandError(f"Hotel con ID {hotel_id} no existe.")

        # Validar habitación
        try:
            room = Room.objects.get(id=room_id, hotel=hotel)
        except Room.DoesNotExist:
            raise CommandError(f"Habitación con ID {room_id} no existe en el hotel {hotel.name}.")

        # Capacidad
        max_capacity = room.max_capacity if room.max_capacity else 1
        if guests > max_capacity:
            self.stdout.write(self.style.WARNING(
                f"⚠️  La habitación {room.name} tiene capacidad máxima de {max_capacity}. Se usará {max_capacity}."))
            guests = max_capacity
        if guests < 1:
            guests = 1
            self.stdout.write(self.style.WARNING("⚠️  Se ajustó el número de huéspedes a 1 (mínimo)."))

        # Fechas
        if check_in_str:
            try:
                check_in = date.fromisoformat(check_in_str)
            except ValueError:
                raise CommandError(f"Fecha de check-in inválida: {check_in_str}. Use YYYY-MM-DD.")
        else:
            check_in = date.today() + timedelta(days=1)
        if check_in < date.today():
            raise CommandError(f"La fecha de check-in ({check_in}) no puede ser en el pasado.")
        check_out = check_in + timedelta(days=nights)

        # Política de cancelación
        cancellation_policy = CancellationPolicy.resolve_for_hotel(hotel)
        if not cancellation_policy:
            self.stdout.write(self.style.WARNING(
                f"⚠️  No hay política de cancelación configurada para el hotel {hotel.name}."))

        # Guests data
        guest_email_base = guest_name.lower().strip().replace(" ", ".").replace("'", "").replace('"', '')
        if not guest_email_base:
            guest_email_base = "huesped"
        guests_data = [{
            "name": guest_name,
            "email": f"{guest_email_base}@example.com",
            "is_primary": True,
            "source": "booking"
        }]
        for i in range(2, guests + 1):
            guests_data.append({
                "name": f"Huésped {i}",
                "email": f"guest{i}@example.com",
                "is_primary": False,
                "source": "booking"
            })

        # Pago OTA opcional
        payment_info = None
        if paid_by_ota:
            if gross_amount is None:
                gross_amount = 100000.0
                self.stdout.write(self.style.WARNING(
                    f"⚠️  No se proporcionó --gross-amount. Usando: ${gross_amount:.2f}"))
            if commission_amount is None:
                commission_amount = gross_amount * 0.15
                self.stdout.write(self.style.SUCCESS(
                    f"💰 Comisión calculada 15%: ${commission_amount:.2f}"))
            net_amount = gross_amount - commission_amount
            payout_date = None
            if payout_date_str:
                try:
                    payout_date = date.fromisoformat(payout_date_str)
                except ValueError:
                    self.stdout.write(self.style.WARNING(
                        f"⚠️  Fecha de payout inválida: {payout_date_str}. Usando check_in+7."))
                    payout_date = check_in + timedelta(days=7)
            else:
                payout_date = check_in + timedelta(days=7)

            payment_info = PaymentInfo(
                paid_by="ota",
                payment_source=payment_source,
                provider="booking",
                external_reference=f"BK_TX_{external_id}",
                currency=currency,
                gross_amount=gross_amount,
                commission_amount=commission_amount,
                net_amount=net_amount,
                payout_date=payout_date,
            )

        # Crear/actualizar con notificación
        with transaction.atomic():
            result = OtaReservationService.upsert_reservation(
                hotel=hotel,
                room=room,
                external_id=external_id,
                channel=ReservationChannel.BOOKING,
                check_in=check_in,
                check_out=check_out,
                guests=guests,
                guests_data=guests_data,
                notes=f"Reserva simulada desde Booking (creada: {timezone.now().isoformat()})",
                payment_info=payment_info,
                provider_name=OtaProvider.BOOKING.label,  # <- dispara notificación al crear
            )

            reservation = Reservation.objects.get(id=result["reservation_id"])

            # Política de cancelación
            if cancellation_policy and not reservation.applied_cancellation_policy:
                reservation.applied_cancellation_policy = cancellation_policy
                reservation.save(update_fields=["applied_cancellation_policy"])

            # Noches y totales
            from apps.reservations.models import ReservationNight
            if not reservation.nights.exists():
                try:
                    generate_nights_for_reservation(reservation)
                    recalc_reservation_totals(reservation)
                    reservation.refresh_from_db()
                except Exception as e:
                    self.stdout.write(self.style.WARNING(
                        f"⚠️  Error al calcular noches/totales: {str(e)}"))

            if result["created"]:
                self.stdout.write(self.style.SUCCESS(f"✅ Reserva creada: ID {reservation.id}"))
            else:
                self.stdout.write(self.style.SUCCESS(f"✅ Reserva actualizada: ID {reservation.id}"))

            if result.get("overbooking"):
                self.stdout.write(self.style.WARNING("⚠️  Overbooking detectado."))

        # OtaSyncJob simulado
        if create_job:
            job = OtaSyncJob.objects.create(
                hotel=hotel,
                provider=OtaProvider.BOOKING,
                job_type=OtaSyncJob.JobType.PULL_RESERVATIONS,
                status=OtaSyncJob.JobStatus.SUCCESS,
                stats={"simulated": True, "source": "management_command", "provider": "booking"},
            )
            OtaSyncLog.objects.create(
                job=job,
                level=OtaSyncLog.Level.INFO,
                message="RESERVATION_CREATED",
                payload={
                    "reservation_id": reservation.id,
                    "external_id": external_id,
                    "source": "booking",
                    "channel": "booking",
                    "check_in": check_in.isoformat(),
                    "check_out": check_out.isoformat(),
                    "room_id": room.id,
                    "provider": "booking",
                    "status": "success",
                    "simulated": True,
                },
            )
            self.stdout.write(self.style.SUCCESS(f"✅ OtaSyncJob/Log creados (Job ID: {job.id})"))

        # Resumen final
        reservation.refresh_from_db()
        self.stdout.write("")
        self.stdout.write(self.style.SUCCESS("=" * 60))
        self.stdout.write(self.style.SUCCESS("Resumen de la reserva simulada (Booking):"))
        self.stdout.write(self.style.SUCCESS("=" * 60))
        self.stdout.write(f"  ID de Reserva: {reservation.id}")
        self.stdout.write(f"  External ID (Booking): {reservation.external_id}")
        self.stdout.write(f"  Canal: {reservation.get_channel_display()} ({reservation.channel})")
        self.stdout.write(f"  Hotel: {hotel.name}")
        self.stdout.write(f"  Habitación: {room.name}")
        self.stdout.write(f"  Check-in: {reservation.check_in}")
        self.stdout.write(f"  Check-out: {reservation.check_out}")
        self.stdout.write(f"  Noches: {nights}")
        self.stdout.write(f"  Huéspedes: {reservation.guests}")
        self.stdout.write(f"  Estado: {reservation.get_status_display()}")
        if reservation.total_price:
            self.stdout.write(f"  Precio total: ${reservation.total_price:.2f}")
        if reservation.overbooking_flag:
            self.stdout.write(self.style.WARNING("  ⚠️  Overbooking: Sí"))
        if reservation.applied_cancellation_policy:
            self.stdout.write("  Política de cancelación: OK")
        else:
            self.stdout.write(self.style.WARNING("  ⚠️  Política de cancelación: No aplicada"))
        self.stdout.write(self.style.SUCCESS("=" * 60))
        self.stdout.write("")


