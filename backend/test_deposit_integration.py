"""
Tests de integración para funcionalidad de señas (pagos parciales)
"""
import json
from decimal import Decimal
from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status

from apps.core.models import Hotel
from apps.rooms.models import Room, RoomType
from apps.reservations.models import Reservation, ReservationStatus
from apps.payments.models import PaymentPolicy, PaymentMethod
from apps.invoicing.models import AfipConfig, InvoiceMode

User = get_user_model()


class DepositIntegrationTestCase(TestCase):
    """Tests de integración para señas"""
    
    def setUp(self):
        """Configurar datos de prueba"""
        # Crear usuario
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        # Crear hotel
        self.hotel = Hotel.objects.create(
            name='Hotel Test',
            address='Calle Test 123',
            phone='1234567890',
            email='hotel@test.com',
            tax_id='20123456789'
        )
        
        # Crear tipo de habitación
        self.room_type = RoomType.objects.create(
            name='Habitación Estándar',
            description='Habitación estándar para 2 personas'
        )
        
        # Crear habitación
        self.room = Room.objects.create(
            hotel=self.hotel,
            name='Habitación 101',
            room_type=self.room_type,
            base_price=Decimal('2000.00'),
            max_occupancy=2
        )
        
        # Crear método de pago
        self.payment_method = PaymentMethod.objects.create(
            code='cash',
            name='Efectivo',
            is_active=True
        )
        
        # Crear política de pago con depósito
        self.payment_policy = PaymentPolicy.objects.create(
            hotel=self.hotel,
            name='Política con Seña',
            is_active=True,
            is_default=True,
            allow_deposit=True,
            deposit_type=PaymentPolicy.DepositType.PERCENTAGE,
            deposit_value=Decimal('50.00'),  # 50% de seña
            deposit_due=PaymentPolicy.DepositDue.CONFIRMATION,
            deposit_days_before=0,
            balance_due=PaymentPolicy.BalanceDue.CHECK_IN,
            methods=[self.payment_method]
        )
        
        # Crear configuración AFIP
        self.afip_config = AfipConfig.objects.create(
            hotel=self.hotel,
            cuit='20123456789',
            point_of_sale=1,
            certificate_path='/path/to/cert.crt',
            private_key_path='/path/to/key.key',
            environment='test',
            invoice_mode=InvoiceMode.RECEIPT_ONLY  # Modo solo recibos
        )
        
        # Crear reserva
        self.reservation = Reservation.objects.create(
            hotel=self.hotel,
            room=self.room,
            guest_name='Juan Pérez',
            guest_email='juan@example.com',
            check_in='2024-02-01',
            check_out='2024-02-03',
            guests=2,
            total_price=Decimal('4000.00'),
            status=ReservationStatus.PENDING
        )
        
        # Configurar cliente API
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)
    
    def test_create_deposit_receipt_only_mode(self):
        """Test crear seña en modo solo recibos"""
        url = reverse('payments-create-deposit')
        data = {
            'reservation_id': self.reservation.id,
            'amount': '2000.00',  # 50% de $4000
            'method': 'cash',
            'send_to_afip': False,
            'notes': 'Seña del 50%'
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('payment', response.data)
        self.assertTrue(response.data['payment']['is_deposit'])
        self.assertEqual(response.data['payment']['amount'], '2000.00')
        self.assertIn('deposit_info', response.data)
        self.assertTrue(response.data['deposit_info']['required'])
        self.assertEqual(response.data['deposit_info']['amount'], '2000.00')
    
    def test_create_deposit_fiscal_mode(self):
        """Test crear seña en modo fiscal"""
        # Cambiar a modo fiscal
        self.afip_config.invoice_mode = InvoiceMode.FISCAL_ON_DEPOSIT
        self.afip_config.save()
        
        url = reverse('payments-create-deposit')
        data = {
            'reservation_id': self.reservation.id,
            'amount': '2000.00',
            'method': 'cash',
            'send_to_afip': True,
            'notes': 'Seña con facturación AFIP'
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('payment', response.data)
        self.assertTrue(response.data['payment']['is_deposit'])
    
    def test_generate_invoice_with_multiple_payments(self):
        """Test generar factura con múltiples pagos (seña + pago final)"""
        # Crear seña
        from apps.reservations.models import Payment
        deposit_payment = Payment.objects.create(
            reservation=self.reservation,
            date='2024-01-15',
            method='cash',
            amount=Decimal('2000.00'),
            is_deposit=True,
            metadata={'deposit_info': {'required': True, 'amount': '2000.00'}}
        )
        
        # Crear pago final
        final_payment = Payment.objects.create(
            reservation=self.reservation,
            date='2024-02-01',
            method='cash',
            amount=Decimal('2000.00'),
            is_deposit=False
        )
        
        # Generar factura con ambos pagos
        url = reverse('payments-generate-invoice-extended', kwargs={'payment_id': final_payment.id})
        data = {
            'send_to_afip': False,
            'reference_payments': [deposit_payment.id, final_payment.id],
            'customer_name': 'Juan Pérez',
            'customer_document_type': 'DNI',
            'customer_document_number': '12345678'
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('payments_included', response.data)
        self.assertEqual(len(response.data['payments_included']), 2)
        self.assertIn(deposit_payment.id, response.data['payments_included'])
        self.assertIn(final_payment.id, response.data['payments_included'])
    
    def test_deposit_amount_validation(self):
        """Test validación de monto de seña"""
        url = reverse('payments-create-deposit')
        data = {
            'reservation_id': self.reservation.id,
            'amount': '3000.00',  # Más del 50% permitido
            'method': 'cash',
            'send_to_afip': False
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)
        self.assertIn('no puede exceder', response.data['error'])
    
    def test_reservation_status_validation(self):
        """Test validación de estado de reserva para señas"""
        # Cambiar reserva a estado no válido
        self.reservation.status = ReservationStatus.CANCELLED
        self.reservation.save()
        
        url = reverse('payments-create-deposit')
        data = {
            'reservation_id': self.reservation.id,
            'amount': '2000.00',
            'method': 'cash',
            'send_to_afip': False
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)
        self.assertIn('debe estar en estado', response.data['error'])
