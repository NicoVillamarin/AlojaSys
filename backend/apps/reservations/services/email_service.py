"""
Servicio de emails para reservas con PDFs adjuntos
"""
import os
import logging
from typing import List, Optional, Dict, Any
from django.core.mail import EmailMessage
from django.conf import settings
from django.template.loader import render_to_string
from apps.payments.services.pdf_generator import PDFReceiptGenerator

logger = logging.getLogger(__name__)


class ReservationEmailService:
    """Servicio para enviar emails de reservas con PDFs adjuntos"""

    @staticmethod
    def send_cancellation_email(
        reservation,
        cancellation_reason: str,
        total_paid: float = 0.0,
        penalty_amount: float = 0.0,
        refund_amount: float = 0.0,
    ) -> bool:
        """Envía email al huésped informando cancelación (con o sin devolución)."""
        try:
            guest_email = getattr(reservation, "guest_email", None)
            if not guest_email:
                logger.warning(
                    f"No se encontró email para reserva {getattr(reservation, 'id', 'N/A')} al enviar cancelación"
                )
                return False

            guest_name = getattr(reservation, "guest_name", None) or "Huésped"
            reservation_code = f"RES-{reservation.id}"
            hotel_name = reservation.hotel.name
            room_name = reservation.room.name if getattr(reservation, "room", None) else "N/A"

            has_refund = (refund_amount or 0) > 0

            financial_lines = [
                f"- Total pagado: ${total_paid:,.2f}",
                f"- Penalidad aplicada: ${penalty_amount:,.2f}",
            ]
            if has_refund:
                financial_lines.append(
                    f"- Monto a devolver (estimado): ${refund_amount:,.2f}"
                )
            else:
                financial_lines.append(
                    "- Devolución: No corresponde devolución según la política aplicada"
                )

            body = f"""
Estimado/a {guest_name},

Su reserva ha sido cancelada.

Detalles de la reserva:
- Código: {reservation_code}
- Hotel: {hotel_name}
- Habitación: {room_name}
- Fechas: {reservation.check_in} - {reservation.check_out}

Motivo de la cancelación:
- {cancellation_reason or 'Sin detalle'}

Detalle financiero:
{chr(10).join(financial_lines)}

Si tiene dudas sobre su cancelación o la política aplicada, por favor contacte al hotel.

Equipo de {hotel_name}
""".strip()

            subject = f"Cancelación de Reserva - {reservation_code}"

            email = EmailMessage(
                subject=subject,
                body=body,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[guest_email],
            )
            email.send()
            logger.info(
                f"Email de cancelación enviado a {guest_email} para reserva {reservation.id} "
                f"(refund_amount={refund_amount}, penalty_amount={penalty_amount})"
            )
            return True
        except Exception as e:
            logger.error(
                f"Error enviando email de cancelación para reserva {getattr(reservation, 'id', 'N/A')}: {e}"
            )
            return False
    
    @staticmethod
    def send_reservation_confirmation(reservation, include_receipts: bool = True):
        """
        Envía email de confirmación de reserva con PDFs de recibos adjuntos
        
        Args:
            reservation: Instancia de Reservation
            include_receipts: Si incluir PDFs de recibos (default: True)
        """
        try:
            # Obtener email del huésped principal
            guest_email = reservation.guest_email
            if not guest_email:
                logger.warning(f"No se encontró email para reserva {reservation.id}")
                return False
            
            # Preparar datos del email
            email_data = {
                'reservation': reservation,
                'guest_name': reservation.guest_name or 'Huésped',
                'hotel_name': reservation.hotel.name,
                'check_in': reservation.check_in,
                'check_out': reservation.check_out,
                'room_name': reservation.room.name if reservation.room else 'N/A',
                'total_price': reservation.total_price,
                'reservation_code': f"RES-{reservation.id}",
            }
            
            # Crear email
            subject = f"Confirmación de Reserva - {email_data['reservation_code']}"
            
            # Cuerpo del email (texto plano)
            body = f"""
Estimado/a {email_data['guest_name']},

Su reserva ha sido confirmada exitosamente.

Detalles de la reserva:
- Código: {email_data['reservation_code']}
- Hotel: {email_data['hotel_name']}
- Habitación: {email_data['room_name']}
- Fechas: {email_data['check_in']} - {email_data['check_out']}
- Total: ${email_data['total_price']:,.2f}

Gracias por elegirnos. Esperamos brindarle una excelente estadía.

Equipo de {email_data['hotel_name']}
            """.strip()
            
            # Crear mensaje de email
            email = EmailMessage(
                subject=subject,
                body=body,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[guest_email],
            )
            
            # Adjuntar PDFs de recibos si están disponibles
            if include_receipts:
                pdf_attachments = ReservationEmailService._get_payment_receipts(reservation)
                for pdf_path, filename in pdf_attachments:
                    if os.path.exists(pdf_path):
                        try:
                            with open(pdf_path, 'rb') as pdf_file:
                                email.attach(
                                    filename=filename,
                                    content=pdf_file.read(),
                                    mimetype='application/pdf'
                                )
                            logger.info(f"PDF adjunto: {filename}")
                        except Exception as e:
                            logger.error(f"Error adjuntando PDF {filename}: {e}")
                    else:
                        logger.warning(f"PDF no encontrado: {pdf_path}")
            
            # Enviar email
            email.send()
            logger.info(f"Email de confirmación enviado a {guest_email} para reserva {reservation.id}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error enviando email de confirmación para reserva {reservation.id}: {e}")
            return False
    
    @staticmethod
    def send_payment_confirmation(reservation, payment, include_receipt: bool = True):
        """
        Envía email de confirmación de pago con PDF adjunto
        
        Args:
            reservation: Instancia de Reservation
            payment: Instancia de Payment
            include_receipt: Si incluir PDF del recibo (default: True)
        """
        try:
            # Obtener email del huésped principal
            guest_email = reservation.guest_email
            if not guest_email:
                logger.warning(f"No se encontró email para reserva {reservation.id}")
                return False
            
            # Preparar datos del email
            email_data = {
                'reservation': reservation,
                'payment': payment,
                'guest_name': reservation.guest_name or 'Huésped',
                'hotel_name': reservation.hotel.name,
                'reservation_code': f"RES-{reservation.id}",
            }
            
            # Crear email
            subject = f"Confirmación de Pago - {email_data['reservation_code']}"
            
            # Cuerpo del email
            body = f"""
Estimado/a {email_data['guest_name']},

Su pago ha sido procesado exitosamente.

Detalles del pago:
- Código de reserva: {email_data['reservation_code']}
- Monto: ${payment.amount:,.2f}
- Método: {payment.method}
- Fecha: {payment.date}

Se adjunta el recibo del pago para sus registros.

Gracias por su pago.

Equipo de {email_data['hotel_name']}
            """.strip()
            
            # Crear mensaje de email
            email = EmailMessage(
                subject=subject,
                body=body,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[guest_email],
            )
            
            # Adjuntar PDF del recibo si está disponible
            if include_receipt:
                pdf_path = ReservationEmailService._get_payment_receipt_path(payment)
                if pdf_path and os.path.exists(pdf_path):
                    try:
                        with open(pdf_path, 'rb') as pdf_file:
                            email.attach(
                                filename=f"recibo_pago_{payment.id}.pdf",
                                content=pdf_file.read(),
                                mimetype='application/pdf'
                            )
                        logger.info(f"PDF de pago adjunto: recibo_pago_{payment.id}.pdf")
                    except Exception as e:
                        logger.error(f"Error adjuntando PDF de pago {payment.id}: {e}")
                else:
                    logger.warning(f"PDF de pago no encontrado: {pdf_path}")
            
            # Enviar email
            email.send()
            logger.info(f"Email de pago enviado a {guest_email} para pago {payment.id}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error enviando email de pago para payment {payment.id}: {e}")
            return False
    
    @staticmethod
    def send_refund_confirmation(reservation, refund, include_receipt: bool = True):
        """
        Envía email de confirmación de reembolso con PDF adjunto
        
        Args:
            reservation: Instancia de Reservation
            refund: Instancia de Refund
            include_receipt: Si incluir PDF del recibo (default: True)
        """
        try:
            # Obtener email del huésped principal
            guest_email = reservation.guest_email
            if not guest_email:
                logger.warning(f"No se encontró email para reserva {reservation.id}")
                return False
            
            # Preparar datos del email
            email_data = {
                'reservation': reservation,
                'refund': refund,
                'guest_name': reservation.guest_name or 'Huésped',
                'hotel_name': reservation.hotel.name,
                'reservation_code': f"RES-{reservation.id}",
            }
            
            # Crear email
            subject = f"Confirmación de Reembolso - {email_data['reservation_code']}"
            
            # Cuerpo del email
            body = f"""
Estimado/a {email_data['guest_name']},

Su reembolso ha sido procesado exitosamente.

Detalles del reembolso:
- Código de reserva: {email_data['reservation_code']}
- Monto: ${refund.amount:,.2f}
- Método: {refund.method}
- Razón: {refund.reason or 'N/A'}
- Fecha: {refund.created_at.strftime('%d/%m/%Y %H:%M')}

Se adjunta el recibo del reembolso para sus registros.

Gracias por su comprensión.

Equipo de {email_data['hotel_name']}
            """.strip()
            
            # Crear mensaje de email
            email = EmailMessage(
                subject=subject,
                body=body,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[guest_email],
            )
            
            # Adjuntar PDF del recibo si está disponible
            if include_receipt:
                pdf_path = ReservationEmailService._get_refund_receipt_path(refund)
                if pdf_path and os.path.exists(pdf_path):
                    try:
                        with open(pdf_path, 'rb') as pdf_file:
                            email.attach(
                                filename=f"recibo_reembolso_{refund.id}.pdf",
                                content=pdf_file.read(),
                                mimetype='application/pdf'
                            )
                        logger.info(f"PDF de reembolso adjunto: recibo_reembolso_{refund.id}.pdf")
                    except Exception as e:
                        logger.error(f"Error adjuntando PDF de reembolso {refund.id}: {e}")
                else:
                    logger.warning(f"PDF de reembolso no encontrado: {pdf_path}")
            
            # Enviar email
            email.send()
            logger.info(f"Email de reembolso enviado a {guest_email} para refund {refund.id}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error enviando email de reembolso para refund {refund.id}: {e}")
            return False
    
    @staticmethod
    def _get_payment_receipts(reservation) -> List[tuple]:
        """
        Obtiene todos los PDFs de recibos de pagos de una reserva
        
        Returns:
            List[tuple]: Lista de (ruta_completa, nombre_archivo)
        """
        pdf_attachments = []
        
        try:
            # Obtener todos los pagos de la reserva
            payments = reservation.payments.all()
            
            for payment in payments:
                pdf_path = ReservationEmailService._get_payment_receipt_path(payment)
                if pdf_path and os.path.exists(pdf_path):
                    filename = f"recibo_pago_{payment.id}.pdf"
                    pdf_attachments.append((pdf_path, filename))
            
            # Obtener todos los refunds de la reserva
            refunds = reservation.refunds.all()
            
            for refund in refunds:
                pdf_path = ReservationEmailService._get_refund_receipt_path(refund)
                if pdf_path and os.path.exists(pdf_path):
                    filename = f"recibo_reembolso_{refund.id}.pdf"
                    pdf_attachments.append((pdf_path, filename))
            
        except Exception as e:
            logger.error(f"Error obteniendo PDFs para reserva {reservation.id}: {e}")
        
        return pdf_attachments
    
    @staticmethod
    def _get_payment_receipt_path(payment) -> Optional[str]:
        """Obtiene la ruta del PDF de recibo de un pago"""
        try:
            generator = PDFReceiptGenerator()
            pdf_path = generator.get_receipt_path(payment.id, is_refund=False)
            full_path = os.path.join(settings.MEDIA_ROOT, pdf_path)
            return full_path if os.path.exists(full_path) else None
        except Exception as e:
            logger.error(f"Error obteniendo path de PDF para pago {payment.id}: {e}")
            return None
    
    @staticmethod
    def _get_refund_receipt_path(refund) -> Optional[str]:
        """Obtiene la ruta del PDF de recibo de un refund"""
        try:
            generator = PDFReceiptGenerator()
            pdf_path = generator.get_receipt_path(refund.id, is_refund=True)
            full_path = os.path.join(settings.MEDIA_ROOT, pdf_path)
            return full_path if os.path.exists(full_path) else None
        except Exception as e:
            logger.error(f"Error obteniendo path de PDF para refund {refund.id}: {e}")
            return None
