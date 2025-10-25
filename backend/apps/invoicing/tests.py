"""
Tests para el módulo de facturación
"""
from django.test import TestCase
from django.contrib.auth.models import User
from decimal import Decimal
from datetime import date, timedelta
from django.utils import timezone

from apps.core.models import Hotel
from apps.enterprises.models import Enterprise
from apps.rooms.models import Room
from apps.reservations.models import Reservation
from apps.locations.models import Country, State, City
from .models import AfipConfig, Invoice, InvoiceItem, InvoiceType, InvoiceStatus, TaxCondition


class AfipConfigModelTest(TestCase):
    """Tests para el modelo AfipConfig"""
    
    def setUp(self):
        """Configuración inicial para los tests"""
        # Crear país, estado y ciudad
        self.country = Country.objects.create(
            code2='AR', code3='ARG', name='Argentina',
            timezone='America/Argentina/Buenos_Aires'
        )
        self.state = State.objects.create(
            country=self.country, name='Buenos Aires'
        )
        self.city = City.objects.create(
            state=self.state, name='Buenos Aires'
        )
        
        # Crear empresa
        self.enterprise = Enterprise.objects.create(
            name='Hotel Test S.A.',
            legal_name='Hotel Test Sociedad Anónima',
            tax_id='30-12345678-9',
            country=self.country,
            state=self.state,
            city=self.city
        )
        
        # Crear hotel
        self.hotel = Hotel.objects.create(
            name='Hotel Test',
            legal_name='Hotel Test S.A.',
            tax_id='30-12345678-9',
            country=self.country,
            state=self.state,
            city=self.city,
            enterprise=self.enterprise
        )
    
    def test_create_afip_config(self):
        """Test crear configuración AFIP"""
        config = AfipConfig.objects.create(
            hotel=self.hotel,
            cuit='30123456789',
            tax_condition=TaxCondition.RESPONSABLE_INSCRIPTO,
            point_of_sale=1,
            certificate_path='/path/to/cert.crt',
            private_key_path='/path/to/key.key',
            environment='test'
        )
        
        self.assertEqual(config.hotel, self.hotel)
        self.assertEqual(config.cuit, '30123456789')
        self.assertEqual(config.tax_condition, TaxCondition.RESPONSABLE_INSCRIPTO)
        self.assertEqual(config.point_of_sale, 1)
        self.assertEqual(config.environment, 'test')
        self.assertTrue(config.is_active)
    
    def test_get_next_invoice_number(self):
        """Test obtener próximo número de factura"""
        config = AfipConfig.objects.create(
            hotel=self.hotel,
            cuit='30123456789',
            point_of_sale=1
        )
        
        self.assertEqual(config.get_next_invoice_number(), 1)
        
        config.last_invoice_number = 5
        config.save()
        self.assertEqual(config.get_next_invoice_number(), 6)
    
    def test_format_invoice_number(self):
        """Test formatear número de factura"""
        config = AfipConfig.objects.create(
            hotel=self.hotel,
            cuit='30123456789',
            point_of_sale=1
        )
        
        formatted = config.format_invoice_number(1234)
        self.assertEqual(formatted, '0001-00001234')
        
        config.point_of_sale = 10
        config.save()
        formatted = config.format_invoice_number(5678)
        self.assertEqual(formatted, '0010-00005678')
    
    def test_validate_cuit(self):
        """Test validación de CUIT"""
        config = AfipConfig(
            hotel=self.hotel,
            cuit='123',  # CUIT inválido
            point_of_sale=1
        )
        
        with self.assertRaises(Exception):
            config.clean()
    
    def test_validate_point_of_sale(self):
        """Test validación de punto de venta"""
        config = AfipConfig(
            hotel=self.hotel,
            cuit='30123456789',
            point_of_sale=10000  # Punto de venta inválido
        )
        
        with self.assertRaises(Exception):
            config.clean()


class InvoiceModelTest(TestCase):
    """Tests para el modelo Invoice"""
    
    def setUp(self):
        """Configuración inicial para los tests"""
        # Crear datos base
        self.country = Country.objects.create(
            code2='AR', code3='ARG', name='Argentina'
        )
        self.state = State.objects.create(
            country=self.country, name='Buenos Aires'
        )
        self.city = City.objects.create(
            state=self.state, name='Buenos Aires'
        )
        
        self.enterprise = Enterprise.objects.create(
            name='Hotel Test S.A.',
            country=self.country,
            state=self.state,
            city=self.city
        )
        
        self.hotel = Hotel.objects.create(
            name='Hotel Test',
            country=self.country,
            state=self.state,
            city=self.city,
            enterprise=self.enterprise
        )
        
        self.room = Room.objects.create(
            name='Habitación 101',
            hotel=self.hotel,
            floor=1,
            room_type='single',
            number=101,
            base_price=Decimal('100.00'),
            capacity=1,
            max_capacity=2
        )
        
        self.reservation = Reservation.objects.create(
            hotel=self.hotel,
            room=self.room,
            guests=1,
            check_in=date.today(),
            check_out=date.today() + timedelta(days=1),
            total_price=Decimal('100.00')
        )
        
        self.afip_config = AfipConfig.objects.create(
            hotel=self.hotel,
            cuit='30123456789',
            point_of_sale=1
        )
    
    def test_create_invoice(self):
        """Test crear factura"""
        invoice = Invoice.objects.create(
            reservation=self.reservation,
            hotel=self.hotel,
            type=InvoiceType.FACTURA_B,
            number='0001-00000001',
            issue_date=date.today(),
            total=Decimal('121.00'),
            net_amount=Decimal('100.00'),
            vat_amount=Decimal('21.00'),
            client_name='Juan Pérez',
            client_document_type='96',
            client_document_number='12345678',
            client_tax_condition=TaxCondition.CONSUMIDOR_FINAL
        )
        
        self.assertEqual(invoice.reservation, self.reservation)
        self.assertEqual(invoice.hotel, self.hotel)
        self.assertEqual(invoice.type, InvoiceType.FACTURA_B)
        self.assertEqual(invoice.total, Decimal('121.00'))
        self.assertEqual(invoice.status, InvoiceStatus.DRAFT)
    
    def test_invoice_validation(self):
        """Test validaciones de factura"""
        # Test total positivo
        invoice = Invoice(
            reservation=self.reservation,
            hotel=self.hotel,
            type=InvoiceType.FACTURA_B,
            number='0001-00000001',
            issue_date=date.today(),
            total=Decimal('-100.00'),  # Total negativo
            net_amount=Decimal('100.00'),
            vat_amount=Decimal('21.00'),
            client_name='Juan Pérez',
            client_document_type='96',
            client_document_number='12345678'
        )
        
        with self.assertRaises(Exception):
            invoice.clean()
    
    def test_get_pdf_url(self):
        """Test obtener URL del PDF"""
        invoice = Invoice.objects.create(
            reservation=self.reservation,
            hotel=self.hotel,
            type=InvoiceType.FACTURA_B,
            number='0001-00000001',
            issue_date=date.today(),
            total=Decimal('121.00'),
            net_amount=Decimal('100.00'),
            vat_amount=Decimal('21.00'),
            client_name='Juan Pérez',
            client_document_type='96',
            client_document_number='12345678'
        )
        
        # Sin PDF
        self.assertIsNone(invoice.get_pdf_url())
        
        # Con PDF URL
        invoice.pdf_url = 'https://example.com/invoice.pdf'
        invoice.save()
        self.assertEqual(invoice.get_pdf_url(), 'https://example.com/invoice.pdf')
    
    def test_is_approved(self):
        """Test verificar si factura está aprobada"""
        invoice = Invoice.objects.create(
            reservation=self.reservation,
            hotel=self.hotel,
            type=InvoiceType.FACTURA_B,
            number='0001-00000001',
            issue_date=date.today(),
            total=Decimal('121.00'),
            net_amount=Decimal('100.00'),
            vat_amount=Decimal('21.00'),
            client_name='Juan Pérez',
            client_document_type='96',
            client_document_number='12345678'
        )
        
        # Sin CAE
        self.assertFalse(invoice.is_approved())
        
        # Con CAE
        invoice.cae = '12345678901234'
        invoice.status = InvoiceStatus.APPROVED
        invoice.save()
        self.assertTrue(invoice.is_approved())
    
    def test_can_be_resent(self):
        """Test verificar si factura puede ser reenviada"""
        invoice = Invoice.objects.create(
            reservation=self.reservation,
            hotel=self.hotel,
            type=InvoiceType.FACTURA_B,
            number='0001-00000001',
            issue_date=date.today(),
            total=Decimal('121.00'),
            net_amount=Decimal('100.00'),
            vat_amount=Decimal('21.00'),
            client_name='Juan Pérez',
            client_document_type='96',
            client_document_number='12345678'
        )
        
        # Estado draft
        self.assertTrue(invoice.can_be_resent())
        
        # Estado error con pocos reintentos
        invoice.status = InvoiceStatus.ERROR
        invoice.retry_count = 1
        invoice.save()
        self.assertTrue(invoice.can_be_resent())
        
        # Estado error con muchos reintentos
        invoice.retry_count = 3
        invoice.save()
        self.assertFalse(invoice.can_be_resent())
        
        # Estado aprobado
        invoice.status = InvoiceStatus.APPROVED
        invoice.save()
        self.assertFalse(invoice.can_be_resent())


class InvoiceItemModelTest(TestCase):
    """Tests para el modelo InvoiceItem"""
    
    def setUp(self):
        """Configuración inicial para los tests"""
        # Crear datos base (simplificado)
        self.country = Country.objects.create(
            code2='AR', code3='ARG', name='Argentina'
        )
        self.state = State.objects.create(
            country=self.country, name='Buenos Aires'
        )
        self.city = City.objects.create(
            state=self.state, name='Buenos Aires'
        )
        
        self.enterprise = Enterprise.objects.create(
            name='Hotel Test S.A.',
            country=self.country,
            state=self.state,
            city=self.city
        )
        
        self.hotel = Hotel.objects.create(
            name='Hotel Test',
            country=self.country,
            state=self.state,
            city=self.city,
            enterprise=self.enterprise
        )
        
        self.room = Room.objects.create(
            name='Habitación 101',
            hotel=self.hotel,
            floor=1,
            room_type='single',
            number=101,
            base_price=Decimal('100.00')
        )
        
        self.reservation = Reservation.objects.create(
            hotel=self.hotel,
            room=self.room,
            guests=1,
            check_in=date.today(),
            check_out=date.today() + timedelta(days=1),
            total_price=Decimal('100.00')
        )
        
        self.invoice = Invoice.objects.create(
            reservation=self.reservation,
            hotel=self.hotel,
            type=InvoiceType.FACTURA_B,
            number='0001-00000001',
            issue_date=date.today(),
            total=Decimal('121.00'),
            net_amount=Decimal('100.00'),
            vat_amount=Decimal('21.00'),
            client_name='Juan Pérez',
            client_document_type='96',
            client_document_number='12345678'
        )
    
    def test_create_invoice_item(self):
        """Test crear item de factura"""
        item = InvoiceItem.objects.create(
            invoice=self.invoice,
            description='Hospedaje - Habitación 101',
            quantity=Decimal('1.00'),
            unit_price=Decimal('100.00'),
            vat_rate=Decimal('21.00'),
            afip_code='1'
        )
        
        self.assertEqual(item.invoice, self.invoice)
        self.assertEqual(item.description, 'Hospedaje - Habitación 101')
        self.assertEqual(item.subtotal, Decimal('100.00'))
        self.assertEqual(item.vat_amount, Decimal('21.00'))
        self.assertEqual(item.total, Decimal('121.00'))
    
    def test_auto_calculate_amounts(self):
        """Test cálculo automático de montos"""
        item = InvoiceItem(
            invoice=self.invoice,
            description='Hospedaje - Habitación 101',
            quantity=Decimal('2.00'),
            unit_price=Decimal('100.00'),
            vat_rate=Decimal('21.00'),
            afip_code='1'
        )
        item.save()
        
        # Verificar cálculos automáticos
        self.assertEqual(item.subtotal, Decimal('200.00'))  # 2 * 100
        self.assertEqual(item.vat_amount, Decimal('42.00'))  # 200 * 0.21
        self.assertEqual(item.total, Decimal('242.00'))  # 200 + 42
