"""
Configuración de pytest para tests de integración
"""
import pytest
from django.test import TestCase
from django.db import transaction
from django.core.management import call_command


@pytest.fixture(scope="session")
def django_db_setup(django_db_setup, django_db_blocker):
    """Configuración de base de datos para tests"""
    with django_db_blocker.unblock():
        call_command('migrate', verbosity=0, interactive=False)


@pytest.fixture(autouse=True)
def enable_db_access_for_all_tests(db):
    """Habilita acceso a base de datos para todos los tests"""
    pass


@pytest.fixture
def transactional_db(transactional_db):
    """Fixture para tests que requieren transacciones"""
    return transactional_db


@pytest.fixture
def mock_timezone():
    """Mock para timezone.now() en tests"""
    from unittest.mock import patch
    from datetime import datetime
    from django.utils import timezone
    
    with patch.object(timezone, 'now') as mock_now:
        mock_now.return_value = datetime(2024, 1, 15, 12, 0, 0, tzinfo=timezone.utc)
        yield mock_now


@pytest.fixture
def mock_celery_tasks():
    """Mock para tareas de Celery en tests"""
    from unittest.mock import patch
    
    with patch('apps.reservations.tasks.auto_cancel_pending_deposits.delay') as mock_deposits, \
         patch('apps.reservations.tasks.auto_cancel_expired_pending_reservations.delay') as mock_expired, \
         patch('apps.payments.tasks.process_pending_refunds.delay') as mock_refunds:
        yield {
            'auto_cancel_pending_deposits': mock_deposits,
            'auto_cancel_expired_pending_reservations': mock_expired,
            'process_pending_refunds': mock_refunds
        }


@pytest.fixture
def mock_notifications():
    """Mock para servicio de notificaciones en tests"""
    from unittest.mock import patch
    
    with patch('apps.notifications.services.NotificationService.create_refund_auto_notification') as mock_notify:
        yield mock_notify


@pytest.fixture
def mock_payment_gateway():
    """Mock para pasarela de pagos en tests"""
    from unittest.mock import patch
    
    with patch('apps.payments.services.refund_processor.RefundProcessor._refund_original_payment') as mock_refund:
        mock_refund.return_value = {
            'refund_id': 1,
            'method': 'credit_card_refund',
            'amount': 100.0,
            'status': 'processing',
            'external_reference': 'MP_REFUND_123',
            'requires_manual_processing': True
        }
        yield mock_refund


@pytest.fixture
def sample_hotel_data():
    """Datos de hotel de ejemplo para tests"""
    from tests.factories import CompleteTestDataFactory
    return CompleteTestDataFactory.create_hotel_with_policies()


@pytest.fixture
def sample_reservation(sample_hotel_data):
    """Reserva de ejemplo para tests"""
    from tests.factories import ConfirmedReservationFactory
    return ConfirmedReservationFactory(
        hotel=sample_hotel_data['hotel'],
        room=sample_hotel_data['room'],
        applied_cancellation_policy=sample_hotel_data['cancellation_policy']
    )


@pytest.fixture
def sample_pending_reservation(sample_hotel_data):
    """Reserva PENDING de ejemplo para tests"""
    from tests.factories import PendingReservationFactory
    return PendingReservationFactory(
        hotel=sample_hotel_data['hotel'],
        room=sample_hotel_data['room'],
        applied_cancellation_policy=sample_hotel_data['cancellation_policy']
    )


@pytest.fixture
def sample_refund(sample_reservation):
    """Reembolso de ejemplo para tests"""
    from tests.factories import CreditCardRefundFactory
    return CreditCardRefundFactory(
        reservation=sample_reservation,
        amount=sample_reservation.total_price
    )


# Configuración para tests de integración
@pytest.mark.integration
class IntegrationTestCase(TestCase):
    """Clase base para tests de integración"""
    
    def setUp(self):
        """Configuración inicial para tests de integración"""
        super().setUp()
        # Configuración adicional si es necesaria
    
    def tearDown(self):
        """Limpieza después de cada test"""
        super().tearDown()
        # Limpieza adicional si es necesaria


# Configuración para tests unitarios
@pytest.mark.unit
class UnitTestCase(TestCase):
    """Clase base para tests unitarios"""
    
    def setUp(self):
        """Configuración inicial para tests unitarios"""
        super().setUp()
        # Configuración adicional si es necesaria
    
    def tearDown(self):
        """Limpieza después de cada test"""
        super().tearDown()
        # Limpieza adicional si es necesaria

