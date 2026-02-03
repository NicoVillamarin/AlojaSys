from django.contrib.auth.models import User
from .models import Notification, NotificationType
from typing import Optional, Dict, Any


class NotificationService:
    """Servicio centralizado para crear notificaciones"""
    
    @staticmethod
    def create(
        notification_type: str,
        title: str,
        message: str,
        user_id: Optional[int] = None,
        hotel_id: Optional[int] = None,
        reservation_id: Optional[int] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Notification:
        """
        Crea una nueva notificación
        
        Args:
            notification_type: Tipo de notificación (auto_cancel, no_show, etc.)
            title: Título de la notificación
            message: Mensaje detallado
            user_id: ID del usuario destinatario (opcional, null = todos)
            hotel_id: ID del hotel relacionado (opcional)
            reservation_id: ID de la reserva relacionada (opcional)
            metadata: Datos adicionales en formato JSON (opcional)
        
        Returns:
            Notification: Instancia de la notificación creada
        """
        user = None
        if user_id:
            try:
                user = User.objects.get(id=user_id)
            except User.DoesNotExist:
                pass  # Si no existe el usuario, se crea para todos
        
        notification = Notification.objects.create(
            type=notification_type,
            title=title,
            message=message,
            user=user,
            hotel_id=hotel_id,
            reservation_id=reservation_id,
            metadata=metadata or {}
        )
        
        return notification
    
    @staticmethod
    def create_auto_cancel_notification(
        reservation_code: str,
        hotel_name: str,
        reason: str,
        hotel_id: Optional[int] = None,
        reservation_id: Optional[int] = None,
        user_id: Optional[int] = None
    ) -> Notification:
        """Crea notificación de auto-cancelación"""
        return NotificationService.create(
            notification_type=NotificationType.AUTO_CANCEL,
            title="Reserva cancelada automáticamente",
            message=f"La reserva #{reservation_code} en {hotel_name} fue cancelada automáticamente. Motivo: {reason}",
            user_id=user_id,
            hotel_id=hotel_id,
            reservation_id=reservation_id,
            metadata={
                'reservation_code': reservation_code,
                'hotel_name': hotel_name,
                'reason': reason
            }
        )
    
    @staticmethod
    def create_manual_cancel_notification(
        reservation_code: str,
        hotel_name: str,
        reason: str,
        hotel_id: Optional[int] = None,
        reservation_id: Optional[int] = None,
        user_id: Optional[int] = None
    ) -> Notification:
        """Crea notificación de cancelación manual"""
        return NotificationService.create(
            notification_type=NotificationType.MANUAL_CANCEL,
            title="Reserva cancelada manualmente",
            message=f"La reserva #{reservation_code} en {hotel_name} fue cancelada manualmente. Motivo: {reason}",
            user_id=user_id,
            hotel_id=hotel_id,
            reservation_id=reservation_id,
            metadata={
                'reservation_code': reservation_code,
                'hotel_name': hotel_name,
                'reason': reason,
                'manual_cancellation': True
            }
        )
    
    @staticmethod
    def create_no_show_notification(
        reservation_code: str,
        hotel_name: str,
        check_in_date: str,
        hotel_id: Optional[int] = None,
        reservation_id: Optional[int] = None,
        user_id: Optional[int] = None
    ) -> Notification:
        """Crea notificación de no-show"""
        return NotificationService.create(
            notification_type=NotificationType.NO_SHOW,
            title="Reserva marcada como No-Show",
            message=f"La reserva #{reservation_code} en {hotel_name} fue marcada como No-Show. Fecha de check-in: {check_in_date}",
            user_id=user_id,
            hotel_id=hotel_id,
            reservation_id=reservation_id,
            metadata={
                'reservation_code': reservation_code,
                'hotel_name': hotel_name,
                'check_in_date': check_in_date
            }
        )
    
    @staticmethod
    def create_refund_auto_notification(
        reservation_code: str,
        hotel_name: str,
        amount: str,
        status: str,
        hotel_id: Optional[int] = None,
        reservation_id: Optional[int] = None,
        user_id: Optional[int] = None
    ) -> Notification:
        """Crea notificación de reembolso automático"""
        normalized = (status or '').lower()
        # Mapear estados a tipo/título amigable
        if normalized in ['failed', 'fallido', 'error']:
            notification_type = NotificationType.REFUND_FAILED
            title = "Reembolso fallido"
        else:
            # success, processing, pending (u otros) → REFUND_AUTO
            notification_type = NotificationType.REFUND_AUTO
            if normalized in ['processing', 'procesando']:
                title = "Reembolso en procesamiento"
            elif normalized in ['pending', 'pendiente']:
                title = "Reembolso pendiente"
            else:
                # success u otros
                title = "Reembolso procesado"
        
        return NotificationService.create(
            notification_type=notification_type,
            title=title,
            message=f"Reembolso de ${amount} para la reserva #{reservation_code} en {hotel_name}. Estado: {normalized or status}",
            user_id=user_id,
            hotel_id=hotel_id,
            reservation_id=reservation_id,
            metadata={
                'reservation_code': reservation_code,
                'hotel_name': hotel_name,
                'amount': amount,
                'status': normalized or status
            }
        )
    
    @staticmethod
    def create_receipt_generated_notification(
        receipt_type: str,
        receipt_number: str,
        reservation_code: str,
        hotel_name: str,
        amount: str,
        hotel_id: Optional[int] = None,
        reservation_id: Optional[int] = None,
        user_id: Optional[int] = None
    ) -> Notification:
        """Crea notificación cuando se genera un comprobante automáticamente"""
        
        # Determinar título y mensaje según el tipo de comprobante
        type_titles = {
            'payment': 'Comprobante de Pago Generado',
            'refund': 'Comprobante de Devolución Generado',
            'deposit': 'Comprobante de Seña Generado'
        }
        
        title = type_titles.get(receipt_type.lower(), 'Comprobante Generado')
        
        # Determinar tipo de notificación
        notification_type = NotificationType.RECEIPT_GENERATED
        
        message = f"Se generó automáticamente el comprobante {receipt_number} por ${amount} para la reserva #{reservation_code} en {hotel_name}"
        
        return NotificationService.create(
            notification_type=notification_type,
            title=title,
            message=message,
            user_id=user_id,
            hotel_id=hotel_id,
            reservation_id=reservation_id,
            metadata={
                'receipt_type': receipt_type,
                'receipt_number': receipt_number,
                'reservation_code': reservation_code,
                'hotel_name': hotel_name,
                'amount': amount
            }
        )
    
    @staticmethod
    def create_ota_reservation_notification(
        provider_name: str,
        reservation_code: str,
        room_name: str,
        check_in_date: str,
        check_out_date: str,
        guest_name: str = "",
        hotel_id: Optional[int] = None,
        reservation_id: Optional[int] = None,
        user_id: Optional[int] = None,
        external_id: Optional[str] = None,
        overbooking: bool = False
    ) -> Notification:
        """Crea notificación cuando se recibe una nueva reserva desde una OTA"""
        
        # Construir mensaje con información relevante
        message_parts = [
            f"Nueva reserva recibida desde {provider_name}",
            f"Reserva: #{reservation_code}",
            f"Habitación: {room_name}",
            f"Check-in: {check_in_date}",
            f"Check-out: {check_out_date}",
        ]
        
        if guest_name:
            message_parts.insert(2, f"Huésped: {guest_name}")
        
        if overbooking:
            message_parts.append("⚠️ Advertencia: Posible sobre-reserva detectada")
        
        message = "\n".join(message_parts)
        
        # Título con información clave
        title = f"Nueva reserva de {provider_name} - {room_name}"
        
        metadata = {
            'provider': provider_name,
            'reservation_code': reservation_code,
            'room_name': room_name,
            'check_in': check_in_date,
            'check_out': check_out_date,
            'guest_name': guest_name,
            'overbooking': overbooking,
        }
        
        if external_id:
            metadata['external_id'] = external_id
        
        return NotificationService.create(
            notification_type=NotificationType.OTA_RESERVATION_RECEIVED,
            title=title,
            message=message,
            user_id=user_id,
            hotel_id=hotel_id,
            reservation_id=reservation_id,
            metadata=metadata
        )

    @staticmethod
    def create_website_reservation_notification(
        reservation_code: str,
        room_name: str,
        check_in_date: str,
        check_out_date: str,
        guest_name: str = "",
        hotel_id: Optional[int] = None,
        reservation_id: Optional[int] = None,
        user_id: Optional[int] = None,
    ) -> Notification:
        """Crea notificación cuando se recibe una reserva desde el sitio web externo."""
        title = f"Nueva reserva desde Sitio Web - {room_name}"
        parts = [
            "Nueva reserva recibida desde Sitio Web",
            f"Reserva: #{reservation_code}",
            f"Habitación: {room_name}",
            f"Check-in: {check_in_date}",
            f"Check-out: {check_out_date}",
        ]
        if guest_name:
            parts.insert(2, f"Huésped: {guest_name}")
        message = "\n".join(parts)
        return NotificationService.create(
            notification_type=NotificationType.WEBSITE_RESERVATION_RECEIVED,
            title=title,
            message=message,
            user_id=user_id,
            hotel_id=hotel_id,
            reservation_id=reservation_id,
            metadata={
                "source": "website",
                "reservation_code": reservation_code,
                "room_name": room_name,
                "check_in": check_in_date,
                "check_out": check_out_date,
                "guest_name": guest_name,
            },
        )
    
    @staticmethod
    def create_bulk_notification(
        notification_type: str,
        title: str,
        message_template: str,
        hotel_id: Optional[int] = None,
        user_ids: Optional[list] = None,
        **template_vars
    ) -> list:
        """
        Crea múltiples notificaciones para varios usuarios
        
        Args:
            notification_type: Tipo de notificación
            title: Título de la notificación
            message_template: Template del mensaje con variables {var}
            hotel_id: ID del hotel relacionado
            user_ids: Lista de IDs de usuarios (opcional, null = todos)
            **template_vars: Variables para el template del mensaje
        
        Returns:
            list: Lista de notificaciones creadas
        """
        notifications = []
        
        if user_ids:
            # Crear notificación para usuarios específicos
            for user_id in user_ids:
                message = message_template.format(**template_vars)
                notification = NotificationService.create(
                    notification_type=notification_type,
                    title=title,
                    message=message,
                    user_id=user_id,
                    hotel_id=hotel_id,
                    metadata=template_vars
                )
                notifications.append(notification)
        else:
            # Crear notificación para todos los usuarios
            message = message_template.format(**template_vars)
            notification = NotificationService.create(
                notification_type=notification_type,
                title=title,
                message=message,
                hotel_id=hotel_id,
                metadata=template_vars
            )
            notifications.append(notification)
        
        return notifications
    
    @staticmethod
    def create_housekeeping_task_notification(
        task_type: str,
        room_name: str,
        staff_name: str,
        hotel_id: Optional[int] = None,
        user_id: Optional[int] = None,
        task_id: Optional[int] = None
    ) -> Notification:
        """
        Crea una notificación cuando se crea automáticamente una tarea de limpieza.
        
        Args:
            task_type: Tipo de tarea (checkout, daily, maintenance)
            room_name: Nombre de la habitación
            staff_name: Nombre del personal asignado
            hotel_id: ID del hotel relacionado
            user_id: ID del usuario destinatario (personal asignado)
            task_id: ID de la tarea creada
        
        Returns:
            Notification: Instancia de la notificación creada
        """
        # Mapear tipos de tarea a nombres legibles
        task_type_names = {
            'checkout': 'Limpieza de Salida',
            'daily': 'Limpieza Diaria',
            'maintenance': 'Mantenimiento',
        }
        task_type_display = task_type_names.get(task_type, task_type.title())
        
        title = f"Nueva Tarea de Limpieza: {task_type_display}"
        message = f"Se creó la tarea '{task_type_display}' para la habitación {room_name}."
        
        if staff_name:
            message += f" Se le asignó a {staff_name}."
        else:
            message += " No se asignó personal automáticamente."
        
        notification = NotificationService.create(
            notification_type=NotificationType.HOUSEKEEPING_TASK_CREATED,
            title=title,
            message=message,
            user_id=user_id,
            hotel_id=hotel_id,
            metadata={
                'task_type': task_type,
                'room_name': room_name,
                'staff_name': staff_name,
                'task_id': task_id
            }
        )
        return notification