"""
Servicio para generar PDFs de facturas
Utiliza el generador de PDFs existente de AlojaSys y el nuevo servicio fiscal
"""
import os
import logging
from datetime import datetime
from decimal import Decimal
from django.conf import settings
from django.utils import timezone
from .invoice_pdf_service import InvoicePDFService, InvoicePDFError

logger = logging.getLogger(__name__)


class InvoiceGeneratorService:
    """Servicio para generar PDFs de facturas"""
    
    def __init__(self):
        self.pdf_generator = None
        self.fiscal_pdf_service = InvoicePDFService()
        self._init_pdf_generator()
    
    def _init_pdf_generator(self):
        """Inicializa el generador de PDFs"""
        try:
            from apps.payments.services.pdf_generator import ModernPDFGenerator
            self.pdf_generator = ModernPDFGenerator()
        except ImportError as e:
            logger.error(f"Error importando generador de PDFs: {e}")
            self.pdf_generator = None
    
    def generate_invoice_pdf(self, invoice) -> str:
        """
        Genera PDF de una factura
        
        Args:
            invoice: Instancia de Invoice
            
        Returns:
            str: Ruta del archivo PDF generado
        """
        try:
            if not self.pdf_generator:
                raise Exception("Generador de PDFs no disponible")
            
            # Preparar datos para el PDF
            pdf_data = self._prepare_invoice_data(invoice)
            
            # Generar nombre de archivo
            filename = f"factura_{invoice.number}_{invoice.issue_date.strftime('%Y%m%d')}.pdf"
            
            # Generar PDF
            pdf_path = self.pdf_generator.generate(pdf_data, filename)
            
            logger.info(f"PDF de factura generado: {pdf_path}")
            return pdf_path
            
        except Exception as e:
            logger.error(f"Error generando PDF de factura: {e}")
            raise
    
    def generate_fiscal_pdf(self, invoice) -> str:
        """
        Genera PDF fiscal con CAE usando el nuevo servicio
        
        Args:
            invoice: Instancia de Invoice
            
        Returns:
            str: Ruta del archivo PDF generado
        """
        try:
            logger.info(f"Generando PDF fiscal para factura {invoice.number}")
            
            # Usar el servicio de PDF fiscal
            return self.fiscal_pdf_service.generate_pdf(invoice)
            
        except InvoicePDFError as e:
            logger.error(f"Error generando PDF fiscal para factura {invoice.number}: {str(e)}")
            raise Exception(f"Error generando PDF fiscal: {str(e)}")
        except Exception as e:
            logger.error(f"Error inesperado generando PDF fiscal para factura {invoice.number}: {str(e)}")
            raise Exception(f"Error inesperado generando PDF fiscal: {str(e)}")
    
    def generate_pdf(self, invoice) -> str:
        """
        Genera PDF de factura (fiscal si tiene CAE, normal si no)
        
        Args:
            invoice: Instancia de Invoice
            
        Returns:
            str: Ruta del archivo PDF generado
        """
        try:
            # Si tiene CAE, generar PDF fiscal
            if invoice.cae and invoice.status == 'approved':
                return self.generate_fiscal_pdf(invoice)
            else:
                # Generar PDF normal
                return self.generate_invoice_pdf(invoice)
                
        except Exception as e:
            logger.error(f"Error generando PDF para factura {invoice.number}: {str(e)}")
            raise
    
    def _prepare_invoice_data(self, invoice) -> dict:
        """
        Prepara los datos de la factura para el generador de PDFs
        
        Args:
            invoice: Instancia de Invoice
            
        Returns:
            dict: Datos formateados para el PDF
        """
        # Datos del hotel
        hotel = invoice.hotel
        hotel_data = {
            'name': hotel.name,
            'legal_name': hotel.legal_name or hotel.name,
            'tax_id': hotel.tax_id or '',
            'address': hotel.address or '',
            'city': hotel.city.name if hotel.city else '',
            'state': hotel.state.name if hotel.state else '',
            'country': hotel.country.name if hotel.country else '',
            'phone': hotel.phone or '',
            'email': hotel.email or '',
        }
        
        # Datos del cliente
        client_data = {
            'name': invoice.client_name,
            'document_type': self._get_document_type_name(invoice.client_document_type),
            'document_number': invoice.client_document_number,
            'tax_condition': invoice.get_client_tax_condition_display(),
            'address': invoice.client_address or '',
        }
        
        # Datos de la factura
        invoice_data = {
            'number': invoice.number,
            'type': invoice.get_type_display(),
            'issue_date': invoice.issue_date.strftime('%d/%m/%Y'),
            'cae': invoice.cae or 'Pendiente',
            'cae_expiration': invoice.cae_expiration.strftime('%d/%m/%Y') if invoice.cae_expiration else '',
            'status': invoice.get_status_display(),
            'currency': invoice.currency,
        }
        
        # Items de la factura
        items_data = []
        for item in invoice.items.all():
            items_data.append({
                'description': item.description,
                'quantity': str(item.quantity),
                'unit_price': f"${item.unit_price:,.2f}",
                'subtotal': f"${item.subtotal:,.2f}",
                'vat_rate': f"{item.vat_rate}%",
                'vat_amount': f"${item.vat_amount:,.2f}",
                'total': f"${item.total:,.2f}",
            })
        
        # Totales
        totals_data = {
            'net_amount': f"${invoice.net_amount:,.2f}",
            'vat_amount': f"${invoice.vat_amount:,.2f}",
            'total': f"${invoice.total:,.2f}",
        }
        
        # Datos de la reserva (si existe)
        reservation_data = {}
        if invoice.reservation:
            reservation = invoice.reservation
            reservation_data = {
                'id': reservation.id,
                'room': reservation.room.name,
                'check_in': reservation.check_in.strftime('%d/%m/%Y'),
                'check_out': reservation.check_out.strftime('%d/%m/%Y'),
                'guests': reservation.guests,
                'nights': (reservation.check_out - reservation.check_in).days,
            }
        
        return {
            'hotel': hotel_data,
            'client': client_data,
            'invoice': invoice_data,
            'items': items_data,
            'totals': totals_data,
            'reservation': reservation_data,
            'generated_at': timezone.now().strftime('%d/%m/%Y %H:%M'),
        }
    
    def _get_document_type_name(self, document_type: str) -> str:
        """
        Convierte código de tipo de documento a nombre legible
        
        Args:
            document_type: Código del tipo de documento
            
        Returns:
            str: Nombre del tipo de documento
        """
        type_mapping = {
            '80': 'CUIT',
            '86': 'CUIL',
            '87': 'CDI',
            '96': 'DNI',
            '99': 'Otro',
        }
        return type_mapping.get(document_type, 'DNI')
    
    def generate_invoice_summary_pdf(self, invoices: list) -> str:
        """
        Genera PDF con resumen de múltiples facturas
        
        Args:
            invoices: Lista de instancias de Invoice
            
        Returns:
            str: Ruta del archivo PDF generado
        """
        try:
            if not self.pdf_generator:
                raise Exception("Generador de PDFs no disponible")
            
            # Preparar datos del resumen
            summary_data = self._prepare_summary_data(invoices)
            
            # Generar nombre de archivo
            filename = f"resumen_facturas_{timezone.now().strftime('%Y%m%d_%H%M')}.pdf"
            
            # Generar PDF
            pdf_path = self.pdf_generator.generate(summary_data, filename)
            
            logger.info(f"PDF de resumen generado: {pdf_path}")
            return pdf_path
            
        except Exception as e:
            logger.error(f"Error generando PDF de resumen: {e}")
            raise
    
    def _prepare_summary_data(self, invoices: list) -> dict:
        """
        Prepara los datos del resumen de facturas
        
        Args:
            invoices: Lista de instancias de Invoice
            
        Returns:
            dict: Datos formateados para el PDF
        """
        # Calcular totales
        total_invoices = len(invoices)
        total_amount = sum(invoice.total for invoice in invoices)
        approved_invoices = len([inv for inv in invoices if inv.status == 'approved'])
        pending_invoices = len([inv for inv in invoices if inv.status in ['draft', 'sent']])
        error_invoices = len([inv for inv in invoices if inv.status == 'error'])
        
        # Agrupar por tipo
        invoices_by_type = {}
        for invoice in invoices:
            invoice_type = invoice.get_type_display()
            if invoice_type not in invoices_by_type:
                invoices_by_type[invoice_type] = 0
            invoices_by_type[invoice_type] += 1
        
        # Agrupar por estado
        invoices_by_status = {}
        for invoice in invoices:
            status = invoice.get_status_display()
            if status not in invoices_by_status:
                invoices_by_status[status] = 0
            invoices_by_status[status] += 1
        
        # Datos de las facturas
        invoices_data = []
        for invoice in invoices:
            invoices_data.append({
                'number': invoice.number,
                'type': invoice.get_type_display(),
                'client_name': invoice.client_name,
                'issue_date': invoice.issue_date.strftime('%d/%m/%Y'),
                'status': invoice.get_status_display(),
                'total': f"${invoice.total:,.2f}",
                'cae': invoice.cae or 'Pendiente',
            })
        
        return {
            'title': 'Resumen de Facturas',
            'period': f"Generado el {timezone.now().strftime('%d/%m/%Y %H:%M')}",
            'summary': {
                'total_invoices': total_invoices,
                'total_amount': f"${total_amount:,.2f}",
                'approved_invoices': approved_invoices,
                'pending_invoices': pending_invoices,
                'error_invoices': error_invoices,
            },
            'invoices_by_type': invoices_by_type,
            'invoices_by_status': invoices_by_status,
            'invoices': invoices_data,
        }
