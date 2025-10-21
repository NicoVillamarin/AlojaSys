"""
Servicio de seguridad para webhooks de Mercado Pago
Maneja verificación HMAC, idempotencia y logging de seguridad
"""
import hmac
import hashlib
import logging
import json
from typing import Optional, Dict, Any
from django.conf import settings
from django.core.cache import cache
from django.utils import timezone

logger = logging.getLogger(__name__)


class WebhookSecurityService:
    """Servicio para manejar la seguridad de webhooks de Mercado Pago"""
    
    @staticmethod
    def verify_webhook_signature(request, webhook_secret: str) -> bool:
        """
        Verifica la firma HMAC del webhook de Mercado Pago
        
        Args:
            request: Request object de Django
            webhook_secret: Secreto del webhook configurado en PaymentGatewayConfig
            
        Returns:
            bool: True si la firma es válida, False en caso contrario
        """
        if not webhook_secret:
            if settings.DEBUG:
                logger.warning("Webhook secret no configurado (modo DEBUG, se permite).")
                return True
            logger.error("Webhook secret ausente en producción, rechazando webhook.")
            return False
        
        # Obtener la firma del header
        signature = request.headers.get('X-Signature')
        if not signature:
            logger.warning("Webhook sin firma HMAC en header X-Signature")
            return False
        
        # Obtener el body del request
        if hasattr(request, '_body'):
            body = request._body
        else:
            body = request.body
        
        if not body:
            logger.warning("Webhook con body vacío")
            return False
        
        try:
            # Calcular la firma esperada
            expected_signature = hmac.new(
                webhook_secret.encode('utf-8'),
                body,
                hashlib.sha256
            ).hexdigest()
            
            # Comparar firmas de forma segura
            is_valid = hmac.compare_digest(signature, expected_signature)
            
            if not is_valid:
                logger.warning(
                    "Firma HMAC inválida",
                    extra={
                        'received_signature': signature,
                        'expected_signature': expected_signature,
                        'webhook_secret_length': len(webhook_secret)
                    }
                )
            
            return is_valid
            
        except Exception as e:
            logger.error(f"Error verificando firma HMAC: {e}")
            return False
    
    @staticmethod
    def is_notification_processed(notification_id: str, external_reference: str = None) -> bool:
        """
        Verifica si una notificación ya fue procesada (idempotencia)
        
        Args:
            notification_id: ID de la notificación de Mercado Pago
            external_reference: Referencia externa de la reserva
            
        Returns:
            bool: True si ya fue procesada, False si es nueva
        """
        if not notification_id:
            return False
        
        try:
            # Usar notification_id como clave principal
            cache_key = f"mp_notification:{notification_id}"
            
            # Verificar en cache
            if cache.get(cache_key):
                logger.info(f"Notificación ya procesada: {notification_id}")
                return True
            
            # Si hay external_reference, también verificar por esa clave
            if external_reference:
                ref_cache_key = f"mp_external_ref:{external_reference}"
                if cache.get(ref_cache_key):
                    logger.info(f"External reference ya procesada: {external_reference}")
                    return True
            
            return False
            
        except Exception as e:
            # Si hay error con cache (ej: DummyCache), usar fallback
            logger.warning(f"Error verificando idempotencia en cache: {e}. Usando fallback.")
            return False
    
    @staticmethod
    def mark_notification_processed(notification_id: str, external_reference: str = None, 
                                  ttl: int = 86400) -> None:
        """
        Marca una notificación como procesada para evitar duplicados
        
        Args:
            notification_id: ID de la notificación de Mercado Pago
            external_reference: Referencia externa de la reserva
            ttl: Tiempo de vida en segundos (default: 24 horas)
        """
        if not notification_id:
            return
        
        try:
            # Marcar notification_id
            cache_key = f"mp_notification:{notification_id}"
            cache.set(cache_key, {
                'processed_at': timezone.now().isoformat(),
                'notification_id': notification_id
            }, ttl)
            
            # Marcar external_reference si existe
            if external_reference:
                ref_cache_key = f"mp_external_ref:{external_reference}"
                cache.set(ref_cache_key, {
                    'processed_at': timezone.now().isoformat(),
                    'external_reference': external_reference,
                    'notification_id': notification_id
                }, ttl)
            
            logger.info(f"Notificación marcada como procesada: {notification_id}")
            
        except Exception as e:
            # Si hay error con cache (ej: DummyCache), solo loggear
            logger.warning(f"Error marcando notificación como procesada en cache: {e}. Continuando sin cache.")
    
    @staticmethod
    def log_webhook_security_event(event_type: str, notification_id: str = None, 
                                 external_reference: str = None, details: Dict[str, Any] = None):
        """
        Registra eventos de seguridad de webhooks para auditoría
        
        Args:
            event_type: Tipo de evento (hmac_verified, hmac_failed, duplicate_detected, etc.)
            notification_id: ID de la notificación
            external_reference: Referencia externa
            details: Detalles adicionales del evento
        """
        log_data = {
            'event_type': event_type,
            'timestamp': timezone.now().isoformat(),
            'notification_id': notification_id,
            'external_reference': external_reference,
            'details': details or {}
        }
        
        # Log estructurado para fácil parsing
        logger.info(
            f"Webhook security event: {event_type}",
            extra=log_data
        )
        
        # En producción, también enviar a sistema de monitoreo
        if settings.DEBUG:
            print(f"[SECURITY] Webhook Security: {json.dumps(log_data, indent=2)}")
    
    @staticmethod
    def extract_webhook_data(request) -> Dict[str, Any]:
        """
        Extrae y valida los datos del webhook de forma segura
        
        Args:
            request: Request object de Django
            
        Returns:
            Dict con los datos extraídos y validados
        """
        try:
            # Obtener datos del query params y body
            topic = (request.query_params.get("type") or 
                    request.query_params.get("topic") or 
                    (request.data.get("type") if isinstance(request.data, dict) else None))
            
            payment_id = (
                request.query_params.get("data.id") or
                request.query_params.get("id") or
                (request.data.get("data", {}) if isinstance(request.data, dict) else {}).get("id") or
                (request.data.get("id") if isinstance(request.data, dict) else None)
            )
            
            notification_id = (request.query_params.get("notification_id") or 
                              (request.data.get("notification_id") if isinstance(request.data, dict) else None))
            external_reference = (request.query_params.get("external_reference") or 
                                 (request.data.get("external_reference") if isinstance(request.data, dict) else None))
            
            return {
                'topic': topic,
                'payment_id': payment_id,
                'notification_id': notification_id,
                'external_reference': external_reference,
                'raw_data': request.data if hasattr(request, 'data') else {},
                'query_params': dict(request.query_params)
            }
            
        except Exception as e:
            logger.error(f"Error extrayendo datos del webhook: {e}")
            return {
                'topic': None,
                'payment_id': None,
                'notification_id': None,
                'external_reference': None,
                'raw_data': {},
                'query_params': {},
                'error': str(e)
            }
