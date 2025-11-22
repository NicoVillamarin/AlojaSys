"""
Servicio de emails para reservas con PDFs adjuntos
"""
import os
import logging
from typing import List, Optional, Dict, Any

import requests
from django.core.mail import EmailMessage
from django.conf import settings
from django.template.loader import render_to_string
from apps.payments.services.pdf_generator import PDFReceiptGenerator

logger = logging.getLogger(__name__)


class ReservationEmailService:
    """Servicio para enviar emails de reservas con PDFs adjuntos"""

    @staticmethod
    def _send_via_resend(to_email: str, subject: str, body: str) -> bool:
        """
        Envia un email de texto plano usando la API HTTP de Resend.
        Pensado para funcionar en Railway Hobby (sin SMTP).
        """
        api_key = getattr(settings, "RESEND_API_KEY", None)
        if not api_key:
            logger.error("RESEND_API_KEY no configurada; no se puede enviar email vía Resend.")
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
            # Convertimos saltos de línea a <br> para que se vea bien en HTML
            "html": body.replace("\n", "<br>"),
        }
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }

        response = requests.post(
            "https://api.resend.com/emails",
            json=payload,
            headers=headers,
            timeout=20,
        )
        logger.info(
            f"📧 [RESERVATION RESEND] Respuesta HTTP {response.status_code}: {response.text[:300]}"
        )
        response.raise_for_status()
        return True

    @staticmethod
    def send_cancellation_email(
        reservation,
        cancellation_reason: str,
        total_paid: float = 0.0,
        penalty_amount: float = 0.0,
        refund_amount: float = 0.0,
    ) -> bool:
        """
        Envía email al huésped informando cancelación (con o sin devolución).
        En producción (Railway Hobby) se envía vía Resend HTTP API.
        """
        try:
            logger.info(
                f"📧 [CANCEL EMAIL] Preparando email de cancelación para reserva {getattr(reservation, 'id', 'N/A')}"
            )

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

            # En producción usamos Resend; si fallara o no hay API key, caemos a EmailMessage
            try:
                logger.info(
                    f"📧 [CANCEL EMAIL] Enviando vía Resend a {guest_email} para reserva {reservation.id}"
                )
                if ReservationEmailService._send_via_resend(guest_email, subject, body):
                    logger.info(
                        f"Email de cancelación enviado vía Resend a {guest_email} para reserva {reservation.id} "
                        f"(refund_amount={refund_amount}, penalty_amount={penalty_amount})"
                    )
                    return True
            except Exception as resend_error:
                logger.error(
                    f"Error enviando email de cancelación vía Resend para reserva {getattr(reservation, 'id', 'N/A')}: {resend_error}"
                )

            # Fallback: backend de email de Django (útil en desarrollo)
            email = EmailMessage(
                subject=subject,
                body=body,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[guest_email],
            )
            email.send()
            logger.info(
                f"Email de cancelación enviado (fallback Django) a {guest_email} para reserva {reservation.id} "
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
    
    @staticmethod
    def send_multi_room_confirmation(reservations: List, include_receipts: bool = True) -> Dict[str, bool]:
        """
        Envía emails consolidados de confirmación para reservas multi-habitación.
        
        Agrupa las reservas por email del huésped principal y envía un solo email
        por huésped con todas sus habitaciones.
        
        Args:
            reservations: Lista de instancias de Reservation con el mismo group_code
            include_receipts: Si incluir PDFs de recibos (default: True)
            
        Returns:
            Dict[str, bool]: Diccionario con {email: success} para cada email enviado
        """
        if not reservations:
            return {}
        
        # Agrupar reservas por email del huésped principal
        reservations_by_email = {}
        for reservation in reservations:
            guest_email = reservation.guest_email
            if not guest_email:
                logger.warning(f"No se encontró email para reserva {reservation.id}, se omite del email consolidado")
                continue
            
            if guest_email not in reservations_by_email:
                reservations_by_email[guest_email] = []
            reservations_by_email[guest_email].append(reservation)
        
        results = {}
        
        # Enviar un email consolidado por cada huésped
        for guest_email, guest_reservations in reservations_by_email.items():
            try:
                if not guest_reservations:
                    continue
                
                # Usar el primer huésped como referencia (todos deberían tener el mismo hotel y fechas)
                first_reservation = guest_reservations[0]
                guest_name = first_reservation.guest_name or 'Huésped'
                hotel_name = first_reservation.hotel.name
                check_in = first_reservation.check_in
                check_out = first_reservation.check_out
                group_code = first_reservation.group_code
                
                # Calcular total del grupo para este huésped
                total_price = sum(float(r.total_price) for r in guest_reservations)
                
                # Construir lista de habitaciones
                rooms_list = []
                for res in guest_reservations:
                    room_name = res.room.name if res.room else f'Habitación {res.room_id}'
                    rooms_list.append(f"  • {room_name} - {res.guests} huésped(es) - ${res.total_price:,.2f} (RES-{res.id})")
                
                # Crear email consolidado
                subject = f"Confirmación de Reserva Multi-Habitación - Grupo {group_code}"
                
                body = f"""
Estimado/a {guest_name},

Su reserva multi-habitación ha sido confirmada exitosamente.

Detalles del grupo de reservas:
- Código de grupo: {group_code}
- Hotel: {hotel_name}
- Fechas: {check_in} - {check_out}
- Total del grupo: ${total_price:,.2f}

Habitaciones incluidas en esta reserva:
{chr(10).join(rooms_list)}

Total de habitaciones: {len(guest_reservations)}
Total de huéspedes: {sum(r.guests for r in guest_reservations)}

Gracias por elegirnos. Esperamos brindarle una excelente estadía.

Equipo de {hotel_name}
                """.strip()
                
                # Crear mensaje de email
                email = EmailMessage(
                    subject=subject,
                    body=body,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    to=[guest_email],
                )
                
                # Adjuntar PDFs de recibos de todas las reservas del huésped
                if include_receipts:
                    for reservation in guest_reservations:
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
                                    logger.info(f"PDF adjunto en email consolidado: {filename}")
                                except Exception as e:
                                    logger.error(f"Error adjuntando PDF {filename} en email consolidado: {e}")
                
                # Intentar enviar vía Resend primero
                try:
                    if ReservationEmailService._send_via_resend(guest_email, subject, body):
                        logger.info(f"Email consolidado enviado vía Resend a {guest_email} para grupo {group_code} ({len(guest_reservations)} habitaciones)")
                        results[guest_email] = True
                        continue
                except Exception as resend_error:
                    logger.warning(f"Error enviando email consolidado vía Resend: {resend_error}, usando fallback Django")
                
                # Fallback: enviar con Django EmailMessage
                email.send()
                logger.info(f"Email consolidado enviado (fallback Django) a {guest_email} para grupo {group_code} ({len(guest_reservations)} habitaciones)")
                results[guest_email] = True
                
            except Exception as e:
                logger.error(f"Error enviando email consolidado a {guest_email} para grupo {group_code}: {e}")
                results[guest_email] = False
        
        return results