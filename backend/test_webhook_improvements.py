"""
Tests para las mejoras del endpoint webhook
Incluye tests de verificación HMAC, idempotencia, respuestas HTTP y post-procesamiento
"""
import unittest
import json
import hmac
import hashlib
from unittest.mock import patch, MagicMock
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from apps.payments.models import PaymentIntent, PaymentGatewayConfig
from apps.reservations.models import Reservation, Hotel, Room
from apps.enterprises.models import Enterprise
from apps.locations.models import Country, State, City


class WebhookImprovementsTestCase(TestCase):
    """Tests para las mejoras del endpoint webhook"""
    
    def setUp(self):
        """Configuración inicial para los tests"""
        self.client = Client()
        
        # Crear datos de prueba
        self.country = Country.objects.create(
            code2='AR', code3='ARG', name='Argentina',
            phone_code='+54', currency_code='ARS'
        )
        self.state = State.objects.create(
            country=self.country, code='BA', name='Buenos Aires'
        )
        self.city = City.objects.create(
            state=self.state, name='Buenos Aires', postal_code='1000'
        )
        
        self.enterprise = Enterprise.objects.create(
            name='Hotel Test Enterprise',
            legal_name='Hotel Test Enterprise S.A.',
            tax_id='20-12345678-9',
            email='test@hotel.com',
            phone='+54 11 1234-5678',
            address='Av. Test 123',
            country=self.country,
            state=self.state,
            city=self.city
        )
        
        self.hotel = Hotel.objects.create(
            enterprise=self.enterprise,
            name='Hotel Test',
            legal_name='Hotel Test S.A.',
            tax_id='20-12345678-9',
            email='hotel@test.com',
            phone='+54 11 1234-5678',
            address='Av. Test 123',
            country=self.country,
            state=self.state,
            city=self.city,
            timezone='America/Argentina/Buenos_Aires',
            check_in_time='14:00:00',
            check_out_time='11:00:00'
        )
        
        from decimal import Decimal
        
        self.room = Room.objects.create(
            name='Habitación 101',
            hotel=self.hotel,
            floor=1,
            room_type='double',
            number=101,
            description='Habitación doble',
            base_price=Decimal('100.00'),
            capacity=2,
            max_capacity=4,
            extra_guest_fee=Decimal('25.00'),
            status='available'
        )
        
        from datetime import date
        
        self.reservation = Reservation.objects.create(
            hotel=self.hotel,
            room=self.room,
            guests=2,
            guests_data=[
                {
                    'name': 'Juan Pérez',
                    'email': 'juan@example.com',
                    'phone': '+54 11 1234-5678',
                    'is_primary': True,
                    'adults': 2,
                    'children': 0
                }
            ],
            channel='direct',
            check_in=date(2024, 1, 15),
            check_out=date(2024, 1, 17),
            status='pending',
            total_price=Decimal('200.00')
        )
        
        self.payment_intent = PaymentIntent.objects.create(
            reservation=self.reservation,
            hotel=self.hotel,
            enterprise=self.enterprise,
            amount=Decimal('200.00'),
            currency='ARS',
            description='Reserva 1',
            external_reference='reservation:1|hotel:1',
            status='pending'
        )
        
        # Configuración de gateway
        self.gateway_config = PaymentGatewayConfig.objects.create(
            provider='mercado_pago',
            enterprise=self.enterprise,
            hotel=self.hotel,
            public_key='TEST_PUBLIC_KEY',
            access_token='TEST_ACCESS_TOKEN',
            webhook_secret='test_webhook_secret',
            is_test=True,
            is_active=True
        )
        
        self.webhook_url = reverse('payments-webhook')
        self.webhook_secret = 'test_webhook_secret'
    
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
    
    @patch('os.environ.get')
    @patch('mercadopago.SDK')
    def test_webhook_hmac_verification_success(self, mock_sdk, mock_env):
        """Test verificación HMAC exitosa"""
        mock_env.return_value = 'TEST_ACCESS_TOKEN'
        
        # Mock de respuesta de Mercado Pago
        mock_payment = MagicMock()
        mock_payment.get.return_value = {
            'status': 200,
            'response': {
                'id': '123456789',
                'status': 'approved',
                'external_reference': 'reservation:1|hotel:1',
                'transaction_amount': 200.00
            }
        }
        mock_sdk.return_value.payment.return_value = mock_payment
        
        # Datos del webhook
        payment_data = {
            'id': '123456789',
            'status': 'approved',
            'external_reference': 'reservation:1|hotel:1',
            'transaction_amount': 200.00
        }
        
        data, headers = self._create_webhook_request(payment_data)
        
        response = self.client.post(
            self.webhook_url,
            data=data,
            content_type='application/json',
            **headers
        )
        
        self.assertEqual(response.status_code, 200)
        response_data = response.json()
        self.assertTrue(response_data['success'])
        self.assertTrue(response_data['processed'])
        self.assertEqual(response_data['status'], 'approved')
    
    @patch('os.environ.get')
    def test_webhook_hmac_verification_failure(self, mock_env):
        """Test fallo en verificación HMAC"""
        mock_env.return_value = 'TEST_ACCESS_TOKEN'
        
        # Datos del webhook con firma inválida
        payment_data = {
            'id': '123456789',
            'status': 'approved',
            'external_reference': 'reservation:1|hotel:1',
            'transaction_amount': 200.00
        }
        
        body = json.dumps(payment_data).encode('utf-8')
        invalid_signature = 'invalid_signature'
        
        data = {
            'data': json.dumps(payment_data),
            'type': 'payment',
            'id': payment_data.get('id'),
            'notification_id': 'test_notification_123',
            'external_reference': 'reservation:1|hotel:1'
        }
        
        headers = {
            'X-Signature': invalid_signature,
            'Content-Type': 'application/json'
        }
        
        response = self.client.post(
            self.webhook_url,
            data=data,
            content_type='application/json',
            **headers
        )
        
        self.assertEqual(response.status_code, 400)
        response_data = response.json()
        self.assertFalse(response_data['success'])
        self.assertEqual(response_data['code'], 'HMAC_VERIFICATION_FAILED')
        self.assertIn('Firma HMAC inválida', response_data['error'])
    
    @patch('os.environ.get')
    @patch('mercadopago.SDK')
    def test_webhook_idempotency_duplicate(self, mock_sdk, mock_env):
        """Test detección de notificación duplicada"""
        mock_env.return_value = 'TEST_ACCESS_TOKEN'
        
        # Mock de respuesta de Mercado Pago
        mock_payment = MagicMock()
        mock_payment.get.return_value = {
            'status': 200,
            'response': {
                'id': '123456789',
                'status': 'approved',
                'external_reference': 'reservation:1|hotel:1',
                'transaction_amount': 200.00
            }
        }
        mock_sdk.return_value.payment.return_value = mock_payment
        
        payment_data = {
            'id': '123456789',
            'status': 'approved',
            'external_reference': 'reservation:1|hotel:1',
            'transaction_amount': 200.00
        }
        
        data, headers = self._create_webhook_request(payment_data, 'duplicate_notification')
        
        # Primera llamada - debe procesar
        response1 = self.client.post(
            self.webhook_url,
            data=data,
            content_type='application/json',
            **headers
        )
        
        self.assertEqual(response1.status_code, 200)
        response1_data = response1.json()
        self.assertTrue(response1_data['success'])
        self.assertTrue(response1_data['processed'])
        
        # Segunda llamada - debe detectar duplicado
        response2 = self.client.post(
            self.webhook_url,
            data=data,
            content_type='application/json',
            **headers
        )
        
        self.assertEqual(response2.status_code, 200)
        response2_data = response2.json()
        self.assertTrue(response2_data['success'])
        self.assertFalse(response2_data['processed'])
        self.assertEqual(response2_data['code'], 'DUPLICATE_NOTIFICATION')
    
    @patch('os.environ.get')
    def test_webhook_missing_access_token(self, mock_env):
        """Test error cuando falta ACCESS_TOKEN"""
        mock_env.return_value = None
        
        payment_data = {
            'id': '123456789',
            'status': 'approved',
            'external_reference': 'reservation:1|hotel:1',
            'transaction_amount': 200.00
        }
        
        data, headers = self._create_webhook_request(payment_data)
        
        response = self.client.post(
            self.webhook_url,
            data=data,
            content_type='application/json',
            **headers
        )
        
        self.assertEqual(response.status_code, 400)
        response_data = response.json()
        self.assertFalse(response_data['success'])
        self.assertEqual(response_data['code'], 'MISSING_ACCESS_TOKEN')
        self.assertIn('ACCESS_TOKEN no configurado', response_data['error'])
    
    @patch('os.environ.get')
    @patch('mercadopago.SDK')
    def test_webhook_mp_api_error(self, mock_sdk, mock_env):
        """Test error en API de Mercado Pago"""
        mock_env.return_value = 'TEST_ACCESS_TOKEN'
        
        # Mock de error en API de Mercado Pago
        mock_payment = MagicMock()
        mock_payment.get.return_value = {
            'status': 400,
            'response': {'error': 'Invalid payment ID'}
        }
        mock_sdk.return_value.payment.return_value = mock_payment
        
        payment_data = {
            'id': 'invalid_payment_id',
            'status': 'approved',
            'external_reference': 'reservation:1|hotel:1',
            'transaction_amount': 200.00
        }
        
        data, headers = self._create_webhook_request(payment_data)
        
        response = self.client.post(
            self.webhook_url,
            data=data,
            content_type='application/json',
            **headers
        )
        
        self.assertEqual(response.status_code, 502)
        response_data = response.json()
        self.assertFalse(response_data['success'])
        self.assertEqual(response_data['code'], 'MP_API_ERROR')
        self.assertIn('No se pudo consultar el pago', response_data['error'])
    
    @patch('os.environ.get')
    @patch('mercadopago.SDK')
    @patch('apps.payments.tasks.process_webhook_post_processing.delay')
    def test_webhook_post_processing_queued(self, mock_celery_task, mock_sdk, mock_env):
        """Test que la tarea de post-procesamiento se encola correctamente"""
        mock_env.return_value = 'TEST_ACCESS_TOKEN'
        
        # Mock de respuesta de Mercado Pago
        mock_payment = MagicMock()
        mock_payment.get.return_value = {
            'status': 200,
            'response': {
                'id': '123456789',
                'status': 'approved',
                'external_reference': 'reservation:1|hotel:1',
                'transaction_amount': 200.00
            }
        }
        mock_sdk.return_value.payment.return_value = mock_payment
        
        payment_data = {
            'id': '123456789',
            'status': 'approved',
            'external_reference': 'reservation:1|hotel:1',
            'transaction_amount': 200.00
        }
        
        data, headers = self._create_webhook_request(payment_data)
        
        response = self.client.post(
            self.webhook_url,
            data=data,
            content_type='application/json',
            **headers
        )
        
        self.assertEqual(response.status_code, 200)
        response_data = response.json()
        self.assertTrue(response_data['success'])
        self.assertTrue(response_data['processed'])
        self.assertTrue(response_data['post_processing_queued'])
        
        # Verificar que la tarea de Celery se encoló
        mock_celery_task.assert_called_once_with(
            payment_intent_id=response_data['payment_intent_id'],
            webhook_data=payment_data,
            notification_id='test_notification_123',
            external_reference='reservation:1|hotel:1'
        )
    
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


if __name__ == '__main__':
    unittest.main()