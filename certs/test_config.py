# Configuración de certificados de prueba para AFIP
# Este archivo contiene las rutas a los certificados generados localmente

import os
from pathlib import Path

# Directorio base del proyecto
BASE_DIR = Path(__file__).parent.parent

# Rutas de certificados (relativas al directorio del proyecto)
CERTIFICATE_PATH = str(BASE_DIR / "certs" / "test_certificate.crt")
PRIVATE_KEY_PATH = str(BASE_DIR / "certs" / "test_private_key.key")
PFX_PATH = str(BASE_DIR / "certs" / "test_certificate.pfx")
CSR_PATH = str(BASE_DIR / "certs" / "test_certificate_request.csr")

# Configuración de AFIP para homologación
AFIP_TEST_CONFIG = {
    "cuit": "20123456789",
    "point_of_sale": 1,
    "environment": "test",
    "wsaa_url": "https://wsaahomo.afip.gov.ar/ws/services/LoginCms",
    "wsfev1_url": "https://wswhomo.afip.gov.ar/wsfev1/service.asmx",
    "timeout": 30,
    "retries": 3,
    "retry_delay": 1
}

# Datos de prueba para facturas
TEST_CUSTOMER_DATA = {
    "name": "Cliente de Prueba",
    "document_type": "DNI",
    "document_number": "12345678",
    "address": "Av. Test 123",
    "city": "Buenos Aires",
    "postal_code": "1000",
    "country": "Argentina"
}

# Items de prueba para facturas
TEST_INVOICE_ITEMS = [
    {
        "description": "Servicio de Hospedaje - Habitación Test",
        "quantity": 1,
        "unit_price": 1000.00,
        "vat_rate": 21.00,
        "afip_code": "1"
    }
]

# Configuración de testing por ambiente
AFIP_ENVIRONMENT_CONFIG = {
    "test": {
        "wsaa_url": "https://wsaahomo.afip.gov.ar/ws/services/LoginCms",
        "wsfev1_url": "https://wswhomo.afip.gov.ar/wsfev1/service.asmx",
        "cuit": "20123456789",
        "point_of_sale": 1,
        "timeout": 30,
        "retries": 3,
        "retry_delay": 1,
    },
    "production": {
        "wsaa_url": "https://wsaa.afip.gov.ar/ws/services/LoginCms",
        "wsfev1_url": "https://servicios1.afip.gov.ar/wsfev1/service.asmx",
        "cuit": None,  # Se configura por hotel
        "point_of_sale": None,  # Se configura por hotel
        "timeout": 60,
        "retries": 5,
        "retry_delay": 5,
    }
}

# Respuestas mock de AFIP para testing
AFIP_MOCK_RESPONSES = {
    "wsaa_login_success": {
        "loginCmsResponse": {
            "loginCmsReturn": {
                "token": "test_token_123456789",
                "sign": "test_sign_abcdefghij",
                "generationTime": "2025-01-01T00:00:00-03:00",
                "expirationTime": "2025-01-01T12:00:00-03:00"
            }
        }
    },
    
    "wsfev1_invoice_success": {
        "FECAESolicitarResponse": {
            "FECAESolicitarResult": {
                "FeCabResp": {
                    "Cuit": 20123456789,
                    "PtoVta": 1,
                    "CbteTipo": 6,  # Factura B
                    "FchProceso": "20250101",
                    "CantReg": 1,
                    "Resultado": "A"  # Aprobado
                },
                "FeDetResp": {
                    "FECAEDetResponse": [
                        {
                            "Concepto": 1,
                            "DocTipo": 96,  # DNI
                            "DocNro": 12345678,
                            "CbteDesde": 1,
                            "CbteHasta": 1,
                            "CbteFch": 20250101,
                            "Resultado": "A",  # Aprobado
                            "CAE": "12345678901234",
                            "CAEFchVto": 20250115,
                            "Obs": []
                        }
                    ]
                }
            }
        }
    }
}
