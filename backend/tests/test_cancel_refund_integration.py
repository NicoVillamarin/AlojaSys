"""
Tests de integración para flujos de cancelación y refund
"""
import pytest
from decimal import Decimal
from datetime import date, datetime, timedelta
from unittest.mock import patch, MagicMock
from django.test import TestCase
from django.utils import timezone
from django.db import transaction

from apps.reservations.models import Reservation, ReservationStatus, Payment
from apps.payments.models import (
    Refund, RefundStatus, RefundReason, PaymentIntent, PaymentIntentStatus,
    CancellationPolicy, RefundPolicy
)
from apps.payments.services.refund_processor import RefundProcessor
from apps.reservations.tasks import (
    auto_cancel_expired_reservations,
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


class TestCancelRefundIntegration(TestCase):
    """Tests de integración para flujos de cancelación y refund"""

    def setUp(self):
        """Configuración inicial para cada test"""
        self.hotel_data = CompleteTestDataFactory.create_hotel_with_policies()
        self.hotel = self.hotel_data['hotel']
        self.room = self.hotel_data['room']
        self.payment_policy = self.hotel_data['payment_policy']
        self.cancellation_policy = self.hotel_data['cancellation_policy']
        self.refund_policy = self.hotel_data['refund_policy']

    def test_pending_reservation_cancelled_no_refund(self):
        """
        Test: Reserva PENDING cancelada → no refund
        """
        # Crear reserva PENDING sin pagos
        reservation = PendingReservationFactory(
            hotel=self.hotel,
            room=self.room,
            applied_cancellation_policy=self.cancellation_policy
        )
        
        # Verificar estado inicial
        self.assertEqual(reservation.status, ReservationStatus.PENDING)
        self.assertEqual(reservation.payments.count(), 0)
        self.assertEqual(reservation.payment_intents.count(), 0)
        
        # Cancelar reserva
        reservation.status = ReservationStatus.CANCELLED
        reservation.save()
        
        # Procesar refund (no debería crear ningún refund)
        result = RefundProcessor.process_refund(reservation)
        
        # Verificaciones
        self.assertFalse(result['success'])
        self.assertEqual(result['refund_amount'], Decimal('0.00'))
        self.assertEqual(Refund.objects.filter(reservation=reservation).count(), 0)
        
        # Verificar que la reserva sigue cancelada
        reservation.refresh_from_db()
        self.assertEqual(reservation.status, ReservationStatus.CANCELLED)

    def test_confirmed_reservation_cancelled_within_cutoff_full_refund(self):
        """
        Test: Reserva CONFIRMED cancelada antes de cutoff → refund total
        """
        # Crear política de cancelación gratuita
        free_policy = FreeCancellationPolicyFactory(hotel=self.hotel)
        
        # Crear reserva CONFIRMED con pago
        reservation = ConfirmedReservationFactory(
            hotel=self.hotel,
            room=self.room,
            applied_cancellation_policy=free_policy,
            check_in=date.today() + timedelta(days=3)  # 3 días en el futuro
        )
        
        # Verificar estado inicial
        self.assertEqual(reservation.status, ReservationStatus.CONFIRMED)
        self.assertEqual(reservation.payment_intents.count(), 1)
        
        payment_intent = reservation.payment_intents.first()
        self.assertEqual(payment_intent.status, PaymentIntentStatus.APPROVED)
        
        # Cancelar reserva
        reservation.status = ReservationStatus.CANCELLED
        reservation.save()
        
        # Procesar refund
        with patch('apps.payments.services.refund_processor.RefundProcessor._refund_original_payment') as mock_refund:
            mock_refund.return_value = {
                'refund_id': 1,
                'method': 'credit_card_refund',
                'amount': float(reservation.total_price),
                'status': 'processing',
                'external_reference': 'MP_REFUND_123',
                'requires_manual_processing': True
            }
            
            result = RefundProcessor.process_refund(reservation)
        
        # Verificaciones
        self.assertTrue(result['success'])
        self.assertEqual(result['refund_amount'], reservation.total_price)
        self.assertTrue(result['refund_processed'])
        
        # Verificar que se creó el refund
        refunds = Refund.objects.filter(reservation=reservation)
        self.assertEqual(refunds.count(), 1)
        
        refund = refunds.first()
        self.assertEqual(refund.amount, reservation.total_price)
        self.assertEqual(refund.reason, RefundReason.CANCELLATION)
        self.assertEqual(refund.status, RefundStatus.PROCESSING)
        self.assertEqual(refund.refund_method, 'original_payment')

    def test_confirmed_reservation_cancelled_outside_cutoff_partial_refund(self):
        """
        Test: Reserva CONFIRMED cancelada fuera de ventana → refund parcial
        """
        # Crear política estricta
        strict_policy = StrictCancellationPolicyFactory(hotel=self.hotel)
        
        # Crear reserva CONFIRMED con pago
        reservation = ConfirmedReservationFactory(
            hotel=self.hotel,
            room=self.room,
            applied_cancellation_policy=strict_policy,
            check_in=date.today() + timedelta(hours=12)  # 12 horas en el futuro
        )
        
        # Cancelar reserva
        reservation.status = ReservationStatus.CANCELLED
        reservation.save()
        
        # Procesar refund
        with patch('apps.payments.services.refund_processor.RefundProcessor._refund_original_payment') as mock_refund:
            mock_refund.return_value = {
                'refund_id': 1,
                'method': 'credit_card_refund',
                'amount': float(reservation.total_price * Decimal('0.75')),  # 75% del total
                'status': 'processing',
                'external_reference': 'MP_REFUND_123',
                'requires_manual_processing': True
            }
            
            result = RefundProcessor.process_refund(reservation)
        
        # Verificaciones
        self.assertTrue(result['success'])
        self.assertGreater(result['refund_amount'], Decimal('0.00'))
        self.assertLess(result['refund_amount'], reservation.total_price)
        self.assertTrue(result['refund_processed'])
        
        # Verificar que se creó el refund
        refunds = Refund.objects.filter(reservation=reservation)
        self.assertEqual(refunds.count(), 1)
        
        refund = refunds.first()
        self.assertEqual(refund.reason, RefundReason.CANCELLATION)
        self.assertEqual(refund.status, RefundStatus.PROCESSING)

    def test_confirmed_reservation_cancelled_outside_cutoff_no_refund(self):
        """
        Test: Reserva CONFIRMED cancelada fuera de ventana → refund marked pending/manual
        """
        # Crear política sin devoluciones
        no_refund_policy = NoRefundPolicyFactory(hotel=self.hotel)
        
        # Crear reserva CONFIRMED con pago
        reservation = ConfirmedReservationFactory(
            hotel=self.hotel,
            room=self.room,
            applied_cancellation_policy=self.cancellation_policy
        )
        
        # Cancelar reserva
        reservation.status = ReservationStatus.CANCELLED
        reservation.save()
        
        # Procesar refund
        result = RefundProcessor.process_refund(reservation)
        
        # Verificaciones
        self.assertTrue(result['success'])
        self.assertEqual(result['refund_amount'], Decimal('0.00'))
        self.assertFalse(result['refund_processed'])
        
        # No debería crear refund
        refunds = Refund.objects.filter(reservation=reservation)
        self.assertEqual(refunds.count(), 0)

    def test_auto_cancel_task_pending_deposit_expired(self):
        """
        Test: Auto-cancel task: PENDING con deposit expired → CANCELLED
        """
        # Crear reserva PENDING sin pagos
        reservation = PendingReservationFactory(
            hotel=self.hotel,
            room=self.room,
            applied_cancellation_policy=self.cancellation_policy
        )
        
        # Simular que el depósito venció (crear la reserva hace 8 días)
        reservation.created_at = timezone.now() - timedelta(days=8)
        reservation.save()
        
        # Verificar estado inicial
        self.assertEqual(reservation.status, ReservationStatus.PENDING)
        
        # Ejecutar tarea de auto-cancelación
        with patch('apps.payments.services.payment_calculator.calculate_balance_due') as mock_calc:
            # Simular que el depósito venció hace 1 día
            mock_calc.return_value = {
                'deposit_due_date': date.today() - timedelta(days=1),
                'deposit_amount': Decimal('100.00'),
                'balance_due': Decimal('400.00')
            }
            
            result = auto_cancel_pending_deposits()
        
        # Verificaciones
        self.assertIn("canceladas", result)
        
        # Verificar que la reserva fue cancelada
        reservation.refresh_from_db()
        self.assertEqual(reservation.status, ReservationStatus.CANCELLED)
        
        # Verificar que la habitación fue liberada
        self.room.refresh_from_db()
        from apps.rooms.models import RoomStatus
        self.assertEqual(self.room.status, RoomStatus.AVAILABLE)

    def test_auto_cancel_task_pending_checkin_expired(self):
        """
        Test: Auto-cancel task: PENDING con check-in vencido → CANCELLED
        """
        # Crear reserva PENDING con check-in vencido
        reservation = ExpiredPendingReservationFactory(
            hotel=self.hotel,
            room=self.room,
            applied_cancellation_policy=self.cancellation_policy
        )
        
        # Verificar estado inicial
        self.assertEqual(reservation.status, ReservationStatus.PENDING)
        self.assertLess(reservation.check_in, date.today())
        
        # Ejecutar tarea de auto-cancelación
        result = auto_cancel_expired_pending_reservations()
        
        # Verificaciones
        self.assertIn("canceladas", result)
        
        # Verificar que la reserva fue cancelada
        reservation.refresh_from_db()
        self.assertEqual(reservation.status, ReservationStatus.CANCELLED)
        
        # Verificar que la habitación fue liberada
        self.room.refresh_from_db()
        from apps.rooms.models import RoomStatus
        self.assertEqual(self.room.status, RoomStatus.AVAILABLE)

    def test_process_pending_refunds_task_retry_logic(self):
        """
        Test: process_pending_refunds task retry logic
        """
        # Crear reserva CONFIRMED con pago
        reservation = ConfirmedReservationFactory(
            hotel=self.hotel,
            room=self.room,
            applied_cancellation_policy=self.cancellation_policy
        )
        
        # Crear refund pendiente
        refund = CreditCardRefundFactory(
            reservation=reservation,
            amount=reservation.total_price,
            status=RefundStatus.PENDING
        )
        
        # Verificar estado inicial
        self.assertEqual(refund.status, RefundStatus.PENDING)
        
        # Ejecutar tarea de procesamiento de refunds pendientes
        with patch('apps.payments.services.refund_processor_v2.RefundProcessorV2.process_refund') as mock_process:
            # Simular fallo en el primer intento, éxito en el segundo
            mock_process.side_effect = [False, True]
            
            result = process_pending_refunds()
        
        # Verificaciones
        self.assertIn("Procesados", result)
        
        # Verificar que el refund fue procesado
        refund.refresh_from_db()
        self.assertEqual(refund.status, RefundStatus.PROCESSING)

    def test_refund_processing_with_different_methods(self):
        """
        Test: Procesamiento de refunds con diferentes métodos
        """
        # Crear reserva CONFIRMED con pago manual
        reservation = ConfirmedReservationWithManualPaymentFactory(
            hotel=self.hotel,
            room=self.room,
            applied_cancellation_policy=self.cancellation_policy
        )
        
        # Cancelar reserva
        reservation.status = ReservationStatus.CANCELLED
        reservation.save()
        
        # Procesar refund con método de transferencia bancaria
        with patch('apps.payments.services.refund_processor.RefundProcessor._create_pending_refund') as mock_create:
            mock_create.return_value = {
                'refund_id': 1,
                'method': 'bank_transfer',
                'amount': float(reservation.total_price),
                'status': 'pending',
                'metadata': {}
            }
            
            result = RefundProcessor.process_refund(reservation)
        
        # Verificaciones
        self.assertTrue(result['success'])
        self.assertEqual(result['refund_amount'], reservation.total_price)
        self.assertTrue(result['refund_processed'])
        
        # Verificar que se creó el refund
        refunds = Refund.objects.filter(reservation=reservation)
        self.assertEqual(refunds.count(), 1)
        
        refund = refunds.first()
        self.assertEqual(refund.refund_method, 'bank_transfer')
        self.assertEqual(refund.status, RefundStatus.PENDING)

    def test_refund_processing_with_voucher(self):
        """
        Test: Procesamiento de refunds con voucher
        """
        # Crear reserva CONFIRMED con pago
        reservation = ConfirmedReservationFactory(
            hotel=self.hotel,
            room=self.room,
            applied_cancellation_policy=self.cancellation_policy
        )
        
        # Cancelar reserva
        reservation.status = ReservationStatus.CANCELLED
        reservation.save()
        
        # Procesar refund con voucher
        with patch('apps.payments.services.refund_processor.RefundProcessor._create_voucher_refund') as mock_voucher:
            mock_voucher.return_value = {
                'refund_id': 1,
                'method': 'voucher',
                'amount': float(reservation.total_price),
                'status': 'processing',
                'metadata': {
                    'voucher_type': 'credit',
                    'expiry_days': 365,
                    'requires_manual_processing': True
                }
            }
            
            result = RefundProcessor.process_refund(reservation)
        
        # Verificaciones
        self.assertTrue(result['success'])
        self.assertEqual(result['refund_amount'], reservation.total_price)
        self.assertTrue(result['refund_processed'])
        
        # Verificar que se creó el refund
        refunds = Refund.objects.filter(reservation=reservation)
        self.assertEqual(refunds.count(), 1)
        
        refund = refunds.first()
        self.assertEqual(refund.refund_method, 'voucher')
        self.assertEqual(refund.status, RefundStatus.PROCESSING)

    def test_refund_expiration_handling(self):
        """
        Test: Manejo de expiración de refunds
        """
        # Crear refund que ha expirado
        reservation = ConfirmedReservationFactory(
            hotel=self.hotel,
            room=self.room,
            applied_cancellation_policy=self.cancellation_policy
        )
        
        refund = CreditCardRefundFactory(
            reservation=reservation,
            amount=reservation.total_price,
            status=RefundStatus.PENDING,
            created_at=timezone.now() - timedelta(days=35)  # 35 días atrás
        )
        
        # Configurar ventana de refund de 30 días
        self.hotel_data['gateway_config'].refund_window_days = 30
        self.hotel_data['gateway_config'].save()
        
        # Ejecutar tarea de procesamiento
        with patch('apps.payments.tasks._notify_staff_refund_expired') as mock_notify:
            result = process_pending_refunds()
        
        # Verificaciones
        self.assertIn("expirados", result.lower())
        
        # Verificar que el refund fue marcado como fallido
        refund.refresh_from_db()
        self.assertEqual(refund.status, RefundStatus.FAILED)
        self.assertIn("expirado", refund.notes.lower())

    def test_cancellation_with_snapshot_policy(self):
        """
        Test: Cancelación usando snapshot de política
        """
        # Crear reserva con snapshot de política
        reservation = ConfirmedReservationFactory(
            hotel=self.hotel,
            room=self.room,
            applied_cancellation_policy=self.cancellation_policy
        )
        
        # Crear snapshot de política
        snapshot_data = {
            'free_cancellation_time': 48,
            'free_cancellation_unit': 'hours',
            'partial_refund_time': 24,
            'partial_refund_unit': 'hours',
            'no_refund_time': 12,
            'no_refund_unit': 'hours',
            'cancellation_fee_type': 'percentage',
            'cancellation_fee_value': 10.0
        }
        
        reservation.applied_cancellation_snapshot = snapshot_data
        reservation.save()
        
        # Cancelar reserva
        reservation.status = ReservationStatus.CANCELLED
        reservation.save()
        
        # Procesar refund
        with patch('apps.payments.services.refund_processor.RefundProcessor._refund_original_payment') as mock_refund:
            mock_refund.return_value = {
                'refund_id': 1,
                'method': 'credit_card_refund',
                'amount': float(reservation.total_price),
                'status': 'processing',
                'external_reference': 'MP_REFUND_123',
                'requires_manual_processing': True
            }
            
            result = RefundProcessor.process_refund(reservation)
        
        # Verificaciones
        self.assertTrue(result['success'])
        self.assertEqual(result['refund_amount'], reservation.total_price)
        self.assertTrue(result['refund_processed'])
        
        # Verificar que se usó el snapshot
        self.assertIn('cancellation_rules', result)
        cancellation_rules = result['cancellation_rules']
        self.assertEqual(cancellation_rules['free_cancellation_time'], 48)

    def test_multiple_refunds_same_reservation(self):
        """
        Test: Múltiples refunds para la misma reserva
        """
        # Crear reserva CONFIRMED con múltiples pagos
        reservation = ConfirmedReservationFactory(
            hotel=self.hotel,
            room=self.room,
            applied_cancellation_policy=self.cancellation_policy
        )
        
        # Agregar pago manual adicional
        Payment.objects.create(
            reservation=reservation,
            date=date.today(),
            method='cash',
            amount=Decimal('100.00')
        )
        
        # Cancelar reserva
        reservation.status = ReservationStatus.CANCELLED
        reservation.save()
        
        # Procesar refund
        with patch('apps.payments.services.refund_processor.RefundProcessor._refund_original_payment') as mock_refund:
            mock_refund.return_value = {
                'refund_id': 1,
                'method': 'credit_card_refund',
                'amount': float(reservation.total_price),
                'status': 'processing',
                'external_reference': 'MP_REFUND_123',
                'requires_manual_processing': True
            }
            
            result = RefundProcessor.process_refund(reservation)
        
        # Verificaciones
        self.assertTrue(result['success'])
        self.assertEqual(result['refund_amount'], reservation.total_price)
        
        # Verificar que se creó el refund
        refunds = Refund.objects.filter(reservation=reservation)
        self.assertEqual(refunds.count(), 1)
        
        # El refund debería ser por el monto total pagado
        total_paid = reservation.payments.aggregate(total=models.Sum('amount'))['total'] + \
                    reservation.payment_intents.filter(status=PaymentIntentStatus.APPROVED).aggregate(total=models.Sum('amount'))['total']
        self.assertEqual(refunds.first().amount, total_paid)

    def test_refund_processing_error_handling(self):
        """
        Test: Manejo de errores en procesamiento de refunds
        """
        # Crear reserva CONFIRMED con pago
        reservation = ConfirmedReservationFactory(
            hotel=self.hotel,
            room=self.room,
            applied_cancellation_policy=self.cancellation_policy
        )
        
        # Cancelar reserva
        reservation.status = ReservationStatus.CANCELLED
        reservation.save()
        
        # Procesar refund con error
        with patch('apps.payments.services.refund_processor.RefundProcessor._refund_original_payment') as mock_refund:
            mock_refund.side_effect = Exception("Error de gateway")
            
            result = RefundProcessor.process_refund(reservation)
        
        # Verificaciones
        self.assertFalse(result['success'])
        self.assertIn('error', result)
        self.assertIn('Error de gateway', result['error'])
        
        # No debería crear refund
        refunds = Refund.objects.filter(reservation=reservation)
        self.assertEqual(refunds.count(), 0)

    def test_refund_processing_with_notifications(self):
        """
        Test: Procesamiento de refunds con notificaciones
        """
        # Crear reserva CONFIRMED con pago
        reservation = ConfirmedReservationFactory(
            hotel=self.hotel,
            room=self.room,
            applied_cancellation_policy=self.cancellation_policy
        )
        
        # Cancelar reserva
        reservation.status = ReservationStatus.CANCELLED
        reservation.save()
        
        # Procesar refund con notificaciones
        with patch('apps.notifications.services.NotificationService.create_refund_auto_notification') as mock_notify:
            with patch('apps.payments.services.refund_processor.RefundProcessor._refund_original_payment') as mock_refund:
                mock_refund.return_value = {
                    'refund_id': 1,
                    'method': 'credit_card_refund',
                    'amount': float(reservation.total_price),
                    'status': 'processing',
                    'external_reference': 'MP_REFUND_123',
                    'requires_manual_processing': True
                }
                
                result = RefundProcessor.process_refund(reservation)
        
        # Verificaciones
        self.assertTrue(result['success'])
        
        # Verificar que se crearon notificaciones
        self.assertEqual(mock_notify.call_count, 2)  # Una para pending, otra para processing
        
        # Verificar contenido de las notificaciones
        calls = mock_notify.call_args_list
        self.assertIn('pending', calls[0][1]['status'])
        self.assertIn('processing', calls[1][1]['status'])


# Tests adicionales para casos edge

class TestCancelRefundEdgeCases(TestCase):
    """Tests para casos edge de cancelación y refund"""

    def setUp(self):
        """Configuración inicial para cada test"""
        self.hotel_data = CompleteTestDataFactory.create_hotel_with_policies()

    def test_cancellation_without_payment_policy(self):
        """
        Test: Cancelación sin política de pago
        """
        # Crear reserva sin política de pago
        reservation = ConfirmedReservationFactory(
            hotel=self.hotel_data['hotel'],
            room=self.hotel_data['room'],
            applied_cancellation_policy=None
        )
        
        # Cancelar reserva
        reservation.status = ReservationStatus.CANCELLED
        reservation.save()
        
        # Procesar refund
        result = RefundProcessor.process_refund(reservation)
        
        # Verificaciones
        self.assertFalse(result['success'])
        self.assertIn('No hay política de cancelación', result['error'])

    def test_cancellation_without_refund_policy(self):
        """
        Test: Cancelación sin política de devolución
        """
        # Crear reserva sin política de devolución
        reservation = ConfirmedReservationFactory(
            hotel=self.hotel_data['hotel'],
            room=self.hotel_data['room'],
            applied_cancellation_policy=self.hotel_data['cancellation_policy']
        )
        
        # Eliminar política de devolución
        self.hotel_data['refund_policy'].delete()
        
        # Cancelar reserva
        reservation.status = ReservationStatus.CANCELLED
        reservation.save()
        
        # Procesar refund
        result = RefundProcessor.process_refund(reservation)
        
        # Verificaciones
        self.assertFalse(result['success'])
        self.assertIn('No hay política de devolución', result['error'])

    def test_cancellation_with_zero_amount(self):
        """
        Test: Cancelación con monto cero
        """
        # Crear reserva con monto cero
        reservation = ConfirmedReservationFactory(
            hotel=self.hotel_data['hotel'],
            room=self.hotel_data['room'],
            applied_cancellation_policy=self.hotel_data['cancellation_policy'],
            total_price=Decimal('0.00')
        )
        
        # Cancelar reserva
        reservation.status = ReservationStatus.CANCELLED
        reservation.save()
        
        # Procesar refund
        result = RefundProcessor.process_refund(reservation)
        
        # Verificaciones
        self.assertTrue(result['success'])
        self.assertEqual(result['refund_amount'], Decimal('0.00'))
        self.assertFalse(result['refund_processed'])

    def test_cancellation_with_negative_amount(self):
        """
        Test: Cancelación con monto negativo (no debería ocurrir)
        """
        # Crear reserva con monto negativo
        reservation = ConfirmedReservationFactory(
            hotel=self.hotel_data['hotel'],
            room=self.hotel_data['room'],
            applied_cancellation_policy=self.hotel_data['cancellation_policy'],
            total_price=Decimal('-100.00')
        )
        
        # Cancelar reserva
        reservation.status = ReservationStatus.CANCELLED
        reservation.save()
        
        # Procesar refund
        result = RefundProcessor.process_refund(reservation)
        
        # Verificaciones
        self.assertTrue(result['success'])
        self.assertEqual(result['refund_amount'], Decimal('0.00'))
        self.assertFalse(result['refund_processed'])

    def test_cancellation_with_invalid_dates(self):
        """
        Test: Cancelación con fechas inválidas
        """
        # Crear reserva con fechas inválidas
        reservation = ConfirmedReservationFactory(
            hotel=self.hotel_data['hotel'],
            room=self.hotel_data['room'],
            applied_cancellation_policy=self.hotel_data['cancellation_policy'],
            check_in=date.today() - timedelta(days=1),
            check_out=date.today() - timedelta(days=2)  # check_out antes de check_in
        )
        
        # Cancelar reserva
        reservation.status = ReservationStatus.CANCELLED
        reservation.save()
        
        # Procesar refund
        result = RefundProcessor.process_refund(reservation)
        
        # Verificaciones
        self.assertTrue(result['success'])
        # El sistema debería manejar fechas inválidas gracefully
        self.assertIsInstance(result['refund_amount'], Decimal)
