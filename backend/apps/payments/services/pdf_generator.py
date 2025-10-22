"""
Servicio para generar PDFs de recibos de pagos y refunds
"""
import os
from datetime import datetime
from decimal import Decimal
from typing import Optional, Dict, Any
from django.conf import settings
from django.core.files.storage import default_storage
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch, mm
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
import io


class PDFReceiptGenerator:
    """Generador de PDFs para recibos de pagos y refunds"""
    
    def __init__(self):
        self.styles = getSampleStyleSheet()
        self._setup_custom_styles()
    
    def _setup_custom_styles(self):
        """Configura estilos personalizados para el PDF"""
        # Estilo para el título principal
        self.styles.add(ParagraphStyle(
            name='CustomTitle',
            parent=self.styles['Heading1'],
            fontSize=18,
            spaceAfter=20,
            alignment=TA_CENTER,
            textColor=colors.darkblue
        ))
        
        # Estilo para subtítulos
        self.styles.add(ParagraphStyle(
            name='CustomSubtitle',
            parent=self.styles['Heading2'],
            fontSize=14,
            spaceAfter=12,
            alignment=TA_LEFT,
            textColor=colors.darkgreen
        ))
        
        # Estilo para información del recibo
        self.styles.add(ParagraphStyle(
            name='ReceiptInfo',
            parent=self.styles['Normal'],
            fontSize=12,
            spaceAfter=8,
            alignment=TA_LEFT
        ))
        
        # Estilo para el sello fiscal
        self.styles.add(ParagraphStyle(
            name='FiscalStamp',
            parent=self.styles['Normal'],
            fontSize=10,
            spaceAfter=20,
            alignment=TA_CENTER,
            textColor=colors.red,
            fontName='Helvetica-Bold'
        ))
    
    def generate_payment_receipt(self, payment_data: Dict[str, Any]) -> str:
        """
        Genera un PDF de recibo para un pago
        
        Args:
            payment_data: Diccionario con datos del pago
                - payment_id: ID del pago
                - reservation_code: Código de la reserva
                - amount: Monto del pago
                - method: Método de pago
                - date: Fecha del pago
                - hotel_info: Información del hotel
                - guest_info: Información del huésped
        
        Returns:
            str: Ruta del archivo PDF generado
        """
        # Crear directorio si no existe
        receipts_dir = os.path.join(settings.MEDIA_ROOT, 'receipts')
        os.makedirs(receipts_dir, exist_ok=True)
        
        # Generar nombre del archivo
        filename = f"payment_{payment_data['payment_id']}.pdf"
        filepath = os.path.join(receipts_dir, filename)
        
        # Crear el PDF
        doc = SimpleDocTemplate(
            filepath,
            pagesize=A4,
            rightMargin=72,
            leftMargin=72,
            topMargin=72,
            bottomMargin=18
        )
        
        # Construir el contenido
        story = []
        story.extend(self._build_header(payment_data))
        story.extend(self._build_payment_info(payment_data))
        story.extend(self._build_footer())
        
        # Generar el PDF
        doc.build(story)
        
        return filepath
    
    def generate_refund_receipt(self, refund_data: Dict[str, Any]) -> str:
        """
        Genera un PDF de recibo para un refund
        
        Args:
            refund_data: Diccionario con datos del refund
                - refund_id: ID del refund
                - payment_id: ID del pago original (opcional)
                - reservation_code: Código de la reserva
                - amount: Monto del refund
                - method: Método de refund
                - date: Fecha del refund
                - reason: Razón del refund
                - hotel_info: Información del hotel
                - guest_info: Información del huésped
        
        Returns:
            str: Ruta del archivo PDF generado
        """
        # Crear directorio si no existe
        receipts_dir = os.path.join(settings.MEDIA_ROOT, 'receipts')
        os.makedirs(receipts_dir, exist_ok=True)
        
        # Generar nombre del archivo
        filename = f"refund_{refund_data['refund_id']}.pdf"
        filepath = os.path.join(receipts_dir, filename)
        
        # Crear el PDF
        doc = SimpleDocTemplate(
            filepath,
            pagesize=A4,
            rightMargin=72,
            leftMargin=72,
            topMargin=72,
            bottomMargin=18
        )
        
        # Construir el contenido
        story = []
        story.extend(self._build_header(refund_data, is_refund=True))
        story.extend(self._build_refund_info(refund_data))
        story.extend(self._build_footer())
        
        # Generar el PDF
        doc.build(story)
        
        return filepath
    
    def _build_header(self, data: Dict[str, Any], is_refund: bool = False) -> list:
        """Construye el encabezado del PDF"""
        story = []
        
        # Título principal
        title = "RECIBO DE REEMBOLSO" if is_refund else "RECIBO DE PAGO"
        story.append(Paragraph(title, self.styles['CustomTitle']))
        
        # Información del hotel
        hotel_info = data.get('hotel_info', {})
        if hotel_info:
            hotel_name = hotel_info.get('name', 'Hotel')
            hotel_address = hotel_info.get('address', '')
            hotel_tax_id = hotel_info.get('tax_id', '')
            
            story.append(Paragraph(f"<b>{hotel_name}</b>", self.styles['CustomSubtitle']))
            if hotel_address:
                story.append(Paragraph(f"Dirección: {hotel_address}", self.styles['ReceiptInfo']))
            if hotel_tax_id:
                story.append(Paragraph(f"RUT: {hotel_tax_id}", self.styles['ReceiptInfo']))
        
        story.append(Spacer(1, 20))
        
        return story
    
    def _build_payment_info(self, data: Dict[str, Any]) -> list:
        """Construye la información del pago"""
        story = []
        
        # Información del recibo
        story.append(Paragraph("INFORMACIÓN DEL PAGO", self.styles['CustomSubtitle']))
        
        # Crear tabla con información
        info_data = [
            ['Código de Reserva:', data.get('reservation_code', 'N/A')],
            ['ID de Pago:', str(data.get('payment_id', 'N/A'))],
            ['Monto:', f"${data.get('amount', 0):,.2f}"],
            ['Método de Pago:', data.get('method', 'N/A')],
            ['Fecha:', data.get('date', 'N/A')],
        ]
        
        # Información del huésped
        guest_info = data.get('guest_info', {})
        if guest_info:
            guest_name = guest_info.get('name', '')
            guest_email = guest_info.get('email', '')
            if guest_name:
                info_data.append(['Huésped:', guest_name])
            if guest_email:
                info_data.append(['Email:', guest_email])
        
        # Crear tabla
        table = Table(info_data, colWidths=[2*inch, 3*inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 12),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
            ('BACKGROUND', (1, 0), (1, -1), colors.beige),
        ]))
        
        story.append(table)
        story.append(Spacer(1, 20))
        
        return story
    
    def _build_refund_info(self, data: Dict[str, Any]) -> list:
        """Construye la información del refund"""
        story = []
        
        # Información del recibo
        story.append(Paragraph("INFORMACIÓN DEL REEMBOLSO", self.styles['CustomSubtitle']))
        
        # Crear tabla con información
        info_data = [
            ['Código de Reserva:', data.get('reservation_code', 'N/A')],
            ['ID de Reembolso:', str(data.get('refund_id', 'N/A'))],
            ['ID de Pago Original:', str(data.get('payment_id', 'N/A'))],
            ['Monto:', f"${data.get('amount', 0):,.2f}"],
            ['Método de Reembolso:', data.get('method', 'N/A')],
            ['Fecha:', data.get('date', 'N/A')],
        ]
        
        # Razón del refund
        reason = data.get('reason', '')
        if reason:
            info_data.append(['Razón:', reason])
        
        # Información del huésped
        guest_info = data.get('guest_info', {})
        if guest_info:
            guest_name = guest_info.get('name', '')
            guest_email = guest_info.get('email', '')
            if guest_name:
                info_data.append(['Huésped:', guest_name])
            if guest_email:
                info_data.append(['Email:', guest_email])
        
        # Crear tabla
        table = Table(info_data, colWidths=[2*inch, 3*inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 12),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
            ('BACKGROUND', (1, 0), (1, -1), colors.beige),
        ]))
        
        story.append(table)
        story.append(Spacer(1, 20))
        
        return story
    
    def _build_footer(self) -> list:
        """Construye el pie del PDF"""
        story = []
        
        # Línea separadora
        story.append(Spacer(1, 20))
        story.append(Paragraph("─" * 50, self.styles['Normal']))
        story.append(Spacer(1, 10))
        
        # Sello fiscal interno
        story.append(Paragraph(
            "Recibo generado automáticamente por AlojaSys (sin validez fiscal)",
            self.styles['FiscalStamp']
        ))
        
        # Fecha de generación
        current_date = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        story.append(Paragraph(
            f"Generado el: {current_date}",
            self.styles['ReceiptInfo']
        ))
        
        return story
    
    def get_receipt_path(self, payment_id: str, is_refund: bool = False) -> str:
        """
        Obtiene la ruta del recibo PDF
        
        Args:
            payment_id: ID del pago o refund
            is_refund: Si es un refund o no
        
        Returns:
            str: Ruta relativa del archivo PDF
        """
        prefix = "refund" if is_refund else "payment"
        filename = f"{prefix}_{payment_id}.pdf"
        return f"receipts/{filename}"
    
    def receipt_exists(self, payment_id: str, is_refund: bool = False) -> bool:
        """
        Verifica si el recibo PDF existe
        
        Args:
            payment_id: ID del pago o refund
            is_refund: Si es un refund o no
        
        Returns:
            bool: True si el archivo existe
        """
        filepath = self.get_receipt_path(payment_id, is_refund)
        full_path = os.path.join(settings.MEDIA_ROOT, filepath)
        return os.path.exists(full_path)
