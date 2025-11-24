"""
Servicio de emails para facturas con PDFs adjuntos
"""
import os
import logging
from typing import Optional

import requests
from django.core.mail import EmailMessage
from django.conf import settings

logger = logging.getLogger(__name__)


class InvoiceEmailService:
    """Servicio para enviar emails de facturas con PDFs adjuntos"""

    @staticmethod
    def _send_via_resend(to_email: str, subject: str, body: str, pdf_path: Optional[str] = None) -> bool:
        """
        Envia un email usando la API HTTP de Resend.
        Funciona en local y producción con HTTPS.
        """
        use_resend_api = getattr(settings, "USE_RESEND_API", False)
        api_key = getattr(settings, "RESEND_API_KEY", None)
        
        if not use_resend_api or not api_key:
            logger.debug("Resend API no configurado o deshabilitado (USE_RESEND_API=False o sin API key)")
            return False

        from_email = getattr(
            settings,
            "DEFAULT_FROM_EMAIL",
            "AlojaSys <onboarding@resend.dev>",
        )

        payload = {
            "from": from_email,
            "to": [to_email],
            "subject": subject,
            "html": body.replace("\n", "<br>"),
        }

        # Adjuntar PDF si existe
        if pdf_path and os.path.exists(pdf_path):
            try:
                import base64
                logger.info(f"📎 [INVOICE RESEND] Adjuntando PDF: {pdf_path}")
                with open(pdf_path, 'rb') as pdf_file:
                    pdf_bytes = pdf_file.read()
                    encoded_pdf = base64.b64encode(pdf_bytes).decode("utf-8")
                    filename = os.path.basename(pdf_path)
                    # Asegurar que el nombre del archivo sea correcto
                    if not filename.endswith('.pdf'):
                        filename = f"factura_{filename}.pdf"
                    payload["attachments"] = [
                        {
                            "filename": filename,
                            "content": encoded_pdf,
                        }
                    ]
                logger.info(f"✅ [INVOICE RESEND] PDF adjuntado: {filename} ({len(pdf_bytes)} bytes)")
            except Exception as e:
                logger.error(f"❌ [INVOICE RESEND] Error adjuntando PDF al email: {e}")
                import traceback
                logger.error(f"❌ [INVOICE RESEND] Traceback:\n{traceback.format_exc()}")
        else:
            if pdf_path:
                logger.warning(f"⚠️ [INVOICE RESEND] PDF no encontrado en ruta: {pdf_path}")
            else:
                logger.warning(f"⚠️ [INVOICE RESEND] No hay PDF para adjuntar")

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }

        try:
            response = requests.post(
                "https://api.resend.com/emails",
                json=payload,
                headers=headers,
                timeout=20,
            )
            logger.info(
                f"📧 [INVOICE RESEND] Respuesta HTTP {response.status_code}: {response.text[:300]}"
            )
            response.raise_for_status()
            return True
        except Exception as e:
            logger.error(f"Error enviando email vía Resend: {e}")
            return False

    @staticmethod
    def send_invoice_email(invoice, recipient_email: Optional[str] = None) -> bool:
        """
        Envía email con factura PDF adjunto cuando la factura está aprobada por AFIP
        
        Args:
            invoice: Instancia de Invoice
            recipient_email: Email del destinatario (opcional, si no se proporciona se obtiene de la reserva)
        
        Returns:
            bool: True si se envió exitosamente, False en caso contrario
        """
        try:
            # Solo enviar si la factura está aprobada por AFIP
            if invoice.status != 'approved' or not invoice.cae:
                logger.warning(
                    f"⚠️ [INVOICE EMAIL] Factura {invoice.id} no está aprobada por AFIP. "
                    f"Status: {invoice.status}, CAE: {invoice.cae}"
                )
                return False

            # Obtener email del destinatario
            if not recipient_email:
                reservation = invoice.reservation
                if reservation and reservation.guests_data:
                    # Buscar huésped principal
                    primary_guest = next(
                        (guest for guest in reservation.guests_data if guest.get('is_primary', False)),
                        None
                    )
                    if not primary_guest and reservation.guests_data:
                        primary_guest = reservation.guests_data[0]
                    
                    if primary_guest:
                        recipient_email = primary_guest.get('email')
            
            if not recipient_email:
                logger.warning(f"⚠️ [INVOICE EMAIL] No se encontró email del destinatario para factura {invoice.id}")
                return False

            logger.info(f"📧 [INVOICE EMAIL] Preparando email de factura {invoice.number} para {recipient_email}")

            # Obtener o generar ruta del PDF
            pdf_path = None
            
            # Primero intentar obtener PDF existente
            if invoice.pdf_file:
                try:
                    # Si es un FileField, obtener la ruta
                    if hasattr(invoice.pdf_file, 'path'):
                        pdf_path = invoice.pdf_file.path
                    elif hasattr(invoice.pdf_file, 'name'):
                        # Si es una ruta relativa, construir la ruta completa
                        pdf_path = os.path.join(settings.MEDIA_ROOT, invoice.pdf_file.name)
                    else:
                        # Intentar como string
                        pdf_path = str(invoice.pdf_file)
                        if not os.path.isabs(pdf_path):
                            pdf_path = os.path.join(settings.MEDIA_ROOT, pdf_path)
                    
                    # Verificar que el archivo existe
                    if not os.path.exists(pdf_path):
                        logger.warning(f"⚠️ [INVOICE EMAIL] PDF no encontrado en ruta: {pdf_path}")
                        pdf_path = None
                    else:
                        logger.info(f"📄 [INVOICE EMAIL] PDF encontrado: {pdf_path}")
                except Exception as e:
                    logger.warning(f"⚠️ [INVOICE EMAIL] Error obteniendo ruta del PDF existente: {e}")
                    pdf_path = None
            
            # Si no hay PDF o no existe, generarlo
            if not pdf_path or not os.path.exists(pdf_path):
                try:
                    logger.info(f"📄 [INVOICE EMAIL] Generando PDF para factura {invoice.id}...")
                    from .invoice_pdf_service import InvoicePDFService
                    pdf_service = InvoicePDFService()
                    pdf_path = pdf_service.generate_pdf(invoice)
                    
                    # Verificar que se generó correctamente
                    if pdf_path and os.path.exists(pdf_path):
                        logger.info(f"✅ [INVOICE EMAIL] PDF generado exitosamente: {pdf_path}")
                    else:
                        logger.error(f"❌ [INVOICE EMAIL] PDF generado pero no encontrado: {pdf_path}")
                        pdf_path = None
                except Exception as e:
                    logger.error(f"❌ [INVOICE EMAIL] Error generando PDF para factura {invoice.id}: {e}")
                    import traceback
                    logger.error(f"❌ [INVOICE EMAIL] Traceback:\n{traceback.format_exc()}")
                    pdf_path = None
            
            # Si aún no hay PDF, no podemos enviar el email con adjunto
            if not pdf_path or not os.path.exists(pdf_path):
                logger.error(f"❌ [INVOICE EMAIL] No se pudo obtener o generar PDF para factura {invoice.id}. No se enviará adjunto.")
                # Continuar sin PDF, pero el email se enviará sin adjunto

            # Preparar cuerpo del email
            client_name = invoice.client_name or 'Cliente'
            hotel_name = invoice.hotel.name
            reservation_code = f"RES-{invoice.reservation.id}" if invoice.reservation else "N/A"
            
            body = f"""
Estimado/a {client_name},

Se adjunta la factura electrónica aprobada por AFIP.

Detalles de la factura:
- Número: {invoice.number}
- Tipo: {invoice.get_type_display()}
- CAE: {invoice.cae}
- Fecha de emisión: {invoice.issue_date.strftime('%d/%m/%Y')}
- Total: ${invoice.total:,.2f}
- Reserva: {reservation_code}

Hotel: {hotel_name}

Esta factura ha sido autorizada por AFIP y es válida como comprobante fiscal.

Gracias por su preferencia.

Equipo de {hotel_name}
            """.strip()

            subject = f"Factura Electrónica {invoice.number} - {hotel_name}"

            # Intentar usar Resend HTTP API si está configurado
            use_resend_api = getattr(settings, "USE_RESEND_API", False)
            api_key = getattr(settings, "RESEND_API_KEY", None)
            
            if use_resend_api and api_key:
                # Usar Resend HTTP API
                try:
                    logger.info(f"📧 [INVOICE EMAIL] Enviando vía Resend HTTP API a {recipient_email}")
                    if InvoiceEmailService._send_via_resend(recipient_email, subject, body, pdf_path):
                        logger.info(
                            f"✅ [INVOICE EMAIL] Email de factura enviado vía Resend API a {recipient_email} para factura {invoice.number}"
                        )
                        return True
                    else:
                        logger.warning("⚠️ [INVOICE EMAIL] Resend API retornó False, intentando con backend de Django...")
                except Exception as resend_error:
                    logger.error(f"❌ [INVOICE EMAIL] Error enviando vía Resend: {resend_error}")
                    logger.warning("⚠️ [INVOICE EMAIL] Fallando back a backend de Django...")

            # Usar backend de Django (consola en desarrollo, SMTP si está configurado)
            logger.info(f"📧 [INVOICE EMAIL] Usando backend de Django para enviar email a {recipient_email}")
            
            hotel_email = getattr(invoice.hotel, 'email', '') or None
            email = EmailMessage(
                subject=subject,
                body=body,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[recipient_email],
                reply_to=[hotel_email] if hotel_email else None,
            )
            
            # Adjuntar PDF si existe
            if pdf_path and os.path.exists(pdf_path):
                try:
                    logger.info(f"📎 [INVOICE EMAIL] Adjuntando PDF: {pdf_path}")
                    with open(pdf_path, 'rb') as pdf_file:
                        pdf_bytes = pdf_file.read()
                        filename = f"factura_{invoice.number}.pdf"
                        email.attach(
                            filename=filename,
                            content=pdf_bytes,
                            mimetype='application/pdf'
                        )
                    logger.info(f"✅ [INVOICE EMAIL] PDF adjunto: {filename} ({len(pdf_bytes)} bytes)")
                except Exception as e:
                    logger.error(f"❌ [INVOICE EMAIL] Error adjuntando PDF: {e}")
                    import traceback
                    logger.error(f"❌ [INVOICE EMAIL] Traceback:\n{traceback.format_exc()}")
            else:
                if pdf_path:
                    logger.warning(f"⚠️ [INVOICE EMAIL] PDF no encontrado en ruta: {pdf_path}")
                else:
                    logger.warning(f"⚠️ [INVOICE EMAIL] No hay PDF para adjuntar - el email se enviará sin adjunto")
            
            email.send()
            logger.info(
                f"✅ [INVOICE EMAIL] Email de factura enviado vía Django backend a {recipient_email} para factura {invoice.number}"
            )
            return True
            
        except Exception as e:
            logger.error(f"❌ [INVOICE EMAIL] Error enviando email de factura {invoice.id}: {e}")
            import traceback
            logger.error(f"❌ [INVOICE EMAIL] Traceback completo:\n{traceback.format_exc()}")
            return False

