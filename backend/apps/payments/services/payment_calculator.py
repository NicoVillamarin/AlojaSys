from decimal import Decimal
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
