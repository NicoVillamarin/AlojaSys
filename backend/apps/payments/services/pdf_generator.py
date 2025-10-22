"""
Generador genérico de PDF elegante para AlojaSys
Autor: Nico & Mate
"""

import os
from datetime import datetime
from typing import Dict, Any
from django.conf import settings
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import inch
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.lib.utils import ImageReader
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle, Frame, PageTemplate
)


class ModernPDFGenerator:
    """Generador moderno, limpio y reutilizable de PDFs para AlojaSys."""

    def __init__(self):
        self.styles = getSampleStyleSheet()
        self._setup_styles()

    def _setup_styles(self):
        """Define estilos base."""
        # Usar nombres únicos para evitar conflictos
        self.styles.add(ParagraphStyle(
            name="CustomTitle",
            fontName="Helvetica-Bold",
            fontSize=20,
            alignment=TA_CENTER,
            textColor=colors.HexColor("#1E293B"),
            spaceAfter=14
        ))

        self.styles.add(ParagraphStyle(
            name="CustomSection",
            fontName="Helvetica-Bold",
            fontSize=13,
            textColor=colors.HexColor("#334155"),
            spaceAfter=8
        ))

        self.styles.add(ParagraphStyle(
            name="CustomNormal",
            fontName="Helvetica",
            fontSize=11,
            textColor=colors.HexColor("#475569"),
            leading=14
        ))

        self.styles.add(ParagraphStyle(
            name="CustomFooter",
            fontName="Helvetica",
            fontSize=9,
            textColor=colors.HexColor("#6B7280"),
            alignment=TA_CENTER
        ))

    # ----------------------------------
    # Generador principal
    # ----------------------------------

    def generate(self, data: Dict[str, Any], filename: str) -> str:
        """Genera un PDF simple y efectivo."""
        output_dir = os.path.join(settings.MEDIA_ROOT, "documents")
        os.makedirs(output_dir, exist_ok=True)
        filepath = os.path.join(output_dir, filename)

        # Documento simple con márgenes normales
        doc = SimpleDocTemplate(
            filepath,
            pagesize=A4,
            leftMargin=40,
            rightMargin=40,
            topMargin=50,
            bottomMargin=50
        )

        story = []
        story += self._build_header(data)
        story += self._build_body(data)
        story += self._build_footer()

        doc.build(story)
        return filepath

    def _build_footer(self):
        """Construir footer simple y efectivo."""
        story = []
        
        # Espaciador para separar del contenido
        story.append(Spacer(1, 20))
        
        # Línea separadora sutil
        line = Table([[""]], colWidths=[7.1*inch])
        line.setStyle(TableStyle([
            ('LINEBELOW', (0, 0), (-1, -1), 0.5, colors.HexColor("#E2E8F0")),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8)
        ]))
        story.append(line)
        
        # Logo de AlojaSys
        alojasys_logo_path = os.path.join(settings.STATIC_ROOT, "images", "logo_complet_black_transparent.png")
        if not os.path.exists(alojasys_logo_path):
            alojasys_logo_path = os.path.join(settings.BASE_DIR, "static", "images", "logo_complet_black_transparent.png")

        logo = ""
        if os.path.exists(alojasys_logo_path):
            try:
                reader = ImageReader(alojasys_logo_path)
                iw, ih = reader.getSize()
                aspect = ih / float(iw)
                logo = Image(alojasys_logo_path, width=60, height=60 * aspect)
            except Exception:
                pass

        current_date = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        
        # Footer simple con logo, fecha y sello
        footer_data = [
            [logo, 
             f"Generado el {current_date}\nSistema automático · Transacción segura",
             "Recibo generado automáticamente por AlojaSys\n(sin validez fiscal)"]
        ]
        
        footer_table = Table(footer_data, colWidths=[1.8*inch, 3*inch, 2.3*inch])
        footer_table.setStyle(TableStyle([
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("ALIGN", (0, 0), (0, 0), "LEFT"),
            ("ALIGN", (1, 0), (1, 0), "CENTER"),
            ("ALIGN", (2, 0), (2, 0), "RIGHT"),
            ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
            ("FONTSIZE", (0, 0), (-1, -1), 9),
            ("TEXTCOLOR", (1, 0), (1, 0), colors.HexColor("#64748B")),
            ("TEXTCOLOR", (2, 0), (2, 0), colors.HexColor("#DC2626")),
            ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#F8FAFC")),
            ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#E2E8F0")),
            ("TOPPADDING", (0, 0), (-1, -1), 12),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 12),
            ("LEFTPADDING", (0, 0), (-1, -1), 8),
            ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ]))
        
        story.append(footer_table)
        return story

    # ----------------------------------
    # Componentes visuales
    # ----------------------------------

    def _build_header(self, data: Dict[str, Any]):
        hotel = data.get("hotel_info", {})
        title_text = data.get("title", "Documento PDF")
        generated_date = datetime.now().strftime("%d/%m/%Y %H:%M:%S")

        logo_path = hotel.get("logo_path")
        logo_cell = ""
        if logo_path and os.path.exists(logo_path):
            try:
                reader = ImageReader(logo_path)
                iw, ih = reader.getSize()
                aspect = ih / float(iw)
                logo_cell = Image(logo_path, width=60, height=60 * aspect)
            except Exception:
                pass

        title = Paragraph(title_text, self.styles["CustomTitle"])
        date = Paragraph(f"<font size='9' color='#64748B'>Generado el {generated_date}</font>",
                         ParagraphStyle(name="Date", alignment=TA_RIGHT, textColor="#64748B"))

        header = Table(
            [[logo_cell, title, date]],
            colWidths=[1.2*inch, 3.8*inch, 2*inch]
        )
        header.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('ALIGN', (1, 0), (1, 0), 'CENTER'),
            ('ALIGN', (2, 0), (2, 0), 'RIGHT'),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 15)
        ]))

        hotel_details = f"""
            <b><font size='14' color='#1E293B'>{hotel.get('name', 'Hotel')}</font></b><br/>
            <font size='10' color='#475569'>
            {hotel.get('address', '')}<br/>
            {hotel.get('phone', '')}<br/>
            {hotel.get('email', '')}<br/>
            {f"RUT: {hotel.get('tax_id')}" if hotel.get('tax_id') else ""}
            </font>
        """

        # Línea sutil y elegante en lugar de cuadrados horribles
        line = Table([[""]], colWidths=[7.1*inch])
        line.setStyle(TableStyle([
            ('LINEBELOW', (0, 0), (-1, -1), 0.5, colors.HexColor("#E2E8F0")),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8)
        ]))

        return [header, Spacer(1, 8), Paragraph(hotel_details, self.styles["CustomNormal"]), Spacer(1, 8), line, Spacer(1, 12)]

    def _build_body(self, data: Dict[str, Any]):
        story = []
        story.append(Paragraph(data.get("section_title", "DETALLES"), self.styles["CustomSection"]))
        story.append(Spacer(1, 4))

        info_data = data.get("info_table", [])
        if not info_data:
            info_data = [["Mensaje:", "Sin información disponible."]]

        table = Table(info_data, colWidths=[2.5*inch, 4.1*inch])
        table.setStyle(TableStyle([
            ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
            ("FONTSIZE", (0, 0), (-1, -1), 11),
            ("TEXTCOLOR", (0, 0), (-1, -1), colors.HexColor("#1E293B")),
            ("ALIGN", (0, 0), (-1, -1), "LEFT"),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("ROWBACKGROUNDS", (0, 0), (-1, -1), [colors.white, colors.HexColor("#F8FAFC")]),
            ("BOX", (0, 0), (-1, -1), 0.8, colors.HexColor("#CBD5E1")),
            ("INNERGRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#E2E8F0")),
            ("LEFTPADDING", (0, 0), (-1, -1), 6),
            ("RIGHTPADDING", (0, 0), (-1, -1), 6),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
        ]))

        story.append(table)
        return story

