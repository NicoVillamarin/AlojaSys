"""
Signals para generar PDFs automáticamente
"""
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.conf import settings
from django.db import transaction
import logging

logger = logging.getLogger(__name__)


@receiver(post_save, sender='reservations.Payment')
def generate_payment_receipt(sender, instance, created, **kwargs):
    """
    Genera PDF de recibo cuando se crea un pago manual
    """
    if created and instance.method in ['cash', 'transfer', 'pos', 'card', 'bank_transfer', 'online']:
        try:
            from .tasks import generate_payment_receipt_pdf

            # Ejecutar la tarea solo después de que se confirme la transacción
            def _on_commit():
                # Solo generamos el PDF; el email lo enviará la tarea cuando detecte el archivo
                generate_payment_receipt_pdf.delay(instance.id, 'payment')
                logger.info(f"[PDF] Generando recibo PDF para Payment manual {instance.id}")

            transaction.on_commit(_on_commit)
        except Exception as e:
            logger.error(f"[PDF] Error generando recibo para Payment {instance.id}: {e}")


@receiver(post_save, sender='payments.Refund')
def generate_refund_receipt(sender, instance, created, **kwargs):
    """
    Genera PDF de recibo cuando se crea un refund
    """
    if created:
        try:
            from .tasks import generate_payment_receipt_pdf

            # Ejecutar la tarea solo después de que se confirme la transacción
            def _on_commit():
                # Solo generamos el PDF; el email lo enviará la tarea cuando detecte el archivo
                generate_payment_receipt_pdf.delay(instance.id, 'refund')
                logger.info(f"[PDF] Generando recibo PDF para Refund {instance.id}")

            transaction.on_commit(_on_commit)
        except Exception as e:
            logger.error(f"[PDF] Error generando recibo para Refund {instance.id}: {e}")