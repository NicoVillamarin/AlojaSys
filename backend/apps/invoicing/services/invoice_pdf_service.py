"""
Servicio de generación de PDFs fiscales para facturas electrónicas argentinas.
Cumple con normativas AFIP y genera documentos profesionales.
"""


class InvoicePDFError(Exception):
    """Excepción para errores en la generación de PDFs"""
    pass

import os
import io
import qrcode
from decimal import Decimal
from datetime import datetime
from typing import Optional, List, Tuple
from django.conf import settings
from django.core.files.base import ContentFile
from django.utils import timezone

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm, mm
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT, TA_JUSTIFY
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    Image, PageBreak, KeepTogether
)
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader

from apps.invoicing.models import Invoice, InvoiceItem, AfipConfig
from django.template.loader import render_to_string

# Import condicional de WeasyPrint para evitar errores al arrancar
try:
    from weasyprint import HTML
    WEASYPRINT_AVAILABLE = True
except ImportError:
    WEASYPRINT_AVAILABLE = False
    HTML = None


class InvoicePDFService:
    """
    Servicio para generar PDFs de facturas electrónicas argentinas.
    Cumple con normativas AFIP y genera documentos profesionales.
    """
    
    def __init__(self):
        self.page_width, self.page_height = A4
        self.margin = 2 * cm
        self.content_width = self.page_width - (2 * self.margin)
        
        # Estilos para el PDF
        self.styles = getSampleStyleSheet()
        self._setup_custom_styles()
    
    def _setup_custom_styles(self):
        """Configura estilos personalizados para el PDF"""
        
        # Título principal
        self.styles.add(ParagraphStyle(
            name='InvoiceTitle',
            parent=self.styles['Heading1'],
            fontSize=18,
            spaceAfter=12,
            alignment=TA_CENTER,
            textColor=colors.darkblue,
            fontName='Helvetica-Bold'
        ))
        
        # Subtítulos
        self.styles.add(ParagraphStyle(
            name='InvoiceSubtitle',
            parent=self.styles['Heading2'],
            fontSize=14,
            spaceAfter=8,
            alignment=TA_LEFT,
            textColor=colors.darkblue,
            fontName='Helvetica-Bold'
        ))
        
        # Datos del emisor/comprador
        self.styles.add(ParagraphStyle(
            name='InvoiceData',
            parent=self.styles['Normal'],
            fontSize=10,
            spaceAfter=4,
            alignment=TA_LEFT,
            fontName='Helvetica'
        ))
        
        # Datos fiscales importantes
        self.styles.add(ParagraphStyle(
            name='FiscalData',
            parent=self.styles['Normal'],
            fontSize=11,
            spaceAfter=6,
            alignment=TA_LEFT,
            fontName='Helvetica-Bold',
            textColor=colors.darkred
        ))
        
        # CAE y autorización
        self.styles.add(ParagraphStyle(
            name='CAEData',
            parent=self.styles['Normal'],
            fontSize=12,
            spaceAfter=8,
            alignment=TA_CENTER,
            fontName='Helvetica-Bold',
            textColor=colors.darkgreen
        ))
    
    def generate_pdf(self, invoice: Invoice) -> str:
        """Genera PDF fiscal (intenta HTML->PDF con pdfkit; fallback ReportLab)."""
        try:
            filename = f"factura_{invoice.number}_{invoice.issue_date.strftime('%Y%m%d')}.pdf"
            file_path = os.path.join(settings.MEDIA_ROOT, 'invoices', 'pdf', filename)
            os.makedirs(os.path.dirname(file_path), exist_ok=True)

            html = self._render_html(invoice)
            try:
                if WEASYPRINT_AVAILABLE and HTML:
                    HTML(string=html, base_url=os.getcwd()).write_pdf(file_path)
                else:
                    raise Exception("WeasyPrint no disponible")
            except Exception:
                # Fallback a ReportLab
                buffer = io.BytesIO()
                doc = SimpleDocTemplate(
                    buffer,
                    pagesize=A4,
                    rightMargin=self.margin,
                    leftMargin=self.margin,
                    topMargin=self.margin,
                    bottomMargin=self.margin
                )
                story = self._build_pdf_content(invoice)
                doc.build(story, onFirstPage=self._add_header, onLaterPages=self._add_header)
                pdf_content = buffer.getvalue()
                buffer.close()
                with open(file_path, 'wb') as f:
                    f.write(pdf_content)

            invoice.pdf_file = f'invoices/pdf/{filename}'
            invoice.save(update_fields=['pdf_file'])
            return file_path

        except Exception as e:
            raise Exception(f"Error generando PDF: {str(e)}")

    def _render_html(self, invoice: Invoice) -> str:
        hotel = invoice.hotel
        try:
            config = hotel.afip_config
        except AfipConfig.DoesNotExist:
            config = None
        context = {
            'invoice': invoice,
            'hotel': hotel,
            'pos': str(config.point_of_sale) if config else '-',
            'cuit': config.cuit if config else '-',
            'gross_income': getattr(config, 'gross_income', ''),
            'activity_start_date': getattr(config, 'activity_start_date', None),
            'hotel_tax_condition': self._get_tax_condition_name(config.tax_condition if config else '5'),
            'client_tax_condition': self._get_tax_condition_name(invoice.client_tax_condition),
            'client_document_number': invoice.client_document_number,
            'items': [
                {
                    'code': getattr(it, 'afip_code', ''),
                    'description': it.description,
                    'quantity': float(getattr(it, 'quantity', 1)),
                    'unit_price': float(getattr(it, 'unit_price', invoice.net_amount or 0)),
                    'total': float(getattr(it, 'total', (getattr(it, 'quantity', 1) * getattr(it, 'unit_price', 0)))),
                } for it in invoice.items.all()
            ] or [
                {
                    'code': '321',
                    'description': f"Hospedaje - {invoice.reservation.room.name if invoice.reservation else 'Servicio'}",
                    'quantity': 1.0,
                    'unit_price': float(invoice.net_amount or 0),
                    'total': float(invoice.total or 0),
                }
            ],
            'subtotal': float(invoice.net_amount or Decimal('0')),
            'total': float(invoice.total or Decimal('0')),
            'period_from': invoice.issue_date,
            'period_to': invoice.issue_date,
            'due_date': invoice.issue_date,
        }
        return render_to_string('invoicing/afipsdk_invoice.html', context)
    
    def _build_pdf_content(self, invoice: Invoice) -> List:
        """Construye el contenido completo del PDF"""
        story = []
        
        # 1. Título del comprobante
        story.append(self._create_invoice_title(invoice))
        story.append(Spacer(1, 12))
        
        # 2. Cabecera compuesta (logo/razón social + bloque a la derecha + banda periodo)
        story.append(self._create_compact_header(invoice))
        story.append(Spacer(1, 6))
        
        # 3. Datos del comprador
        story.append(self._create_buyer_section(invoice))
        story.append(Spacer(1, 12))
        
        # 4. Datos de la factura
        story.append(self._create_invoice_data_section(invoice))
        story.append(Spacer(1, 12))
        
        # 5. Tabla de items
        story.append(self._create_items_table(invoice))
        story.append(Spacer(1, 12))
        
        # 6. Totales
        story.append(self._create_totals_section(invoice))
        story.append(Spacer(1, 12))
        
        # 7. Autorización AFIP
        story.append(self._create_afip_authorization_section(invoice))
        story.append(Spacer(1, 12))
        
        # 8. (QR removido por requerimiento actual)
        # story.append(self._create_qr_code_section(invoice))
        
        return story
    
    def _create_invoice_title(self, invoice: Invoice) -> Paragraph:
        """Crea el título del comprobante"""
        invoice_type_names = {
            'A': 'FACTURA A',
            'B': 'FACTURA B', 
            'C': 'FACTURA C',
            'E': 'FACTURA E',
            'NC': 'NOTA DE CRÉDITO',
            'ND': 'NOTA DE DÉBITO'
        }
        
        title = invoice_type_names.get(invoice.type, 'COMPROBANTE')
        return Paragraph(f"<b>{title}</b>", self.styles['InvoiceTitle'])
    
    def _create_issuer_section(self, invoice: Invoice) -> Table:
        """Crea sección de datos del emisor"""
        hotel = invoice.hotel
        try:
            config = hotel.afip_config
        except AfipConfig.DoesNotExist:
            config = None
        
        issuer_data = [
            [Paragraph('<b>EMISOR</b>', self.styles['InvoiceSubtitle']), ''],
            ['Razón Social:', hotel.legal_name or hotel.name],
            ['CUIT:', config.cuit if config else 'N/A'],
            ['Domicilio:', hotel.address],
            ['Condición IVA:', self._get_tax_condition_name(config.tax_condition if config else '5')],
        ]
        
        table = Table(issuer_data, colWidths=[self.content_width * 0.3, self.content_width * 0.7])
        table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
            ('FONTNAME', (0, 1), (0, -1), 'Helvetica-Bold'),
            ('FONTNAME', (1, 1), (1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 10),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('LEFTPADDING', (0, 0), (-1, -1), 6),
            ('RIGHTPADDING', (0, 0), (-1, -1), 6),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ]))
        
        return table

    def _create_compact_header(self, invoice: Invoice) -> Table:
        """Crea cabecera estilo ejemplo: izquierda datos empresa, centro cuadro letra, derecha info básica."""
        hotel = invoice.hotel
        try:
            config = hotel.afip_config
        except AfipConfig.DoesNotExist:
            config = None

        # Columna izquierda (razón social y domicilio comercial)
        left = [
            [Paragraph('<b>%s</b>' % (hotel.legal_name or hotel.name), self.styles['InvoiceSubtitle'])],
            ['Razón social: %s' % (hotel.legal_name or hotel.name)],
            ['Domicilio Comercial: %s' % (hotel.address or '-')],
            ['Condición Frente al IVA: %s' % self._get_tax_condition_name(config.tax_condition if config else '5')],
        ]
        left_table = Table(left, colWidths=[self.content_width * 0.45])
        left_table.setStyle(TableStyle([
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('LEADING', (0, 0), (-1, -1), 11),
        ]))

        # Columna centro (cuadro letra)
        box_size = 24
        letter_table = Table([[Paragraph('<b>%s</b>' % (invoice.type or 'B'), self.styles['InvoiceSubtitle'])]],
                              colWidths=[box_size], rowHeights=[box_size])
        letter_table.setStyle(TableStyle([
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))

        # Columna derecha (datos básicos)
        right = [
            [Paragraph('<b>Factura</b>', self.styles['InvoiceSubtitle'])],
            ['Punto de Venta: %s    Comp. Nro: %s' % (str(config.point_of_sale) if config else '-', invoice.number or '-')],
            ['Fecha de Emisión: %s' % invoice.issue_date.strftime('%d/%m/%Y')],
            ['CUIT: %s' % (config.cuit if config else '-')],
        ]
        right_table = Table(right, colWidths=[self.content_width * 0.45])
        right_table.setStyle(TableStyle([
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('LEADING', (0, 0), (-1, -1), 11),
        ]))

        header = Table([[left_table, letter_table, right_table]],
                       colWidths=[self.content_width * 0.45, 30, self.content_width * 0.45])
        header.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ]))

        # Banda de período (placeholder con fecha emisión como período)
        period = Table([["Período Facturado Desde: %s   Hasta: %s   Fecha de Vto. para el pago: %s" % (
            invoice.issue_date.strftime('%d/%m/%Y'),
            invoice.issue_date.strftime('%d/%m/%Y'),
            invoice.issue_date.strftime('%d/%m/%Y')
        )]], colWidths=[self.content_width])
        period.setStyle(TableStyle([
            ('FONTSIZE', (0, 0), (-1, -1), 8.5),
            ('BACKGROUND', (0, 0), (-1, -1), colors.whitesmoke),
            ('BOX', (0, 0), (-1, -1), 0.5, colors.lightgrey),
            ('LEFTPADDING', (0, 0), (-1, -1), 6),
            ('RIGHTPADDING', (0, 0), (-1, -1), 6),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ]))

        return KeepTogether([header, Spacer(1, 6), period])
    
    def _create_buyer_section(self, invoice: Invoice) -> Table:
        """Crea sección de datos del comprador"""
        buyer_data = [
            [Paragraph('<b>COMPRADOR</b>', self.styles['InvoiceSubtitle']), ''],
            ['Nombre/Razón Social:', invoice.client_name],
            ['Documento:', f"{self._get_document_type_name(invoice.client_document_type)} {invoice.client_document_number}"],
            ['Condición IVA:', self._get_tax_condition_name(invoice.client_tax_condition)],
            ['Domicilio:', invoice.client_address or 'No especificado'],
        ]
        
        table = Table(buyer_data, colWidths=[self.content_width * 0.3, self.content_width * 0.7])
        table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
            ('FONTNAME', (0, 1), (0, -1), 'Helvetica-Bold'),
            ('FONTNAME', (1, 1), (1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 10),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('LEFTPADDING', (0, 0), (-1, -1), 6),
            ('RIGHTPADDING', (0, 0), (-1, -1), 6),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ]))
        
        return table
    
    def _create_invoice_data_section(self, invoice: Invoice) -> Table:
        """Crea sección de datos de la factura"""
        try:
            config = invoice.hotel.afip_config
        except AfipConfig.DoesNotExist:
            config = None
        
        invoice_data = [
            [Paragraph('<b>DATOS DEL COMPROBANTE</b>', self.styles['InvoiceSubtitle']), ''],
            ['Número:', invoice.number],
            ['Fecha de Emisión:', invoice.issue_date.strftime('%d/%m/%Y')],
            ['Punto de Venta:', str(config.point_of_sale) if config else 'N/A'],
            ['Moneda:', invoice.currency],
            ['Estado:', self._get_status_name(invoice.status)],
        ]
        
        table = Table(invoice_data, colWidths=[self.content_width * 0.3, self.content_width * 0.7])
        table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
            ('FONTNAME', (0, 1), (0, -1), 'Helvetica-Bold'),
            ('FONTNAME', (1, 1), (1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 10),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('LEFTPADDING', (0, 0), (-1, -1), 6),
            ('RIGHTPADDING', (0, 0), (-1, -1), 6),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ]))
        
        return table
    
    def _create_items_table(self, invoice: Invoice) -> Table:
        """Crea tabla de items de la factura"""
        # Encabezados
        headers = ['Código', 'Producto / Servicio', 'Cantidad', 'U. Medida', 'Precio Unit.', '% Bonif.', 'Imp. Bonif.', 'Subtotal']
        
        # Datos de items
        data = [headers]
        for item in invoice.items.all():
            data.append([
                '321',  # código placeholder
                item.description,
                f"{item.quantity:.2f}",
                'Unidad',
                f"{item.unit_price:.2f}",
                '0,00',
                '0,00',
                f"{item.total:.2f}"
            ])
        
        # Calcular anchos de columna
        col_widths = [
            self.content_width * 0.08,  # Código
            self.content_width * 0.28,  # Producto
            self.content_width * 0.09,  # Cantidad
            self.content_width * 0.09,  # U. Medida
            self.content_width * 0.12,  # Precio Unit.
            self.content_width * 0.08,  # % Bonif.
            self.content_width * 0.12,  # Imp. Bonif.
            self.content_width * 0.14,  # Subtotal
        ]
        
        table = Table(data, colWidths=col_widths)
        table.setStyle(TableStyle([
            # Encabezados
            ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            
            # Datos
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
            ('ALIGN', (1, 1), (-1, -1), 'RIGHT'),  # Números a la derecha
            ('ALIGN', (0, 1), (0, -1), 'LEFT'),    # Descripción a la izquierda
            
            # Alternar colores de filas
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.whitesmoke]),
            
            # Bordes
            ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
            
            # Padding
            ('LEFTPADDING', (0, 0), (-1, -1), 4),
            ('RIGHTPADDING', (0, 0), (-1, -1), 4),
            ('TOPPADDING', (0, 0), (-1, -1), 3),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
        ]))
        
        return table
    
    def _create_totals_section(self, invoice: Invoice) -> Table:
        """Crea sección de totales"""
        totals_data = [
            ['', '', 'Subtotal:', f"{invoice.net_amount:.2f}"],
            ['', '', 'Importe Otros Tributos:', f"0,00"],
            ['', '', 'Importe total:', f"{invoice.total:.2f}"]
        ]
        
        table = Table(totals_data, colWidths=[self.content_width * 0.6, self.content_width * 0.2, self.content_width * 0.1, self.content_width * 0.1])
        table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('ALIGN', (2, 0), (-1, -1), 'RIGHT'),
            ('FONTNAME', (2, 0), (2, -1), 'Helvetica-Bold'),
            ('FONTNAME', (3, 0), (3, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (2, -1), (-1, -1), 12),  # Total en tamaño más grande
            ('TOPPADDING', (0, 0), (-1, -1), 4),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ]))
        
        return table
    
    def _create_afip_authorization_section(self, invoice: Invoice) -> Table:
        """Crea sección de autorización AFIP"""
        if not invoice.cae:
            return Paragraph("Sin autorización AFIP", self.styles['FiscalData'])
        
        auth_data = [
            [Paragraph('<b>AUTORIZACIÓN AFIP</b>', self.styles['InvoiceSubtitle']), ''],
            ['CAE:', invoice.cae],
            ['Vencimiento CAE:', invoice.cae_expiration.strftime('%d/%m/%Y') if invoice.cae_expiration else 'N/A'],
            ['Fecha de Autorización:', invoice.approved_at.strftime('%d/%m/%Y %H:%M') if invoice.approved_at else 'N/A'],
        ]
        
        table = Table(auth_data, colWidths=[self.content_width * 0.3, self.content_width * 0.7])
        table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 0), (-1, 0), colors.darkgreen),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 1), (0, -1), 'Helvetica-Bold'),
            ('FONTNAME', (1, 1), (1, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 1), (-1, -1), 11),
            ('TEXTCOLOR', (0, 1), (-1, -1), colors.darkgreen),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('LEFTPADDING', (0, 0), (-1, -1), 6),
            ('RIGHTPADDING', (0, 0), (-1, -1), 6),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ]))
        
        return table
    
    def _create_qr_code_section(self, invoice: Invoice) -> Table:
        """Crea sección con código QR"""
        try:
            # Generar código QR
            qr_data = self._build_qr_data(invoice)
            qr_image = self._generate_qr_code(qr_data)
            
            # Crear tabla con QR y datos
            qr_table_data = [
                [Paragraph('<b>CÓDIGO QR PARA VERIFICACIÓN AFIP</b>', self.styles['InvoiceSubtitle']), ''],
                ['', ''],  # Espacio para el QR
            ]
            
            table = Table(qr_table_data, colWidths=[self.content_width * 0.7, self.content_width * 0.3])
            
            # Agregar imagen QR
            if qr_image:
                qr_img = Image(qr_image, width=100, height=100)
                table.setStyle(TableStyle([
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, 0), 10),
                    ('BACKGROUND', (0, 0), (-1, 0), colors.lightblue),
                    ('ALIGN', (1, 1), (1, 1), 'CENTER'),
                    ('VALIGN', (1, 1), (1, 1), 'MIDDLE'),
                ]))
                
                # Insertar imagen en la celda
                table._cellvalues[1][1] = qr_img
            
            return table
            
        except Exception as e:
            return Paragraph(f"Error generando QR: {str(e)}", self.styles['Normal'])
    
    def _build_qr_data(self, invoice: Invoice) -> str:
        """Construye datos para código QR según normativas AFIP"""
        try:
            config = invoice.hotel.afip_config
        except AfipConfig.DoesNotExist:
            config = None
        
        # Datos para QR según normativas AFIP
        qr_data = {
            'ver': 1,
            'fecha': invoice.issue_date.strftime('%Y-%m-%d'),
            'cuit': config.cuit if config else '',
            'ptoVta': config.point_of_sale if config else 1,
            'tipoCmp': self._get_afip_comprobante_code(invoice.type),
            'nroCmp': invoice.number.split('-')[-1] if '-' in invoice.number else invoice.number,
            'importe': f"{invoice.total:.2f}",
            'moneda': 'PES',
            'ctz': '1.000000',
            'tipoDocRec': invoice.client_document_type,
            'nroDocRec': invoice.client_document_number,
            'tipoCodAut': 'E',
            'codAut': invoice.cae or '',
        }
        
        # Convertir a string para QR
        qr_string = "|".join([f"{k}={v}" for k, v in qr_data.items()])
        return qr_string
    
    def _generate_qr_code(self, data: str) -> Optional[ImageReader]:
        """Genera código QR como imagen"""
        try:
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=10,
                border=4,
            )
            qr.add_data(data)
            qr.make(fit=True)
            
            # Crear imagen
            qr_image = qr.make_image(fill_color="black", back_color="white")
            
            # Convertir a bytes
            img_buffer = io.BytesIO()
            qr_image.save(img_buffer, format='PNG')
            img_buffer.seek(0)
            
            return ImageReader(img_buffer)
            
        except Exception as e:
            print(f"Error generando QR: {e}")
            return None
    
    def _add_header(self, canvas, doc):
        """Header minimal: línea superior estética (el contenido va en el bloque de cabecera)."""
        canvas.saveState()
        canvas.setStrokeColor(colors.lightgrey)
        canvas.setLineWidth(1)
        canvas.line(self.margin, self.page_height - 40, self.page_width - self.margin, self.page_height - 40)
        canvas.restoreState()
    
    # Métodos auxiliares
    def _get_tax_condition_name(self, code: str) -> str:
        """Obtiene nombre de condición de IVA"""
        conditions = {
            '1': 'Responsable Inscripto',
            '5': 'Consumidor Final',
            '6': 'Exento',
            '7': 'No Responsable',
            '8': 'Monotributo',
            '9': 'Monotributo Social'
        }
        return conditions.get(code, 'No especificado')
    
    def _get_document_type_name(self, code: str) -> str:
        """Obtiene nombre de tipo de documento"""
        types = {
            '80': 'CUIT',
            '96': 'DNI',
            '86': 'CUIL',
            '87': 'CDI',
            '89': 'LE',
            '90': 'LC',
            '91': 'CI',
            '92': 'Dni',
            '93': 'CI',
            '94': 'CI',
            '95': 'CI',
            '99': 'Otro'
        }
        return types.get(code, 'Otro')
    
    def _get_status_name(self, status: str) -> str:
        """Obtiene nombre del estado"""
        statuses = {
            'draft': 'Borrador',
            'sent': 'Enviada a AFIP',
            'approved': 'Aprobada',
            'error': 'Error'
        }
        return statuses.get(status, status)
    
    def _get_afip_comprobante_code(self, invoice_type: str) -> str:
        """Obtiene código AFIP para tipo de comprobante"""
        codes = {
            'A': '1',    # Factura A
            'B': '6',    # Factura B
            'C': '11',   # Factura C
            'E': '19',   # Factura E
            'NC': '3',   # Nota de Crédito A
            'ND': '2',   # Nota de Débito A
        }
        return codes.get(invoice_type, '1')