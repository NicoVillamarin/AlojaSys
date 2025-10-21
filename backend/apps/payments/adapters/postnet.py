import logging
from typing import Dict, Any, Optional
from decimal import Decimal

from .base import PaymentGatewayAdapter, RefundResult

logger = logging.getLogger(__name__)

class PostnetAdapter(PaymentGatewayAdapter):
    """Adapter mínimo para POSTNET (pagos offline con terminales)"""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        logger.info(f"PostnetAdapter initialized with config: {config}")

    @property
    def provider_name(self) -> str:
        return "POSTNET"

    def create_payment(self, payment_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Crea un pago POSTNET.
        Retorna el pago creado con el status correspondiente.
        """
        try:
            # Determinar el status basado en si está liquidado
            is_settled = payment_data.get('is_settled', False)
            status = 'approved' if is_settled else 'pending_settlement'
            
            # Crear el pago
            payment_data.update({
                'method': 'pos',
                'status': status,
                'provider': 'POSTNET'
            })
            
            logger.info(f"POSTNET payment created with status: {status}")
            return {
                'success': True,
                'payment_data': payment_data,
                'status': status
            }
            
        except Exception as e:
            logger.error(f"Error creating POSTNET payment: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    def settle_payment(self, payment_id: str, settlement_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Confirma o rechaza un pago POSTNET pendiente.
        """
        try:
            # settlement_data debe contener: {'action': 'approve'|'reject', 'notes': '...'}
            action = settlement_data.get('action')
            
            if action not in ['approve', 'reject']:
                raise ValueError("Action must be 'approve' or 'reject'")
            
            new_status = 'approved' if action == 'approve' else 'failed'
            
            logger.info(f"POSTNET payment {payment_id} settled as: {new_status}")
            return {
                'success': True,
                'payment_id': payment_id,
                'new_status': new_status,
                'action': action
            }
            
        except Exception as e:
            logger.error(f"Error settling POSTNET payment {payment_id}: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    def refund(self, payment_external_id: str, amount: Decimal, reason: Optional[str] = None) -> RefundResult:
        """
        POSTNET no maneja reembolsos directamente a través de una API.
        Los reembolsos deben ser gestionados manualmente.
        """
        logger.warning(f"Attempted to refund via POSTNET adapter for payment {payment_external_id}. "
                       "POSTNET does not support direct API refunds. Manual intervention required.")
        return RefundResult(
            success=False,
            error="POSTNET does not support direct API refunds. Manual intervention required.",
            raw_response={"message": "Manual refund required for POSTNET transactions."}
        )

    def get_refund_status(self, refund_external_id: str) -> Dict[str, Any]:
        """
        POSTNET no tiene un sistema de seguimiento de reembolsos por API.
        """
        logger.warning(f"Attempted to get refund status via POSTNET adapter for refund {refund_external_id}. "
                       "POSTNET does not support direct API refund status checks. Manual verification required.")
        return {
            "status": "unknown",
            "message": "POSTNET does not support direct API refund status checks. Manual verification required."
        }

    def is_available(self) -> bool:
        """
        POSTNET siempre está disponible a nivel de sistema.
        """
        return True
