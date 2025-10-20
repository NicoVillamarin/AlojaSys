"""
Servicio mejorado para procesar reembolsos con adaptadores de pasarelas
"""
import logging
from typing import Optional, Dict, Any
from decimal import Decimal
from datetime import datetime, timedelta
from django.utils import timezone
from django.db import transaction
from django.core.exceptions import ValidationError

from ..models import Refund, PaymentGatewayConfig, RefundStatus
from ..adapters.base import PaymentGatewayAdapter, RefundResult
from ..adapters.mercado_pago import MercadoPagoAdapter
from .refund_audit_service import RefundAuditService

logger = logging.getLogger(__name__)


class RefundProcessorV2:
    """Servicio mejorado para procesar reembolsos con adaptadores de pasarelas"""
    
    def __init__(self):
        self.adapters = {
            'mercado_pago': MercadoPagoAdapter
        }
    
    def process_refund(self, refund: Refund, max_retries: int = 3) -> bool:
        """
        Procesa un reembolso a través de la pasarela de pago correspondiente
        
        Args:
            refund: Instancia del reembolso a procesar
            max_retries: Número máximo de reintentos
            
        Returns:
            bool: True si el reembolso se procesó exitosamente
        """
        logger.info(f"Iniciando procesamiento de reembolso {refund.id}")
        
        try:
            # Validar ventana de reembolso
            if not self._validate_refund_window(refund):
                logger.warning(f"Reembolso {refund.id} fuera de ventana permitida")
                RefundAuditService.log_gateway_error(
                    refund, 
                    "system", 
                    "Reembolso fuera de ventana permitida"
                )
                refund.mark_as_failed("Reembolso fuera de ventana permitida")
                return False
            
            # Obtener adapter de la pasarela
            adapter = self._get_payment_adapter(refund)
            if not adapter:
                logger.error(f"No se pudo obtener adapter para reembolso {refund.id}")
                RefundAuditService.log_gateway_error(
                    refund, 
                    "system", 
                    "No se pudo obtener adapter de pasarela"
                )
                refund.mark_as_failed("Pasarela de pago no disponible")
                return False
            
            # Verificar disponibilidad de la pasarela
            if not adapter.is_available():
                logger.error(f"Pasarela {adapter.provider_name} no disponible para reembolso {refund.id}")
                RefundAuditService.log_gateway_error(
                    refund, 
                    adapter.provider_name, 
                    "Pasarela no disponible"
                )
                refund.mark_as_failed("Pasarela de pago no disponible")
                return False
            
            # Procesar reembolso con reintentos
            return self._process_with_retries(refund, adapter, max_retries)
            
        except Exception as e:
            logger.error(f"Error procesando reembolso {refund.id}: {e}")
            RefundAuditService.log_processing_failed(
                refund, 
                f"Error interno: {str(e)}", 
                details={'exception_type': type(e).__name__}
            )
            refund.mark_as_failed(f"Error interno: {str(e)}")
            return False
    
    def _validate_refund_window(self, refund: Refund) -> bool:
        """
        Valida si el reembolso está dentro de la ventana permitida
        
        Args:
            refund: Instancia del reembolso
            
        Returns:
            bool: True si está dentro de la ventana
        """
        # Obtener configuración de la pasarela
        gateway_config = self._get_gateway_config(refund)
        if not gateway_config or not gateway_config.refund_window_days:
            # Sin límite de ventana
            return True
        
        # Calcular fecha límite
        window_days = gateway_config.refund_window_days
        limit_date = refund.created_at + timedelta(days=window_days)
        
        # Verificar si estamos dentro de la ventana
        now = timezone.now()
        is_within_window = now <= limit_date
        
        if not is_within_window:
            logger.warning(
                f"Reembolso {refund.id} fuera de ventana: "
                f"creado={refund.created_at}, límite={limit_date}, ahora={now}"
            )
        
        return is_within_window
    
    def _get_gateway_config(self, refund: Refund) -> Optional[PaymentGatewayConfig]:
        """Obtiene la configuración de la pasarela para el reembolso"""
        try:
            # Obtener configuración del hotel de la reserva
            return PaymentGatewayConfig.resolve_for_hotel(refund.reservation.hotel)
        except Exception as e:
            logger.error(f"Error obteniendo configuración de pasarela: {e}")
            return None
    
    def _get_payment_adapter(self, refund: Refund) -> Optional[PaymentGatewayAdapter]:
        """
        Obtiene el adapter apropiado para procesar el reembolso
        
        Args:
            refund: Instancia del reembolso
            
        Returns:
            PaymentGatewayAdapter: Adapter configurado o None si no se puede obtener
        """
        try:
            # Obtener configuración de la pasarela
            gateway_config = self._get_gateway_config(refund)
            if not gateway_config:
                return None
            
            # Determinar el proveedor
            provider = gateway_config.provider
            
            # Obtener clase del adapter
            adapter_class = self.adapters.get(provider)
            if not adapter_class:
                logger.error(f"Adapter no disponible para proveedor: {provider}")
                return None
            
            # Crear configuración para el adapter
            config = {
                'access_token': gateway_config.access_token,
                'public_key': gateway_config.public_key,
                'is_test': gateway_config.is_test,
                'country_code': gateway_config.country_code,
                'currency_code': gateway_config.currency_code,
                # Configuraciones para testing
                'failure_rate': 0.0,  # Sin fallos por defecto
                'simulate_delay': False,
                'delay_seconds': 1
            }
            
            # Crear instancia del adapter
            adapter = adapter_class(config, mock_mode=gateway_config.is_test)
            
            logger.info(f"Adapter creado para {provider}: {adapter.provider_name}")
            return adapter
            
        except Exception as e:
            logger.error(f"Error creando adapter: {e}")
            return None
    
    def _process_with_retries(self, refund: Refund, adapter: PaymentGatewayAdapter, max_retries: int) -> bool:
        """
        Procesa el reembolso con reintentos en caso de fallo
        
        Args:
            refund: Instancia del reembolso
            adapter: Adapter de la pasarela
            max_retries: Número máximo de reintentos
            
        Returns:
            bool: True si se procesó exitosamente
        """
        last_error = None
        
        for attempt in range(max_retries + 1):
            try:
                logger.info(f"Intento {attempt + 1}/{max_retries + 1} para reembolso {refund.id}")
                
                # Marcar como procesando en el primer intento
                if attempt == 0:
                    refund.mark_as_processing()
                else:
                    # Log de reintento
                    RefundAuditService.log_retry_attempt(
                        refund, 
                        attempt + 1, 
                        details={'previous_error': last_error}
                    )
                
                # Procesar reembolso
                result = self._execute_refund(refund, adapter)
                
                if result.success:
                    # Reembolso exitoso
                    refund.mark_as_completed(
                        external_reference=result.external_id
                    )
                    
                    logger.info(f"Reembolso {refund.id} procesado exitosamente")
                    return True
                else:
                    # Reembolso falló
                    last_error = result.error
                    logger.warning(f"Intento {attempt + 1} falló: {result.error}")
                    
                    # Si es el último intento, marcar como fallido
                    if attempt == max_retries:
                        RefundAuditService.log_processing_failed(
                            refund, 
                            f"Falló después de {max_retries + 1} intentos: {last_error}",
                            details={
                                'attempts': max_retries + 1,
                                'provider': adapter.provider_name,
                                'final_error': last_error
                            }
                        )
                        refund.mark_as_failed(f"Falló después de {max_retries + 1} intentos: {last_error}")
                        return False
                    else:
                        # Esperar antes del siguiente intento
                        wait_time = 2 ** attempt  # Backoff exponencial
                        logger.info(f"Esperando {wait_time} segundos antes del siguiente intento")
                        import time
                        time.sleep(wait_time)
                
            except Exception as e:
                last_error = str(e)
                logger.error(f"Error en intento {attempt + 1}: {e}")
                
                if attempt == max_retries:
                    RefundAuditService.log_processing_failed(
                        refund, 
                        f"Error después de {max_retries + 1} intentos: {last_error}",
                        details={
                            'attempts': max_retries + 1,
                            'exception_type': type(e).__name__,
                            'final_error': last_error
                        }
                    )
                    refund.mark_as_failed(f"Error después de {max_retries + 1} intentos: {last_error}")
                    return False
        
        return False
    
    def _execute_refund(self, refund: Refund, adapter: PaymentGatewayAdapter) -> RefundResult:
        """
        Ejecuta el reembolso a través del adapter
        
        Args:
            refund: Instancia del reembolso
            adapter: Adapter de la pasarela
            
        Returns:
            RefundResult: Resultado del procesamiento
        """
        # Obtener ID externo del pago original
        payment_external_id = self._get_payment_external_id(refund)
        if not payment_external_id:
            return RefundResult(
                success=False,
                error="No se pudo obtener ID externo del pago original"
            )
        
        # Ejecutar reembolso
        result = adapter.refund(
            payment_external_id=payment_external_id,
            amount=refund.amount,
            reason=refund.reason
        )
        
        # Log del resultado
        if result.success:
            logger.info(f"Reembolso exitoso: external_id={result.external_id}")
        else:
            logger.warning(f"Reembolso falló: {result.error}")
        
        return result
    
    def _get_payment_external_id(self, refund: Refund) -> Optional[str]:
        """
        Obtiene el ID externo del pago original
        
        Args:
            refund: Instancia del reembolso
            
        Returns:
            str: ID externo del pago o None si no se encuentra
        """
        # Buscar en PaymentIntent para obtener external_reference
        try:
            from ..models import PaymentIntent
            payment_intent = PaymentIntent.objects.filter(
                reservation=refund.reservation,
                status='approved'
            ).first()
            
            if payment_intent and payment_intent.external_reference:
                return payment_intent.external_reference
            
            # Si hay pago asociado, usar su ID
            if refund.payment:
                return str(refund.payment.id)
            
            # Fallback: usar ID de la reserva
            return f"reservation_{refund.reservation.id}"
            
        except Exception as e:
            logger.error(f"Error obteniendo external_id del pago: {e}")
            # Fallback final
            return f"reservation_{refund.reservation.id}"
    


# Instancia global del procesador
refund_processor_v2 = RefundProcessorV2()
