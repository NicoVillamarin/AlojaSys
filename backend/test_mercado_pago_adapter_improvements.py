"""
Tests para las mejoras del MercadoPagoAdapter
Incluye tests de idempotencia, simulación de errores y logging de trace_id
"""
import unittest
from decimal import Decimal
from unittest.mock import patch, MagicMock
from apps.payments.adapters.mercado_pago import MercadoPagoAdapter


class MercadoPagoAdapterImprovementsTestCase(unittest.TestCase):
    """Tests para las mejoras del MercadoPagoAdapter"""
    
    def setUp(self):
        """Configuración inicial para los tests"""
        self.config = {
            'access_token': 'test_access_token',
            'public_key': 'test_public_key',
            'is_test': True,
            'mock_mode': True
        }
        self.adapter = MercadoPagoAdapter(self.config, mock_mode=True)
    
    def test_idempotency_key_generation(self):
        """Test generación de claves de idempotencia únicas"""
        payment_id = "test_payment_123"
        
        # Generar múltiples claves para el mismo pago
        key1 = self.adapter._generate_idempotency_key("refund", payment_id)
        key2 = self.adapter._generate_idempotency_key("refund", payment_id)
        
        # Las claves deben ser diferentes
        self.assertNotEqual(key1, key2)
        
        # Deben contener información relevante
        self.assertIn("refund", key1)
        self.assertIn(payment_id, key1)
        self.assertIn("refund", key2)
        self.assertIn(payment_id, key2)
    
    def test_trace_id_generation(self):
        """Test generación de trace IDs únicos"""
        trace1 = self.adapter._generate_trace_id()
        trace2 = self.adapter._generate_trace_id()
        
        # Los trace IDs deben ser diferentes
        self.assertNotEqual(trace1, trace2)
        
        # Deben tener el formato correcto
        self.assertTrue(trace1.startswith("mp_trace_"))
        self.assertTrue(trace2.startswith("mp_trace_"))
        self.assertEqual(len(trace1), len("mp_trace_") + 16)  # 16 caracteres hex
    
    def test_refund_with_idempotency_and_trace(self):
        """Test refund con idempotencia y trace_id"""
        payment_id = "test_payment_123"
        amount = Decimal("100.00")
        reason = "Test refund"
        
        result = self.adapter.refund(payment_id, amount, reason)
        
        # Verificar que el resultado contiene trace_id e idempotency_key
        self.assertIn("trace_id", result.raw_response)
        self.assertIn("idempotency_key", result.raw_response)
        self.assertTrue(result.success)
    
    def test_capture_with_idempotency_and_trace(self):
        """Test capture con idempotencia y trace_id"""
        payment_id = "test_payment_123"
        amount = Decimal("50.00")
        
        result = self.adapter.capture(payment_id, amount)
        
        # Verificar que el resultado contiene trace_id e idempotency_key
        self.assertIn("trace_id", result.raw_response)
        self.assertIn("idempotency_key", result.raw_response)
        self.assertTrue(result.success)
    
    def test_connection_error_simulation(self):
        """Test simulación de error de conexión"""
        config = self.config.copy()
        config.update({
            'simulate_connection_error': True,
            'connection_error_rate': 1.0  # 100% de probabilidad
        })
        
        adapter = MercadoPagoAdapter(config, mock_mode=True)
        
        with self.assertRaises(Exception):  # Debe lanzar ConnectionError
            adapter._make_api_request("POST", "/test", {"test": "data"})
    
    def test_partial_refund_error_simulation(self):
        """Test simulación de error de reembolso parcial"""
        config = self.config.copy()
        config.update({
            'simulate_partial_refund_error': True,
            'partial_refund_error_rate': 1.0  # 100% de probabilidad
        })
        
        adapter = MercadoPagoAdapter(config, mock_mode=True)
        
        result = adapter.refund("test_payment_123", Decimal("50.00"))
        
        # Debe fallar con error específico
        self.assertFalse(result.success)
        self.assertEqual(result.error, "partial_refund_not_allowed")
        self.assertIn("partial_refund_not_allowed", result.raw_response["error"])
    
    def test_duplicate_simulation(self):
        """Test simulación de duplicados"""
        config = self.config.copy()
        config.update({
            'simulate_duplicates': True,
            'duplicate_rate': 1.0  # 100% de probabilidad
        })
        
        adapter = MercadoPagoAdapter(config, mock_mode=True)
        
        result = adapter.refund("test_payment_123", Decimal("100.00"))
        
        # Debe fallar con error de duplicado
        self.assertFalse(result.success)
        self.assertIn("ya procesado", result.error)
        self.assertTrue(result.raw_response.get("duplicate", False))
    
    def test_latency_simulation(self):
        """Test simulación de latencia"""
        import time
        
        config = self.config.copy()
        config.update({
            'simulate_latency': True,
            'latency_min_ms': 100,
            'latency_max_ms': 200
        })
        
        adapter = MercadoPagoAdapter(config, mock_mode=True)
        
        start_time = time.time()
        result = adapter.refund("test_payment_123", Decimal("100.00"))
        end_time = time.time()
        
        # Debe haber tomado al menos 100ms
        self.assertGreaterEqual(end_time - start_time, 0.1)
        self.assertTrue(result.success)
    
    def test_get_refund_status_with_trace(self):
        """Test consulta de estado con trace_id"""
        refund_id = "test_refund_123"
        
        result = self.adapter.get_refund_status(refund_id)
        
        # Debe contener trace_id
        self.assertIn("trace_id", result)
        self.assertIn("id", result)
        self.assertIn("status", result)
    
    def test_api_request_logging(self):
        """Test logging de peticiones API"""
        with patch('apps.payments.adapters.mercado_pago.logger') as mock_logger:
            # Configurar adapter para no simular errores
            config = self.config.copy()
            config.update({
                'failure_rate': 0.0,
                'simulate_duplicates': False,
                'simulate_connection_error': False
            })
            
            adapter = MercadoPagoAdapter(config, mock_mode=True)
            
            # Hacer una petición mock
            adapter._make_api_request("POST", "/test", {"test": "data"})
            
            # Verificar que se loggeó la petición
            mock_logger.info.assert_called()
            call_args = mock_logger.info.call_args
            self.assertIn("Petición saliente a MercadoPago", call_args[0][0])
            self.assertIn("trace_id", call_args[1]["extra"])
    
    def test_error_handling_with_trace(self):
        """Test manejo de errores con trace_id"""
        config = self.config.copy()
        config.update({
            'failure_rate': 1.0  # 100% de probabilidad de fallo
        })
        
        adapter = MercadoPagoAdapter(config, mock_mode=True)
        
        result = adapter.refund("test_payment_123", Decimal("100.00"))
        
        # Debe fallar pero incluir trace_id
        self.assertFalse(result.success)
        self.assertIn("trace_id", result.raw_response)
        self.assertIn("idempotency_key", result.raw_response)
    
    def test_capture_without_amount(self):
        """Test captura sin especificar monto"""
        payment_id = "test_payment_123"
        
        result = self.adapter.capture(payment_id)
        
        # Debe funcionar sin monto específico
        self.assertTrue(result.success)
        self.assertIn("trace_id", result.raw_response)
        self.assertIn("idempotency_key", result.raw_response)
    
    def test_real_mode_configuration(self):
        """Test configuración en modo real"""
        config = self.config.copy()
        config['mock_mode'] = False
        
        adapter = MercadoPagoAdapter(config, mock_mode=False)
        
        # Debe estar en modo real
        self.assertFalse(adapter.mock_mode)
        self.assertEqual(adapter.api_base_url, "https://api.mercadopago.com")
    
    def test_configuration_parameters(self):
        """Test parámetros de configuración"""
        config = self.config.copy()
        config.update({
            'simulate_connection_error': True,
            'connection_error_rate': 0.5,
            'simulate_partial_refund_error': True,
            'partial_refund_error_rate': 0.3
        })
        
        adapter = MercadoPagoAdapter(config, mock_mode=True)
        
        # Verificar configuración
        self.assertTrue(adapter.simulate_connection_error)
        self.assertEqual(adapter.connection_error_rate, 0.5)
        self.assertTrue(adapter.simulate_partial_refund_error)
        self.assertEqual(adapter.partial_refund_error_rate, 0.3)


class MercadoPagoAdapterIntegrationTestCase(unittest.TestCase):
    """Tests de integración para el MercadoPagoAdapter mejorado"""
    
    def setUp(self):
        """Configuración para tests de integración"""
        self.config = {
            'access_token': 'test_access_token',
            'public_key': 'test_public_key',
            'is_test': True,
            'mock_mode': True,
            'simulate_latency': True,
            'latency_min_ms': 50,
            'latency_max_ms': 100
        }
        self.adapter = MercadoPagoAdapter(self.config, mock_mode=True)
    
    def test_full_refund_flow(self):
        """Test flujo completo de reembolso"""
        payment_id = "test_payment_123"
        amount = Decimal("150.00")
        reason = "Customer cancellation"
        
        # 1. Procesar reembolso
        refund_result = self.adapter.refund(payment_id, amount, reason)
        
        self.assertTrue(refund_result.success)
        self.assertIn("trace_id", refund_result.raw_response)
        self.assertIn("idempotency_key", refund_result.raw_response)
        
        # 2. Consultar estado del reembolso
        refund_id = refund_result.external_id
        status_result = self.adapter.get_refund_status(refund_id)
        
        self.assertIn("trace_id", status_result)
        self.assertIn("status", status_result)
    
    def test_full_capture_flow(self):
        """Test flujo completo de captura"""
        payment_id = "test_payment_456"
        amount = Decimal("200.00")
        
        # 1. Procesar captura
        capture_result = self.adapter.capture(payment_id, amount)
        
        self.assertTrue(capture_result.success)
        self.assertIn("trace_id", capture_result.raw_response)
        self.assertIn("idempotency_key", capture_result.raw_response)
    
    def test_error_scenarios(self):
        """Test escenarios de error"""
        payment_id = "test_payment_error"
        amount = Decimal("100.00")
        
        # Configurar para simular errores
        config = self.config.copy()
        config.update({
            'simulate_partial_refund_error': True,
            'partial_refund_error_rate': 1.0
        })
        
        error_adapter = MercadoPagoAdapter(config, mock_mode=True)
        
        # Debe fallar con error específico
        result = error_adapter.refund(payment_id, amount)
        
        self.assertFalse(result.success)
        self.assertEqual(result.error, "partial_refund_not_allowed")
        self.assertIn("trace_id", result.raw_response)


if __name__ == '__main__':
    unittest.main()
