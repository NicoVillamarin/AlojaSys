"""
Señales (signals) para eventos internos del sistema de pagos
Permite notificar cambios de estado de pagos a otros módulos del sistema
"""
from django.dispatch import Signal
from django.dispatch import receiver
from django.db.models.signals import post_save
from apps.payments.models import PaymentIntent, PaymentIntentStatus
import logging

logger = logging.getLogger(__name__)

# Señales personalizadas para eventos de pago
payment_approved = Signal()
payment_rejected = Signal()
payment_created = Signal()
payment_updated = Signal()

# Señales para eventos de reembolso
refund_created = Signal()
refund_approved = Signal()
refund_rejected = Signal()
refund_completed = Signal()

# Señales para eventos de voucher
voucher_created = Signal()
voucher_used = Signal()
voucher_expired = Signal()


@receiver(post_save, sender=PaymentIntent)
def payment_intent_changed(sender, instance, created, **kwargs):
    """
    Maneja cambios en PaymentIntent y emite eventos apropiados
    """
    if created:
        # Nuevo PaymentIntent creado
        payment_created.send(
            sender=PaymentIntent,
            instance=instance,
            status=instance.status,
            created=True
        )
        logger.info(f"PaymentIntent creado: {instance.id} - Status: {instance.status}")
    else:
        # PaymentIntent actualizado
        payment_updated.send(
            sender=PaymentIntent,
            instance=instance,
            status=instance.status,
            created=False
        )
        logger.info(f"PaymentIntent actualizado: {instance.id} - Status: {instance.status}")


def emit_payment_event(event_type: str, payment_intent: PaymentIntent, **kwargs):
    """
    Función helper para emitir eventos de pago de forma consistente
    
    Args:
        event_type: Tipo de evento ('payment:approved', 'payment:rejected', etc.)
        payment_intent: Instancia del PaymentIntent
        **kwargs: Datos adicionales del evento
    """
    event_data = {
        'payment_intent_id': payment_intent.id,
        'reservation_id': payment_intent.reservation_id,
        'hotel_id': payment_intent.hotel_id,
        'amount': str(payment_intent.amount),
        'currency': payment_intent.currency,
        'status': payment_intent.status,
        'external_reference': payment_intent.external_reference,
        'mp_payment_id': payment_intent.mp_payment_id,
        'created_at': payment_intent.created_at.isoformat(),
        'updated_at': payment_intent.updated_at.isoformat(),
        **kwargs
    }
    
    # Emitir señal específica según el tipo de evento
    if event_type == 'payment:approved':
        payment_approved.send(
            sender=PaymentIntent,
            instance=payment_intent,
            event_data=event_data
        )
    elif event_type == 'payment:rejected':
        payment_rejected.send(
            sender=PaymentIntent,
            instance=payment_intent,
            event_data=event_data
        )
    elif event_type == 'payment:created':
        payment_created.send(
            sender=PaymentIntent,
            instance=payment_intent,
            event_data=event_data
        )
    elif event_type == 'payment:updated':
        payment_updated.send(
            sender=PaymentIntent,
            instance=payment_intent,
            event_data=event_data
        )
    else:
        logger.warning(f"Tipo de evento de pago no reconocido: {event_type}")
    
    # Log del evento
    logger.info(
        f"Evento de pago emitido: {event_type}",
        extra={
            'event_type': event_type,
            'payment_intent_id': payment_intent.id,
            'reservation_id': payment_intent.reservation_id,
            'hotel_id': payment_intent.hotel_id,
            'status': payment_intent.status
        }
    )


# Handlers de ejemplo para los eventos (pueden ser movidos a otros módulos)
@receiver(payment_approved)
def handle_payment_approved(sender, instance, event_data, **kwargs):
    """
    Handler para cuando un pago es aprobado
    Aquí se pueden agregar acciones como:
    - Enviar notificaciones
    - Actualizar inventario
    - Generar comprobantes
    - Etc.
    """
    logger.info(f"Pago aprobado procesado: {instance.id}")
    
    # Ejemplo: Actualizar estado de la reserva
    try:
        reservation = instance.reservation
        if reservation.status == 'pending':
            reservation.status = 'confirmed'
            reservation.save(update_fields=['status', 'updated_at'])
            logger.info(f"Reserva {reservation.id} confirmada por pago aprobado")
    except Exception as e:
        logger.error(f"Error actualizando reserva después de pago aprobado: {e}")


@receiver(payment_rejected)
def handle_payment_rejected(sender, instance, event_data, **kwargs):
    """
    Handler para cuando un pago es rechazado
    """
    logger.info(f"Pago rechazado procesado: {instance.id}")
    
    # Aquí se pueden agregar acciones como:
    # - Enviar notificación al huésped
    # - Liberar inventario
    # - Etc.


@receiver(payment_created)
def handle_payment_created(sender, instance, event_data, **kwargs):
    """
    Handler para cuando se crea un nuevo PaymentIntent
    """
    logger.info(f"Nuevo PaymentIntent creado: {instance.id}")


@receiver(payment_updated)
def handle_payment_updated(sender, instance, event_data, **kwargs):
    """
    Handler para cuando se actualiza un PaymentIntent
    """
    logger.info(f"PaymentIntent actualizado: {instance.id} - Status: {instance.status}")
