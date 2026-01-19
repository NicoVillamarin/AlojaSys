from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta
from typing import Optional, Dict, Any

from decimal import Decimal

from django.db import transaction
from django.utils import timezone

from apps.reservations.models import (
    Reservation,
    ReservationStatus,
    ReservationChannel,
    Payment,
    ChannelCommission,
    ReservationNight,
)
from apps.notifications.services import NotificationService


@dataclass
class PaymentInfo:
    paid_by: Optional[str] = None  # "ota" | "hotel"
    payment_source: Optional[str] = None  # Payment.PaymentSource.*
    provider: Optional[str] = None  # booking | airbnb | expedia
    external_reference: Optional[str] = None
    currency: Optional[str] = None
    gross_amount: Optional[float] = None
    commission_amount: Optional[float] = None
    net_amount: Optional[float] = None
    activation_date: Optional[date] = None
    payout_date: Optional[date] = None


class OtaReservationService:
    @staticmethod
    def _to_decimal(val: Any) -> Decimal | None:
        if val is None:
            return None
        try:
            s = str(val).strip()
            if not s:
                return None
            # Normalizar coma decimal si llegara a venir así
            s = s.replace(",", ".")
            d = Decimal(s).quantize(Decimal("0.01"))
            if d <= 0:
                return None
            return d
        except Exception:
            return None

    @staticmethod
    def _apply_ota_total_price(reservation: Reservation, ota_total_price: Decimal) -> None:
        """
        Para reservas OTA, si tenemos un total real desde el channel manager (Smoobu),
        lo usamos como total_price y generamos nights "planas" para que:
        - total_price sea coherente con lo que se ve en OTAs
        - recálculos posteriores no lo pisen con base_price
        """
        if not reservation or not getattr(reservation, "external_id", None):
            return

        nights_count = (reservation.check_out - reservation.check_in).days if (reservation.check_in and reservation.check_out) else 0
        if nights_count <= 0:
            return

        # Reemplazar noches existentes por un prorrateo simple
        ReservationNight.objects.filter(reservation=reservation).delete()

        base = (ota_total_price / Decimal(nights_count)).quantize(Decimal("0.01"))
        # Ajuste en la última noche para que la suma dé exacta (por redondeo)
        running = Decimal("0.00")
        current = reservation.check_in
        for idx in range(nights_count):
            amount = base
            if idx == nights_count - 1:
                amount = (ota_total_price - running).quantize(Decimal("0.01"))
            ReservationNight.objects.create(
                reservation=reservation,
                hotel=reservation.hotel,
                room=reservation.room,
                date=current,
                base_rate=amount,
                extra_guest_fee=Decimal("0.00"),
                discount=Decimal("0.00"),
                tax=Decimal("0.00"),
                total_night=amount,
            )
            running += amount
            current = current + timedelta(days=1)

        # Setear total_price sin disparar save() (evitar recalcular por base_price)
        type(reservation).objects.filter(pk=reservation.pk).update(total_price=ota_total_price)
        reservation.total_price = ota_total_price

    @staticmethod
    def _channel_label(channel_value: str) -> str:
        """
        Label humano del canal para UI/notificaciones.
        Nota: No usamos gettext acá para mantenerlo simple y consistente con el resto.
        """
        return {
            ReservationChannel.BOOKING: "Booking",
            ReservationChannel.AIRBNB: "Airbnb",
            ReservationChannel.EXPEDIA: "Expedia",
            ReservationChannel.DIRECT: "Directa",
            ReservationChannel.OTHER: "Otro",
        }.get(channel_value, str(channel_value or "Otro"))

    @staticmethod
    def _provider_display_name(provider_name: str | None, external_id: str, channel_value: str) -> str | None:
        """
        Para reservas que entran vía Smoobu, queremos mostrar el canal real + " - Smoobu"
        en notificaciones (ej: "Booking - Smoobu"), porque Smoobu es el intermediario.
        """
        if not provider_name:
            return None
        try:
            ext = str(external_id or "")
        except Exception:
            ext = ""

        # Caso Smoobu: external_id con prefijo "smoobu:" (tanto webhook como pull)
        if ext.startswith("smoobu:"):
            base = OtaReservationService._channel_label(channel_value or ReservationChannel.OTHER)
            # Evitar "Otro - Smoobu" si quedó sin mapping de canal
            if base.lower() in ("otro", "other"):
                return "Smoobu"
            return f"{base} - Smoobu"

        return provider_name

    @staticmethod
    @transaction.atomic
    def upsert_reservation(
        *,
        hotel,
        room,
        external_id: str,
        channel: str,
        check_in: date,
        check_out: date,
        guests: int,
        guests_data: list,
        notes: str | None = None,
        ota_total_price: float | str | Decimal | None = None,
        payment_info: PaymentInfo | None = None,
        auto_confirm: bool = True,
        provider_name: str | None = None,
    ) -> Dict[str, Any]:
        """
        Crea/actualiza una reserva OTA de forma tolerante a solapes y registra información de pago OTA si aplica.
        """
        assert external_id, "external_id es requerido para reservas OTA"
        channel_value = channel or ReservationChannel.OTHER

        reservation = (
            Reservation.objects.select_for_update()
            .filter(hotel=hotel, external_id=str(external_id), channel=channel_value)
            .first()
        )

        created = False
        ota_total_dec = OtaReservationService._to_decimal(ota_total_price)
        if reservation:
            # Actualización mínima
            changed = False
            if reservation.room_id != room.id:
                reservation.room = room
                changed = True
            if reservation.check_in != check_in or reservation.check_out != check_out:
                reservation.check_in = check_in
                reservation.check_out = check_out
                changed = True
            if reservation.guests != guests:
                reservation.guests = guests
                changed = True
            if guests_data:
                reservation.guests_data = guests_data
                changed = True
            if notes:
                reservation.notes = (reservation.notes or "") + f"\n{notes}"
                changed = True
            # Si nos llega el total OTA real, lo actualizamos aunque no haya otros cambios
            if ota_total_dec is not None and reservation.total_price != ota_total_dec:
                reservation.total_price = ota_total_dec
                changed = True
            if reservation.status == ReservationStatus.PENDING and auto_confirm:
                reservation.status = ReservationStatus.CONFIRMED
                changed = True
            if changed:
                reservation.save(skip_clean=True)
        else:
            # Crear con skip_clean para tolerar solapes
            reservation = Reservation(
                hotel=hotel,
                room=room,
                external_id=str(external_id),
                channel=channel_value,
                check_in=check_in,
                check_out=check_out,
                status=ReservationStatus.CONFIRMED if auto_confirm else ReservationStatus.PENDING,
                guests=guests,
                guests_data=guests_data or [],
                notes=notes or "",
            )
            if ota_total_dec is not None:
                reservation.total_price = ota_total_dec
            reservation.save(skip_clean=True)
            created = True

        # Si tenemos total OTA real, dejamos el total coherente con OTAs y generamos nights planas.
        if ota_total_dec is not None:
            try:
                OtaReservationService._apply_ota_total_price(reservation, ota_total_dec)
            except Exception:
                # No romper import OTA por falla en nights; el total ya quedó seteado arriba.
                pass

        # Asegurar política de cancelación aplicada (necesaria para UI de cancelación)
        # Las reservas OTA se crean por servicio (no por ReservationSerializer), así que la asignamos acá.
        if not getattr(reservation, "applied_cancellation_policy_id", None):
            try:
                from apps.payments.models import CancellationPolicy
                policy = CancellationPolicy.resolve_for_hotel(reservation.hotel)
                if policy:
                    reservation.applied_cancellation_policy = policy
                    reservation.save(update_fields=["applied_cancellation_policy"])
            except Exception:
                # No romper el flujo de import OTA si falla la asignación
                pass

        # Marcar overbooking_flag si hay otras reservas activas que se superponen
        active_status = [
            ReservationStatus.PENDING,
            ReservationStatus.CONFIRMED,
            ReservationStatus.CHECK_IN,
        ]
        overlap_qs = (
            Reservation.objects.filter(
                hotel=reservation.hotel,
                room=reservation.room,
                status__in=active_status,
                check_in__lt=reservation.check_out,
                check_out__gt=reservation.check_in,
            )
            .exclude(pk=reservation.pk)
        )
        has_overlap = overlap_qs.exists()
        if has_overlap and not reservation.overbooking_flag:
            reservation.overbooking_flag = True
            reservation.save(update_fields=["overbooking_flag"])  # no necesita skip_clean

        # Registrar pago/conciliación si corresponde
        if payment_info and payment_info.paid_by:
            reservation.paid_by = payment_info.paid_by
            reservation.save(update_fields=["paid_by"])  # no necesita skip_clean

            if payment_info.paid_by == Reservation.PaidBy.OTA and payment_info.payment_source:
                gross = payment_info.gross_amount or 0
                commission = payment_info.commission_amount or 0
                net = payment_info.net_amount if payment_info.net_amount is not None else (gross - commission)

                pay = Payment.objects.create(
                    reservation=reservation,
                    date=timezone.now().date(),
                    method="ota",
                    amount=net,
                    currency=payment_info.currency or "ARS",
                    status="pending_settlement",
                    payment_source=payment_info.payment_source,
                    provider=payment_info.provider,
                    external_reference=payment_info.external_reference,
                    gross_amount=gross,
                    commission_amount=commission,
                    net_amount=net,
                    activation_date=payment_info.activation_date,
                    payout_date=payment_info.payout_date,
                    metadata={
                        "source": "ota",
                        "details": {
                            "gross": gross,
                            "commission": commission,
                            "net": net,
                        },
                    },
                )

                # Registrar comisión del canal si hay dato (usar update_or_create para evitar duplicados)
                if commission and commission > 0:
                    ChannelCommission.objects.update_or_create(
                        reservation=reservation,
                        defaults={
                            'channel': channel_value,
                            'rate_percent': 0,  # desconocido; se puede actualizar luego
                            'amount': commission,
                        },
                    )

        # Generar notificación si se creó una nueva reserva y se proporcionó el nombre del provider
        provider_display_name = OtaReservationService._provider_display_name(provider_name, external_id, channel_value)
        if created and provider_display_name:
            try:
                # Obtener nombre del huésped principal
                guest_name = ""
                if guests_data:
                    primary_guest = next((g for g in guests_data if g.get('is_primary', False)), guests_data[0] if guests_data else None)
                    if primary_guest:
                        guest_name = primary_guest.get('name', '')
                
                NotificationService.create_ota_reservation_notification(
                    provider_name=provider_display_name,
                    reservation_code=f"RES-{reservation.id}",
                    room_name=room.name or f"Habitación {room.number}",
                    check_in_date=check_in.strftime("%d/%m/%Y"),
                    check_out_date=check_out.strftime("%d/%m/%Y"),
                    guest_name=guest_name,
                    hotel_id=hotel.id,
                    reservation_id=reservation.id,
                    external_id=external_id,
                    overbooking=has_overlap
                )
            except Exception as e:
                # No fallar la creación de la reserva si la notificación falla
                import logging
                logger = logging.getLogger(__name__)
                logger.warning(f"Error al crear notificación para reserva OTA {reservation.id}: {e}")

        return {
            "created": created,
            "reservation_id": reservation.id,
            "overbooking": has_overlap,
            "paid_by": reservation.paid_by,
        }


