from decimal import Decimal
from django.db import models
from ..models import PaymentPolicy


def calculate_deposit(policy, total_amount):
    """
    Calcula el monto del depósito según la política de pago
    
    Args:
        policy: PaymentPolicy instance
        total_amount: Decimal - Monto total de la reserva
    
    Returns:
        dict: Información del depósito
    """
    if not policy or policy.deposit_type == PaymentPolicy.DepositType.NONE:
        return {
            'required': False,
            'amount': Decimal('0.00'),
            'percentage': 0,
            'type': 'none'
        }

    amount = Decimal('0.00')
    if policy.deposit_type == PaymentPolicy.DepositType.PERCENTAGE:
        amount = (total_amount * policy.deposit_value) / 100
    elif policy.deposit_type == PaymentPolicy.DepositType.FIXED:
        amount = policy.deposit_value

    return {
        'required': True,
        'amount': amount.quantize(Decimal('0.01')),
        'percentage': policy.deposit_type == PaymentPolicy.DepositType.PERCENTAGE and policy.deposit_value or 0,
        'type': policy.deposit_type,
        'due': policy.deposit_due,
        'days_before': policy.deposit_days_before,
        'balance_due': policy.balance_due
    }


def calculate_balance_due(reservation, policy=None):
    """
    Calcula el saldo pendiente de pago de una reserva.
    Si la reserva tiene group_code (multi-habitación), calcula el balance del grupo completo.
    
    Args:
        reservation: Reservation instance
        policy: PaymentPolicy instance (opcional, se obtiene automáticamente si no se proporciona)
    
    Returns:
        dict: Información del saldo pendiente
    """
    from apps.reservations.models import Payment, Reservation
    
    # Obtener política si no se proporciona
    if not policy:
        policy = PaymentPolicy.resolve_for_hotel(reservation.hotel)
    
    # Si es una reserva multi-habitación, calcular el balance del grupo completo
    if reservation.group_code:
        # Buscar todas las reservas del grupo
        group_reservations = Reservation.objects.filter(group_code=reservation.group_code)
        
        # Sumar todos los total_price de las reservas del grupo
        total_reservation = group_reservations.aggregate(
            total=models.Sum('total_price')
        )['total'] or Decimal('0.00')
        
        # Sumar todos los pagos de todas las reservas del grupo
        total_paid = Payment.objects.filter(
            reservation__group_code=reservation.group_code
        ).aggregate(
            total=models.Sum('amount')
        )['total'] or Decimal('0.00')
    else:
        # Reserva simple: calcular normalmente
        total_paid = reservation.payments.aggregate(
            total=models.Sum('amount')
        )['total'] or Decimal('0.00')
        
        total_reservation = reservation.total_price or Decimal('0.00')
    
    # Calcular saldo pendiente
    balance_due = total_reservation - total_paid
    
    # Determinar si hay saldo pendiente considerando la política
    has_balance = False
    
    if policy and policy.deposit_type != PaymentPolicy.DepositType.NONE:
        # Si hay política de depósito, verificar si el pago inicial fue completo o parcial
        deposit_info = calculate_deposit(policy, total_reservation)
        expected_deposit = deposit_info['amount']
        
        # Si el total pagado es igual al total de la reserva, no hay saldo pendiente
        if total_paid >= total_reservation - Decimal('0.01'):  # Tolerancia de 1 centavo
            has_balance = False
        # Si el total pagado es igual al depósito esperado, hay saldo pendiente
        elif total_paid >= expected_deposit - Decimal('0.01'):  # Tolerancia de 1 centavo
            has_balance = True
        # Si el total pagado es menor al depósito esperado, también hay saldo pendiente
        else:
            has_balance = True
    else:
        # Si no hay política de depósito, solo verificar si se pagó el total
        has_balance = balance_due > Decimal('0.01')  # Tolerancia de 1 centavo
    
    # Calcular información del depósito si aplica
    deposit_info = None
    if policy and policy.deposit_type != PaymentPolicy.DepositType.NONE:
        deposit_info = calculate_deposit(policy, total_reservation)
    
    return {
        'has_balance': has_balance,
        'balance_due': balance_due.quantize(Decimal('0.01')),
        'total_paid': total_paid.quantize(Decimal('0.01')),
        'total_reservation': total_reservation.quantize(Decimal('0.01')),
        'deposit_info': deposit_info,
        'policy': policy
    }