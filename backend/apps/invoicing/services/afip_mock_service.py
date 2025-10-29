"""
Servicio de mocking para respuestas de AFIP
Permite testing local sin conectarse a los servicios reales de AFIP
"""
import logging
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Dict, Any, Optional
import json

from .afip_auth_service import AfipAuthService
from .afip_invoice_service import AfipInvoiceService
from ..test_config import AFIP_MOCK_RESPONSES, AFIP_TEST_CONFIG

logger = logging.getLogger(__name__)


class AfipMockService:
    """
    Servicio de mocking para AFIP que simula respuestas reales
    """
    
    def __init__(self, environment: str = 'test'):
        self.environment = environment
        self.mock_responses = AFIP_MOCK_RESPONSES
        self.test_config = AFIP_TEST_CONFIG
        
    def mock_wsaa_login(self, cuit: str) -> Dict[str, Any]:
        """
        Simula la respuesta de login de WSAA
        """
        logger.info(f"Mocking WSAA login for CUIT: {cuit}")
        
        # Generar token y sign de prueba
        token = f"test_token_{cuit}_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        sign = f"test_sign_{cuit}_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        # Tiempo de expiración: 12 horas desde ahora
        generation_time = datetime.now()
        expiration_time = generation_time + timedelta(hours=12)
        
        return {
            'loginCmsResponse': {
                'loginCmsReturn': {
                    'token': token,
                    'sign': sign,
                    'generationTime': generation_time.strftime('%Y-%m-%dT%H:%M:%S-03:00'),
                    'expirationTime': expiration_time.strftime('%Y-%m-%dT%H:%M:%S-03:00')
                }
            }
        }
    
    def mock_wsfev1_invoice(self, invoice_data: Dict[str, Any], success: bool = True) -> Dict[str, Any]:
        """
        Simula la respuesta de emisión de factura de WSFEv1
        """
        logger.info(f"Mocking WSFEv1 invoice emission - Success: {success}")
        
        if success:
            # Generar CAE de prueba (exactamente 14 dígitos)
            now = datetime.now()
            base = now.strftime('%y%m%d%H%M%S')  # 12 dígitos
            last2 = f"{(now.microsecond // 10000) % 100:02d}"  # 2 dígitos
            cae = f"{base}{last2}"
            cae_expiration = (datetime.now() + timedelta(days=10)).strftime('%Y%m%d')
            
            return {
                'FECAESolicitarResponse': {
                    'FECAESolicitarResult': {
                        'FeCabResp': {
                            'Cuit': int(invoice_data.get('cuit', self.test_config['TEST_CUIT'])),
                            'PtoVta': invoice_data.get('point_of_sale', self.test_config['TEST_POINT_OF_SALE']),
                            'CbteTipo': self._get_invoice_type_code(invoice_data.get('type', 'B')),
                            'FchProceso': datetime.now().strftime('%Y%m%d'),
                            'CantReg': 1,
                            'Resultado': 'A'  # Aprobado
                        },
                        'FeDetResp': {
                            'FECAEDetResponse': [
                                {
                                    'Concepto': 1,
                                    'DocTipo': self._get_document_type_code(invoice_data.get('customer_document_type', 'DNI')),
                                    'DocNro': int(invoice_data.get('customer_document_number', '12345678')),
                                    'CbteDesde': invoice_data.get('invoice_number', 1),
                                    'CbteHasta': invoice_data.get('invoice_number', 1),
                                    'CbteFch': int(datetime.now().strftime('%Y%m%d')),
                                    'Resultado': 'A',  # Aprobado
                                    'CAE': cae,
                                    'CAEFchVto': cae_expiration,
                                    'Obs': []
                                }
                            ]
                        }
                    }
                }
            }
        else:
            # Respuesta de error
            return {
                'FECAESolicitarResponse': {
                    'FECAESolicitarResult': {
                        'FeCabResp': {
                            'Cuit': int(invoice_data.get('cuit', self.test_config['TEST_CUIT'])),
                            'PtoVta': invoice_data.get('point_of_sale', self.test_config['TEST_POINT_OF_SALE']),
                            'CbteTipo': self._get_invoice_type_code(invoice_data.get('type', 'B')),
                            'FchProceso': datetime.now().strftime('%Y%m%d'),
                            'CantReg': 1,
                            'Resultado': 'R'  # Rechazado
                        },
                        'FeDetResp': {
                            'FECAEDetResponse': [
                                {
                                    'Concepto': 1,
                                    'DocTipo': self._get_document_type_code(invoice_data.get('customer_document_type', 'DNI')),
                                    'DocNro': int(invoice_data.get('customer_document_number', '12345678')),
                                    'CbteDesde': invoice_data.get('invoice_number', 1),
                                    'CbteHasta': invoice_data.get('invoice_number', 1),
                                    'CbteFch': int(datetime.now().strftime('%Y%m%d')),
                                    'Resultado': 'R',  # Rechazado
                                    'CAE': '',
                                    'CAEFchVto': 0,
                                    'Obs': [
                                        {
                                            'Code': 1001,
                                            'Msg': 'Error de validación en modo mock'
                                        }
                                    ]
                                }
                            ]
                        }
                    }
                }
            }
    
    def mock_wsfev1_credit_note(self, credit_note_data: Dict[str, Any], success: bool = True) -> Dict[str, Any]:
        """
        Simula la respuesta de emisión de nota de crédito de WSFEv1
        """
        logger.info(f"Mocking WSFEv1 credit note emission - Success: {success}")
        
        # Usar la misma lógica que facturas pero con tipo NC
        credit_note_data['type'] = 'NC'
        return self.mock_wsfev1_invoice(credit_note_data, success)
    
    def _get_invoice_type_code(self, invoice_type: str) -> int:
        """Convierte tipo de factura a código AFIP"""
        type_codes = {
            'A': 1,   # Factura A
            'B': 6,   # Factura B
            'C': 11,  # Factura C
            'E': 19,  # Factura E
            'NC': 3,  # Nota de Crédito
            'ND': 2,  # Nota de Débito
        }
        return type_codes.get(invoice_type, 6)  # Default: Factura B
    
    def _get_document_type_code(self, document_type: str) -> int:
        """Convierte tipo de documento a código AFIP"""
        doc_codes = {
            'DNI': 96,
            'CUIT': 80,
            'CUIL': 86,
            'PASAPORTE': 94,
        }
        return doc_codes.get(document_type, 96)  # Default: DNI


class MockAfipAuthService(AfipAuthService):
    """
    Versión mock de AfipAuthService para testing
    """
    
    def __init__(self, afip_config, mock_service: AfipMockService = None):
        super().__init__(afip_config)
        self.mock_service = mock_service or AfipMockService()
        self.is_mock = True
    
    def authenticate(self) -> Dict[str, Any]:
        """
        Mock de autenticación WSAA
        """
        logger.info("Mocking AFIP authentication")
        
        # Simular respuesta de WSAA
        mock_response = self.mock_service.mock_wsaa_login(self.config.cuit)
        
        # Extraer datos de la respuesta mock
        login_return = mock_response['loginCmsResponse']['loginCmsReturn']
        
        # Guardar en caché (simulado)
        self.cache_token(login_return['token'], login_return['sign'])
        
        return {
            'success': True,
            'token': login_return['token'],
            'sign': login_return['sign'],
            'generation_time': login_return['generationTime'],
            'expiration_time': login_return['expirationTime']
        }


class MockAfipInvoiceService(AfipInvoiceService):
    """
    Versión mock de AfipInvoiceService para testing
    """
    
    def __init__(self, afip_config, mock_service: AfipMockService = None):
        super().__init__(afip_config)
        self.mock_service = mock_service or AfipMockService()
        self.is_mock = True
    
    def send_invoice(self, invoice) -> Dict[str, Any]:
        """
        Mock de envío de factura a AFIP
        """
        logger.info(f"Mocking invoice send for invoice {invoice.id}")
        
        # Preparar datos de la factura
        number_str = getattr(invoice, 'number', '0001-00000001')
        try:
            invoice_number = int(str(number_str).split('-')[1])
        except Exception:
            invoice_number = 1

        invoice_data = {
            'cuit': self.config.cuit,
            'point_of_sale': self.config.point_of_sale,
            'type': getattr(invoice, 'type', 'B'),
            'invoice_number': invoice_number,
            'customer_document_type': getattr(invoice, 'client_document_type', getattr(invoice, 'customer_document_type', 'DNI')),
            'customer_document_number': getattr(invoice, 'client_document_number', getattr(invoice, 'customer_document_number', '12345678')),
            'total': float(getattr(invoice, 'total', 0) or 0),
            'net_amount': float(getattr(invoice, 'net_amount', 0) or 0),
            'vat_amount': float(getattr(invoice, 'vat_amount', 0) or 0),
        }
        
        # Simular respuesta de WSFEv1
        mock_response = self.mock_service.mock_wsfev1_invoice(invoice_data, success=True)
        
        # Procesar respuesta mock
        result = mock_response['FECAESolicitarResponse']['FECAESolicitarResult']
        fe_det = result['FeDetResp']['FECAEDetResponse'][0]
        
        if result['FeCabResp']['Resultado'] == 'A' and fe_det['Resultado'] == 'A':
            return {
                'success': True,
                'cae': fe_det['CAE'],
                'cae_expiration': str(fe_det['CAEFchVto']),
                'invoice_number': fe_det['CbteDesde'],
                'afip_response': mock_response
            }
        else:
            error_msg = fe_det.get('Obs', [{}])[0].get('Msg', 'Error desconocido')
            return {
                'success': False,
                'error': error_msg,
                'afip_response': mock_response
            }
    
    def send_credit_note(self, credit_note) -> Dict[str, Any]:
        """
        Mock de envío de nota de crédito a AFIP
        """
        logger.info(f"Mocking credit note send for credit note {credit_note.id}")
        
        # Preparar datos de la nota de crédito
        number_str = getattr(credit_note, 'number', '0001-00000001')
        try:
            invoice_number = int(str(number_str).split('-')[1])
        except Exception:
            invoice_number = 1

        credit_note_data = {
            'cuit': self.config.cuit,
            'point_of_sale': self.config.point_of_sale,
            'type': getattr(credit_note, 'type', 'NC'),
            'invoice_number': invoice_number,
            'customer_document_type': getattr(credit_note, 'client_document_type', getattr(credit_note, 'customer_document_type', 'DNI')),
            'customer_document_number': getattr(credit_note, 'client_document_number', getattr(credit_note, 'customer_document_number', '12345678')),
            'total': float(getattr(credit_note, 'total', 0) or 0),
            'net_amount': float(getattr(credit_note, 'net_amount', 0) or 0),
            'vat_amount': float(getattr(credit_note, 'vat_amount', 0) or 0),
        }
        
        # Simular respuesta de WSFEv1
        mock_response = self.mock_service.mock_wsfev1_credit_note(credit_note_data, success=True)
        
        # Procesar respuesta mock (misma lógica que facturas)
        result = mock_response['FECAESolicitarResponse']['FECAESolicitarResult']
        fe_det = result['FeDetResp']['FECAEDetResponse'][0]
        
        if result['FeCabResp']['Resultado'] == 'A' and fe_det['Resultado'] == 'A':
            return {
                'success': True,
                'cae': fe_det['CAE'],
                'cae_expiration': fe_det['CAEFchVto'],
                'invoice_number': fe_det['CbteDesde'],
                'afip_response': mock_response
            }
        else:
            error_msg = fe_det.get('Obs', [{}])[0].get('Msg', 'Error desconocido')
            return {
                'success': False,
                'error': error_msg,
                'afip_response': mock_response
            }
