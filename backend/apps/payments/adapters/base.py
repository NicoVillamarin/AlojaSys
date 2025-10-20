"""
Interfaz base para adaptadores de pasarelas de pago
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from decimal import Decimal


class RefundResult:
    """Resultado de un reembolso procesado por una pasarela"""
    
    def __init__(self, success: bool, external_id: Optional[str] = None, error: Optional[str] = None, raw_response: Optional[Dict[str, Any]] = None):
        self.success = success
        self.external_id = external_id
        self.error = error
        self.raw_response = raw_response or {}
    
    def __str__(self):
        if self.success:
            return f"RefundResult(success=True, external_id={self.external_id})"
        else:
            return f"RefundResult(success=False, error={self.error})"


class PaymentGatewayAdapter(ABC):
    """Interfaz base para adaptadores de pasarelas de pago"""
    
    @abstractmethod
    def refund(self, payment_external_id: str, amount: Decimal, reason: Optional[str] = None) -> RefundResult:
        """
        Procesa un reembolso a través de la pasarela de pago
        
        Args:
            payment_external_id: ID externo del pago original
            amount: Monto a reembolsar
            reason: Razón del reembolso (opcional)
            
        Returns:
            RefundResult: Resultado del procesamiento
        """
        pass
    
    @abstractmethod
    def get_refund_status(self, refund_external_id: str) -> Dict[str, Any]:
        """
        Obtiene el estado de un reembolso
        
        Args:
            refund_external_id: ID externo del reembolso
            
        Returns:
            Dict con información del estado del reembolso
        """
        pass
    
    @abstractmethod
    def is_available(self) -> bool:
        """
        Verifica si la pasarela está disponible para procesar reembolsos
        
        Returns:
            bool: True si está disponible, False en caso contrario
        """
        pass
    
    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Nombre del proveedor de la pasarela"""
        pass
