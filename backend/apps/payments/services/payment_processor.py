"""
Servicio para procesar pagos de forma atómica y segura
Maneja actualizaciones de estado, eventos internos y logging
"""
import logging
from typing import Optional, Dict, Any
from django.db import transaction
from django.utils import timezone
from apps.payments.models import PaymentIntent, PaymentIntentStatus
from apps.payments.signals import emit_payment_event
from apps.payments.services.webhook_security import WebhookSecurityService

logger = logging.getLogger(__name__)


class PaymentProcessorService:
    """Servicio para procesar pagos de forma atómica y segura"""
    
    @staticmethod
    @transaction.atomic
    def update_payment_status(payment_intent: PaymentIntent, new_status: str, 
                            mp_payment_id: str = None, external_reference: str = None,
                            notification_id: str = None, raw_payment_data: Dict = None) -> bool:
        """
        Actualiza el estado de un PaymentIntent de forma atómica y emite eventos
        
        Args:
            payment_intent: Instancia del PaymentIntent a actualizar
            new_status: Nuevo estado del pago
            mp_payment_id: ID del pago en Mercado Pago (opcional)
            external_reference: Referencia externa (opcional)
            notification_id: ID de la notificación (opcional)
            raw_payment_data: Datos raw del pago de MP (opcional)
            
        Returns:
            bool: True si la actualización fue exitosa, False en caso contrario
        """
        try:
            # Bloquear el registro para actualización atómica
            payment_intent = PaymentIntent.objects.select_for_update().get(
                id=payment_intent.id
            )
            
            old_status = payment_intent.status
            
            # Actualizar campos
            payment_intent.status = new_status
            if mp_payment_id:
                payment_intent.mp_payment_id = mp_payment_id
            if external_reference:
                payment_intent.external_reference = external_reference
            
            # Guardar cambios
            payment_intent.save(update_fields=[
                'status', 'mp_payment_id', 'external_reference', 'updated_at'
            ])
            
            # Emitir evento interno según el nuevo estado
            event_type = PaymentProcessorService._get_event_type(new_status)
            if event_type:
                emit_payment_event(
                    event_type=event_type,
                    payment_intent=payment_intent,
                    old_status=old_status,
                    new_status=new_status,
                    mp_payment_id=mp_payment_id,
                    notification_id=notification_id,
                    raw_payment_data=raw_payment_data
                )
            
            # Log del cambio de estado
            logger.info(
                f"PaymentIntent {payment_intent.id} actualizado: {old_status} -> {new_status}",
                extra={
                    'payment_intent_id': payment_intent.id,
                    'reservation_id': payment_intent.reservation_id,
                    'hotel_id': payment_intent.hotel_id,
                    'old_status': old_status,
                    'new_status': new_status,
                    'mp_payment_id': mp_payment_id,
                    'notification_id': notification_id
                }
            )
            
            return True
            
        except Exception as e:
            logger.error(
                f"Error actualizando PaymentIntent {payment_intent.id}: {e}",
                extra={
                    'payment_intent_id': payment_intent.id,
                    'new_status': new_status,
                    'error': str(e)
                }
            )
            return False
    
    @staticmethod
    def _get_event_type(status: str) -> Optional[str]:
        """
        Mapea el estado del pago al tipo de evento correspondiente
        
        Args:
            status: Estado del pago
            
        Returns:
            str: Tipo de evento o None si no aplica
        """
        event_mapping = {
            PaymentIntentStatus.APPROVED: 'payment:approved',
            PaymentIntentStatus.REJECTED: 'payment:rejected',
            PaymentIntentStatus.CREATED: 'payment:created',
            PaymentIntentStatus.CANCELLED: 'payment:cancelled',
            PaymentIntentStatus.PENDING: 'payment:pending'
        }
        
        return event_mapping.get(status)
    
    @staticmethod
    @transaction.atomic
    def process_webhook_payment(payment_data: Dict[str, Any], 
                              webhook_secret: str = None,
                              notification_id: str = None) -> Dict[str, Any]:
        """
        Procesa un pago desde webhook de forma segura y atómica
        
        Args:
            payment_data: Datos del pago de Mercado Pago
            webhook_secret: Secreto del webhook para verificación
            notification_id: ID de la notificación
            
        Returns:
            Dict con el resultado del procesamiento
        """
        try:
            payment_id = payment_data.get('id')
            status_detail = payment_data.get('status')
            external_reference = payment_data.get('external_reference', '')
            
            # Verificar idempotencia
            if WebhookSecurityService.is_notification_processed(notification_id, external_reference):
                WebhookSecurityService.log_webhook_security_event(
                    'duplicate_detected',
                    notification_id=notification_id,
                    external_reference=external_reference,
                    details={'payment_id': payment_id}
                )
                return {
                    'success': True,
                    'processed': False,
                    'reason': 'duplicate_notification',
                    'message': 'Notificación ya procesada'
                }
            
            # Buscar PaymentIntent existente
            payment_intent = None
            if external_reference:
                payment_intent = PaymentIntent.objects.filter(
                    external_reference=external_reference
                ).order_by('-created_at').first()
            
            # Si no existe, crear uno nuevo (esto puede pasar si el webhook llega antes que la confirmación)
            if not payment_intent:
                # Intentar extraer datos de la reserva desde external_reference
                reservation_id = PaymentProcessorService._extract_reservation_id(external_reference)
                if not reservation_id:
                    return {
                        'success': False,
                        'error': 'No se pudo determinar la reserva desde external_reference'
                    }
                
                # Crear PaymentIntent básico
                from apps.reservations.models import Reservation
                try:
                    reservation = Reservation.objects.get(id=reservation_id)
                    payment_intent = PaymentIntent.objects.create(
                        reservation=reservation,
                        hotel=reservation.hotel,
                        enterprise=reservation.hotel.enterprise if hasattr(reservation.hotel, 'enterprise') else None,
                        amount=payment_data.get('transaction_amount', 0),
                        currency=payment_data.get('currency_id', 'ARS'),
                        description=f"Reserva {reservation.id}",
                        external_reference=external_reference,
                        status=PaymentIntentStatus.CREATED
                    )
                except Exception as e:
                    logger.error(f"Error creando PaymentIntent: {e}")
                    return {
                        'success': False,
                        'error': f'Error creando PaymentIntent: {str(e)}'
                    }
            
            # Actualizar estado del pago
            success = PaymentProcessorService.update_payment_status(
                payment_intent=payment_intent,
                new_status=status_detail,
                mp_payment_id=str(payment_id),
                external_reference=external_reference,
                notification_id=notification_id,
                raw_payment_data=payment_data
            )
            
            if success:
                # Marcar notificación como procesada
                WebhookSecurityService.mark_notification_processed(
                    notification_id, external_reference
                )
                
                # Log de seguridad
                WebhookSecurityService.log_webhook_security_event(
                    'payment_processed',
                    notification_id=notification_id,
                    external_reference=external_reference,
                    details={
                        'payment_id': payment_id,
                        'status': status_detail,
                        'payment_intent_id': payment_intent.id
                    }
                )
                
                return {
                    'success': True,
                    'processed': True,
                    'payment_intent_id': payment_intent.id,
                    'status': status_detail,
                    'message': 'Pago procesado exitosamente'
                }
            else:
                return {
                    'success': False,
                    'error': 'Error actualizando estado del pago'
                }
                
        except Exception as e:
            logger.error(f"Error procesando webhook de pago: {e}")
            return {
                'success': False,
                'error': f'Error interno: {str(e)}'
            }
    
    @staticmethod
    def _extract_reservation_id(external_reference: str) -> Optional[int]:
        """
        Extrae el ID de reserva desde external_reference
        
        Args:
            external_reference: Referencia externa en formato "reservation:123|hotel:456"
            
        Returns:
            int: ID de la reserva o None si no se puede extraer
        """
        try:
            if not external_reference:
                return None
            
            # Formato esperado: "reservation:123|hotel:456"
            parts = external_reference.split('|')
            for part in parts:
                if ':' in part:
                    key, value = part.split(':', 1)
                    if key.strip() == 'reservation':
                        return int(value.strip())
            
            return None
            
        except (ValueError, AttributeError) as e:
            logger.warning(f"Error extrayendo reservation_id de external_reference '{external_reference}': {e}")
            return None
