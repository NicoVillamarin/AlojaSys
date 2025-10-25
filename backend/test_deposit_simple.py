"""
Test simple para verificar la funcionalidad de señas sin dependencias complejas
"""
import os
import sys
import django
from decimal import Decimal

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'hotel.settings')
django.setup()

from apps.payments.services.payment_calculator import calculate_deposit
from apps.payments.models import PaymentPolicy


def test_calculate_deposit():
    """Test básico de cálculo de depósito"""
    print("🧪 Probando cálculo de depósito...")
    
    # Crear política de pago
    policy = PaymentPolicy(
        allow_deposit=True,
        deposit_type=PaymentPolicy.DepositType.PERCENTAGE,
        deposit_value=Decimal('50.00'),
        deposit_due=PaymentPolicy.DepositDue.CONFIRMATION,
        deposit_days_before=0,
        balance_due=PaymentPolicy.BalanceDue.CHECK_IN
    )
    
    # Calcular depósito para $4000
    total_amount = Decimal('4000.00')
    result = calculate_deposit(policy, total_amount)
    
    print(f"   Total: ${total_amount}")
    print(f"   Resultado: {result}")
    
    # Verificaciones
    assert result['required'] == True, "Debería requerir depósito"
    assert result['amount'] == Decimal('2000.00'), f"Debería ser $2000, pero es ${result['amount']}"
    assert result['percentage'] == 50, f"Debería ser 50%, pero es {result['percentage']}%"
    assert result['type'] == 'percentage', f"Debería ser 'percentage', pero es {result['type']}"
    
    print("   ✅ Cálculo de depósito funciona correctamente")
    return True


def test_deposit_validation():
    """Test de validación de montos de depósito"""
    print("🧪 Probando validación de depósito...")
    
    policy = PaymentPolicy(
        allow_deposit=True,
        deposit_type=PaymentPolicy.DepositType.PERCENTAGE,
        deposit_value=Decimal('50.00')
    )
    
    total_amount = Decimal('4000.00')
    result = calculate_deposit(policy, total_amount)
    
    # Test: monto válido (50%)
    valid_amount = Decimal('2000.00')
    assert valid_amount <= result['amount'], f"${valid_amount} debería ser válido"
    print(f"   ✅ ${valid_amount} es un monto válido")
    
    # Test: monto inválido (más del 50%)
    invalid_amount = Decimal('2500.00')
    assert invalid_amount > result['amount'], f"${invalid_amount} debería ser inválido"
    print(f"   ✅ ${invalid_amount} es un monto inválido (correcto)")
    
    return True


def test_no_deposit_policy():
    """Test de política sin depósito"""
    print("🧪 Probando política sin depósito...")
    
    policy = PaymentPolicy(
        allow_deposit=False,
        deposit_type=PaymentPolicy.DepositType.NONE,
        deposit_value=Decimal('0.00')
    )
    
    total_amount = Decimal('4000.00')
    result = calculate_deposit(policy, total_amount)
    
    assert result['required'] == False, "No debería requerir depósito"
    assert result['amount'] == Decimal('0.00'), f"Debería ser $0, pero es ${result['amount']}"
    assert result['type'] == 'none', f"Debería ser 'none', pero es {result['type']}"
    
    print("   ✅ Política sin depósito funciona correctamente")
    return True


def test_fixed_deposit():
    """Test de depósito con monto fijo"""
    print("🧪 Probando depósito con monto fijo...")
    
    policy = PaymentPolicy(
        allow_deposit=True,
        deposit_type=PaymentPolicy.DepositType.FIXED,
        deposit_value=Decimal('1000.00')
    )
    
    total_amount = Decimal('4000.00')
    result = calculate_deposit(policy, total_amount)
    
    assert result['required'] == True, "Debería requerir depósito"
    assert result['amount'] == Decimal('1000.00'), f"Debería ser $1000, pero es ${result['amount']}"
    assert result['type'] == 'fixed', f"Debería ser 'fixed', pero es {result['type']}"
    
    print("   ✅ Depósito con monto fijo funciona correctamente")
    return True


def main():
    """Ejecutar todos los tests"""
    print("🚀 Iniciando tests de funcionalidad de señas...")
    print("=" * 50)
    
    try:
        test_calculate_deposit()
        print()
        test_deposit_validation()
        print()
        test_no_deposit_policy()
        print()
        test_fixed_deposit()
        print()
        
        print("=" * 50)
        print("🎉 ¡Todos los tests pasaron exitosamente!")
        print("✅ La funcionalidad de señas está funcionando correctamente")
        
    except Exception as e:
        print("=" * 50)
        print(f"❌ Error en los tests: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True


if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
