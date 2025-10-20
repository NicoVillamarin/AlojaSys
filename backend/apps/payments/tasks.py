"""
Tareas Celery para el módulo de pagos
"""
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from decimal import Decimal

from celery import shared_task
from django.db import transaction, OperationalError, ProgrammingError
from django.utils import timezone
from django.core.cache import cache
from django.core.exceptions import ValidationError

from .models import Refund, RefundStatus, PaymentGatewayConfig
from .services.refund_processor_v2 import RefundProcessorV2
from apps.notifications.services import NotificationService

logger = logging.getLogger(__name__)


@shared_task(bind=True, autoretry_for=(ProgrammingError, OperationalError), retry_backoff=5, retry_jitter=True, retry_kwargs={"max_retries": 3})
def process_pending_refunds(self):
    """
    Tarea Celery que procesa reembolsos pendientes con backoff/retries.
    
    Características:
    - Recupera Refund con status PENDING
    - Intenta process_refund() para cada uno con backoff/retries
    - Si refund_window_days expiró, marca como FAILED y notifica al staff
    - Limita concurrencia e implementa idempotencia
    - Maneja errores de gateway con reintentos inteligentes
    """
    logger.info("🚀 Iniciando procesamiento de reembolsos pendientes")
    
    # Lock para evitar concurrencia
    lock_key = "process_pending_refunds_lock"
    lock_timeout = 300  # 5 minutos
    
    if not cache.add(lock_key, "locked", lock_timeout):
        logger.warning("⚠️ Tarea process_pending_refunds ya en ejecución")
        return "Tarea ya en ejecución"
    
    try:
        # Estadísticas de procesamiento
        stats = {
            'processed': 0,
            'completed': 0,
            'failed': 0,
            'expired': 0,
            'retry_errors': 0,
            'total_amount_processed': Decimal('0.00')
        }
        
        # Obtener reembolsos pendientes ordenados por fecha de creación
        pending_refunds = Refund.objects.filter(
            status=RefundStatus.PENDING
        ).select_related(
            'reservation__hotel',
            'payment'
        ).order_by('created_at')
        
        if not pending_refunds.exists():
            logger.info("ℹ️ No hay reembolsos pendientes para procesar")
            return "No hay reembolsos pendientes"
        
        logger.info(f"📋 Encontrados {pending_refunds.count()} reembolsos pendientes")
        
        # Inicializar procesador
        processor = RefundProcessorV2()
        
        for refund in pending_refunds:
            try:
                stats['processed'] += 1
                
                # Verificar si el reembolso ha expirado
                if _is_refund_expired(refund):
                    logger.warning(f"⏰ Reembolso {refund.id} expirado - marcando como FAILED")
                    _mark_refund_as_expired(refund)
                    stats['expired'] += 1
                    continue
                
                # Procesar reembolso con reintentos
                success = _process_single_refund_with_retries(processor, refund, self)
                
                if success:
                    stats['completed'] += 1
                    stats['total_amount_processed'] += refund.amount
                    logger.info(f"✅ Reembolso {refund.id} procesado exitosamente - ${refund.amount}")
                else:
                    stats['failed'] += 1
                    logger.error(f"❌ Reembolso {refund.id} falló después de reintentos")
                
            except Exception as e:
                logger.error(f"💥 Error procesando reembolso {refund.id}: {e}")
                stats['retry_errors'] += 1
                
                # Marcar como fallido si es un error crítico
                if _is_critical_error(e):
                    try:
                        refund.mark_as_failed(f"Error crítico: {str(e)}")
                        stats['failed'] += 1
                    except Exception as mark_error:
                        logger.error(f"Error marcando reembolso {refund.id} como fallido: {mark_error}")
        
        # Log de estadísticas finales
        logger.info(f"📊 Procesamiento completado: {stats}")
        
        return f"Procesados: {stats['processed']}, Completados: {stats['completed']}, Fallidos: {stats['failed']}, Expirados: {stats['expired']}, Total: ${stats['total_amount_processed']}"
        
    except Exception as e:
        logger.error(f"💥 Error crítico en process_pending_refunds: {e}")
        raise
    finally:
        # Liberar lock
        cache.delete(lock_key)


def _is_refund_expired(refund: Refund) -> bool:
    """
    Verifica si un reembolso ha expirado según refund_window_days
    """
    try:
        # Obtener configuración de la pasarela
        gateway_config = PaymentGatewayConfig.resolve_for_hotel(refund.reservation.hotel)
        
        if not gateway_config or not gateway_config.refund_window_days:
            # Sin límite de ventana
            return False
        
        # Calcular fecha límite
        window_days = gateway_config.refund_window_days
        limit_date = refund.created_at + timedelta(days=window_days)
        
        # Verificar si estamos dentro de la ventana
        now = timezone.now()
        is_expired = now > limit_date
        
        if is_expired:
            logger.warning(
                f"Reembolso {refund.id} expirado: "
                f"creado={refund.created_at}, límite={limit_date}, ahora={now}"
            )
        
        return is_expired
        
    except Exception as e:
        logger.error(f"Error verificando expiración de reembolso {refund.id}: {e}")
        return False


def _mark_refund_as_expired(refund: Refund):
    """
    Marca un reembolso como fallido por expiración y notifica al staff
    """
    try:
        with transaction.atomic():
            # Marcar como fallido
            refund.mark_as_failed("Reembolso expirado: ventana de tiempo excedida")
            
            # Notificar al staff
            _notify_staff_refund_expired(refund)
            
    except Exception as e:
        logger.error(f"Error marcando reembolso {refund.id} como expirado: {e}")


def _notify_staff_refund_expired(refund: Refund):
    """
    Notifica al staff sobre un reembolso expirado
    """
    try:
        NotificationService.create(
            notification_type='refund_failed',
            title=f"⚠️ Reembolso Expirado - ${refund.amount}",
            message=f"El reembolso #{refund.id} para la reserva RES-{refund.reservation.id} ha expirado. "
                   f"Ventana de tiempo excedida. Requiere procesamiento manual.",
            hotel_id=refund.reservation.hotel.id,
            reservation_id=refund.reservation.id,
            metadata={
                'refund_id': refund.id,
                'amount': float(refund.amount),
                'reason': 'expired',
                'expired_at': timezone.now().isoformat(),
                'requires_manual_processing': True
            }
        )
    except Exception as e:
        logger.error(f"Error creando notificación de reembolso expirado: {e}")


def _process_single_refund_with_retries(processor: RefundProcessorV2, refund: Refund, task_instance) -> bool:
    """
    Procesa un reembolso individual con reintentos y backoff
    """
    max_retries = 3
    base_delay = 1  # segundo base
    
    for attempt in range(max_retries):
        try:
            logger.info(f"🔄 Intento {attempt + 1}/{max_retries} para reembolso {refund.id}")
            
            # Procesar reembolso
            success = processor.process_refund(refund, max_retries=1)
            
            if success:
                logger.info(f"✅ Reembolso {refund.id} procesado exitosamente en intento {attempt + 1}")
                return True
            else:
                logger.warning(f"⚠️ Reembolso {refund.id} falló en intento {attempt + 1}")
                
                # Si no es el último intento, esperar con backoff exponencial
                if attempt < max_retries - 1:
                    delay = base_delay * (2 ** attempt)  # 1s, 2s, 4s
                    logger.info(f"⏳ Esperando {delay}s antes del siguiente intento")
                    task_instance.retry(countdown=delay)
                
        except Exception as e:
            logger.error(f"💥 Error en intento {attempt + 1} para reembolso {refund.id}: {e}")
            
            # Si es el último intento, marcar como fallido
            if attempt == max_retries - 1:
                try:
                    refund.mark_as_failed(f"Falló después de {max_retries} intentos: {str(e)}")
                except Exception as mark_error:
                    logger.error(f"Error marcando reembolso {refund.id} como fallido: {mark_error}")
                return False
            else:
                # Esperar antes del siguiente intento
                delay = base_delay * (2 ** attempt)
                logger.info(f"⏳ Esperando {delay}s antes del siguiente intento")
                task_instance.retry(countdown=delay)
    
    return False


def _is_critical_error(error: Exception) -> bool:
    """
    Determina si un error es crítico y debe marcar el reembolso como fallido
    """
    critical_errors = (
        ValidationError,
        ValueError,
        TypeError,
        AttributeError,
    )
    
    return isinstance(error, critical_errors)


@shared_task(bind=True, autoretry_for=(ProgrammingError, OperationalError), retry_backoff=5, retry_jitter=True, retry_kwargs={"max_retries": 3})
def retry_failed_refunds(self):
    """
    Tarea Celery que reintenta reembolsos fallidos que pueden ser recuperables
    """
    logger.info("🔄 Iniciando reintento de reembolsos fallidos")
    
    # Lock para evitar concurrencia
    lock_key = "retry_failed_refunds_lock"
    lock_timeout = 300  # 5 minutos
    
    if not cache.add(lock_key, "locked", lock_timeout):
        logger.warning("⚠️ Tarea retry_failed_refunds ya en ejecución")
        return "Tarea ya en ejecución"
    
    try:
        # Obtener reembolsos fallidos recientes (últimas 24 horas)
        cutoff_time = timezone.now() - timedelta(hours=24)
        failed_refunds = Refund.objects.filter(
            status=RefundStatus.FAILED,
            updated_at__gte=cutoff_time
        ).select_related(
            'reservation__hotel',
            'payment'
        ).order_by('updated_at')
        
        if not failed_refunds.exists():
            logger.info("ℹ️ No hay reembolsos fallidos recientes para reintentar")
            return "No hay reembolsos fallidos recientes"
        
        logger.info(f"📋 Encontrados {failed_refunds.count()} reembolsos fallidos para reintentar")
        
        # Estadísticas
        stats = {
            'processed': 0,
            'recovered': 0,
            'still_failed': 0
        }
        
        processor = RefundProcessorV2()
        
        for refund in failed_refunds:
            try:
                stats['processed'] += 1
                
                # Verificar si el reembolso ha expirado
                if _is_refund_expired(refund):
                    logger.warning(f"⏰ Reembolso {refund.id} expirado - no se puede reintentar")
                    continue
                
                # Reintentar procesamiento
                success = _process_single_refund_with_retries(processor, refund, self)
                
                if success:
                    stats['recovered'] += 1
                    logger.info(f"✅ Reembolso {refund.id} recuperado exitosamente")
                else:
                    stats['still_failed'] += 1
                    logger.warning(f"❌ Reembolso {refund.id} sigue fallando")
                
            except Exception as e:
                logger.error(f"💥 Error reintentando reembolso {refund.id}: {e}")
                stats['still_failed'] += 1
        
        logger.info(f"📊 Reintento completado: {stats}")
        return f"Procesados: {stats['processed']}, Recuperados: {stats['recovered']}, Siguen fallando: {stats['still_failed']}"
        
    except Exception as e:
        logger.error(f"💥 Error crítico en retry_failed_refunds: {e}")
        raise
    finally:
        # Liberar lock
        cache.delete(lock_key)
