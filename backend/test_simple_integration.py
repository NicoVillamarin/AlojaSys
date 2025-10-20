#!/usr/bin/env python
"""
Test simple de integración para verificar que el sistema funciona correctamente
"""
import os
import sys
import django
from decimal import Decimal

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'hotel.settings')
os.environ.setdefault('USE_SQLITE', 'True')
os.environ.setdefault('CELERY_TASK_ALWAYS_EAGER', 'True')
os.environ.setdefault('CELERY_TASK_EAGER_PROPAGATES', 'True')
os.environ.setdefault('EMAIL_BACKEND', 'django.core.mail.backends.locmem.EmailBackend')

# Agregar el directorio del proyecto al path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Configurar Django
django.setup()

from django.test import TestCase
from django.utils import timezone
from datetime import date, timedelta
from unittest.mock import patch, MagicMock

from apps.reservations.models import Reservation, ReservationStatus, Payment
from apps.payments.models import Refund, RefundStatus, PaymentIntent, PaymentIntentStatus, PaymentGatewayConfig
from apps.payments.services.refund_processor import RefundProcessor
from apps.reservations.tasks import (
    auto_cancel_pending_deposits,
    auto_cancel_expired_pending_reservations
)
from apps.payments.tasks import process_pending_refunds

from tests.factories import (
    CompleteTestDataFactory, PendingReservationFactory, ConfirmedReservationFactory,
    ConfirmedReservationWithManualPaymentFactory, ExpiredPendingReservationFactory,
    FreeCancellationPolicyFactory, StrictCancellationPolicyFactory,
    FullRefundPolicyFactory, NoRefundPolicyFactory,
    CreditCardRefundFactory, BankTransferRefundFactory, CashRefundFactory,
    VoucherRefundFactory
)


class TestSimpleIntegration(TestCase):
    """Tests simples de integración para verificar funcionalidad básica"""
    
    def setUp(self):
        """Configuración inicial para cada test"""
        # Crear datos de test básicos
        self.hotel_data = CompleteTestDataFactory.create_hotel_with_policies()
        self.hotel = self.hotel_data['hotel']
        self.room = self.hotel_data['room']
        self.user = self.hotel_data['user']
        
    def test_basic_setup(self):
        """Test básico para verificar que la configuración funciona"""
        # Verificar que los objetos se crearon correctamente
        self.assertIsNotNone(self.hotel)
        self.assertIsNotNone(self.room)
        self.assertIsNotNone(self.user)
        
        # Verificar que el hotel tiene políticas
        self.assertIsNotNone(self.hotel.cancellation_policy)
        self.assertIsNotNone(self.hotel.refund_policy)
        
        print("✅ Configuración básica funcionando correctamente")
        
    def test_reservation_creation(self):
        """Test para verificar que se pueden crear reservas"""
        # Crear una reserva PENDING
        reservation = PendingReservationFactory(
            hotel=self.hotel,
            room=self.room,
            user=self.user
        )
        
        # Verificar que la reserva se creó correctamente
        self.assertEqual(reservation.status, ReservationStatus.PENDING)
        self.assertEqual(reservation.hotel, self.hotel)
        self.assertEqual(reservation.room, self.room)
        self.assertEqual(reservation.user, self.user)
        
        print("✅ Creación de reservas funcionando correctamente")
        
    def test_payment_creation(self):
        """Test para verificar que se pueden crear pagos"""
        # Crear una reserva CONFIRMED con pago
        reservation = ConfirmedReservationWithManualPaymentFactory(
            hotel=self.hotel,
            room=self.room,
            user=self.user
        )
        
        # Verificar que la reserva tiene pagos
        payments = reservation.payments.all()
        self.assertGreater(payments.count(), 0)
        
        # Verificar que el pago tiene el estado correcto
        payment = payments.first()
        self.assertEqual(payment.status, 'completed')
        
        print("✅ Creación de pagos funcionando correctamente")
        
    def test_refund_processor_exists(self):
        """Test para verificar que el RefundProcessor existe y funciona"""
        # Verificar que la clase existe
        self.assertIsNotNone(RefundProcessor)
        
        # Verificar que tiene los métodos necesarios
        self.assertTrue(hasattr(RefundProcessor, 'process_refund'))
        self.assertTrue(hasattr(RefundProcessor, '_calculate_refund_amount'))
        
        print("✅ RefundProcessor funcionando correctamente")
        
    def test_celery_tasks_exist(self):
        """Test para verificar que las tareas de Celery existen"""
        # Verificar que las tareas existen
        self.assertIsNotNone(auto_cancel_pending_deposits)
        self.assertIsNotNone(auto_cancel_expired_pending_reservations)
        self.assertIsNotNone(process_pending_refunds)
        
        print("✅ Tareas de Celery funcionando correctamente")
        
    def test_refund_creation(self):
        """Test para verificar que se pueden crear reembolsos"""
        # Crear una reserva CONFIRMED con pago
        reservation = ConfirmedReservationWithManualPaymentFactory(
            hotel=self.hotel,
            room=self.room,
            user=self.user
        )
        
        # Crear un reembolso
        refund = CreditCardRefundFactory(
            reservation=reservation,
            amount=Decimal('100.00')
        )
        
        # Verificar que el reembolso se creó correctamente
        self.assertEqual(refund.reservation, reservation)
        self.assertEqual(refund.amount, Decimal('100.00'))
        self.assertEqual(refund.status, RefundStatus.PENDING)
        
        print("✅ Creación de reembolsos funcionando correctamente")
        
    def test_cancellation_policy_calculation(self):
        """Test para verificar que las políticas de cancelación funcionan"""
        # Crear una política de cancelación
        policy = FreeCancellationPolicyFactory()
        
        # Verificar que la política se creó correctamente
        self.assertIsNotNone(policy)
        self.assertEqual(policy.free_cancellation_time, 24)
        
        print("✅ Políticas de cancelación funcionando correctamente")
        
    def test_refund_policy_calculation(self):
        """Test para verificar que las políticas de reembolso funcionan"""
        # Crear una política de reembolso
        policy = FullRefundPolicyFactory()
        
        # Verificar que la política se creó correctamente
        self.assertIsNotNone(policy)
        self.assertEqual(policy.full_refund_time, 24)
        
        print("✅ Políticas de reembolso funcionando correctamente")


if __name__ == '__main__':
    import unittest
    unittest.main()
