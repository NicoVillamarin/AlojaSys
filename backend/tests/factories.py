"""
Factories para tests de integración de cancelación y refund
"""
import factory
from decimal import Decimal
from datetime import date, datetime, timedelta
from django.utils import timezone
from factory.django import DjangoModelFactory
from factory.fuzzy import FuzzyDecimal, FuzzyDate, FuzzyChoice

from apps.core.models import Hotel
from apps.core.models import Currency
from apps.rooms.models import Room, RoomType
from apps.enterprises.models import Enterprise
from apps.reservations.models import Reservation, ReservationStatus, Payment, ReservationChannel
from apps.payments.models import (
    CancellationPolicy, RefundPolicy, Refund, RefundStatus, RefundReason,
    PaymentIntent, PaymentIntentStatus, PaymentGatewayConfig, PaymentMethod,
    PaymentPolicy, PaymentGatewayProvider
)
from apps.users.models import User


class EnterpriseFactory(DjangoModelFactory):
    class Meta:
        model = Enterprise

    name = factory.Sequence(lambda n: f"Empresa Test {n}")
    email = factory.Sequence(lambda n: f"empresa{n}@test.com")
    phone = "+5491123456789"
    address = "Calle Test 123"
    city = None
    country = None
    is_active = True


class HotelFactory(DjangoModelFactory):
    class Meta:
        model = Hotel

    name = factory.Sequence(lambda n: f"Hotel Test {n}")
    email = factory.Sequence(lambda n: f"hotel{n}@test.com")
    phone = "+5491123456789"
    address = "Calle Hotel 123"
    city = None
    country = None
    timezone = "America/Argentina/Buenos_Aires"
    check_in_time = "15:00"
    check_out_time = "11:00"
    is_active = True
    enterprise = factory.SubFactory(EnterpriseFactory)
    auto_check_in_enabled = True
    auto_no_show_enabled = True


class CurrencyFactory(DjangoModelFactory):
    class Meta:
        model = Currency
        django_get_or_create = ("code",)

    code = "ARS"
    name = "ARS"
    symbol = "$"
    is_active = True


class RoomTypeFactory(DjangoModelFactory):
    class Meta:
        model = RoomType
        django_get_or_create = ("code",)

    code = "single"
    name = "Single"
    description = "Tipo de habitación para tests"
    sort_order = 0
    is_active = True


class RoomFactory(DjangoModelFactory):
    class Meta:
        model = Room

    name = factory.Sequence(lambda n: f"Habitación {n}")
    room_type = factory.LazyAttribute(lambda obj: RoomTypeFactory().code)
    hotel = factory.SubFactory(HotelFactory)
    floor = 1
    number = factory.Sequence(lambda n: 100 + n)
    capacity = 2
    max_capacity = 4
    base_price = FuzzyDecimal(100.00, 500.00, 2)
    base_currency = factory.SubFactory(CurrencyFactory)
    extra_guest_fee = FuzzyDecimal(20.00, 50.00, 2)
    is_active = True


class UserFactory(DjangoModelFactory):
    class Meta:
        model = User

    username = factory.Sequence(lambda n: f"user{n}")
    email = factory.Sequence(lambda n: f"user{n}@test.com")
    first_name = "Test"
    last_name = "User"
    is_active = True


class PaymentMethodFactory(DjangoModelFactory):
    class Meta:
        model = PaymentMethod

    code = factory.Sequence(lambda n: f"method_{n}")
    name = factory.Sequence(lambda n: f"Método de Pago {n}")
    is_active = True


class PaymentPolicyFactory(DjangoModelFactory):
    class Meta:
        model = PaymentPolicy

    hotel = factory.SubFactory(HotelFactory)
    name = factory.Sequence(lambda n: f"Política de Pago {n}")
    is_active = True
    is_default = True
    allow_deposit = True
    deposit_type = PaymentPolicy.DepositType.PERCENTAGE
    deposit_value = Decimal('20.00')  # 20%
    deposit_due = PaymentPolicy.DepositDue.CONFIRMATION
    balance_due = PaymentPolicy.BalanceDue.CHECK_IN
    auto_cancel_enabled = True
    auto_cancel_days = 7

    @factory.post_generation
    def methods(self, create, extracted, **kwargs):
        if not create:
            return
        if extracted:
            for method in extracted:
                self.methods.add(method)


class CancellationPolicyFactory(DjangoModelFactory):
    class Meta:
        model = CancellationPolicy

    hotel = factory.SubFactory(HotelFactory)
    name = factory.Sequence(lambda n: f"Política Cancelación {n}")
    is_active = True
    is_default = True
    free_cancellation_time = 24
    free_cancellation_unit = CancellationPolicy.TimeUnit.HOURS
    partial_refund_time = 72
    partial_refund_unit = CancellationPolicy.TimeUnit.HOURS
    partial_refund_percentage = Decimal('50.00')
    no_refund_time = 168
    no_refund_unit = CancellationPolicy.TimeUnit.HOURS
    cancellation_fee_type = CancellationPolicy.CancellationFeeType.PERCENTAGE
    cancellation_fee_value = Decimal('10.00')
    allow_cancellation_after_checkin = False
    allow_cancellation_after_checkout = False
    allow_cancellation_no_show = True
    allow_cancellation_early_checkout = False
    auto_refund_on_cancel = True


class RefundPolicyFactory(DjangoModelFactory):
    class Meta:
        model = RefundPolicy

    hotel = factory.SubFactory(HotelFactory)
    name = factory.Sequence(lambda n: f"Política Devolución {n}")
    is_active = True
    is_default = True
    full_refund_time = 24
    full_refund_unit = RefundPolicy.TimeUnit.HOURS
    partial_refund_time = 72
    partial_refund_unit = RefundPolicy.TimeUnit.HOURS
    partial_refund_percentage = Decimal('50.00')
    no_refund_time = 168
    no_refund_unit = RefundPolicy.TimeUnit.HOURS
    refund_method = RefundPolicy.RefundMethod.ORIGINAL_PAYMENT
    refund_processing_days = 7


class PaymentGatewayConfigFactory(DjangoModelFactory):
    class Meta:
        model = PaymentGatewayConfig

    provider = PaymentGatewayProvider.MERCADO_PAGO
    hotel = factory.SubFactory(HotelFactory)
    public_key = "TEST_PUBLIC_KEY"
    access_token = "TEST_ACCESS_TOKEN"
    is_test = True
    country_code = "AR"
    currency_code = "ARS"
    is_active = True
    refund_window_days = 30
    partial_refunds_allowed = True


class ReservationFactory(DjangoModelFactory):
    class Meta:
        model = Reservation

    hotel = factory.SubFactory(HotelFactory)
    room = factory.SubFactory(RoomFactory)
    guests = 2
    guests_data = factory.LazyFunction(lambda: [
        {
            "name": "Juan Pérez",
            "email": "juan@test.com",
            "phone": "+5491123456789",
            "is_primary": True
        },
        {
            "name": "María García",
            "email": "maria@test.com",
            "phone": "+5491123456790",
            "is_primary": False
        }
    ])
    channel = ReservationChannel.DIRECT
    check_in = factory.LazyFunction(lambda: date.today() + timedelta(days=7))
    check_out = factory.LazyFunction(lambda: date.today() + timedelta(days=10))
    status = ReservationStatus.PENDING
    total_price = FuzzyDecimal(300.00, 1000.00, 2)
    notes = "Reserva de prueba"

    @factory.post_generation
    def applied_cancellation_policy(self, create, extracted, **kwargs):
        if not create:
            return
        if extracted:
            self.applied_cancellation_policy = extracted
        else:
            # Crear política de cancelación por defecto
            policy = CancellationPolicyFactory(hotel=self.hotel)
            self.applied_cancellation_policy = policy


class PaymentFactory(DjangoModelFactory):
    class Meta:
        model = Payment

    reservation = factory.SubFactory(ReservationFactory)
    date = factory.LazyFunction(lambda: date.today())
    method = FuzzyChoice(['cash', 'transfer', 'pos'])
    amount = FuzzyDecimal(50.00, 500.00, 2)


class PaymentIntentFactory(DjangoModelFactory):
    class Meta:
        model = PaymentIntent

    reservation = factory.SubFactory(ReservationFactory)
    hotel = factory.LazyAttribute(lambda obj: obj.reservation.hotel)
    enterprise = factory.LazyAttribute(lambda obj: obj.reservation.hotel.enterprise)
    amount = FuzzyDecimal(100.00, 1000.00, 2)
    currency = "ARS"
    description = "Pago de prueba"
    mp_preference_id = factory.Sequence(lambda n: f"pref_{n}")
    mp_payment_id = factory.Sequence(lambda n: f"payment_{n}")
    external_reference = factory.Sequence(lambda n: f"ref_{n}")
    status = PaymentIntentStatus.APPROVED


class RefundFactory(DjangoModelFactory):
    class Meta:
        model = Refund

    reservation = factory.SubFactory(ReservationFactory)
    payment = factory.SubFactory(PaymentFactory)
    amount = FuzzyDecimal(50.00, 500.00, 2)
    reason = RefundReason.CANCELLATION
    status = RefundStatus.PENDING
    method = 'original_payment'
    refund_method = 'credit_card'
    processing_days = 7
    notes = "Reembolso de prueba"


# Factories especializadas para diferentes escenarios de test

class PendingReservationFactory(ReservationFactory):
    """Reserva PENDING sin pagos"""
    status = ReservationStatus.PENDING
    total_price = Decimal('300.00')

    @factory.post_generation
    def payments(self, create, extracted, **kwargs):
        # No crear pagos por defecto para reservas PENDING
        pass


class ConfirmedReservationFactory(ReservationFactory):
    """Reserva CONFIRMED con pago"""
    status = ReservationStatus.CONFIRMED
    total_price = Decimal('500.00')

    @factory.post_generation
    def payments(self, create, extracted, **kwargs):
        if not create:
            return
        # Crear un pago aprobado
        PaymentIntentFactory(
            reservation=self,
            amount=self.total_price,
            status=PaymentIntentStatus.APPROVED
        )


class ConfirmedReservationWithManualPaymentFactory(ReservationFactory):
    """Reserva CONFIRMED con pago manual"""
    status = ReservationStatus.CONFIRMED
    total_price = Decimal('400.00')

    @factory.post_generation
    def payments(self, create, extracted, **kwargs):
        if not create:
            return
        # Crear un pago manual
        PaymentFactory(
            reservation=self,
            amount=self.total_price,
            method='cash'
        )


class ExpiredPendingReservationFactory(ReservationFactory):
    """Reserva PENDING con check-in vencido"""
    status = ReservationStatus.PENDING
    check_in = factory.LazyFunction(lambda: date.today() - timedelta(days=1))
    check_out = factory.LazyFunction(lambda: date.today() + timedelta(days=2))
    total_price = Decimal('300.00')


class CancelledReservationFactory(ReservationFactory):
    """Reserva CANCELLED"""
    status = ReservationStatus.CANCELLED
    total_price = Decimal('300.00')


class NoShowReservationFactory(ReservationFactory):
    """Reserva NO_SHOW"""
    status = ReservationStatus.NO_SHOW
    check_in = factory.LazyFunction(lambda: date.today() - timedelta(days=1))
    check_out = factory.LazyFunction(lambda: date.today() + timedelta(days=2))
    total_price = Decimal('500.00')


# Factories para políticas específicas

class FreeCancellationPolicyFactory(CancellationPolicyFactory):
    """Política de cancelación gratuita"""
    free_cancellation_time = 48  # 48 horas
    free_cancellation_unit = CancellationPolicy.TimeUnit.HOURS
    partial_refund_time = 24
    partial_refund_unit = CancellationPolicy.TimeUnit.HOURS
    no_refund_time = 12
    no_refund_unit = CancellationPolicy.TimeUnit.HOURS
    cancellation_fee_type = CancellationPolicy.CancellationFeeType.NONE
    cancellation_fee_value = Decimal('0.00')


class StrictCancellationPolicyFactory(CancellationPolicyFactory):
    """Política de cancelación estricta"""
    free_cancellation_time = 168  # 7 días
    free_cancellation_unit = CancellationPolicy.TimeUnit.HOURS
    partial_refund_time = 72  # 3 días
    partial_refund_unit = CancellationPolicy.TimeUnit.HOURS
    no_refund_time = 24  # 1 día
    no_refund_unit = CancellationPolicy.TimeUnit.HOURS
    cancellation_fee_type = CancellationPolicy.CancellationFeeType.PERCENTAGE
    cancellation_fee_value = Decimal('25.00')  # 25% de penalidad


class FullRefundPolicyFactory(RefundPolicyFactory):
    """Política de devolución completa"""
    full_refund_time = 48  # 48 horas
    full_refund_unit = RefundPolicy.TimeUnit.HOURS
    partial_refund_time = 24  # 24 horas
    partial_refund_unit = RefundPolicy.TimeUnit.HOURS
    no_refund_time = 12  # 12 horas
    no_refund_unit = RefundPolicy.TimeUnit.HOURS
    refund_method = RefundPolicy.RefundMethod.ORIGINAL_PAYMENT


class NoRefundPolicyFactory(RefundPolicyFactory):
    """Política sin devoluciones"""
    full_refund_time = 0
    full_refund_unit = RefundPolicy.TimeUnit.HOURS
    partial_refund_time = 0
    partial_refund_unit = RefundPolicy.TimeUnit.HOURS
    no_refund_time = 0
    no_refund_unit = RefundPolicy.TimeUnit.HOURS
    refund_method = RefundPolicy.RefundMethod.CASH


# Factories para diferentes métodos de reembolso

class CreditCardRefundFactory(RefundFactory):
    """Reembolso por tarjeta de crédito"""
    refund_method = 'credit_card'
    method = 'original_payment'
    status = RefundStatus.PROCESSING


class BankTransferRefundFactory(RefundFactory):
    """Reembolso por transferencia bancaria"""
    refund_method = 'bank_transfer'
    method = 'bank_transfer'
    status = RefundStatus.PENDING


class CashRefundFactory(RefundFactory):
    """Reembolso en efectivo"""
    refund_method = 'cash'
    method = 'cash'
    status = RefundStatus.PENDING


class VoucherRefundFactory(RefundFactory):
    """Reembolso por voucher"""
    refund_method = 'voucher'
    method = 'voucher'
    status = RefundStatus.PROCESSING


# Factory para crear datos de test completos

class CompleteTestDataFactory:
    """Factory que crea un conjunto completo de datos para tests"""
    
    @staticmethod
    def create_hotel_with_policies():
        """Crea un hotel con todas las políticas necesarias"""
        hotel = HotelFactory()
        
        # Crear políticas
        payment_policy = PaymentPolicyFactory(hotel=hotel)
        cancellation_policy = CancellationPolicyFactory(hotel=hotel)
        refund_policy = RefundPolicyFactory(hotel=hotel)
        gateway_config = PaymentGatewayConfigFactory(hotel=hotel)
        
        # Crear habitación
        room = RoomFactory(hotel=hotel)
        
        return {
            'hotel': hotel,
            'room': room,
            'payment_policy': payment_policy,
            'cancellation_policy': cancellation_policy,
            'refund_policy': refund_policy,
            'gateway_config': gateway_config
        }
    
    @staticmethod
    def create_reservation_with_payment(hotel_data, status=ReservationStatus.CONFIRMED):
        """Crea una reserva con pago"""
        reservation = ReservationFactory(
            hotel=hotel_data['hotel'],
            room=hotel_data['room'],
            status=status,
            applied_cancellation_policy=hotel_data['cancellation_policy']
        )
        
        if status == ReservationStatus.CONFIRMED:
            # Crear pago aprobado
            PaymentIntentFactory(
                reservation=reservation,
                amount=reservation.total_price,
                status=PaymentIntentStatus.APPROVED
            )
        
        return reservation
