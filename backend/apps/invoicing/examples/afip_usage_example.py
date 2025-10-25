"""
Ejemplos de uso de los servicios AFIP
Este archivo muestra cómo usar los servicios de facturación electrónica
"""

from django.conf import settings
from apps.invoicing.models import AfipConfig, Invoice, InvoiceItem
from apps.invoicing.services import AfipService, AfipTestService
from apps.core.models import Hotel
from decimal import Decimal


def example_afip_configuration():
    """
    Ejemplo de configuración de AFIP
    """
    print("=== Ejemplo de Configuración AFIP ===")
    
    # Obtener hotel (asumiendo que existe)
    hotel = Hotel.objects.first()
    
    if not hotel:
        print("❌ No hay hoteles configurados")
        return
    
    # Crear configuración AFIP
    config, created = AfipConfig.objects.get_or_create(
        hotel=hotel,
        defaults={
            'cuit': '20123456789',  # CUIT de ejemplo
            'tax_condition': 'Responsable Inscripto',
            'point_of_sale': 1,
            'certificate_path': '/path/to/certificate.crt',
            'private_key_path': '/path/to/private.key',
            'environment': 'test',  # Usar test para pruebas
            'last_invoice_number': 0
        }
    )
    
    if created:
        print(f"✅ Configuración AFIP creada para hotel {hotel.name}")
    else:
        print(f"✅ Configuración AFIP ya existe para hotel {hotel.name}")
    
    return config


def example_afip_service_usage():
    """
    Ejemplo de uso del servicio AFIP
    """
    print("\n=== Ejemplo de Uso del Servicio AFIP ===")
    
    # Obtener configuración
    config = example_afip_configuration()
    
    if not config:
        return
    
    # Crear servicio AFIP
    afip_service = AfipService(config)
    
    # Obtener información del servicio
    service_info = afip_service.get_service_info()
    print(f"✅ Servicio AFIP inicializado:")
    print(f"   - Ambiente: {service_info['environment']}")
    print(f"   - Es producción: {service_info['is_production']}")
    print(f"   - CUIT: {service_info['cuit']}")
    print(f"   - Punto de venta: {service_info['point_of_sale']}")
    
    # Probar conexión
    print("\n🔍 Probando conexión con AFIP...")
    connection_result = afip_service.test_connection()
    
    if connection_result['success']:
        print(f"✅ Conexión exitosa: {connection_result['message']}")
    else:
        print(f"❌ Error de conexión: {connection_result['message']}")
    
    # Validar ambiente
    print("\n🔍 Validando configuración del ambiente...")
    validation_result = afip_service.validate_environment()
    
    if validation_result['overall_success']:
        print("✅ Configuración del ambiente válida")
    else:
        print("❌ Configuración del ambiente inválida:")
        for check_name, check_result in validation_result['checks'].items():
            status = "✅" if check_result['success'] else "❌"
            print(f"   {status} {check_name}: {check_result['message']}")
    
    return afip_service


def example_test_service_usage():
    """
    Ejemplo de uso del servicio de testing
    """
    print("\n=== Ejemplo de Uso del Servicio de Testing ===")
    
    # Obtener configuración de test
    config = example_afip_configuration()
    
    if not config or config.environment != 'test':
        print("❌ Configuración de test no disponible")
        return
    
    # Crear servicio de testing
    test_service = AfipTestService(config)
    
    # Obtener parámetros de testing
    test_params = test_service.get_test_parameters()
    print("✅ Parámetros de testing disponibles:")
    print(f"   - Tipos de documento: {list(test_params['document_types'].keys())}")
    print(f"   - Tipos de factura: {test_params['invoice_types']}")
    print(f"   - Rangos de montos: {test_params['amount_ranges']}")
    
    # Crear datos de prueba
    test_data = test_service.create_test_invoice_data(config.hotel)
    print(f"\n✅ Datos de prueba creados:")
    print(f"   - Cliente: {test_data['customer_name']}")
    print(f"   - Documento: {test_data['customer_document_number']}")
    print(f"   - Total: ${test_data['total']}")
    
    return test_service


def example_invoice_creation():
    """
    Ejemplo de creación de factura
    """
    print("\n=== Ejemplo de Creación de Factura ===")
    
    # Obtener configuración
    config = example_afip_configuration()
    
    if not config:
        return
    
    # Crear factura de ejemplo
    invoice = Invoice.objects.create(
        hotel=config.hotel,
        type='B',  # Factura B
        customer_name='Cliente de Prueba',
        customer_document_type='DNI',
        customer_document_number='12345678',
        customer_address='Dirección de Prueba 123',
        customer_city='Buenos Aires',
        customer_postal_code='1000',
        customer_country='AR',
        issue_date=timezone.now(),
        total=Decimal('1000.00'),
        net_amount=Decimal('909.09'),
        vat_amount=Decimal('90.91'),
        currency='ARS',
        status='draft'
    )
    
    # Crear item de la factura
    InvoiceItem.objects.create(
        invoice=invoice,
        description='Servicio de Alojamiento',
        quantity=Decimal('1.00'),
        unit_price=Decimal('1000.00'),
        total_price=Decimal('1000.00'),
        vat_rate=Decimal('10.00'),
        vat_amount=Decimal('90.91'),
        afip_code='1'
    )
    
    print(f"✅ Factura creada: {invoice.number}")
    print(f"   - Tipo: {invoice.type}")
    print(f"   - Cliente: {invoice.customer_name}")
    print(f"   - Total: ${invoice.total}")
    print(f"   - Estado: {invoice.status}")
    
    return invoice


def example_send_invoice_to_afip():
    """
    Ejemplo de envío de factura a AFIP
    """
    print("\n=== Ejemplo de Envío de Factura a AFIP ===")
    
    # Crear factura
    invoice = example_invoice_creation()
    
    if not invoice:
        return
    
    # Obtener configuración
    config = AfipConfig.objects.get(hotel=invoice.hotel)
    
    # Crear servicio AFIP
    afip_service = AfipService(config)
    
    try:
        # Enviar factura a AFIP
        print(f"📤 Enviando factura {invoice.number} a AFIP...")
        result = afip_service.send_invoice(invoice)
        
        if result['success']:
            print(f"✅ Factura enviada exitosamente:")
            print(f"   - CAE: {result['cae']}")
            print(f"   - Vencimiento CAE: {result['cae_expiration']}")
            print(f"   - Número: {result['invoice_number']}")
        else:
            print(f"❌ Error enviando factura: {result.get('message', 'Error desconocido')}")
    
    except Exception as e:
        print(f"❌ Error enviando factura: {str(e)}")
    
    return invoice


def run_all_examples():
    """
    Ejecuta todos los ejemplos
    """
    print("🚀 Iniciando ejemplos de servicios AFIP...")
    
    try:
        # Ejemplo 1: Configuración
        config = example_afip_configuration()
        
        # Ejemplo 2: Servicio AFIP
        afip_service = example_afip_service_usage()
        
        # Ejemplo 3: Servicio de testing
        test_service = example_test_service_usage()
        
        # Ejemplo 4: Creación de factura
        invoice = example_invoice_creation()
        
        # Ejemplo 5: Envío a AFIP (solo si está en modo test)
        if config and config.environment == 'test':
            example_send_invoice_to_afip()
        
        print("\n🎉 Todos los ejemplos ejecutados correctamente!")
        
    except Exception as e:
        print(f"\n❌ Error ejecutando ejemplos: {str(e)}")


if __name__ == "__main__":
    run_all_examples()
