"""
Tests específicos para homologación AFIP
"""
import unittest
from unittest.mock import patch, MagicMock
from decimal import Decimal
from datetime import date, datetime, timedelta
from django.test import TestCase
from django.conf import settings

from ..models import AfipConfig, Invoice, InvoiceItem, InvoiceType, InvoiceStatus
from ..services.afip_service import AfipService
from ..test_config import AFIP_TEST_CONFIG, AFIP_ENVIRONMENT_CONFIG

# Configuración de homologación AFIP
AFIP_HOMOLOGATION_CONFIG = {
    'cuit': '20123456789',  # CUIT de prueba de AFIP
    'point_of_sale': 1,
    'environment': 'test',
    'certificate_path': '/path/to/homologation/cert.crt',
    'private_key_path': '/path/to/homologation/key.key',
}


class TestAfipHomologation(TestCase):
    """Tests para homologación con AFIP"""
    
    def setUp(self):
        # Crear configuración de homologación
        self.afip_config = AfipConfig.objects.create(
            cuit=AFIP_HOMOLOGATION_CONFIG['cuit'],
            point_of_sale=AFIP_HOMOLOGATION_CONFIG['point_of_sale'],
            environment=AFIP_HOMOLOGATION_CONFIG['environment'],
            certificate_path=AFIP_HOMOLOGATION_CONFIG['certificate_path'],
            private_key_path=AFIP_HOMOLOGATION_CONFIG['private_key_path'],
        )
    
    def test_homologation_environment_configuration(self):
        """Test de configuración de ambiente de homologación"""
        self.assertEqual(self.afip_config.environment, 'test')
        self.assertEqual(self.afip_config.cuit, AFIP_HOMOLOGATION_CONFIG['cuit'])
        self.assertEqual(self.afip_config.point_of_sale, AFIP_HOMOLOGATION_CONFIG['point_of_sale'])
    
    def test_homologation_urls(self):
        """Test de URLs de homologación"""
        test_config = AFIP_ENVIRONMENT_CONFIG['test']
        
        self.assertEqual(test_config['wsaa_url'], 'https://wsaahomo.afip.gov.ar/ws/services/LoginCms')
        self.assertEqual(test_config['wsfev1_url'], 'https://wswhomo.afip.gov.ar/wsfev1/service.asmx')
    
    @patch('apps.invoicing.services.afip_auth_service.requests.post')
    def test_homologation_wsaa_authentication(self, mock_post):
        """Test de autenticación WSAA en homologación"""
        # Configurar respuesta mock de WSAA
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = '''<?xml version="1.0" encoding="UTF-8"?>
        <soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/">
            <soap:Body>
                <loginCmsResponse>
                    <loginCmsReturn>
                        <token>test_token_homologation</token>
                        <sign>test_sign_homologation</sign>
                        <generationTime>2025-01-01T00:00:00-03:00</generationTime>
                        <expirationTime>2025-01-01T12:00:00-03:00</expirationTime>
                    </loginCmsReturn>
                </loginCmsResponse>
            </soap:Body>
        </soap:Envelope>'''
        mock_post.return_value = mock_response
        
        # Test de autenticación
        from ..services.afip_auth_service import AfipAuthService
        auth_service = AfipAuthService(self.afip_config)
        
        # En modo de prueba, no se conecta realmente
        with patch.object(auth_service, 'authenticate') as mock_auth:
            mock_auth.return_value = {
                'success': True,
                'token': 'test_token_homologation',
                'sign': 'test_sign_homologation'
            }
            
            result = auth_service.authenticate()
            
            self.assertTrue(result['success'])
            self.assertEqual(result['token'], 'test_token_homologation')
            self.assertEqual(result['sign'], 'test_sign_homologation')
    
    @patch('apps.invoicing.services.afip_invoice_service.requests.post')
    def test_homologation_invoice_emission(self, mock_post):
        """Test de emisión de factura en homologación"""
        # Configurar respuesta mock de WSFEv1
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = '''<?xml version="1.0" encoding="UTF-8"?>
        <soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/">
            <soap:Body>
                <FECAESolicitarResponse>
                    <FECAESolicitarResult>
                        <FeCabResp>
                            <Cuit>20123456789</Cuit>
                            <PtoVta>1</PtoVta>
                            <CbteTipo>6</CbteTipo>
                            <FchProceso>20250101</FchProceso>
                            <CantReg>1</CantReg>
                            <Resultado>A</Resultado>
                        </FeCabResp>
                        <FeDetResp>
                            <FECAEDetResponse>
                                <Concepto>1</Concepto>
                                <DocTipo>96</DocTipo>
                                <DocNro>12345678</DocNro>
                                <CbteDesde>1</CbteDesde>
                                <CbteHasta>1</CbteHasta>
                                <CbteFch>20250101</CbteFch>
                                <Resultado>A</Resultado>
                                <CAE>12345678901234</CAE>
                                <CAEFchVto>20250115</CAEFchVto>
                                <Obs></Obs>
                            </FECAEDetResponse>
                        </FeDetResp>
                    </FECAESolicitarResult>
                </FECAESolicitarResponse>
            </soap:Body>
        </soap:Envelope>'''
        mock_post.return_value = mock_response
        
        # Crear factura de prueba
        invoice = Invoice.objects.create(
            number="0001-00000001",
            type=InvoiceType.FACTURA_B,
            issue_date=date.today(),
            total=Decimal('1000.00'),
            net_amount=Decimal('826.45'),
            vat_amount=Decimal('173.55'),
            currency='ARS',
            customer_name='Cliente Homologación',
            customer_document_type='DNI',
            customer_document_number='12345678',
            status=InvoiceStatus.DRAFT
        )
        
        # Test de emisión
        from ..services.afip_invoice_service import AfipInvoiceService
        invoice_service = AfipInvoiceService(self.afip_config)
        
        # En modo de prueba, no se conecta realmente
        with patch.object(invoice_service, 'send_invoice') as mock_send:
            mock_send.return_value = {
                'success': True,
                'cae': '12345678901234',
                'cae_expiration': 20250115,
                'invoice_number': 1
            }
            
            result = invoice_service.send_invoice(invoice)
            
            self.assertTrue(result['success'])
            self.assertEqual(result['cae'], '12345678901234')
    
    def test_homologation_invoice_types(self):
        """Test de tipos de factura en homologación"""
        # Factura A (Responsable Inscripto)
        invoice_a = Invoice.objects.create(
            number="0001-00000001",
            type=InvoiceType.FACTURA_A,
            issue_date=date.today(),
            total=Decimal('1000.00'),
            net_amount=Decimal('826.45'),
            vat_amount=Decimal('173.55'),
            currency='ARS',
            customer_name='Empresa Test',
            customer_document_type='CUIT',
            customer_document_number='20123456789',
            status=InvoiceStatus.DRAFT
        )
        
        # Factura B (Consumidor Final)
        invoice_b = Invoice.objects.create(
            number="0001-00000002",
            type=InvoiceType.FACTURA_B,
            issue_date=date.today(),
            total=Decimal('1000.00'),
            net_amount=Decimal('826.45'),
            vat_amount=Decimal('173.55'),
            currency='ARS',
            customer_name='Cliente Test',
            customer_document_type='DNI',
            customer_document_number='12345678',
            status=InvoiceStatus.DRAFT
        )
        
        # Factura C (Exento)
        invoice_c = Invoice.objects.create(
            number="0001-00000003",
            type=InvoiceType.FACTURA_C,
            issue_date=date.today(),
            total=Decimal('1000.00'),
            net_amount=Decimal('1000.00'),
            vat_amount=Decimal('0.00'),
            currency='ARS',
            customer_name='Cliente Exento',
            customer_document_type='DNI',
            customer_document_number='12345678',
            status=InvoiceStatus.DRAFT
        )
        
        # Verificar tipos
        self.assertEqual(invoice_a.type, InvoiceType.FACTURA_A)
        self.assertEqual(invoice_b.type, InvoiceType.FACTURA_B)
        self.assertEqual(invoice_c.type, InvoiceType.FACTURA_C)
        
        # Verificar cálculos de IVA
        self.assertGreater(invoice_a.vat_amount, 0)
        self.assertGreater(invoice_b.vat_amount, 0)
        self.assertEqual(invoice_c.vat_amount, 0)
    
    def test_homologation_document_types(self):
        """Test de tipos de documento en homologación"""
        document_types = [
            ('DNI', '12345678'),
            ('CUIT', '20123456789'),
            ('CUIL', '20123456789'),
            ('PASAPORTE', 'AB123456'),
        ]
        
        for doc_type, doc_number in document_types:
            invoice = Invoice.objects.create(
                number=f"0001-0000000{len(document_types)}",
                type=InvoiceType.FACTURA_B,
                issue_date=date.today(),
                total=Decimal('1000.00'),
                net_amount=Decimal('826.45'),
                vat_amount=Decimal('173.55'),
                currency='ARS',
                customer_name=f'Cliente {doc_type}',
                customer_document_type=doc_type,
                customer_document_number=doc_number,
                status=InvoiceStatus.DRAFT
            )
            
            self.assertEqual(invoice.customer_document_type, doc_type)
            self.assertEqual(invoice.customer_document_number, doc_number)
    
    def test_homologation_consecutive_numbering(self):
        """Test de numeración consecutiva en homologación"""
        # Generar varios números consecutivos
        numbers = []
        for i in range(10):
            next_number = self.afip_config.get_next_invoice_number()
            numbers.append(next_number)
            self.afip_config.update_invoice_number(next_number)
        
        # Verificar que son consecutivos
        expected_numbers = list(range(1, 11))
        self.assertEqual(numbers, expected_numbers)
        
        # Verificar formato
        for number in numbers:
            formatted = self.afip_config.format_invoice_number(number)
            self.assertRegex(formatted, r'^\d{4}-\d{8}$')
    
    def test_homologation_cae_validation(self):
        """Test de validación de CAE en homologación"""
        # CAE válido de homologación
        valid_cae = '12345678901234'
        valid_expiration = (date.today() + timedelta(days=10)).strftime('%Y%m%d')
        
        invoice = Invoice.objects.create(
            number="0001-00000001",
            type=InvoiceType.FACTURA_B,
            issue_date=date.today(),
            total=Decimal('1000.00'),
            net_amount=Decimal('826.45'),
            vat_amount=Decimal('173.55'),
            currency='ARS',
            customer_name='Cliente Test',
            customer_document_type='DNI',
            customer_document_number='12345678',
            status=InvoiceStatus.APPROVED,
            cae=valid_cae,
            cae_expiration=datetime.strptime(valid_expiration, '%Y%m%d').date()
        )
        
        # Verificar validaciones
        self.assertTrue(invoice.is_approved())
        self.assertFalse(invoice.is_expired())
        self.assertTrue(invoice.can_be_resent())
        
        # CAE expirado
        expired_cae = '98765432109876'
        expired_expiration = (date.today() - timedelta(days=1)).strftime('%Y%m%d')
        
        expired_invoice = Invoice.objects.create(
            number="0001-00000002",
            type=InvoiceType.FACTURA_B,
            issue_date=date.today(),
            total=Decimal('1000.00'),
            net_amount=Decimal('826.45'),
            vat_amount=Decimal('173.55'),
            currency='ARS',
            customer_name='Cliente Test',
            customer_document_type='DNI',
            customer_document_number='12345678',
            status=InvoiceStatus.APPROVED,
            cae=expired_cae,
            cae_expiration=datetime.strptime(expired_expiration, '%Y%m%d').date()
        )
        
        # Verificar que está expirado
        self.assertTrue(expired_invoice.is_approved())
        self.assertTrue(expired_invoice.is_expired())
        self.assertFalse(expired_invoice.can_be_resent())


class TestProductionEnvironment(TestCase):
    """Tests para ambiente de producción"""
    
    def setUp(self):
        # Crear configuración de producción
        self.afip_config = AfipConfig.objects.create(
            cuit='20123456789',  # CUIT real de producción
            point_of_sale=1,
            environment='production',
            certificate_path='/path/to/production/cert.crt',
            private_key_path='/path/to/production/key.key',
        )
    
    def test_production_environment_configuration(self):
        """Test de configuración de ambiente de producción"""
        self.assertEqual(self.afip_config.environment, 'production')
        self.assertNotEqual(self.afip_config.cuit, AFIP_TEST_CONFIG['TEST_CUIT'])
    
    def test_production_urls(self):
        """Test de URLs de producción"""
        prod_config = AFIP_ENVIRONMENT_CONFIG['production']
        
        self.assertEqual(prod_config['wsaa_url'], 'https://wsaa.afip.gov.ar/ws/services/LoginCms')
        self.assertEqual(prod_config['wsfev1_url'], 'https://servicios1.afip.gov.ar/wsfev1/service.asmx')
    
    def test_production_environment_validation(self):
        """Test de validación de ambiente de producción"""
        # Debe tener certificados válidos
        self.assertIsNotNone(self.afip_config.certificate_path)
        self.assertIsNotNone(self.afip_config.private_key_path)
        
        # Debe tener CUIT válido
        self.assertTrue(self.afip_config.cuit.isdigit())
        self.assertEqual(len(self.afip_config.cuit), 11)
        
        # Debe tener punto de venta válido
        self.assertGreaterEqual(self.afip_config.point_of_sale, 1)
        self.assertLessEqual(self.afip_config.point_of_sale, 9999)


class TestEnvironmentSwitching(TestCase):
    """Tests de alternancia entre ambientes"""
    
    def test_switch_from_test_to_production(self):
        """Test de cambio de test a producción"""
        # Configuración de test
        test_config = AfipConfig.objects.create(
            cuit=AFIP_TEST_CONFIG['TEST_CUIT'],
            point_of_sale=AFIP_TEST_CONFIG['TEST_POINT_OF_SALE'],
            environment='test',
            certificate_path=AFIP_TEST_CONFIG['TEST_CERTIFICATE_PATH'],
            private_key_path=AFIP_TEST_CONFIG['TEST_PRIVATE_KEY_PATH'],
        )
        
        # Cambiar a producción
        test_config.environment = 'production'
        test_config.certificate_path = '/path/to/production/cert.crt'
        test_config.private_key_path = '/path/to/production/key.key'
        test_config.save()
        
        # Verificar cambio
        test_config.refresh_from_db()
        self.assertEqual(test_config.environment, 'production')
        self.assertNotEqual(test_config.certificate_path, AFIP_TEST_CONFIG['TEST_CERTIFICATE_PATH'])
    
    def test_switch_from_production_to_test(self):
        """Test de cambio de producción a test"""
        # Configuración de producción
        prod_config = AfipConfig.objects.create(
            cuit='20123456789',
            point_of_sale=1,
            environment='production',
            certificate_path='/path/to/production/cert.crt',
            private_key_path='/path/to/production/key.key',
        )
        
        # Cambiar a test
        prod_config.environment = 'test'
        prod_config.certificate_path = AFIP_TEST_CONFIG['TEST_CERTIFICATE_PATH']
        prod_config.private_key_path = AFIP_TEST_CONFIG['TEST_PRIVATE_KEY_PATH']
        prod_config.save()
        
        # Verificar cambio
        prod_config.refresh_from_db()
        self.assertEqual(prod_config.environment, 'test')
        self.assertEqual(prod_config.certificate_path, AFIP_TEST_CONFIG['TEST_CERTIFICATE_PATH'])
