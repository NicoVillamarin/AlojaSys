from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from apps.reservations.models import Reservation, ReservationChangeLog, ReservationStatusChange, ReservationChangeEvent, ReservationChannel, ReservationStatus
from .services.pricing import generate_nights_for_reservation, recalc_reservation_totals
from django.conf import settings
from .models import Reservation, ReservationCharge, ChannelCommission
from .services.audit import build_snapshot, build_diff
from .middleware import get_current_user

AUDIT_FIELDS = [
    "room_id",
    "check_in",
    "check_out",
    "guests",
    "guests_data",
    "status",
    "channel",
    "notes",
]

def _should_autogenerate_pricing(reservation: Reservation) -> bool:
    """
    Para reservas que entran vía Smoobu (external_id prefijo 'smoobu:'), el total real
    puede venir desde el channel manager y nosotros generamos nights "planas" para
    mantener coherencia. En ese caso NO debemos regenerar nights con el motor interno
    porque pisa el total OTA.
    """
    try:
        ext = str(getattr(reservation, "external_id", "") or "")
    except Exception:
        ext = ""
    if ext.startswith("smoobu:"):
        return False
    return True

def upsert_channel_commission(reservation: Reservation):
    from decimal import Decimal
    # Si la reserva ya tiene una comisión (especialmente de OTA), no sobrescribirla
    existing = ChannelCommission.objects.filter(reservation=reservation).first()
    if existing:
        # Si ya existe y tiene un amount > 0, probablemente fue creada por OtaReservationService
        # No sobrescribirla para evitar conflictos
        return
    
    rates = getattr(settings, "CHANNEL_COMMISSION_RATES", {})
    rate = Decimal(str(rates.get(reservation.channel, 0)))
    if rate == 0:
        # Si no hay tasa configurada, no crear comisión
        return
    
    amount = (reservation.total_price or Decimal('0.00')) * (rate / Decimal('100'))
    if amount > 0:
        ChannelCommission.objects.update_or_create(
            reservation=reservation,
            defaults={'channel': reservation.channel, 'rate_percent': rate, 'amount': amount},
        )

@receiver(post_save, sender=Reservation)
def reservation_post_save_first(sender, instance: Reservation, created, **kwargs):
    if not instance.check_in or not instance.check_out or not instance.room_id:
        return
    if _should_autogenerate_pricing(instance):
        generate_nights_for_reservation(instance)
        recalc_reservation_totals(instance)
    upsert_channel_commission(instance)

@receiver(pre_save, sender=Reservation)
def reservation_pre_save(sender, instance: Reservation, **kwargs):
    if instance.pk:
        try:
            instance._prev = Reservation.objects.get(pk=instance.pk)
        except Reservation.DoesNotExist:
            instance._prev = None
    else:
        instance._prev = None

@receiver(post_save, sender=Reservation)
def reservation_post_save_log(sender, instance: Reservation, created, **kwargs):
    if instance.check_in and instance.check_out and instance.room_id:
        if _should_autogenerate_pricing(instance):
            generate_nights_for_reservation(instance)
            recalc_reservation_totals(instance)

    prev = getattr(instance, "_prev", None)
    user = get_current_user()

    if created:
        room_name = getattr(getattr(instance, "room", None), "name", "Habitación")
        msg = (
            f"Reserva #{instance.id} creada: "
            f"{instance.guest_name or 'Sin nombre'} • {room_name} • "
            f"{instance.check_in} → {instance.check_out}"
        )
        ReservationChangeLog.objects.create(
            reservation=instance,
            event_type=ReservationChangeEvent.CREATED,
            changed_by=user if user is not None else None,
            fields_changed={},
            snapshot=build_snapshot(instance),
            message=msg,
        )
        return

    changed = build_diff(prev, instance, AUDIT_FIELDS) if prev else {}
    if changed:
        ReservationChangeLog.objects.create(
            reservation=instance,
            event_type=ReservationChangeEvent.UPDATED,
            changed_by=user if user is not None else None,
            fields_changed=changed,
            snapshot=build_snapshot(instance),
            message=f"Reserva actualizada: {instance.id}",
        )
    
    if prev and prev.status != instance.status:
        ReservationStatusChange.objects.create(
            reservation=instance,
            from_status=prev.status,
            to_status=instance.status,
            changed_by=user if user is not None else None,
            notes=f"Estado actualizado: {instance.status}",
        )
        ReservationChangeLog.objects.create(
            reservation=instance,
            event_type=ReservationChangeEvent.STATUS_CHANGED,
            changed_by=user if user is not None else None,
            fields_changed={"status": {"old": prev.status, "new": instance.status}},
            snapshot=build_snapshot(instance),
        )


@receiver(post_save, sender=Reservation)
def reservation_export_to_google(sender, instance: Reservation, created, **kwargs):
    """Exporta reservas a Google Calendar cuando se crean/actualizan."""
    import logging
    logger = logging.getLogger(__name__)
    
    # Solo procesar si tiene fechas y habitación
    if not instance.check_in or not instance.check_out or not instance.room_id:
        logger.debug(f"Reservation {instance.id}: Skipping Google export - missing dates or room")
        return
    
    # Solo exportar si NO viene de Google Calendar (evitar loops)
    if instance.channel == ReservationChannel.OTHER and instance.notes and 'google calendar' in instance.notes.lower():
        logger.debug(f"Reservation {instance.id}: Skipping Google export - came from Google Calendar")
        return
    
    try:
        from django.db import transaction
        from apps.otas.services.google_sync_service import export_reservation_to_google, delete_reservation_from_google

        def _run():
            try:
                # Si se cancela, eliminar de Google
                if instance.status == ReservationStatus.CANCELLED:
                    result = delete_reservation_from_google(instance)
                    logger.info(f"Reservation {instance.id}: Google Calendar delete result: {result}")
                # Si está confirmada, exportar/actualizar
                elif instance.status == ReservationStatus.CONFIRMED:
                    result = export_reservation_to_google(instance)
                    logger.info(f"Reservation {instance.id}: Google Calendar export result: {result}")
                    if result.get("status") != "ok":
                        logger.warning(f"Reservation {instance.id}: Google Calendar export failed: {result}")
            except Exception as e:
                logger.error(f"Reservation {instance.id}: Error exporting to Google Calendar: {str(e)}", exc_info=True)

        # Ejecutar después del commit para evitar inconsistencias
        transaction.on_commit(_run)
    except Exception as e:
        logger.error(f"Reservation {instance.id}: Error scheduling Google Calendar export: {str(e)}", exc_info=True)