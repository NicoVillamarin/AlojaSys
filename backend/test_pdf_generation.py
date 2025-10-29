#!/usr/bin/env python
"""
Script para probar la generación de PDF de reembolso
"""
import os
import sys
import django

# Configurar Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'hotel.settings')
django.setup()

from apps.payments.models import Refund
from apps.payments.services.pdf_generator import ModernPDFGenerator
from django.conf import settings

def test_pdf_generation():
    print("🔍 Probando generación de PDF...")
    
    # Buscar un reembolso completado sin PDF
    refund = Refund.objects.filter(status='completed', receipt_pdf_url__isnull=True).first()
    
    if not refund:
        print("❌ No hay reembolsos completados sin PDF")
        return
    
    print(f"✅ Usando reembolso ID: {refund.id}")
    print(f"   - Monto: ${refund.amount}")
    print(f"   - Estado: {refund.status}")
    print(f"   - PDF URL actual: {refund.receipt_pdf_url}")
    
    # Generar PDF manualmente
    try:
        generator = ModernPDFGenerator()
        
        info_table = [
            ['Código de Reserva:', f"RES-{refund.reservation.id}"],
            ['ID de Reembolso:', str(refund.id)],
            ['ID de Pago Original:', str(refund.payment.id) if refund.payment else '—'],
            ['Monto del Reembolso:', f"${float(refund.amount):,.2f}"],
            ['Método de Reembolso:', refund.method],
            ['Fecha del Reembolso:', refund.created_at.strftime('%d/%m/%Y %H:%M:%S')],
        ]
        if refund.reason:
            info_table.append(['Razón del Reembolso:', refund.reason])
        
        data = {
            'title': 'RECIBO DE REEMBOLSO',
            'section_title': 'INFORMACIÓN DEL REEMBOLSO',
            'hotel_info': {
                'name': refund.reservation.hotel.name,
                'address': getattr(refund.reservation.hotel, 'address', ''),
                'tax_id': getattr(refund.reservation.hotel, 'tax_id', ''),
                'phone': getattr(refund.reservation.hotel, 'phone', ''),
                'email': getattr(refund.reservation.hotel, 'email', ''),
                'logo_path': refund.reservation.hotel.logo.path if refund.reservation.hotel.logo else None,
            },
            'info_table': info_table,
        }
        
        filename = f"refund_{refund.id}.pdf"
        print(f"   - Generando PDF: {filename}")
        pdf_path = generator.generate(data, filename)
        print(f"   - PDF generado en: {pdf_path}")
        
        # Verificar que el archivo existe
        if os.path.exists(pdf_path):
            print(f"   ✅ Archivo existe: {os.path.getsize(pdf_path)} bytes")
            
            # Construir URL
            relative_path = os.path.relpath(pdf_path, settings.MEDIA_ROOT)
            media_url = getattr(settings, 'MEDIA_URL', '/media/')
            if not media_url.startswith('/'):
                media_url = '/' + media_url
            if not media_url.endswith('/'):
                media_url += '/'
            receipt_url = f"{media_url}{relative_path.replace(os.sep, '/')}"
            
            print(f"   - URL del comprobante: {receipt_url}")
            
            # Actualizar el reembolso
            refund.receipt_pdf_url = receipt_url
            refund.save(update_fields=['receipt_pdf_url'])
            
            print(f"   ✅ Reembolso actualizado con URL: {refund.receipt_pdf_url}")
        else:
            print(f"   ❌ Archivo no existe: {pdf_path}")
            
    except Exception as e:
        print(f"   ❌ Error generando PDF: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_pdf_generation()
