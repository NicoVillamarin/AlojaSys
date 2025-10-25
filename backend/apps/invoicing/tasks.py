"""
Tareas de Celery para el módulo de facturación
"""
from celery import shared_task
from django.utils import timezone
from datetime import datetime, timedelta
import logging
from .services import AfipService, InvoiceGeneratorService
from .models import AfipConfig

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3)
def send_invoice_to_afip_task(self, invoice_id):
    """
    Tarea para enviar factura a AFIP de forma asíncrona
    
    Args:
        invoice_id: ID de la factura a enviar
    """
    try:
        from .models import Invoice
        from .services.afip_service import AfipService
        
        # Obtener la factura
        try:
            invoice = Invoice.objects.get(id=invoice_id)
        except Invoice.DoesNotExist:
            logger.error(f"Factura {invoice_id} no encontrada")
            return {'success': False, 'error': 'Factura no encontrada'}
        
        # Verificar que puede ser enviada
        if not invoice.can_be_resent():
            logger.warning(f"Factura {invoice_id} no puede ser enviada")
            return {'success': False, 'error': 'Factura no puede ser enviada'}
        
        # Obtener configuración AFIP
        try:
            afip_config = invoice.hotel.afip_config
        except AfipConfig.DoesNotExist:
            logger.error(f"Hotel {invoice.hotel.id} no tiene configuración AFIP")
            return {'success': False, 'error': 'Hotel sin configuración AFIP'}
        
        # Marcar como enviada
        invoice.mark_as_sent()
        
        # Enviar a AFIP
        afip_service = AfipService(afip_config)
        result = afip_service.send_invoice(invoice)
        
        if result['success']:
            invoice.mark_as_approved(result['cae'], result['cae_expiration'])
            logger.info(f"Factura {invoice_id} enviada exitosamente a AFIP")
            return {'success': True, 'cae': result['cae']}
        else:
            invoice.mark_as_error(result['error'])
            logger.error(f"Error enviando factura {invoice_id} a AFIP: {result['error']}")
            return {'success': False, 'error': result['error']}
            
    except Exception as e:
        logger.error(f"Error en tarea de envío a AFIP: {e}")
        
        # Marcar factura como error si existe
        try:
            from .models import Invoice
            invoice = Invoice.objects.get(id=invoice_id)
            invoice.mark_as_error(str(e))
        except:
            pass
        
        # Reintentar si no se ha excedido el límite
        if self.request.retries < self.max_retries:
            raise self.retry(countdown=60 * (2 ** self.request.retries))
        
        return {'success': False, 'error': str(e)}


@shared_task
def generate_invoice_pdf_task(invoice_id):
    """
    Tarea para generar PDF de factura de forma asíncrona
    
    Args:
        invoice_id: ID de la factura
    """
    try:
        from .models import Invoice
        from .services.invoice_generator import InvoiceGeneratorService
        
        # Obtener la factura
        try:
            invoice = Invoice.objects.get(id=invoice_id)
        except Invoice.DoesNotExist:
            logger.error(f"Factura {invoice_id} no encontrada")
            return {'success': False, 'error': 'Factura no encontrada'}
        
        # Generar PDF
        generator = InvoiceGeneratorService()
        pdf_path = generator.generate_invoice_pdf(invoice)
        
        # Actualizar factura con ruta del PDF
        invoice.pdf_file = pdf_path
        invoice.save(update_fields=['pdf_file'])
        
        logger.info(f"PDF de factura {invoice_id} generado: {pdf_path}")
        return {'success': True, 'pdf_path': pdf_path}
        
    except Exception as e:
        logger.error(f"Error generando PDF de factura {invoice_id}: {e}")
        return {'success': False, 'error': str(e)}


@shared_task
def retry_failed_invoices_task():
    """
    Tarea para reintentar facturas fallidas
    Se ejecuta cada hora
    """
    try:
        from .models import Invoice
        
        # Obtener facturas que pueden ser reintentadas
        failed_invoices = Invoice.objects.filter(
            status='error',
            retry_count__lt=3,
            created_at__gte=timezone.now() - timedelta(days=7)  # Solo las de los últimos 7 días
        )
        
        retry_count = 0
        success_count = 0
        
        for invoice in failed_invoices:
            try:
                # Enviar tarea de reintento
                send_invoice_to_afip_task.delay(str(invoice.id))
                retry_count += 1
                
            except Exception as e:
                logger.error(f"Error programando reintento para factura {invoice.id}: {e}")
        
        logger.info(f"Programados {retry_count} reintentos de facturas fallidas")
        return {
            'success': True,
            'retry_count': retry_count,
            'success_count': success_count
        }
        
    except Exception as e:
        logger.error(f"Error en tarea de reintento de facturas: {e}")
        return {'success': False, 'error': str(e)}


@shared_task
def cleanup_expired_invoices_task():
    """
    Tarea para limpiar facturas expiradas
    Se ejecuta diariamente
    """
    try:
        from .models import Invoice
        
        # Obtener facturas con CAE expirado
        expired_invoices = Invoice.objects.filter(
            status='approved',
            cae_expiration__lt=timezone.now().date()
        )
        
        cleanup_count = 0
        
        for invoice in expired_invoices:
            # Marcar como expirada (podrías crear un nuevo estado)
            invoice.last_error = "CAE expirado"
            invoice.save(update_fields=['last_error'])
            cleanup_count += 1
        
        logger.info(f"Procesadas {cleanup_count} facturas expiradas")
        return {
            'success': True,
            'cleanup_count': cleanup_count
        }
        
    except Exception as e:
        logger.error(f"Error en tarea de limpieza de facturas: {e}")
        return {'success': False, 'error': str(e)}


@shared_task
def generate_daily_invoice_report_task(hotel_id=None):
    """
    Tarea para generar reporte diario de facturas
    
    Args:
        hotel_id: ID del hotel (opcional, si no se especifica procesa todos)
    """
    try:
        from .models import Invoice
        from .services.invoice_generator import InvoiceGeneratorService
        
        # Filtrar facturas del día
        today = timezone.now().date()
        invoices_query = Invoice.objects.filter(issue_date=today)
        
        if hotel_id:
            invoices_query = invoices_query.filter(hotel_id=hotel_id)
        
        invoices = list(invoices_query)
        
        if not invoices:
            logger.info("No hay facturas para el reporte diario")
            return {'success': True, 'message': 'No hay facturas para reportar'}
        
        # Generar PDF del reporte
        generator = InvoiceGeneratorService()
        pdf_path = generator.generate_invoice_summary_pdf(invoices)
        
        logger.info(f"Reporte diario generado: {pdf_path}")
        return {
            'success': True,
            'pdf_path': pdf_path,
            'invoices_count': len(invoices)
        }
        
    except Exception as e:
        logger.error(f"Error generando reporte diario: {e}")
        return {'success': False, 'error': str(e)}


@shared_task
def validate_afip_connection_task():
    """
    Tarea para validar conexión con AFIP
    Se ejecuta cada 30 minutos
    """
    try:
        from .models import AfipConfig
        
        # Obtener configuraciones activas
        configs = AfipConfig.objects.filter(is_active=True)
        
        validation_results = []
        
        for config in configs:
            try:
                from .services.afip_service import AfipService
                afip_service = AfipService(config)
                is_available = afip_service.test_connection()
                
                validation_results.append({
                    'hotel_id': config.hotel.id,
                    'hotel_name': config.hotel.name,
                    'is_available': is_available,
                    'environment': config.environment
                })
                
            except Exception as e:
                logger.error(f"Error validando conexión AFIP para hotel {config.hotel.id}: {e}")
                validation_results.append({
                    'hotel_id': config.hotel.id,
                    'hotel_name': config.hotel.name,
                    'is_available': False,
                    'error': str(e)
                })
        
        logger.info(f"Validación AFIP completada para {len(configs)} hoteles")
        return {
            'success': True,
            'validation_results': validation_results
        }
        
    except Exception as e:
        logger.error(f"Error en validación de conexión AFIP: {e}")
        return {'success': False, 'error': str(e)}
