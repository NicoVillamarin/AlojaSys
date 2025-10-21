"""
Tests simplificados para las mejoras del endpoint webhook
Enfocado en la funcionalidad principal sin dependencias complejas
"""
import unittest
import json
import hmac
import hashlib
from unittest.mock import patch, MagicMock
from django.test import TestCase, Client
from django.urls import reverse
from django.conf import settings
from rest_framework.test import APIClient
from apps.payments.services.webhook_security import WebhookSecurityService


class SimpleWebhookTestCase(TestCase):
    """Tests simplificados para webhook improvements"""
    
    def setUp(self):
        """Configuración inicial para los tests"""
        self.client = APIClient()
        self.webhook_url = reverse('payments-webhook')
        self.webhook_secret = 'test_webhook_secret'
        
        # Configurar ALLOWED_HOSTS para testing
        from django.conf import settings
        if 'testserver' not in settings.ALLOWED_HOSTS:
            settings.ALLOWED_HOSTS.append('testserver')
    
    def _create_webhook_signature(self, body, secret):
        """Crea una firma HMAC para el webhook"""
        return hmac.new(
            secret.encode('utf-8'),
            body,
            hashlib.sha256
        ).hexdigest()
    
    def _create_webhook_request(self, payment_data, notification_id='test_notification_123'):
        """Crea una petición de webhook con firma HMAC válida"""
        body = json.dumps(payment_data).encode('utf-8')
        signature = self._create_webhook_signature(body, self.webhook_secret)
        
        return {
            'data': json.dumps(payment_data),
            'type': 'payment',
            'id': payment_data.get('id'),
            'notification_id': notification_id,
            'external_reference': 'reservation:1|hotel:1'
        }, {
            'X-Signature': signature,
            'Content-Type': 'application/json'
        }
    
    def test_webhook_hmac_verification_success(self):
        """Test verificación HMAC exitosa"""
        payment_data = {
            'id': '123456789',
            'status': 'approved',
            'external_reference': 'reservation:1|hotel:1',
            'transaction_amount': 200.00
        }
        
        data, headers = self._create_webhook_request(payment_data)
        
        # Mock de la verificación HMAC para que pase
        with patch('apps.payments.services.webhook_security.WebhookSecurityService.verify_webhook_signature', return_value=True):
            with patch('apps.payments.services.webhook_security.WebhookSecurityService.is_notification_processed', return_value=False):
                with patch('os.environ.get', return_value='TEST_ACCESS_TOKEN'):
                    with patch('mercadopago.SDK') as mock_sdk:
                        # Mock de respuesta de Mercado Pago
                        mock_payment = MagicMock()
                        mock_payment.get.return_value = {
                            'status': 200,
                            'response': payment_data
                        }
                        mock_sdk.return_value.payment.return_value = mock_payment
                        
                        with patch('apps.payments.services.payment_processor.PaymentProcessorService.process_webhook_payment', return_value={
                            'success': True,
                            'processed': True,
                            'payment_intent_id': 123,
                            'status': 'approved',
                            'message': 'Pago procesado exitosamente'
                        }):
                            response = self.client.post(
                                f"{self.webhook_url}?type=payment&notification_id=test_123",
                                data=data,
                                content_type='application/json',
                                **headers
                            )
        
        self.assertEqual(response.status_code, 200)
        response_data = response.json()
        self.assertTrue(response_data['success'])
        self.assertTrue(response_data['processed'])
        self.assertEqual(response_data['status'], 'approved')
    
    def test_webhook_hmac_verification_failure(self):
        """Test fallo en verificación HMAC"""
        payment_data = {
            'id': '123456789',
            'status': 'approved',
            'external_reference': 'reservation:1|hotel:1',
            'transaction_amount': 200.00
        }
        
        data, headers = self._create_webhook_request(payment_data)
        
        # Mock de la verificación HMAC para que falle
        with patch('apps.payments.services.webhook_security.WebhookSecurityService.verify_webhook_signature', return_value=False):
            response = self.client.post(
                f"{self.webhook_url}?type=payment&notification_id=test_123",
                data=data,
                content_type='application/json',
                **headers
            )
        
        self.assertEqual(response.status_code, 400)
        response_data = response.json()
        self.assertFalse(response_data['success'])
        self.assertEqual(response_data['code'], 'HMAC_VERIFICATION_FAILED')
        self.assertIn('Firma HMAC inválida', response_data['error'])
    
    def test_webhook_idempotency_duplicate(self):
        """Test detección de notificación duplicada"""
        payment_data = {
            'id': '123456789',
            'status': 'approved',
            'external_reference': 'reservation:1|hotel:1',
            'transaction_amount': 200.00
        }
        
        data, headers = self._create_webhook_request(payment_data, 'duplicate_notification')
        
        # Mock de verificación HMAC exitosa pero notificación duplicada
        with patch('apps.payments.services.webhook_security.WebhookSecurityService.verify_webhook_signature', return_value=True):
            with patch('apps.payments.services.webhook_security.WebhookSecurityService.is_notification_processed', return_value=True):
                response = self.client.post(
                    f"{self.webhook_url}?type=payment&notification_id=test_123",
                    data=data,
                    content_type='application/json',
                    **headers
                )
        
        self.assertEqual(response.status_code, 200)
        response_data = response.json()
        self.assertTrue(response_data['success'])
        self.assertFalse(response_data['processed'])
        self.assertEqual(response_data['code'], 'DUPLICATE_NOTIFICATION')
    
    def test_webhook_missing_access_token(self):
        """Test error cuando falta ACCESS_TOKEN"""
        payment_data = {
            'id': '123456789',
            'status': 'approved',
            'external_reference': 'reservation:1|hotel:1',
            'transaction_amount': 200.00
        }
        
        data, headers = self._create_webhook_request(payment_data)
        
        # Mock de verificación HMAC exitosa pero sin ACCESS_TOKEN
        with patch('apps.payments.services.webhook_security.WebhookSecurityService.verify_webhook_signature', return_value=True):
            with patch('apps.payments.services.webhook_security.WebhookSecurityService.is_notification_processed', return_value=False):
                with patch('os.environ.get', return_value=None):
                    response = self.client.post(
                        f"{self.webhook_url}?type=payment&notification_id=test_123",
                        data=data,
                        content_type='application/json',
                        **headers
                    )
        
        self.assertEqual(response.status_code, 400)
        response_data = response.json()
        self.assertFalse(response_data['success'])
        self.assertEqual(response_data['code'], 'MISSING_ACCESS_TOKEN')
        self.assertIn('ACCESS_TOKEN no configurado', response_data['error'])
    
    def test_webhook_invalid_event_type(self):
        """Test webhook con tipo de evento inválido"""
        data = {
            'data': json.dumps({'id': '123456789'}),
            'type': 'invalid_event',
            'id': '123456789',
            'notification_id': 'test_notification_123'
        }
        
        response = self.client.post(
            self.webhook_url,
            data=data,
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        response_data = response.json()
        self.assertTrue(response_data['received'])
        self.assertIn('evento no procesado', response_data['note'])
    
    def test_webhook_missing_payment_id(self):
        """Test webhook sin payment_id"""
        data = {
            'data': json.dumps({'status': 'approved'}),
            'type': 'payment',
            'notification_id': 'test_notification_123'
        }
        
        response = self.client.post(
            self.webhook_url,
            data=data,
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        response_data = response.json()
        self.assertTrue(response_data['received'])
        self.assertIn('evento no procesado', response_data['note'])
    
    def test_webhook_security_service_hmac_verification(self):
        """Test directo del WebhookSecurityService"""
        # Crear un request mock
        class MockRequest:
            def __init__(self, body, signature):
                self.body = body
                self.headers = {'X-Signature': signature}
        
        body = b'{"test": "data"}'
        signature = self._create_webhook_signature(body, self.webhook_secret)
        request = MockRequest(body, signature)
        
        # Test verificación exitosa
        result = WebhookSecurityService.verify_webhook_signature(request, self.webhook_secret)
        self.assertTrue(result)
        
        # Test verificación fallida
        invalid_signature = 'invalid_signature'
        request_invalid = MockRequest(body, invalid_signature)
        result_invalid = WebhookSecurityService.verify_webhook_signature(request_invalid, self.webhook_secret)
        self.assertFalse(result_invalid)
    
    def test_webhook_security_service_idempotency(self):
        """Test directo del sistema de idempotencia"""
        notification_id = 'test_notification_123'
        external_reference = 'reservation:1|hotel:1'
        
        # Test notificación no procesada
        result = WebhookSecurityService.is_notification_processed(notification_id, external_reference)
        self.assertFalse(result)
        
        # Marcar como procesada
        WebhookSecurityService.mark_notification_processed(notification_id, external_reference)
        
        # Test notificación ya procesada
        result = WebhookSecurityService.is_notification_processed(notification_id, external_reference)
        self.assertTrue(result)
    
    def test_webhook_security_service_extract_data(self):
        """Test extracción de datos del webhook"""
        class MockRequest:
            def __init__(self, data, query_params):
                self.data = data
                self.query_params = query_params
        
        request = MockRequest(
            {'id': '123456789', 'status': 'approved'},
            {'type': 'payment', 'notification_id': 'test_123'}
        )
        
        result = WebhookSecurityService.extract_webhook_data(request)
        
        self.assertEqual(result['topic'], 'payment')
        self.assertEqual(result['payment_id'], '123456789')
        self.assertEqual(result['notification_id'], 'test_123')
        self.assertIsNotNone(result['raw_data'])


if __name__ == '__main__':
    unittest.main()
