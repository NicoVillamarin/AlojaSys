from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Optional, Dict, Any

from django.db import transaction
from django.utils import timezone

from apps.reservations.models import Reservation, ReservationStatus, ReservationChannel, Payment, ChannelCommission
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
            reservation.save(skip_clean=True)
            created = True

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
        if created and provider_name:
            try:
                # Obtener nombre del huésped principal
                guest_name = ""
                if guests_data:
                    primary_guest = next((g for g in guests_data if g.get('is_primary', False)), guests_data[0] if guests_data else None)
                    if primary_guest:
                        guest_name = primary_guest.get('name', '')
                
                NotificationService.create_ota_reservation_notification(
                    provider_name=provider_name,
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


