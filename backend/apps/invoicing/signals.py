"""
Señales para automatizar la generación de facturas
"""
import logging
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.db import transaction
from django.utils import timezone
from decimal import Decimal

from .models import Invoice, InvoiceItem
from .services import AfipService, InvoiceGeneratorService

logger = logging.getLogger(__name__)


@receiver(post_save, sender='reservations.Payment')
def generate_invoice_on_payment_approved(sender, instance, created, **kwargs):
    """
    Genera automáticamente una factura cuando un pago es aprobado
    """
    # Solo procesar si el pago fue aprobado
    if instance.status == 'approved':
        try:
            # Verificar que no exista ya una factura para este pago
            if Invoice.objects.filter(payment=instance).exists():
                logger.info(f"Ya existe una factura para el pago {instance.id}")
                return
            
            # Verificar que el pago tenga una reserva
            if not hasattr(instance, 'reservation') or not instance.reservation:
                logger.warning(f"El pago {instance.id} no tiene reserva asociada")
                return
            
            # Verificar que el hotel tenga configuración AFIP
            try:
                afip_config = instance.reservation.hotel.afip_config
            except Exception:
                afip_config = None
            if not afip_config:
                logger.warning(f"El hotel {instance.reservation.hotel.id} no tiene configuración AFIP")
                return
            
            # Generar factura automáticamente
            with transaction.atomic():
                # Generar número de factura
                next_number = afip_config.get_next_invoice_number()
                formatted_number = afip_config.format_invoice_number(next_number)
                
                # Determinar tipo de factura (por defecto Factura B)
                invoice_type = 'B'  # Consumidor final
                
                # Obtener datos del cliente desde la reserva
                reservation = instance.reservation
                primary_guest = reservation.get_primary_guest() or {}
                
                customer_name = primary_guest.get('name', 'Cliente')
                customer_document_type = primary_guest.get('document_type', 'DNI')
                customer_document_number = primary_guest.get('document_number', '00000000')
                customer_address = primary_guest.get('address', '')
                customer_city = primary_guest.get('city', '')
                customer_postal_code = primary_guest.get('postal_code', '')
                customer_country = primary_guest.get('country', 'Argentina')
                
                # Crear factura
                invoice_data = {
                    'reservation': instance.reservation,
                    'payment': instance,
                    'hotel': instance.reservation.hotel,
                    'type': invoice_type,
                    'number': formatted_number,
                    'issue_date': timezone.now().date(),
                    'total': instance.amount,
                    'net_amount': instance.amount * Decimal('0.83'),  # Aproximado sin IVA
                    'vat_amount': instance.amount * Decimal('0.17'),  # Aproximado con IVA
                    'currency': 'ARS',
                    'customer_name': customer_name,
                    'customer_document_type': customer_document_type,
                    'customer_document_number': customer_document_number,
                    'customer_address': customer_address,
                    'customer_city': customer_city,
                    'customer_postal_code': customer_postal_code,
                    'customer_country': customer_country,
                    'status': 'draft',
                    'created_by': None  # Sistema automático
                }
                
                invoice = Invoice.objects.create(**invoice_data)
                
                # Crear item por defecto basado en la reserva
                item_data = {
                    'invoice': invoice,
                    'description': f'Hospedaje - {instance.reservation.room.name}',
                    'quantity': (instance.reservation.check_out - instance.reservation.check_in).days,
                    'unit_price': instance.reservation.room.base_price,
                    'vat_rate': Decimal('21.00'),
                    'afip_code': '1'  # Servicios
                }
                InvoiceItem.objects.create(**item_data)
                
                # Actualizar número en configuración
                afip_config.update_invoice_number(next_number)
                
                logger.info(f"Factura {invoice.number} generada automáticamente para el pago {instance.id}")
                
                # Intentar enviar a AFIP automáticamente si está configurado
                try:
                    afip_service = AfipService(afip_config)
                    result = afip_service.send_invoice(invoice)
                    
                    if result['success']:
                        invoice.mark_as_approved(result['cae'], result['cae_expiration'])
                        logger.info(f"Factura {invoice.number} enviada automáticamente a AFIP")
                    else:
                        invoice.mark_as_error(result['error'])
                        logger.error(f"Error enviando factura {invoice.number} a AFIP: {result['error']}")
                        
                except Exception as e:
                    logger.error(f"Error enviando factura {invoice.number} a AFIP: {str(e)}")
                    invoice.mark_as_error(str(e))
                
        except Exception as e:
            logger.error(f"Error generando factura automática para pago {instance.id}: {str(e)}")


@receiver(post_save, sender='payments.Refund')
def generate_credit_note_on_refund(sender, instance, created, **kwargs):
    """
    Genera automáticamente una nota de crédito cuando se crea un reembolso
    """
    if created and instance.status == 'completed':
        try:
            # Verificar que el reembolso tenga un pago asociado
            if not hasattr(instance, 'payment') or not instance.payment:
                logger.warning(f"El reembolso {instance.id} no tiene pago asociado")
                return
            
            # Verificar que exista una factura para el pago
            invoice = Invoice.objects.filter(payment=instance.payment).first()
            if not invoice:
                logger.warning(f"No existe factura para el pago {instance.payment.id}")
                return
            
            # Verificar que la factura esté aprobada
            if invoice.status != 'approved':
                logger.warning(f"La factura {invoice.number} no está aprobada")
                return
            
            # Verificar que no exista ya una nota de crédito para este reembolso
            if Invoice.objects.filter(related_invoice=invoice, type='NC').exists():
                logger.info(f"Ya existe una nota de crédito para la factura {invoice.number}")
                return
            
            # Obtener configuración AFIP
            try:
                afip_config = invoice.hotel.afip_config
            except Exception:
                afip_config = None
            if not afip_config:
                logger.warning(f"El hotel {invoice.hotel.id} no tiene configuración AFIP")
                return
            
            # Generar nota de crédito automáticamente
            with transaction.atomic():
                # Generar número de nota de crédito
                next_number = afip_config.get_next_invoice_number()
                formatted_number = afip_config.format_invoice_number(next_number)
                
                # Crear nota de crédito
                credit_note_data = {
                    'reservation': invoice.reservation,
                    'payment': invoice.payment,
                    'hotel': invoice.hotel,
                    'type': 'NC',  # Nota de Crédito
                    'number': formatted_number,
                    'issue_date': timezone.now().date(),
                    'total': instance.amount,
                    'net_amount': instance.amount * Decimal('0.83'),  # Aproximado sin IVA
                    'vat_amount': instance.amount * Decimal('0.17'),  # Aproximado con IVA
                    'currency': invoice.currency,
                    'customer_name': invoice.customer_name,
                    'customer_document_type': invoice.customer_document_type,
                    'customer_document_number': invoice.customer_document_number,
                    'customer_address': invoice.customer_address,
                    'customer_city': invoice.customer_city,
                    'customer_postal_code': invoice.customer_postal_code,
                    'customer_country': invoice.customer_country,
                    'status': 'draft',
                    'created_by': None,  # Sistema automático
                    'related_invoice': invoice
                }
                
                credit_note = Invoice.objects.create(**credit_note_data)
                
                # Crear item de la nota de crédito
                item_data = {
                    'invoice': credit_note,
                    'description': f'Reembolso - {invoice.number}',
                    'quantity': 1,
                    'unit_price': instance.amount,
                    'vat_rate': Decimal('21.00'),
                    'afip_code': '1'  # Servicios
                }
                InvoiceItem.objects.create(**item_data)
                
                # Actualizar número en configuración
                afip_config.update_invoice_number(next_number)
                
                logger.info(f"Nota de crédito {credit_note.number} generada automáticamente para el reembolso {instance.id}")
                
                # Intentar enviar a AFIP automáticamente si está configurado
                try:
                    afip_service = AfipService(afip_config)
                    result = afip_service.send_invoice(credit_note)
                    
                    if result['success']:
                        credit_note.mark_as_approved(result['cae'], result['cae_expiration'])
                        logger.info(f"Nota de crédito {credit_note.number} enviada automáticamente a AFIP")
                    else:
                        credit_note.mark_as_error(result['error'])
                        logger.error(f"Error enviando nota de crédito {credit_note.number} a AFIP: {result['error']}")
                        
                except Exception as e:
                    logger.error(f"Error enviando nota de crédito {credit_note.number} a AFIP: {str(e)}")
                    credit_note.mark_as_error(str(e))
                
        except Exception as e:
            logger.error(f"Error generando nota de crédito automática para reembolso {instance.id}: {str(e)}")