"""
Adapter para MercadoPago
Implementación mockeable para testing y desarrollo
"""
import logging
from typing import Dict, Any, Optional
from decimal import Decimal
from datetime import datetime, timedelta
import random

from .base import PaymentGatewayAdapter, RefundResult

logger = logging.getLogger(__name__)


class MercadoPagoAdapter(PaymentGatewayAdapter):
    """Adapter para MercadoPago con implementación mockeable"""
    
    def __init__(self, config: Dict[str, Any], mock_mode: bool = True):
        """
        Inicializa el adapter de MercadoPago
        
        Args:
            config: Configuración de la pasarela
            mock_mode: Si True, usa implementación mock para testing
        """
        self.config = config
        self.mock_mode = mock_mode
        self.access_token = config.get('access_token')
        self.public_key = config.get('public_key')
        self.is_test = config.get('is_test', True)
        
        # Para simular fallos en testing
        self.failure_rate = config.get('failure_rate', 0.0)  # 0-1, probabilidad de fallo
        self.simulate_delay = config.get('simulate_delay', False)
        self.delay_seconds = config.get('delay_seconds', 1)
    
    @property
    def provider_name(self) -> str:
        return "MercadoPago"
    
    def is_available(self) -> bool:
        """Verifica si MercadoPago está disponible"""
        if self.mock_mode:
            return True
        
        # En modo real, verificar conectividad con la API
        try:
            # Aquí iría la verificación real de la API
            return bool(self.access_token and self.public_key)
        except Exception as e:
            logger.error(f"Error verificando disponibilidad de MercadoPago: {e}")
            return False
    
    def refund(self, payment_external_id: str, amount: Decimal, reason: Optional[str] = None) -> RefundResult:
        """
        Procesa un reembolso a través de MercadoPago
        
        Args:
            payment_external_id: ID del pago en MercadoPago
            amount: Monto a reembolsar
            reason: Razón del reembolso
            
        Returns:
            RefundResult: Resultado del procesamiento
        """
        logger.info(f"Iniciando reembolso MercadoPago: payment_id={payment_external_id}, amount={amount}")
        
        try:
            if self.mock_mode:
                return self._mock_refund(payment_external_id, amount, reason)
            else:
                return self._real_refund(payment_external_id, amount, reason)
                
        except Exception as e:
            logger.error(f"Error procesando reembolso MercadoPago: {e}")
            return RefundResult(
                success=False,
                error=f"Error interno: {str(e)}"
            )
    
    def _mock_refund(self, payment_external_id: str, amount: Decimal, reason: Optional[str] = None) -> RefundResult:
        """Implementación mock para testing"""
        
        # Simular delay si está configurado
        if self.simulate_delay:
            import time
            time.sleep(self.delay_seconds)
        
        # Simular fallo aleatorio si está configurado
        if random.random() < self.failure_rate:
            error_messages = [
                "Pago no encontrado",
                "Monto excede el límite permitido",
                "Reembolso ya procesado",
                "Error de conectividad con el banco",
                "Cuenta del vendedor suspendida"
            ]
            error = random.choice(error_messages)
            logger.warning(f"Mock fallo simulado: {error}")
            return RefundResult(
                success=False,
                error=error,
                raw_response={
                    "status": "rejected",
                    "error": error,
                    "payment_id": payment_external_id
                }
            )
        
        # Simular éxito
        refund_id = f"refund_{payment_external_id}_{int(datetime.now().timestamp())}"
        
        logger.info(f"Mock reembolso exitoso: refund_id={refund_id}")
        return RefundResult(
            success=True,
            external_id=refund_id,
            raw_response={
                "id": refund_id,
                "status": "approved",
                "amount": float(amount),
                "payment_id": payment_external_id,
                "created_at": datetime.now().isoformat(),
                "reason": reason
            }
        )
    
    def _real_refund(self, payment_external_id: str, amount: Decimal, reason: Optional[str] = None) -> RefundResult:
        """Implementación real para producción (placeholder)"""
        
        # TODO: Implementar llamada real a la API de MercadoPago
        # Por ahora, simular como si fuera mock
        logger.warning("Implementación real de MercadoPago no disponible, usando mock")
        return self._mock_refund(payment_external_id, amount, reason)
    
    def get_refund_status(self, refund_external_id: str) -> Dict[str, Any]:
        """
        Obtiene el estado de un reembolso
        
        Args:
            refund_external_id: ID del reembolso en MercadoPago
            
        Returns:
            Dict con información del estado
        """
        logger.info(f"Consultando estado de reembolso: {refund_external_id}")
        
        try:
            if self.mock_mode:
                return self._mock_get_refund_status(refund_external_id)
            else:
                return self._real_get_refund_status(refund_external_id)
                
        except Exception as e:
            logger.error(f"Error consultando estado de reembolso: {e}")
            return {
                "status": "error",
                "error": str(e),
                "refund_id": refund_external_id
            }
    
    def _mock_get_refund_status(self, refund_external_id: str) -> Dict[str, Any]:
        """Mock para consulta de estado"""
        
        # Simular diferentes estados
        statuses = ["pending", "approved", "rejected", "cancelled"]
        status = random.choice(statuses)
        
        return {
            "id": refund_external_id,
            "status": status,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        }
    
    def _real_get_refund_status(self, refund_external_id: str) -> Dict[str, Any]:
        """Implementación real para consulta de estado (placeholder)"""
        
        # TODO: Implementar consulta real a la API de MercadoPago
        logger.warning("Consulta real de estado no disponible, usando mock")
        return self._mock_get_refund_status(refund_external_id)
