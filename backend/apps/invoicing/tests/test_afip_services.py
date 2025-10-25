"""
Tests unitarios para servicios AFIP
"""
import unittest
from unittest.mock import patch, MagicMock
from decimal import Decimal
from datetime import date, datetime, timedelta
from django.test import TestCase
from django.contrib.auth import get_user_model

from ..models import AfipConfig, Invoice, InvoiceItem, InvoiceType, InvoiceStatus
from ..services.afip_auth_service import AfipAuthService, AfipAuthError
from ..services.afip_invoice_service import AfipInvoiceService, AfipInvoiceError
from ..services.afip_mock_service import MockAfipAuthService, MockAfipInvoiceService, AfipMockService
from ..test_config import AFIP_TEST_CONFIG, AFIP_TEST_INVOICE_DATA

User = get_user_model()


class TestAfipMockService(TestCase):
    """Tests para el servicio de mocking de AFIP"""
    
    def setUp(self):
        self.mock_service = AfipMockService()
    
    def test_mock_wsaa_login(self):
        """Test de mock de login WSAA"""
        cuit = "20123456789"
        response = self.mock_service.mock_wsaa_login(cuit)
        
        self.assertIn('loginCmsResponse', response)
        self.assertIn('loginCmsReturn', response['loginCmsResponse'])
        
        login_return = response['loginCmsResponse']['loginCmsReturn']
        self.assertIn('token', login_return)
        self.assertIn('sign', login_return)
        self.assertIn('generationTime', login_return)
        self.assertIn('expirationTime', login_return)
        
        # Verificar que el token contiene el CUIT
        self.assertIn(cuit, login_return['token'])
    
    def test_mock_wsfev1_invoice_success(self):
        """Test de mock de emisión de factura exitosa"""
        invoice_data = {
            'cuit': '20123456789',
            'point_of_sale': 1,
            'type': 'B',
            'invoice_number': 1,
            'customer_document_type': 'DNI',
            'customer_document_number': '12345678',
        }
        
        response = self.mock_service.mock_wsfev1_invoice(invoice_data, success=True)
        
        self.assertIn('FECAESolicitarResponse', response)
        result = response['FECAESolicitarResponse']['FECAESolicitarResult']
        
        # Verificar respuesta exitosa
        self.assertEqual(result['FeCabResp']['Resultado'], 'A')
        self.assertEqual(result['FeDetResp']['FECAEDetResponse'][0]['Resultado'], 'A')
        self.assertIn('CAE', result['FeDetResp']['FECAEDetResponse'][0])
    
    def test_mock_wsfev1_invoice_error(self):
        """Test de mock de emisión de factura con error"""
        invoice_data = {
            'cuit': '20123456789',
            'point_of_sale': 1,
            'type': 'B',
            'invoice_number': 1,
        }
        
        response = self.mock_service.mock_wsfev1_invoice(invoice_data, success=False)
        
        result = response['FECAESolicitarResponse']['FECAESolicitarResult']
        
        # Verificar respuesta de error
        self.assertEqual(result['FeCabResp']['Resultado'], 'R')
        self.assertEqual(result['FeDetResp']['FECAEDetResponse'][0]['Resultado'], 'R')
        self.assertEqual(result['FeDetResp']['FECAEDetResponse'][0]['CAE'], '')
    
    def test_get_invoice_type_code(self):
        """Test de conversión de tipos de factura"""
        self.assertEqual(self.mock_service._get_invoice_type_code('A'), 1)
        self.assertEqual(self.mock_service._get_invoice_type_code('B'), 6)
        self.assertEqual(self.mock_service._get_invoice_type_code('C'), 11)
        self.assertEqual(self.mock_service._get_invoice_type_code('E'), 19)
        self.assertEqual(self.mock_service._get_invoice_type_code('NC'), 3)
        self.assertEqual(self.mock_service._get_invoice_type_code('ND'), 2)
        self.assertEqual(self.mock_service._get_invoice_type_code('UNKNOWN'), 6)  # Default
    
    def test_get_document_type_code(self):
        """Test de conversión de tipos de documento"""
        self.assertEqual(self.mock_service._get_document_type_code('DNI'), 96)
        self.assertEqual(self.mock_service._get_document_type_code('CUIT'), 80)
        self.assertEqual(self.mock_service._get_document_type_code('CUIL'), 86)
        self.assertEqual(self.mock_service._get_document_type_code('PASAPORTE'), 94)
        self.assertEqual(self.mock_service._get_document_type_code('UNKNOWN'), 96)  # Default


class TestMockAfipAuthService(TestCase):
    """Tests para el servicio mock de autenticación AFIP"""
    
    def setUp(self):
        # Crear hotel de prueba
        from apps.core.models import Hotel
        from apps.locations.models import City, State, Country
        self.country = Country.objects.create(name='Argentina', code2='AR', code3='ARG')
        self.state = State.objects.create(name='Buenos Aires', country=self.country)
        self.city = City.objects.create(name='Buenos Aires', state=self.state)
        self.hotel = Hotel.objects.create(
            name='Hotel Test',
            address='Av. Test 123',
            city=self.city,
            state=self.state,
            country=self.country,
            tax_id='20123456789'
        )
        
        # Crear configuración AFIP de prueba
        self.afip_config = AfipConfig.objects.create(
            hotel=self.hotel,
            cuit=AFIP_TEST_CONFIG['TEST_CUIT'],
            point_of_sale=AFIP_TEST_CONFIG['TEST_POINT_OF_SALE'],
            environment='test',
            certificate_path=AFIP_TEST_CONFIG['TEST_CERTIFICATE_PATH'],
            private_key_path=AFIP_TEST_CONFIG['TEST_PRIVATE_KEY_PATH'],
        )
        self.mock_auth_service = MockAfipAuthService(self.afip_config)
    
    def test_authenticate_success(self):
        """Test de autenticación exitosa"""
        result = self.mock_auth_service.authenticate()
        
        self.assertTrue(result['success'])
        self.assertIn('token', result)
        self.assertIn('sign', result)
        self.assertIn('generation_time', result)
        self.assertIn('expiration_time', result)
        
        # Verificar que se guardó en caché
        self.assertIsNotNone(self.mock_auth_service.get_cached_credentials())


class TestMockAfipInvoiceService(TestCase):
    """Tests para el servicio mock de emisión de facturas AFIP"""
    
    def setUp(self):
        # Crear hotel de prueba
        from apps.core.models import Hotel
        from apps.locations.models import City, State, Country
        self.country = Country.objects.create(name='Argentina', code2='AR', code3='ARG')
        self.state = State.objects.create(name='Buenos Aires', country=self.country)
        self.city = City.objects.create(name='Buenos Aires', state=self.state)
        self.hotel = Hotel.objects.create(
            name='Hotel Test',
            address='Av. Test 123',
            city=self.city,
            state=self.state,
            country=self.country,
            tax_id='20123456789'
        )
        
        # Crear configuración AFIP de prueba
        self.afip_config = AfipConfig.objects.create(
            hotel=self.hotel,
            cuit=AFIP_TEST_CONFIG['TEST_CUIT'],
            point_of_sale=AFIP_TEST_CONFIG['TEST_POINT_OF_SALE'],
            environment='test',
            certificate_path=AFIP_TEST_CONFIG['TEST_CERTIFICATE_PATH'],
            private_key_path=AFIP_TEST_CONFIG['TEST_PRIVATE_KEY_PATH'],
        )
        
        # Crear factura de prueba
        self.invoice = Invoice.objects.create(
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
            status=InvoiceStatus.DRAFT,
        )
        
        self.mock_invoice_service = MockAfipInvoiceService(self.afip_config)
    
    def test_send_invoice_success(self):
        """Test de envío de factura exitoso"""
        result = self.mock_invoice_service.send_invoice(self.invoice)
        
        self.assertTrue(result['success'])
        self.assertIn('cae', result)
        self.assertIn('cae_expiration', result)
        self.assertIn('invoice_number', result)
        self.assertIn('afip_response', result)
        
        # Verificar formato del CAE
        self.assertRegex(result['cae'], r'^\d{14}$')
    
    def test_send_credit_note_success(self):
        """Test de envío de nota de crédito exitoso"""
        # Crear nota de crédito de prueba
        credit_note = Invoice.objects.create(
            number="0001-00000002",
            type=InvoiceType.NOTA_CREDITO,
            issue_date=date.today(),
            total=Decimal('500.00'),
            net_amount=Decimal('413.22'),
            vat_amount=Decimal('86.78'),
            currency='ARS',
            customer_name='Cliente Test',
            customer_document_type='DNI',
            customer_document_number='12345678',
            status=InvoiceStatus.DRAFT,
        )
        
        result = self.mock_invoice_service.send_credit_note(credit_note)
        
        self.assertTrue(result['success'])
        self.assertIn('cae', result)
        self.assertIn('cae_expiration', result)
        self.assertIn('invoice_number', result)
        self.assertIn('afip_response', result)


class TestAfipServiceIntegration(TestCase):
    """Tests de integración para servicios AFIP"""
    
    def setUp(self):
        # Crear hotel de prueba
        from apps.core.models import Hotel
        from apps.locations.models import City, State, Country
        self.country = Country.objects.create(name='Argentina', code2='AR', code3='ARG')
        self.state = State.objects.create(name='Buenos Aires', country=self.country)
        self.city = City.objects.create(name='Buenos Aires', state=self.state)
        self.hotel = Hotel.objects.create(
            name='Hotel Test',
            address='Av. Test 123',
            city=self.city,
            state=self.state,
            country=self.country,
            tax_id='20123456789'
        )
        
        # Crear configuración AFIP de prueba
        self.afip_config = AfipConfig.objects.create(
            hotel=self.hotel,
            cuit=AFIP_TEST_CONFIG['TEST_CUIT'],
            point_of_sale=AFIP_TEST_CONFIG['TEST_POINT_OF_SALE'],
            environment='test',
            certificate_path=AFIP_TEST_CONFIG['TEST_CERTIFICATE_PATH'],
            private_key_path=AFIP_TEST_CONFIG['TEST_PRIVATE_KEY_PATH'],
        )
    
    @patch('apps.invoicing.services.afip_service.AfipService._get_service')
    def test_afip_service_uses_mock_in_test_mode(self, mock_get_service):
        """Test de que AfipService usa mocks en modo test"""
        from ..services.afip_service import AfipService
        
        # Configurar mock para que devuelva servicio mock
        mock_service = MagicMock()
        mock_get_service.return_value = mock_service
        
        afip_service = AfipService(self.afip_config)
        
        # Verificar que se creó el servicio correcto
        mock_get_service.assert_called_once()
    
    def test_environment_switching(self):
        """Test de alternancia entre ambientes test y production"""
        # Test environment
        test_config = AfipConfig.objects.create(
            cuit=AFIP_TEST_CONFIG['TEST_CUIT'],
            point_of_sale=AFIP_TEST_CONFIG['TEST_POINT_OF_SALE'],
            environment='test',
            certificate_path=AFIP_TEST_CONFIG['TEST_CERTIFICATE_PATH'],
            private_key_path=AFIP_TEST_CONFIG['TEST_PRIVATE_KEY_PATH'],
        )
        
        # Production environment
        prod_config = AfipConfig.objects.create(
            cuit='20123456789',
            point_of_sale=1,
            environment='production',
            certificate_path='/path/to/prod/cert.crt',
            private_key_path='/path/to/prod/key.key',
        )
        
        # Verificar que las configuraciones son diferentes
        self.assertEqual(test_config.environment, 'test')
        self.assertEqual(prod_config.environment, 'production')
        
        # Verificar que los CUITs son diferentes (en producción sería real)
        self.assertNotEqual(test_config.cuit, prod_config.cuit)


class TestCaeValidation(TestCase):
    """Tests para validación de CAE"""
    
    def setUp(self):
        # Crear hotel de prueba
        from apps.core.models import Hotel
        from apps.locations.models import City, State, Country
        self.country = Country.objects.create(name='Argentina', code2='AR', code3='ARG')
        self.state = State.objects.create(name='Buenos Aires', country=self.country)
        self.city = City.objects.create(name='Buenos Aires', state=self.state)
        self.hotel = Hotel.objects.create(
            name='Hotel Test',
            address='Av. Test 123',
            city=self.city,
            state=self.state,
            country=self.country,
            tax_id='20123456789'
        )
        
        # Crear configuración AFIP de prueba
        self.afip_config = AfipConfig.objects.create(
            hotel=self.hotel,
            cuit=AFIP_TEST_CONFIG['TEST_CUIT'],
            point_of_sale=AFIP_TEST_CONFIG['TEST_POINT_OF_SALE'],
            environment='test',
            certificate_path=AFIP_TEST_CONFIG['TEST_CERTIFICATE_PATH'],
            private_key_path=AFIP_TEST_CONFIG['TEST_PRIVATE_KEY_PATH'],
        )
    
    def test_cae_format_validation(self):
        """Test de validación de formato de CAE"""
        # CAE válido (14 dígitos)
        valid_cae = "12345678901234"
        self.assertTrue(self._is_valid_cae_format(valid_cae))
        
        # CAE inválido (muy corto)
        invalid_cae = "1234567890123"
        self.assertFalse(self._is_valid_cae_format(invalid_cae))
        
        # CAE inválido (muy largo)
        invalid_cae = "123456789012345"
        self.assertFalse(self._is_valid_cae_format(invalid_cae))
        
        # CAE inválido (contiene letras)
        invalid_cae = "1234567890123a"
        self.assertFalse(self._is_valid_cae_format(invalid_cae))
    
    def test_cae_expiration_validation(self):
        """Test de validación de expiración de CAE"""
        # CAE válido (no expirado)
        future_date = (datetime.now() + timedelta(days=10)).strftime('%Y%m%d')
        self.assertTrue(self._is_cae_not_expired(future_date))
        
        # CAE expirado
        past_date = (datetime.now() - timedelta(days=1)).strftime('%Y%m%d')
        self.assertFalse(self._is_cae_not_expired(past_date))
    
    def _is_valid_cae_format(self, cae: str) -> bool:
        """Valida formato de CAE"""
        return cae.isdigit() and len(cae) == 14
    
    def _is_cae_not_expired(self, expiration_date_str: str) -> bool:
        """Valida que CAE no esté expirado"""
        try:
            expiration_date = datetime.strptime(expiration_date_str, '%Y%m%d').date()
            return expiration_date > date.today()
        except ValueError:
            return False


class TestInvoiceNumbering(TestCase):
    """Tests para numeración de facturas"""
    
    def setUp(self):
        # Crear hotel de prueba
        from apps.core.models import Hotel
        from apps.locations.models import City, State, Country
        self.country = Country.objects.create(name='Argentina', code2='AR', code3='ARG')
        self.state = State.objects.create(name='Buenos Aires', country=self.country)
        self.city = City.objects.create(name='Buenos Aires', state=self.state)
        self.hotel = Hotel.objects.create(
            name='Hotel Test',
            address='Av. Test 123',
            city=self.city,
            state=self.state,
            country=self.country,
            tax_id='20123456789'
        )
        
        # Crear configuración AFIP de prueba
        self.afip_config = AfipConfig.objects.create(
            hotel=self.hotel,
            cuit=AFIP_TEST_CONFIG['TEST_CUIT'],
            point_of_sale=AFIP_TEST_CONFIG['TEST_POINT_OF_SALE'],
            environment='test',
            certificate_path=AFIP_TEST_CONFIG['TEST_CERTIFICATE_PATH'],
            private_key_path=AFIP_TEST_CONFIG['TEST_PRIVATE_KEY_PATH'],
        )
    
    def test_invoice_number_generation(self):
        """Test de generación de números de factura"""
        # Generar primer número
        next_number = self.afip_config.get_next_invoice_number()
        self.assertEqual(next_number, 1)
        
        # Formatear número
        formatted = self.afip_config.format_invoice_number(next_number)
        self.assertEqual(formatted, "0001-00000001")
        
        # Actualizar número
        self.afip_config.update_invoice_number(next_number)
        self.assertEqual(self.afip_config.last_invoice_number, 1)
        
        # Generar siguiente número
        next_number = self.afip_config.get_next_invoice_number()
        self.assertEqual(next_number, 2)
        
        formatted = self.afip_config.format_invoice_number(next_number)
        self.assertEqual(formatted, "0001-00000002")
    
    def test_invoice_number_format(self):
        """Test de formato de números de factura"""
        # Probar diferentes números
        test_cases = [
            (1, "0001-00000001"),
            (10, "0001-00000010"),
            (100, "0001-00000100"),
            (1000, "0001-00001000"),
            (10000, "0001-00010000"),
        ]
        
        for number, expected_format in test_cases:
            formatted = self.afip_config.format_invoice_number(number)
            self.assertEqual(formatted, expected_format)
    
    def test_consecutive_numbering(self):
        """Test de numeración consecutiva"""
        # Generar varios números consecutivos
        numbers = []
        for i in range(5):
            next_number = self.afip_config.get_next_invoice_number()
            numbers.append(next_number)
            self.afip_config.update_invoice_number(next_number)
        
        # Verificar que son consecutivos
        expected_numbers = [1, 2, 3, 4, 5]
        self.assertEqual(numbers, expected_numbers)
