"""
Configuración de testing para AFIP homologación
"""
import os
from django.conf import settings

# Configuración de AFIP para homologación (testing)
AFIP_TEST_CONFIG = {
    # CUIT de prueba de AFIP (homologación)
    'TEST_CUIT': '20123456789',
    
    # Punto de venta de prueba
    'TEST_POINT_OF_SALE': 1,
    
    # URLs de AFIP
    'WSAA_URL_TEST': 'https://wsaahomo.afip.gov.ar/ws/services/LoginCms',
    'WSFEV1_URL_TEST': 'https://wswhomo.afip.gov.ar/wsfev1/service.asmx',
    
    # URLs de producción
    'WSAA_URL_PROD': 'https://wsaa.afip.gov.ar/ws/services/LoginCms',
    'WSFEV1_URL_PROD': 'https://servicios1.afip.gov.ar/wsfev1/service.asmx',
    
    # Certificados de prueba (deben estar en el proyecto)
    'TEST_CERTIFICATE_PATH': os.path.join(settings.BASE_DIR, 'certs', 'test_cert.crt'),
    'TEST_PRIVATE_KEY_PATH': os.path.join(settings.BASE_DIR, 'certs', 'test_key.key'),
    
    # Configuración de testing
    'TEST_TIMEOUT': 30,
    'TEST_RETRIES': 3,
    'TEST_RETRY_DELAY': 1,
}

# Datos de prueba para facturas
AFIP_TEST_INVOICE_DATA = {
    'customer_name': 'Cliente de Prueba',
    'customer_document_type': 'DNI',
    'customer_document_number': '12345678',
    'customer_address': 'Av. Test 123',
    'customer_city': 'Buenos Aires',
    'customer_postal_code': '1000',
    'customer_country': 'Argentina',
    'items': [
        {
            'description': 'Servicio de Hospedaje - Habitación Test',
            'quantity': 1,
            'unit_price': 1000.00,
            'vat_rate': 21.00,
            'afip_code': '1'
        }
    ]
}

# Respuestas mock de AFIP para testing
AFIP_MOCK_RESPONSES = {
    'wsaa_login_success': {
        'loginCmsResponse': {
            'loginCmsReturn': {
                'token': 'test_token_123456789',
                'sign': 'test_sign_abcdefghij',
                'generationTime': '2025-01-01T00:00:00-03:00',
                'expirationTime': '2025-01-01T12:00:00-03:00'
            }
        }
    },
    
    'wsfev1_invoice_success': {
        'FECAESolicitarResponse': {
            'FECAESolicitarResult': {
                'FeCabResp': {
                    'Cuit': 20123456789,
                    'PtoVta': 1,
                    'CbteTipo': 6,  # Factura B
                    'FchProceso': '20250101',
                    'CantReg': 1,
                    'Resultado': 'A'  # Aprobado
                },
                'FeDetResp': {
                    'FECAEDetResponse': [
                        {
                            'Concepto': 1,
                            'DocTipo': 96,  # DNI
                            'DocNro': 12345678,
                            'CbteDesde': 1,
                            'CbteHasta': 1,
                            'CbteFch': 20250101,
                            'Resultado': 'A',  # Aprobado
                            'CAE': '12345678901234',
                            'CAEFchVto': 20250115,
                            'Obs': []
                        }
                    ]
                }
            }
        }
    },
    
    'wsfev1_invoice_error': {
        'FECAESolicitarResponse': {
            'FECAESolicitarResult': {
                'FeCabResp': {
                    'Cuit': 20123456789,
                    'PtoVta': 1,
                    'CbteTipo': 6,
                    'FchProceso': '20250101',
                    'CantReg': 1,
                    'Resultado': 'R'  # Rechazado
                },
                'FeDetResp': {
                    'FECAEDetResponse': [
                        {
                            'Concepto': 1,
                            'DocTipo': 96,
                            'DocNro': 12345678,
                            'CbteDesde': 1,
                            'CbteHasta': 1,
                            'CbteFch': 20250101,
                            'Resultado': 'R',  # Rechazado
                            'CAE': '',
                            'CAEFchVto': 0,
                            'Obs': [
                                {
                                    'Code': 1001,
                                    'Msg': 'Error de validación'
                                }
                            ]
                        }
                    ]
                }
            }
        }
    }
}

# Configuración de testing por ambiente
AFIP_ENVIRONMENT_CONFIG = {
    'test': {
        'wsaa_url': AFIP_TEST_CONFIG['WSAA_URL_TEST'],
        'wsfev1_url': AFIP_TEST_CONFIG['WSFEV1_URL_TEST'],
        'cuit': AFIP_TEST_CONFIG['TEST_CUIT'],
        'point_of_sale': AFIP_TEST_CONFIG['TEST_POINT_OF_SALE'],
        'timeout': AFIP_TEST_CONFIG['TEST_TIMEOUT'],
        'retries': AFIP_TEST_CONFIG['TEST_RETRIES'],
        'retry_delay': AFIP_TEST_CONFIG['TEST_RETRY_DELAY'],
    },
    'production': {
        'wsaa_url': AFIP_TEST_CONFIG['WSAA_URL_PROD'],
        'wsfev1_url': AFIP_TEST_CONFIG['WSFEV1_URL_PROD'],
        'cuit': None,  # Se configura por hotel
        'point_of_sale': None,  # Se configura por hotel
        'timeout': 60,
        'retries': 5,
        'retry_delay': 5,
    }
}
