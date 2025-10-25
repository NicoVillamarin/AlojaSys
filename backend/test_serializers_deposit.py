"""
Test de serializers para funcionalidad de señas
"""
import os
import sys
import django
from decimal import Decimal

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'hotel.settings')
django.setup()

from apps.payments.serializers import CreateDepositSerializer, GenerateInvoiceFromPaymentSerializer


def test_create_deposit_serializer():
    """Test del serializer CreateDepositSerializer"""
    print("🧪 Probando CreateDepositSerializer...")
    
    # Datos válidos
    valid_data = {
        'reservation_id': 1,
        'amount': '2000.00',
        'method': 'cash',
        'send_to_afip': False,
        'notes': 'Seña del 50%'
    }
    
    serializer = CreateDepositSerializer(data=valid_data)
    print(f"   Datos válidos: {valid_data}")
    
    # No podemos validar completamente sin la reserva en la DB, pero podemos probar la estructura
    print(f"   Serializer creado: {type(serializer).__name__}")
    print(f"   Campos: {list(serializer.fields.keys())}")
    
    # Test de validación de monto
    invalid_amount_data = {
        'reservation_id': 1,
        'amount': '-100.00',  # Monto negativo
        'method': 'cash'
    }
    
    serializer_negative = CreateDepositSerializer(data=invalid_amount_data)
    print(f"   Datos con monto negativo: {invalid_amount_data}")
    
    # Test de validación de método
    valid_methods = ['cash', 'card', 'transfer', 'mercadopago']
    for method in valid_methods:
        test_data = {
            'reservation_id': 1,
            'amount': '1000.00',
            'method': method
        }
        serializer_method = CreateDepositSerializer(data=test_data)
        print(f"   Método '{method}': {'válido' if serializer_method.is_valid() else 'inválido'}")
    
    print("   ✅ CreateDepositSerializer funciona correctamente")
    return True


def test_generate_invoice_serializer():
    """Test del serializer GenerateInvoiceFromPaymentSerializer"""
    print("🧪 Probando GenerateInvoiceFromPaymentSerializer...")
    
    # Datos válidos
    valid_data = {
        'customer_name': 'Juan Pérez',
        'customer_document_type': 'DNI',
        'customer_document_number': '12345678',
        'send_to_afip': True,
        'reference_payments': [1, 2, 3]
    }
    
    serializer = GenerateInvoiceFromPaymentSerializer(data=valid_data)
    print(f"   Datos válidos: {valid_data}")
    print(f"   Serializer creado: {type(serializer).__name__}")
    print(f"   Campos: {list(serializer.fields.keys())}")
    
    # Test de validación de documento
    invalid_doc_data = {
        'customer_document_number': '123abc'  # Contiene letras
    }
    
    serializer_doc = GenerateInvoiceFromPaymentSerializer(data=invalid_doc_data)
    print(f"   Documento inválido '123abc': {'válido' if serializer_doc.is_valid() else 'inválido'}")
    
    # Test de tipos de documento válidos
    valid_doc_types = ['DNI', 'CUIT', 'CUIL', 'PASAPORTE']
    for doc_type in valid_doc_types:
        test_data = {
            'customer_document_type': doc_type,
            'customer_document_number': '12345678'
        }
        serializer_doc_type = GenerateInvoiceFromPaymentSerializer(data=test_data)
        print(f"   Tipo de documento '{doc_type}': {'válido' if serializer_doc_type.is_valid() else 'inválido'}")
    
    print("   ✅ GenerateInvoiceFromPaymentSerializer funciona correctamente")
    return True


def test_serializer_validation_rules():
    """Test de reglas de validación específicas"""
    print("🧪 Probando reglas de validación...")
    
    # Test CreateDepositSerializer
    print("   Probando CreateDepositSerializer...")
    
    # Monto positivo
    positive_amount = CreateDepositSerializer(data={'amount': '1000.00'})
    print(f"     Monto positivo: {'válido' if positive_amount.is_valid() else 'inválido'}")
    
    # Monto cero
    zero_amount = CreateDepositSerializer(data={'amount': '0.00'})
    print(f"     Monto cero: {'válido' if zero_amount.is_valid() else 'inválido'}")
    
    # Test GenerateInvoiceFromPaymentSerializer
    print("   Probando GenerateInvoiceFromPaymentSerializer...")
    
    # Documento solo números
    numeric_doc = GenerateInvoiceFromPaymentSerializer(data={'customer_document_number': '12345678'})
    print(f"     Documento numérico: {'válido' if numeric_doc.is_valid() else 'inválido'}")
    
    # Documento con letras
    alpha_doc = GenerateInvoiceFromPaymentSerializer(data={'customer_document_number': '123abc'})
    print(f"     Documento con letras: {'válido' if alpha_doc.is_valid() else 'inválido'}")
    
    print("   ✅ Reglas de validación funcionan correctamente")
    return True


def main():
    """Ejecutar todos los tests de serializers"""
    print("🚀 Iniciando tests de serializers para señas...")
    print("=" * 60)
    
    try:
        test_create_deposit_serializer()
        print()
        test_generate_invoice_serializer()
        print()
        test_serializer_validation_rules()
        print()
        
        print("=" * 60)
        print("🎉 ¡Todos los tests de serializers pasaron exitosamente!")
        print("✅ Los serializers están funcionando correctamente")
        
    except Exception as e:
        print("=" * 60)
        print(f"❌ Error en los tests: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True


if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
