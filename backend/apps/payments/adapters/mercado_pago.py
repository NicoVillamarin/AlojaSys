"""
Adapter para MercadoPago
Implementación mockeable para testing y desarrollo
"""
import logging
import uuid
import requests
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
        
        # Para simular duplicados y latencia en tests
        self.simulate_duplicates = config.get('simulate_duplicates', False)
        self.duplicate_rate = config.get('duplicate_rate', 0.0)  # 0-1, probabilidad de duplicado
        self.simulate_latency = config.get('simulate_latency', False)
        self.latency_min_ms = config.get('latency_min_ms', 100)
        self.latency_max_ms = config.get('latency_max_ms', 2000)
        
        # Nuevas configuraciones para mejoras
        self.simulate_connection_error = config.get('simulate_connection_error', False)
        self.simulate_partial_refund_error = config.get('simulate_partial_refund_error', False)
        self.connection_error_rate = config.get('connection_error_rate', 0.0)  # 0-1, probabilidad de error de conexión
        self.partial_refund_error_rate = config.get('partial_refund_error_rate', 0.0)  # 0-1, probabilidad de error de reembolso parcial
        
        # URL base de la API de MercadoPago
        self.api_base_url = "https://api.mercadopago.com" if not self.is_test else "https://api.mercadopago.com"
    
    @property
    def provider_name(self) -> str:
        return "MercadoPago"
    
    def _generate_idempotency_key(self, operation: str, payment_id: str) -> str:
        """
        Genera una clave de idempotencia única para una operación
        
        Args:
            operation: Tipo de operación (refund, capture, etc.)
            payment_id: ID del pago
            
        Returns:
            str: Clave de idempotencia única
        """
        timestamp = int(datetime.now().timestamp())
        unique_id = str(uuid.uuid4())[:8]
        return f"{operation}_{payment_id}_{timestamp}_{unique_id}"
    
    def _generate_trace_id(self) -> str:
        """
        Genera un trace ID único para rastrear peticiones
        
        Returns:
            str: Trace ID único
        """
        return f"mp_trace_{uuid.uuid4().hex[:16]}"
    
    def _make_api_request(self, method: str, endpoint: str, data: Dict[str, Any] = None, 
                         idempotency_key: str = None, trace_id: str = None) -> Dict[str, Any]:
        """
        Realiza una petición HTTP a la API de MercadoPago con logging y manejo de errores
        
        Args:
            method: Método HTTP (GET, POST, PUT, etc.)
            endpoint: Endpoint de la API
            data: Datos a enviar
            idempotency_key: Clave de idempotencia
            trace_id: ID de trazabilidad
            
        Returns:
            Dict con la respuesta de la API
        """
        if not trace_id:
            trace_id = self._generate_trace_id()
        
        url = f"{self.api_base_url}{endpoint}"
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'Content-Type': 'application/json',
            'X-Trace-Id': trace_id
        }
        
        if idempotency_key:
            headers['X-Idempotency-Key'] = idempotency_key
        
        # Log de la petición saliente
        logger.info(
            f"Petición saliente a MercadoPago",
            extra={
                'trace_id': trace_id,
                'method': method,
                'endpoint': endpoint,
                'idempotency_key': idempotency_key,
                'is_test': self.is_test
            }
        )
        
        try:
            if self.mock_mode:
                return self._mock_api_request(method, endpoint, data, trace_id)
            
            response = requests.request(
                method=method,
                url=url,
                headers=headers,
                json=data,
                timeout=30
            )
            
            # Log de la respuesta
            logger.info(
                f"Respuesta recibida de MercadoPago",
                extra={
                    'trace_id': trace_id,
                    'status_code': response.status_code,
                    'response_size': len(response.content) if response.content else 0
                }
            )
            
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.RequestException as e:
            logger.error(
                f"Error en petición a MercadoPago: {e}",
                extra={
                    'trace_id': trace_id,
                    'method': method,
                    'endpoint': endpoint,
                    'error': str(e)
                }
            )
            raise
    
    def _mock_api_request(self, method: str, endpoint: str, data: Dict[str, Any] = None, 
                         trace_id: str = None) -> Dict[str, Any]:
        """
        Simula una petición a la API de MercadoPago para testing
        """
        # Simular latencia si está configurado
        if self.simulate_latency:
            import time
            latency_ms = random.randint(self.latency_min_ms, self.latency_max_ms)
            time.sleep(latency_ms / 1000.0)
            logger.info(f"Mock latencia simulada: {latency_ms}ms (trace_id: {trace_id})")
        
        # Simular error de conexión si está configurado
        if self.simulate_connection_error and random.random() < self.connection_error_rate:
            logger.warning(f"Mock error de conexión simulado (trace_id: {trace_id})")
            raise requests.exceptions.ConnectionError("Mock connection error")
        
        # Simular delay si está configurado
        if self.simulate_delay:
            import time
            time.sleep(self.delay_seconds)
        
        # Simular duplicados si está configurado
        if self.simulate_duplicates and random.random() < self.duplicate_rate:
            logger.warning(f"Mock duplicado simulado (trace_id: {trace_id})")
            return {
                "error": "idempotency_key_already_used",
                "message": "La clave de idempotencia ya fue utilizada",
                "trace_id": trace_id
            }
        
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
            logger.warning(f"Mock fallo simulado: {error} (trace_id: {trace_id})")
            return {
                "error": "mock_error",
                "message": error,
                "trace_id": trace_id
            }
        
        # Simular respuesta exitosa
        if "refunds" in endpoint:
            refund_id = f"refund_{int(datetime.now().timestamp())}"
            return {
                "id": refund_id,
                "status": "approved",
                "amount": data.get("amount", 0) if data else 0,
                "payment_id": data.get("payment_id", "unknown") if data else "unknown",
                "created_at": datetime.now().isoformat(),
                "trace_id": trace_id
            }
        
        return {
            "success": True,
            "trace_id": trace_id,
            "mock_response": True
        }
    
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
        Procesa un reembolso a través de MercadoPago con idempotencia y logging
        
        Args:
            payment_external_id: ID del pago en MercadoPago
            amount: Monto a reembolsar
            reason: Razón del reembolso
            
        Returns:
            RefundResult: Resultado del procesamiento
        """
        trace_id = self._generate_trace_id()
        idempotency_key = self._generate_idempotency_key("refund", payment_external_id)
        
        logger.info(
            f"Iniciando reembolso MercadoPago",
            extra={
                'trace_id': trace_id,
                'payment_id': payment_external_id,
                'amount': float(amount),
                'reason': reason,
                'idempotency_key': idempotency_key
            }
        )
        
        try:
            # Simular error de reembolso parcial si está configurado
            if (self.simulate_partial_refund_error and 
                random.random() < self.partial_refund_error_rate):
                logger.warning(f"Mock error de reembolso parcial simulado (trace_id: {trace_id})")
                return RefundResult(
                    success=False,
                    error="partial_refund_not_allowed",
                    raw_response={
                        "error": "partial_refund_not_allowed",
                        "message": "Los reembolsos parciales no están permitidos para este pago",
                        "trace_id": trace_id
                    }
                )
            
            if self.mock_mode:
                return self._mock_refund(payment_external_id, amount, reason, trace_id, idempotency_key)
            else:
                return self._real_refund(payment_external_id, amount, reason, trace_id, idempotency_key)
                
        except Exception as e:
            logger.error(
                f"Error procesando reembolso MercadoPago: {e}",
                extra={
                    'trace_id': trace_id,
                    'payment_id': payment_external_id,
                    'error': str(e)
                }
            )
            return RefundResult(
                success=False,
                error=f"Error interno: {str(e)}",
                raw_response={
                    "error": "internal_error",
                    "message": str(e),
                    "trace_id": trace_id
                }
            )
    
    def _mock_refund(self, payment_external_id: str, amount: Decimal, reason: Optional[str] = None, 
                     trace_id: str = None, idempotency_key: str = None) -> RefundResult:
        """Implementación mock para testing con nuevas funcionalidades"""
        
        # Simular latencia si está configurado
        if self.simulate_latency:
            import time
            latency_ms = random.randint(self.latency_min_ms, self.latency_max_ms)
            time.sleep(latency_ms / 1000.0)
            logger.info(f"Mock latencia simulada: {latency_ms}ms (trace_id: {trace_id})")
        
        # Simular delay si está configurado
        if self.simulate_delay:
            import time
            time.sleep(self.delay_seconds)
        
        # Simular duplicados si está configurado
        if self.simulate_duplicates and random.random() < self.duplicate_rate:
            logger.warning(f"Mock duplicado simulado para payment: {payment_external_id} (trace_id: {trace_id})")
            return RefundResult(
                success=False,
                error="Reembolso ya procesado",
                raw_response={
                    "status": "rejected",
                    "error": "Reembolso ya procesado",
                    "payment_id": payment_external_id,
                    "duplicate": True,
                    "trace_id": trace_id,
                    "idempotency_key": idempotency_key
                }
            )
        
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
            logger.warning(f"Mock fallo simulado: {error} (trace_id: {trace_id})")
            return RefundResult(
                success=False,
                error=error,
                raw_response={
                    "status": "rejected",
                    "error": error,
                    "payment_id": payment_external_id,
                    "trace_id": trace_id,
                    "idempotency_key": idempotency_key
                }
            )
        
        # Simular éxito
        refund_id = f"refund_{payment_external_id}_{int(datetime.now().timestamp())}"
        
        logger.info(
            f"Mock reembolso exitoso: refund_id={refund_id}",
            extra={
                'trace_id': trace_id,
                'refund_id': refund_id,
                'payment_id': payment_external_id,
                'amount': float(amount)
            }
        )
        
        return RefundResult(
            success=True,
            external_id=refund_id,
            raw_response={
                "id": refund_id,
                "status": "approved",
                "amount": float(amount),
                "payment_id": payment_external_id,
                "created_at": datetime.now().isoformat(),
                "reason": reason,
                "trace_id": trace_id,
                "idempotency_key": idempotency_key
            }
        )
    
    def _real_refund(self, payment_external_id: str, amount: Decimal, reason: Optional[str] = None, 
                     trace_id: str = None, idempotency_key: str = None) -> RefundResult:
        """Implementación real para producción con idempotencia"""
        
        try:
            # Preparar datos para la API
            refund_data = {
                "amount": float(amount),
                "payment_id": payment_external_id
            }
            
            if reason:
                refund_data["reason"] = reason
            
            # Llamar a la API de MercadoPago
            response = self._make_api_request(
                method="POST",
                endpoint=f"/v1/payments/{payment_external_id}/refunds",
                data=refund_data,
                idempotency_key=idempotency_key,
                trace_id=trace_id
            )
            
            # Procesar respuesta
            if response.get("error"):
                return RefundResult(
                    success=False,
                    error=response.get("message", "Error desconocido"),
                    raw_response=response
                )
            
            return RefundResult(
                success=True,
                external_id=response.get("id"),
                raw_response=response
            )
            
        except requests.exceptions.ConnectionError as e:
            logger.error(f"Error de conexión en reembolso real: {e} (trace_id: {trace_id})")
            return RefundResult(
                success=False,
                error="connection_error",
                raw_response={
                    "error": "connection_error",
                    "message": "Error de conexión con MercadoPago",
                    "trace_id": trace_id
                }
            )
        except Exception as e:
            logger.error(f"Error en reembolso real: {e} (trace_id: {trace_id})")
            return RefundResult(
                success=False,
                error=f"Error interno: {str(e)}",
                raw_response={
                    "error": "internal_error",
                    "message": str(e),
                    "trace_id": trace_id
                }
            )
    
    def capture(self, payment_external_id: str, amount: Decimal = None) -> RefundResult:
        """
        Captura un pago autorizado en MercadoPago
        
        Args:
            payment_external_id: ID del pago en MercadoPago
            amount: Monto a capturar (opcional, si no se especifica captura el total)
            
        Returns:
            RefundResult: Resultado del procesamiento
        """
        trace_id = self._generate_trace_id()
        idempotency_key = self._generate_idempotency_key("capture", payment_external_id)
        
        logger.info(
            f"Iniciando captura MercadoPago",
            extra={
                'trace_id': trace_id,
                'payment_id': payment_external_id,
                'amount': float(amount) if amount else None,
                'idempotency_key': idempotency_key
            }
        )
        
        try:
            if self.mock_mode:
                return self._mock_capture(payment_external_id, amount, trace_id, idempotency_key)
            else:
                return self._real_capture(payment_external_id, amount, trace_id, idempotency_key)
                
        except Exception as e:
            logger.error(
                f"Error procesando captura MercadoPago: {e}",
                extra={
                    'trace_id': trace_id,
                    'payment_id': payment_external_id,
                    'error': str(e)
                }
            )
            return RefundResult(
                success=False,
                error=f"Error interno: {str(e)}",
                raw_response={
                    "error": "internal_error",
                    "message": str(e),
                    "trace_id": trace_id
                }
            )
    
    def _mock_capture(self, payment_external_id: str, amount: Decimal = None, 
                     trace_id: str = None, idempotency_key: str = None) -> RefundResult:
        """Implementación mock para captura"""
        
        # Simular latencia si está configurado
        if self.simulate_latency:
            import time
            latency_ms = random.randint(self.latency_min_ms, self.latency_max_ms)
            time.sleep(latency_ms / 1000.0)
            logger.info(f"Mock latencia simulada en captura: {latency_ms}ms (trace_id: {trace_id})")
        
        # Simular delay si está configurado
        if self.simulate_delay:
            import time
            time.sleep(self.delay_seconds)
        
        # Simular duplicados si está configurado
        if self.simulate_duplicates and random.random() < self.duplicate_rate:
            logger.warning(f"Mock duplicado simulado en captura para payment: {payment_external_id} (trace_id: {trace_id})")
            return RefundResult(
                success=False,
                error="Captura ya procesada",
                raw_response={
                    "status": "rejected",
                    "error": "Captura ya procesada",
                    "payment_id": payment_external_id,
                    "duplicate": True,
                    "trace_id": trace_id,
                    "idempotency_key": idempotency_key
                }
            )
        
        # Simular fallo aleatorio si está configurado
        if random.random() < self.failure_rate:
            error_messages = [
                "Pago no encontrado",
                "Pago ya capturado",
                "Monto excede el límite permitido",
                "Error de conectividad con el banco",
                "Cuenta del vendedor suspendida"
            ]
            error = random.choice(error_messages)
            logger.warning(f"Mock fallo simulado en captura: {error} (trace_id: {trace_id})")
            return RefundResult(
                success=False,
                error=error,
                raw_response={
                    "status": "rejected",
                    "error": error,
                    "payment_id": payment_external_id,
                    "trace_id": trace_id,
                    "idempotency_key": idempotency_key
                }
            )
        
        # Simular éxito
        capture_id = f"capture_{payment_external_id}_{int(datetime.now().timestamp())}"
        
        logger.info(
            f"Mock captura exitosa: capture_id={capture_id}",
            extra={
                'trace_id': trace_id,
                'capture_id': capture_id,
                'payment_id': payment_external_id,
                'amount': float(amount) if amount else None
            }
        )
        
        return RefundResult(
            success=True,
            external_id=capture_id,
            raw_response={
                "id": capture_id,
                "status": "approved",
                "amount": float(amount) if amount else 0,
                "payment_id": payment_external_id,
                "created_at": datetime.now().isoformat(),
                "trace_id": trace_id,
                "idempotency_key": idempotency_key
            }
        )
    
    def _real_capture(self, payment_external_id: str, amount: Decimal = None, 
                     trace_id: str = None, idempotency_key: str = None) -> RefundResult:
        """Implementación real para captura"""
        
        try:
            # Preparar datos para la API
            capture_data = {}
            if amount:
                capture_data["transaction_amount"] = float(amount)
            
            # Llamar a la API de MercadoPago
            response = self._make_api_request(
                method="POST",
                endpoint=f"/v1/payments/{payment_external_id}/capture",
                data=capture_data,
                idempotency_key=idempotency_key,
                trace_id=trace_id
            )
            
            # Procesar respuesta
            if response.get("error"):
                return RefundResult(
                    success=False,
                    error=response.get("message", "Error desconocido"),
                    raw_response=response
                )
            
            return RefundResult(
                success=True,
                external_id=response.get("id"),
                raw_response=response
            )
            
        except requests.exceptions.ConnectionError as e:
            logger.error(f"Error de conexión en captura real: {e} (trace_id: {trace_id})")
            return RefundResult(
                success=False,
                error="connection_error",
                raw_response={
                    "error": "connection_error",
                    "message": "Error de conexión con MercadoPago",
                    "trace_id": trace_id
                }
            )
        except Exception as e:
            logger.error(f"Error en captura real: {e} (trace_id: {trace_id})")
            return RefundResult(
                success=False,
                error=f"Error interno: {str(e)}",
                raw_response={
                    "error": "internal_error",
                    "message": str(e),
                    "trace_id": trace_id
                }
            )
    
    def get_refund_status(self, refund_external_id: str) -> Dict[str, Any]:
        """
        Obtiene el estado de un reembolso con logging de trace_id
        
        Args:
            refund_external_id: ID del reembolso en MercadoPago
            
        Returns:
            Dict con información del estado
        """
        trace_id = self._generate_trace_id()
        
        logger.info(
            f"Consultando estado de reembolso",
            extra={
                'trace_id': trace_id,
                'refund_id': refund_external_id
            }
        )
        
        try:
            if self.mock_mode:
                return self._mock_get_refund_status(refund_external_id, trace_id)
            else:
                return self._real_get_refund_status(refund_external_id, trace_id)
                
        except Exception as e:
            logger.error(
                f"Error consultando estado de reembolso: {e}",
                extra={
                    'trace_id': trace_id,
                    'refund_id': refund_external_id,
                    'error': str(e)
                }
            )
            return {
                "status": "error",
                "error": str(e),
                "refund_id": refund_external_id,
                "trace_id": trace_id
            }
    
    def _mock_get_refund_status(self, refund_external_id: str, trace_id: str = None) -> Dict[str, Any]:
        """Mock para consulta de estado con trace_id"""
        
        # Simular latencia si está configurado
        if self.simulate_latency:
            import time
            latency_ms = random.randint(self.latency_min_ms, self.latency_max_ms)
            time.sleep(latency_ms / 1000.0)
            logger.info(f"Mock latencia simulada en consulta: {latency_ms}ms (trace_id: {trace_id})")
        
        # Simular diferentes estados
        statuses = ["pending", "approved", "rejected", "cancelled"]
        status = random.choice(statuses)
        
        result = {
            "id": refund_external_id,
            "status": status,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "trace_id": trace_id
        }
        
        logger.info(
            f"Mock consulta de estado completada",
            extra={
                'trace_id': trace_id,
                'refund_id': refund_external_id,
                'status': status
            }
        )
        
        return result
    
    def _real_get_refund_status(self, refund_external_id: str, trace_id: str = None) -> Dict[str, Any]:
        """Implementación real para consulta de estado"""
        
        try:
            # Llamar a la API de MercadoPago
            response = self._make_api_request(
                method="GET",
                endpoint=f"/v1/refunds/{refund_external_id}",
                trace_id=trace_id
            )
            
            # Agregar trace_id a la respuesta
            response["trace_id"] = trace_id
            
            logger.info(
                f"Consulta real de estado completada",
                extra={
                    'trace_id': trace_id,
                    'refund_id': refund_external_id,
                    'status': response.get('status')
                }
            )
            
            return response
            
        except Exception as e:
            logger.error(f"Error en consulta real de estado: {e} (trace_id: {trace_id})")
            return {
                "id": refund_external_id,
                "status": "error",
                "error": str(e),
                "trace_id": trace_id
            }
