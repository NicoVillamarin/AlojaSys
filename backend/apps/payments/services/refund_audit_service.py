"""
Servicio de auditoría para reembolsos
Maneja el logging detallado de eventos de refunds para auditoría
"""
import logging
from typing import Optional, Dict, Any
from django.utils import timezone
from django.contrib.auth.models import User

from ..models import Refund, RefundLog, RefundLogEvent, RefundStatus

logger = logging.getLogger(__name__)


class RefundAuditService:
    """Servicio centralizado para auditoría de reembolsos"""
    
    @staticmethod
    def log_refund_event(
        refund: Refund,
        event_type: str,
        action: str,
        user: Optional[User] = None,
        details: Optional[Dict[str, Any]] = None,
        external_reference: Optional[str] = None,
        error_message: Optional[str] = None,
        message: Optional[str] = None
    ) -> RefundLog:
        """
        Registra un evento en el log de auditoría del reembolso
        
        Args:
            refund: Instancia del reembolso
            event_type: Tipo de evento (RefundLogEvent)
            action: Acción específica realizada
            user: Usuario que realizó la acción (opcional)
            details: Detalles adicionales del evento
            external_reference: Referencia externa si aplica
            error_message: Mensaje de error si aplica
            message: Mensaje descriptivo del evento
            
        Returns:
            RefundLog: Instancia del log creado
        """
        try:
            # Crear log detallado
            log = RefundLog.objects.create(
                refund=refund,
                event_type=event_type,
                status=refund.status,
                user=user,
                action=action,
                details=details or {},
                external_reference=external_reference,
                error_message=error_message,
                message=message
            )
            
            # Actualizar historial compacto en el modelo Refund
            RefundAuditService._update_refund_history(refund, log)
            
            logger.info(f"Log de auditoría creado para refund {refund.id}: {event_type}")
            return log
            
        except Exception as e:
            logger.error(f"Error creando log de auditoría para refund {refund.id}: {e}")
            raise
    
    @staticmethod
    def _update_refund_history(refund: Refund, log: RefundLog):
        """
        Actualiza el historial compacto en el campo history del refund
        
        Args:
            refund: Instancia del reembolso
            log: Instancia del log creado
        """
        try:
            # Obtener historial actual
            history = refund.history or []
            
            # Crear entrada compacta
            history_entry = {
                'timestamp': log.timestamp.isoformat(),
                'event_type': log.event_type,
                'status': log.status,
                'action': log.action,
                'user': {
                    'id': log.user.id,
                    'username': log.user.username
                } if log.user else None,
                'message': log.message,
                'external_reference': log.external_reference,
                'has_error': bool(log.error_message)
            }
            
            # Agregar al historial (máximo 50 entradas para evitar que crezca demasiado)
            history.insert(0, history_entry)
            if len(history) > 50:
                history = history[:50]
            
            # Actualizar el campo history
            refund.history = history
            refund.save(update_fields=['history'])
            
        except Exception as e:
            logger.error(f"Error actualizando historial de refund {refund.id}: {e}")
    
    @staticmethod
    def log_refund_created(refund: Refund, user: Optional[User] = None):
        """Registra la creación de un reembolso"""
        return RefundAuditService.log_refund_event(
            refund=refund,
            event_type=RefundLogEvent.CREATED,
            action="refund_created",
            user=user,
            details={
                'amount': float(refund.amount),
                'reason': refund.reason,
                'method': refund.method,
                'refund_method': refund.refund_method,
                'reservation_id': refund.reservation.id
            },
            message=f"Reembolso creado por ${refund.amount} - {refund.get_reason_display()}"
        )
    
    @staticmethod
    def log_status_change(
        refund: Refund, 
        old_status: str, 
        new_status: str, 
        user: Optional[User] = None,
        reason: Optional[str] = None
    ):
        """Registra un cambio de estado del reembolso"""
        return RefundAuditService.log_refund_event(
            refund=refund,
            event_type=RefundLogEvent.STATUS_CHANGED,
            action="status_changed",
            user=user,
            details={
                'old_status': old_status,
                'new_status': new_status,
                'reason': reason
            },
            message=f"Estado cambiado de {old_status} a {new_status}" + (f" - {reason}" if reason else "")
        )
    
    @staticmethod
    def log_processing_started(refund: Refund, user: Optional[User] = None):
        """Registra el inicio del procesamiento del reembolso"""
        return RefundAuditService.log_refund_event(
            refund=refund,
            event_type=RefundLogEvent.PROCESSING_STARTED,
            action="processing_started",
            user=user,
            message="Procesamiento del reembolso iniciado"
        )
    
    @staticmethod
    def log_processing_completed(
        refund: Refund, 
        external_reference: str, 
        user: Optional[User] = None
    ):
        """Registra la finalización exitosa del procesamiento"""
        return RefundAuditService.log_refund_event(
            refund=refund,
            event_type=RefundLogEvent.PROCESSING_COMPLETED,
            action="processing_completed",
            user=user,
            external_reference=external_reference,
            details={
                'external_reference': external_reference,
                'completed_at': timezone.now().isoformat()
            },
            message=f"Reembolso procesado exitosamente - Ref: {external_reference}"
        )
    
    @staticmethod
    def log_processing_failed(
        refund: Refund, 
        error_message: str, 
        user: Optional[User] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        """Registra el fallo en el procesamiento del reembolso"""
        return RefundAuditService.log_refund_event(
            refund=refund,
            event_type=RefundLogEvent.PROCESSING_FAILED,
            action="processing_failed",
            user=user,
            error_message=error_message,
            details=details or {},
            message=f"Procesamiento falló: {error_message}"
        )
    
    @staticmethod
    def log_retry_attempt(
        refund: Refund, 
        attempt_number: int, 
        user: Optional[User] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        """Registra un intento de reintento"""
        return RefundAuditService.log_refund_event(
            refund=refund,
            event_type=RefundLogEvent.RETRY_ATTEMPT,
            action="retry_attempt",
            user=user,
            details={
                'attempt_number': attempt_number,
                **(details or {})
            },
            message=f"Intento de reintento #{attempt_number}"
        )
    
    @staticmethod
    def log_gateway_error(
        refund: Refund, 
        gateway_name: str, 
        error_message: str, 
        user: Optional[User] = None
    ):
        """Registra un error de la pasarela de pago"""
        return RefundAuditService.log_refund_event(
            refund=refund,
            event_type=RefundLogEvent.GATEWAY_ERROR,
            action="gateway_error",
            user=user,
            error_message=error_message,
            details={
                'gateway_name': gateway_name,
                'error_message': error_message
            },
            message=f"Error de pasarela {gateway_name}: {error_message}"
        )
    
    @staticmethod
    def log_manual_intervention(
        refund: Refund, 
        action: str, 
        user: User,
        details: Optional[Dict[str, Any]] = None
    ):
        """Registra una intervención manual del staff"""
        return RefundAuditService.log_refund_event(
            refund=refund,
            event_type=RefundLogEvent.MANUAL_INTERVENTION,
            action=action,
            user=user,
            details=details or {},
            message=f"Intervención manual: {action}"
        )
    
    @staticmethod
    def get_refund_audit_trail(refund: Refund) -> list:
        """
        Obtiene el trail completo de auditoría de un reembolso
        
        Args:
            refund: Instancia del reembolso
            
        Returns:
            list: Lista de logs ordenados por timestamp (más reciente primero)
        """
        return list(refund.logs.select_related('user').order_by('-timestamp'))
    
    @staticmethod
    def get_refund_timeline(refund: Refund) -> list:
        """
        Obtiene el timeline del reembolso en formato compatible con el frontend
        
        Args:
            refund: Instancia del reembolso
            
        Returns:
            list: Timeline formateado para el frontend
        """
        logs = RefundAuditService.get_refund_audit_trail(refund)
        
        timeline = []
        for log in logs:
            timeline.append({
                'type': 'refund_log',
                'changed_at': log.timestamp,
                'changed_by': {
                    'id': log.user.id,
                    'username': log.user.username,
                    'email': getattr(log.user, 'email', None)
                } if log.user else None,
                'detail': {
                    'event_type': log.event_type,
                    'action': log.action,
                    'status': log.status,
                    'message': log.message,
                    'details': log.details,
                    'external_reference': log.external_reference,
                    'error_message': log.error_message
                }
            })
        
        return timeline
