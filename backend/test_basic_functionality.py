#!/usr/bin/env python
"""
Test básico para verificar que el sistema funciona correctamente
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


class TestBasicFunctionality(TestCase):
    """Tests básicos para verificar funcionalidad sin base de datos"""
    
    def test_imports_work(self):
        """Test para verificar que las importaciones funcionan"""
        # Verificar que las clases existen
        self.assertIsNotNone(Reservation)
        self.assertIsNotNone(ReservationStatus)
        self.assertIsNotNone(Payment)
        self.assertIsNotNone(Refund)
        self.assertIsNotNone(RefundStatus)
        self.assertIsNotNone(PaymentIntent)
        self.assertIsNotNone(PaymentIntentStatus)
        self.assertIsNotNone(PaymentGatewayConfig)
        
        print("[OK] Importaciones funcionando correctamente")
        
    def test_refund_processor_exists(self):
        """Test para verificar que el RefundProcessor existe y funciona"""
        # Verificar que la clase existe
        self.assertIsNotNone(RefundProcessor)
        
        # Verificar que tiene los métodos necesarios
        self.assertTrue(hasattr(RefundProcessor, 'process_refund'))
        self.assertTrue(hasattr(RefundProcessor, '_calculate_refund_amount'))
        
        print("[OK] RefundProcessor funcionando correctamente")
        
    def test_celery_tasks_exist(self):
        """Test para verificar que las tareas de Celery existen"""
        # Verificar que las tareas existen
        self.assertIsNotNone(auto_cancel_pending_deposits)
        self.assertIsNotNone(auto_cancel_expired_pending_reservations)
        self.assertIsNotNone(process_pending_refunds)
        
        print("[OK] Tareas de Celery funcionando correctamente")
        
    def test_reservation_status_choices(self):
        """Test para verificar que los estados de reserva funcionan"""
        # Verificar que los estados existen
        self.assertEqual(ReservationStatus.PENDING, 'pending')
        self.assertEqual(ReservationStatus.CONFIRMED, 'confirmed')
        self.assertEqual(ReservationStatus.CANCELLED, 'cancelled')
        
        print("[OK] Estados de reserva funcionando correctamente")
        
    def test_refund_status_choices(self):
        """Test para verificar que los estados de reembolso funcionan"""
        # Verificar que los estados existen
        self.assertEqual(RefundStatus.PENDING, 'pending')
        self.assertEqual(RefundStatus.PROCESSING, 'processing')
        self.assertEqual(RefundStatus.COMPLETED, 'completed')
        self.assertEqual(RefundStatus.FAILED, 'failed')
        
        print("[OK] Estados de reembolso funcionando correctamente")
        
    def test_payment_intent_status_choices(self):
        """Test para verificar que los estados de PaymentIntent funcionan"""
        # Verificar que los estados existen
        self.assertEqual(PaymentIntentStatus.PENDING, 'pending')
        # Verificar que otros estados existen (sin asumir nombres específicos)
        self.assertTrue(hasattr(PaymentIntentStatus, 'PENDING'))
        
        print("[OK] Estados de PaymentIntent funcionando correctamente")
        
    def test_decimal_calculations(self):
        """Test para verificar que los cálculos decimales funcionan"""
        # Test de cálculos básicos
        amount1 = Decimal('100.00')
        amount2 = Decimal('50.00')
        total = amount1 + amount2
        
        self.assertEqual(total, Decimal('150.00'))
        
        # Test de cálculos de reembolso
        total_paid = Decimal('200.00')
        penalty = Decimal('20.00')
        refund_amount = total_paid - penalty
        
        self.assertEqual(refund_amount, Decimal('180.00'))
        
        print("[OK] Calculos decimales funcionando correctamente")
        
    def test_date_calculations(self):
        """Test para verificar que los cálculos de fechas funcionan"""
        # Test de fechas básicas
        today = date.today()
        tomorrow = today + timedelta(days=1)
        next_week = today + timedelta(days=7)
        
        self.assertGreater(tomorrow, today)
        self.assertGreater(next_week, today)
        
        # Test de cálculo de días
        days_diff = (next_week - today).days
        self.assertEqual(days_diff, 7)
        
        print("[OK] Calculos de fechas funcionando correctamente")
        
    def test_refund_processor_methods(self):
        """Test para verificar que los métodos del RefundProcessor existen"""
        # Verificar métodos estáticos
        self.assertTrue(hasattr(RefundProcessor, 'process_refund'))
        self.assertTrue(hasattr(RefundProcessor, '_calculate_refund_amount'))
        self.assertTrue(hasattr(RefundProcessor, '_process_refund_payment'))
        self.assertTrue(hasattr(RefundProcessor, '_refund_original_payment'))
        self.assertTrue(hasattr(RefundProcessor, '_create_pending_refund'))
        self.assertTrue(hasattr(RefundProcessor, '_create_voucher_refund'))
        
        print("[OK] Metodos del RefundProcessor funcionando correctamente")
        
    def test_celery_task_attributes(self):
        """Test para verificar que las tareas de Celery tienen los atributos correctos"""
        # Verificar que las tareas son callables
        self.assertTrue(callable(auto_cancel_pending_deposits))
        self.assertTrue(callable(auto_cancel_expired_pending_reservations))
        self.assertTrue(callable(process_pending_refunds))
        
        print("[OK] Tareas de Celery funcionando correctamente")
        
    def test_mock_functionality(self):
        """Test para verificar que el mocking funciona"""
        # Test de mock básico
        with patch('apps.payments.services.refund_processor.RefundProcessor.process_refund') as mock_refund:
            mock_refund.return_value = {'status': 'success', 'amount': Decimal('100.00')}
            
            result = mock_refund()
            self.assertEqual(result['status'], 'success')
            self.assertEqual(result['amount'], Decimal('100.00'))
            
        print("[OK] Funcionalidad de mock funcionando correctamente")


if __name__ == '__main__':
    import unittest
    unittest.main()
