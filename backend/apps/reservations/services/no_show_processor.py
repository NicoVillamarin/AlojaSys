from decimal import Decimal
from typing import Dict, Any, Optional
from django.db import transaction
from django.utils import timezone
from apps.reservations.models import Reservation, ReservationStatusChange, ReservationChangeLog, ReservationChangeEvent
from apps.payments.models import CancellationPolicy, RefundPolicy, Refund, RefundStatus, RefundReason
from apps.notifications.services import NotificationService


class NoShowProcessor:
    """
    Servicio para procesar penalidades automáticas en reservas NO_SHOW
    """
    
    @staticmethod
    def process_no_show_penalties(reservation: Reservation) -> Dict[str, Any]:
        """
        Procesa las penalidades automáticas para una reserva NO_SHOW
        
        Args:
            reservation: Reserva marcada como NO_SHOW
            
        Returns:
            Dict con información del procesamiento de penalidades
        """
        print(f"🔍 Procesando penalidades NO_SHOW para reserva {reservation.id}")
        
        try:
            with transaction.atomic():
                # 1. Verificar que la reserva esté en estado NO_SHOW
                if reservation.status != 'no_show':
                    return {
                        'success': False,
                        'error': 'La reserva no está en estado NO_SHOW',
                        'penalty_amount': Decimal('0.00')
                    }
                
                # 2. Obtener política de cancelación aplicada a la reserva
                cancellation_policy = reservation.applied_cancellation_policy
                if not cancellation_policy:
                    print(f"⚠️ No hay política de cancelación para reserva {reservation.id}")
                    return {
                        'success': False,
                        'error': 'No hay política de cancelación aplicada a esta reserva',
                        'penalty_amount': Decimal('0.00')
                    }
                
                # 3. Obtener política de devolución del hotel
                refund_policy = RefundPolicy.resolve_for_hotel(reservation.hotel)
                if not refund_policy:
                    print(f"⚠️ No hay política de devolución para hotel {reservation.hotel.id}")
                    return {
                        'success': False,
                        'error': 'No hay política de devolución configurada para este hotel',
                        'penalty_amount': Decimal('0.00')
                    }
                
                # 4. Calcular reglas de cancelación para NO_SHOW (usando fecha actual)
                cancellation_rules = cancellation_policy.get_cancellation_rules(
                    reservation.check_in, 
                    room_type=reservation.room.room_type if reservation.room else None
                )
                
                # 5. Calcular monto total pagado
                total_paid = NoShowProcessor._calculate_total_paid(reservation)
                
                # 6. Calcular penalidad según política (NO_SHOW generalmente tiene penalidad completa)
                penalty_amount = NoShowProcessor._calculate_no_show_penalty(
                    reservation, 
                    cancellation_rules, 
                    total_paid
                )
                
                # 7. Calcular reembolso (generalmente 0 para NO_SHOW)
                refund_amount = NoShowProcessor._calculate_no_show_refund(
                    total_paid, 
                    penalty_amount, 
                    refund_policy
                )
                
                # 8. Procesar penalidad si aplica
                penalty_result = None
                if penalty_amount > 0:
                    penalty_result = NoShowProcessor._process_no_show_penalty(
                        reservation, 
                        penalty_amount, 
                        cancellation_rules
                    )
                
                # 9. Procesar reembolso si aplica (generalmente no para NO_SHOW)
                refund_result = None
                if refund_amount > 0:
                    refund_result = NoShowProcessor._process_no_show_refund(
                        reservation, 
                        refund_amount, 
                        refund_policy
                    )
                
                # 10. Registrar log detallado
                NoShowProcessor._log_no_show_processing(
                    reservation, 
                    cancellation_rules, 
                    total_paid, 
                    penalty_amount, 
                    refund_amount,
                    penalty_result,
                    refund_result
                )
                
                # 11. Crear notificación detallada
                NoShowProcessor._create_no_show_notification(
                    reservation, 
                    penalty_amount, 
                    refund_amount
                )
                
                result = {
                    'success': True,
                    'total_paid': float(total_paid),
                    'penalty_amount': float(penalty_amount),
                    'refund_amount': float(refund_amount),
                    'penalty_processed': penalty_result is not None,
                    'refund_processed': refund_result is not None,
                    'penalty_result': penalty_result,
                    'refund_result': refund_result,
                    'cancellation_rules': cancellation_rules
                }
                
                print(f"✅ Penalidades NO_SHOW procesadas para reserva {reservation.id}: {result}")
                return result
                
        except Exception as e:
            print(f"❌ Error procesando penalidades NO_SHOW para reserva {reservation.id}: {e}")
            return {
                'success': False,
                'error': f'Error procesando penalidades NO_SHOW: {str(e)}',
                'penalty_amount': Decimal('0.00')
            }
    
    @staticmethod
    def _calculate_total_paid(reservation: Reservation) -> Decimal:
        """Calcula el total pagado de una reserva"""
        from apps.payments.models import PaymentIntent, PaymentIntentStatus
        from django.db import models
        
        total_paid = Decimal('0.00')
        
        # Sumar pagos manuales
        manual_payments = reservation.payments.filter(
            method__in=['cash', 'transfer', 'pos']
        ).aggregate(total=models.Sum('amount'))['total'] or Decimal('0.00')
        
        # Sumar pagos con tarjeta aprobados
        card_payments = PaymentIntent.objects.filter(
            reservation=reservation,
            status=PaymentIntentStatus.APPROVED
        ).aggregate(total=models.Sum('amount'))['total'] or Decimal('0.00')
        
        total_paid = manual_payments + card_payments
        return total_paid
    
    @staticmethod
    def _calculate_no_show_penalty(
        reservation: Reservation, 
        cancellation_rules: Dict[str, Any], 
        total_paid: Decimal
    ) -> Decimal:
        """
        Calcula la penalidad específica para NO_SHOW
        Generalmente NO_SHOW tiene penalidad completa (100% del total pagado)
        """
        if not cancellation_rules:
            return total_paid  # Penalidad completa por defecto
        
        # Para NO_SHOW, generalmente se aplica penalidad completa
        # independientemente de los tiempos de cancelación
        if cancellation_rules.get('type') == 'free':
            # Aunque la política diga cancelación gratuita, NO_SHOW puede tener penalidad
            # Esto se puede configurar en la política específicamente para NO_SHOW
            return total_paid * Decimal('0.5')  # 50% de penalidad mínima para NO_SHOW
        
        # Para otros casos, penalidad completa
        return total_paid
    
    @staticmethod
    def _calculate_no_show_refund(
        total_paid: Decimal, 
        penalty_amount: Decimal, 
        refund_policy: RefundPolicy
    ) -> Decimal:
        """
        Calcula el reembolso específico para NO_SHOW
        Considera políticas especiales para NO_SHOW vs cancelaciones normales
        """
        # Para NO_SHOW, generalmente no hay reembolso
        # Pero se puede configurar políticas especiales
        
        # Verificar si hay política específica para NO_SHOW
        no_show_refund_percentage = getattr(refund_policy, 'no_show_refund_percentage', None)
        
        if no_show_refund_percentage is not None:
            # Hay política específica para NO_SHOW
            refund_amount = (total_paid * Decimal(no_show_refund_percentage)) / Decimal('100')
            return max(Decimal('0.00'), refund_amount - penalty_amount)
        
        # Verificar si la política permite reembolso para NO_SHOW
        allow_no_show_refund = getattr(refund_policy, 'allow_no_show_refund', False)
        
        if not allow_no_show_refund:
            return Decimal('0.00')
        
        # Aplicar política de devolución normal pero con penalidad completa
        if refund_policy.refund_method == 'voucher':
            # Para vouchers, se puede dar un porcentaje reducido
            voucher_percentage = getattr(refund_policy, 'no_show_voucher_percentage', 25)  # 25% por defecto
            refund_amount = (total_paid * Decimal(voucher_percentage)) / Decimal('100')
            return max(Decimal('0.00'), refund_amount - penalty_amount)
        
        # Para otros métodos, generalmente no hay reembolso
        return Decimal('0.00')
    
    @staticmethod
    def _process_no_show_penalty(
        reservation: Reservation, 
        penalty_amount: Decimal, 
        cancellation_rules: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """
        Procesa la penalidad de NO_SHOW
        Crea un registro de penalidad o cargo
        """
        # Crear registro de penalidad en el log de cambios
        penalty_notes = f"Penalidad NO_SHOW aplicada: ${penalty_amount}"
        if cancellation_rules:
            penalty_notes += f" - Política: {cancellation_rules.get('type', 'N/A')}"
        
        # Registrar en el log de cambios
        ReservationChangeLog.objects.create(
            reservation=reservation,
            event_type=ReservationChangeEvent.NO_SHOW_PENALTY,
            changed_by=None,  # Sistema automático
            message=penalty_notes,
            snapshot={
                'penalty_amount': float(penalty_amount),
                'cancellation_rules': cancellation_rules,
                'penalty_type': 'no_show_automatic'
            }
        )
        
        return {
            'penalty_id': f"PENALTY-{reservation.id}-{timezone.now().strftime('%Y%m%d%H%M%S')}",
            'amount': float(penalty_amount),
            'type': 'no_show_penalty',
            'status': 'applied',
            'notes': penalty_notes
        }
    
    @staticmethod
    def _process_no_show_refund(
        reservation: Reservation, 
        refund_amount: Decimal, 
        refund_policy: RefundPolicy
    ) -> Optional[Dict[str, Any]]:
        """
        Procesa el reembolso específico para NO_SHOW
        Maneja diferentes tipos de reembolsos según la política
        """
        if refund_amount <= 0:
            return None
        
        # Determinar método de reembolso específico para NO_SHOW
        refund_method = NoShowProcessor._get_no_show_refund_method(refund_policy)
        
        # Calcular días de procesamiento específicos para NO_SHOW
        processing_days = NoShowProcessor._get_no_show_processing_days(refund_policy)
        
        # Crear mensaje específico para NO_SHOW
        notes = NoShowProcessor._create_no_show_refund_notes(refund_amount, refund_method, refund_policy)
        
        # Crear registro de reembolso
        refund = Refund.objects.create(
            reservation=reservation,
            payment=None,  # NO_SHOW no tiene pago original específico
            amount=refund_amount,
            reason=RefundReason.NO_SHOW,
            refund_method=refund_method,
            processing_days=processing_days,
            notes=notes
        )
        
        # Procesar según el método específico
        if refund_method == 'voucher':
            return NoShowProcessor._process_voucher_refund(refund, refund_amount)
        elif refund_method == 'bank_transfer':
            return NoShowProcessor._process_bank_transfer_refund(refund, refund_amount)
        elif refund_method == 'original_payment':
            return NoShowProcessor._process_original_payment_refund(refund, refund_amount, reservation)
        else:
            return NoShowProcessor._process_manual_refund(refund, refund_amount, refund_method)
    
    @staticmethod
    def _get_no_show_refund_method(refund_policy: RefundPolicy) -> str:
        """Determina el método de reembolso específico para NO_SHOW"""
        # Verificar si hay método específico para NO_SHOW
        no_show_method = getattr(refund_policy, 'no_show_refund_method', None)
        if no_show_method:
            return no_show_method
        
        # Usar método por defecto de la política
        return refund_policy.refund_method or 'voucher'
    
    @staticmethod
    def _get_no_show_processing_days(refund_policy: RefundPolicy) -> int:
        """Calcula días de procesamiento específicos para NO_SHOW"""
        # Verificar si hay días específicos para NO_SHOW
        no_show_days = getattr(refund_policy, 'no_show_processing_days', None)
        if no_show_days:
            return no_show_days
        
        # Usar días por defecto (más tiempo para NO_SHOW)
        return getattr(refund_policy, 'processing_days', 30)
    
    @staticmethod
    def _create_no_show_refund_notes(refund_amount: Decimal, method: str, refund_policy: RefundPolicy) -> str:
        """Crea notas específicas para reembolsos de NO_SHOW"""
        notes_parts = [
            f"Reembolso por NO_SHOW - Monto: ${refund_amount}",
            f"Método: {method}",
            f"Política: {refund_policy.name if refund_policy else 'N/A'}"
        ]
        
        # Agregar información específica según el método
        if method == 'voucher':
            notes_parts.append("Voucher de crédito con validez extendida")
        elif method == 'bank_transfer':
            notes_parts.append("Transferencia bancaria - Verificar datos del huésped")
        elif method == 'original_payment':
            notes_parts.append("Reembolso al método de pago original")
        
        return " | ".join(notes_parts)
    
    @staticmethod
    def _process_voucher_refund(refund: Refund, amount: Decimal) -> Dict[str, Any]:
        """Procesa reembolso como voucher de crédito"""
        refund.mark_as_processing()
        refund.notes += " - Voucher pendiente de generación"
        refund.save()
        
        return {
            'refund_id': refund.id,
            'method': 'voucher',
            'amount': float(amount),
            'status': 'processing',
            'voucher_type': 'credit',
            'expiry_days': 365,  # Vouchers de NO_SHOW con validez extendida
            'requires_manual_processing': True
        }
    
    @staticmethod
    def _process_bank_transfer_refund(refund: Refund, amount: Decimal) -> Dict[str, Any]:
        """Procesa reembolso como transferencia bancaria"""
        refund.status = RefundStatus.PENDING
        refund.notes += " - Transferencia bancaria pendiente"
        refund.save()
        
        return {
            'refund_id': refund.id,
            'method': 'bank_transfer',
            'amount': float(amount),
            'status': 'pending',
            'requires_manual_processing': True,
            'requires_guest_data': True
        }
    
    @staticmethod
    def _process_original_payment_refund(refund: Refund, amount: Decimal, reservation: Reservation) -> Dict[str, Any]:
        """Procesa reembolso al método de pago original"""
        refund.mark_as_processing()
        refund.notes += " - Reembolso al método original"
        refund.save()
        
        return {
            'refund_id': refund.id,
            'method': 'original_payment',
            'amount': float(amount),
            'status': 'processing',
            'requires_manual_processing': True,
            'original_payment_required': True
        }
    
    @staticmethod
    def _process_manual_refund(refund: Refund, amount: Decimal, method: str) -> Dict[str, Any]:
        """Procesa reembolso manual"""
        refund.status = RefundStatus.PENDING
        refund.notes += f" - Reembolso manual ({method})"
        refund.save()
        
        return {
            'refund_id': refund.id,
            'method': method,
            'amount': float(amount),
            'status': 'pending',
            'requires_manual_processing': True
        }
    
    @staticmethod
    def _log_no_show_processing(
        reservation: Reservation,
        cancellation_rules: Dict[str, Any],
        total_paid: Decimal,
        penalty_amount: Decimal,
        refund_amount: Decimal,
        penalty_result: Optional[Dict[str, Any]],
        refund_result: Optional[Dict[str, Any]]
    ):
        """Registra un log detallado del procesamiento NO_SHOW"""
        
        message_parts = [
            f"NO_SHOW procesado - Total pagado: ${total_paid}",
            f"Penalidad aplicada: ${penalty_amount}",
            f"Reembolso calculado: ${refund_amount}"
        ]
        
        if penalty_result:
            message_parts.append(f"Penalidad procesada: {penalty_result.get('type', 'N/A')}")
        
        if refund_result:
            message_parts.append(f"Reembolso procesado: {refund_result.get('method', 'N/A')}")
        
        message = " | ".join(message_parts)
        
        # Registrar en el log de cambios
        ReservationChangeLog.objects.create(
            reservation=reservation,
            event_type=ReservationChangeEvent.NO_SHOW_PROCESSED,
            changed_by=None,  # Sistema automático
            message=message,
            snapshot={
                'cancellation_rules': cancellation_rules,
                'total_paid': float(total_paid),
                'penalty_amount': float(penalty_amount),
                'refund_amount': float(refund_amount),
                'penalty_result': penalty_result,
                'refund_result': refund_result
            }
        )
    
    @staticmethod
    def _create_no_show_notification(
        reservation: Reservation, 
        penalty_amount: Decimal, 
        refund_amount: Decimal
    ):
        """Crea notificación detallada de NO_SHOW con información financiera completa"""
        
        try:
            total_paid = NoShowProcessor._calculate_total_paid(reservation)
            net_loss = penalty_amount - refund_amount
            
            # Notificación detallada para el hotel
            hotel_title = f"🚨 NO_SHOW - Reserva #{reservation.id} - Pérdida: ${net_loss}"
            hotel_message = NoShowProcessor._create_hotel_notification_message(
                reservation, penalty_amount, refund_amount, total_paid, net_loss
            )
            
            try:
                hotel_notification = NotificationService.create(
                    notification_type='no_show',
                    title=hotel_title,
                    message=hotel_message,
                    hotel_id=reservation.hotel.id,
                    reservation_id=reservation.id,
                    metadata={
                        'reservation_code': f"RES-{reservation.id}",
                        'hotel_name': reservation.hotel.name,
                        'check_in_date': str(reservation.check_in),
                        'check_out_date': str(reservation.check_out),
                        'penalty_amount': float(penalty_amount),
                        'refund_amount': float(refund_amount),
                        'total_paid': float(total_paid),
                        'net_loss': float(net_loss),
                        'guests_count': reservation.guests,
                        'room_name': reservation.room.name if reservation.room else 'N/A',
                        'is_hotel_notification': True,
                        'notification_level': 'high',
                        'requires_action': True
                    }
                )
                print(f"  ✅ Notificación del hotel creada para reserva {reservation.id}")
            except Exception as e:
                print(f"  ⚠️ Error creando notificación del hotel para reserva {reservation.id}: {e}")
            
            # Notificación detallada para el huésped (si tiene usuario asociado)
            if reservation.guest_user:
                try:
                    guest_title = f"❌ Su reserva #{reservation.id} fue marcada como NO_SHOW"
                    guest_message = NoShowProcessor._create_guest_notification_message(
                        reservation, penalty_amount, refund_amount, total_paid
                    )
                    
                    guest_notification = NotificationService.create(
                        notification_type='no_show',
                        title=guest_title,
                        message=guest_message,
                        user_id=reservation.guest_user.id,
                        hotel_id=reservation.hotel.id,
                        reservation_id=reservation.id,
                        metadata={
                            'reservation_code': f"RES-{reservation.id}",
                            'hotel_name': reservation.hotel.name,
                            'check_in_date': str(reservation.check_in),
                            'check_out_date': str(reservation.check_out),
                            'penalty_amount': float(penalty_amount),
                            'refund_amount': float(refund_amount),
                            'total_paid': float(total_paid),
                            'is_guest_notification': True,
                            'notification_level': 'high',
                            'requires_guest_action': refund_amount > 0
                        }
                    )
                    print(f"  ✅ Notificación del huésped creada para reserva {reservation.id}")
                except Exception as e:
                    print(f"  ⚠️ Error creando notificación del huésped para reserva {reservation.id}: {e}")
            
            # Notificación para administradores del sistema
            try:
                admin_notification = NotificationService.create(
                    notification_type='no_show',
                    title=f"📊 NO_SHOW Report - Hotel: {reservation.hotel.name}",
                    message=f"Reserva #{reservation.id} marcada como NO_SHOW. Impacto financiero: ${net_loss}",
                    hotel_id=reservation.hotel.id,
                    reservation_id=reservation.id,
                    metadata={
                        'reservation_code': f"RES-{reservation.id}",
                        'hotel_name': reservation.hotel.name,
                        'penalty_amount': float(penalty_amount),
                        'refund_amount': float(refund_amount),
                        'net_loss': float(net_loss),
                        'is_admin_notification': True,
                        'notification_level': 'medium'
                    }
                )
                print(f"  ✅ Notificación de administrador creada para reserva {reservation.id}")
            except Exception as e:
                print(f"  ⚠️ Error creando notificación de administrador para reserva {reservation.id}: {e}")
                
        except Exception as e:
            print(f"  ❌ Error general creando notificaciones NO_SHOW para reserva {reservation.id}: {e}")
            # Crear notificación básica de respaldo
            try:
                NotificationService.create(
                    notification_type='no_show',
                    title=f"🚨 NO_SHOW - Reserva #{reservation.id}",
                    message=f"La reserva #{reservation.id} fue marcada como NO_SHOW. Error al generar notificación detallada: {str(e)}",
                    hotel_id=reservation.hotel.id if reservation else None,
                    reservation_id=reservation.id if reservation else None,
                    metadata={
                        'reservation_code': f"RES-{reservation.id}" if reservation else 'N/A',
                        'error_creating_detailed_notification': True,
                        'error_message': str(e)
                    }
                )
                print(f"  📬 Notificación básica de respaldo creada para reserva {reservation.id if reservation else 'desconocida'}")
            except Exception as backup_error:
                print(f"  ❌ Error crítico creando notificación de respaldo: {backup_error}")
    
    @staticmethod
    def _create_hotel_notification_message(
        reservation: Reservation, 
        penalty_amount: Decimal, 
        refund_amount: Decimal, 
        total_paid: Decimal, 
        net_loss: Decimal
    ) -> str:
        """Crea mensaje detallado para notificación del hotel"""
        message_parts = [
            f"🚨 RESERVA NO_SHOW DETECTADA",
            f"",
            f"📋 Detalles de la reserva:",
            f"   • Código: RES-{reservation.id}",
            f"   • Huéspedes: {reservation.guests}",
            f"   • Habitación: {reservation.room.name if reservation.room else 'N/A'}",
            f"   • Check-in: {reservation.check_in}",
            f"   • Check-out: {reservation.check_out}",
            f"",
            f"💰 Impacto financiero:",
            f"   • Total pagado: ${total_paid}",
            f"   • Penalidad aplicada: ${penalty_amount}",
            f"   • Reembolso: ${refund_amount}",
            f"   • Pérdida neta: ${net_loss}",
            f"",
            f"📝 Acciones requeridas:",
        ]
        
        if refund_amount > 0:
            message_parts.append(f"   • Procesar reembolso de ${refund_amount}")
        
        message_parts.extend([
            f"   • Actualizar estadísticas de NO_SHOW",
            f"   • Revisar política de cancelación si es necesario",
            f"",
            f"⏰ Procesado automáticamente el {reservation.updated_at.strftime('%d/%m/%Y a las %H:%M')}"
        ])
        
        return "\n".join(message_parts)
    
    @staticmethod
    def _create_guest_notification_message(
        reservation: Reservation, 
        penalty_amount: Decimal, 
        refund_amount: Decimal, 
        total_paid: Decimal
    ) -> str:
        """Crea mensaje detallado para notificación del huésped"""
        message_parts = [
            f"❌ SU RESERVA FUE MARCADA COMO NO_SHOW",
            f"",
            f"📋 Detalles de su reserva:",
            f"   • Código: RES-{reservation.id}",
            f"   • Hotel: {reservation.hotel.name}",
            f"   • Habitación: {reservation.room.name if reservation.room else 'N/A'}",
            f"   • Fecha de llegada: {reservation.check_in}",
            f"   • Fecha de salida: {reservation.check_out}",
            f"",
            f"💰 Información financiera:",
            f"   • Total pagado: ${total_paid}",
            f"   • Penalidad aplicada: ${penalty_amount}",
        ]
        
        if refund_amount > 0:
            message_parts.extend([
                f"   • Reembolso disponible: ${refund_amount}",
                f"",
                f"✅ PRÓXIMOS PASOS:",
                f"   • Su reembolso será procesado según la política del hotel",
                f"   • Recibirá más información por email",
                f"   • El proceso puede tomar hasta 30 días hábiles"
            ])
        else:
            message_parts.extend([
                f"   • Reembolso: $0.00",
                f"",
                f"ℹ️ INFORMACIÓN:",
                f"   • No se aplica reembolso según la política de NO_SHOW",
                f"   • La penalidad corresponde al 100% del monto pagado",
                f"   • Contacte al hotel para más información"
            ])
        
        message_parts.extend([
            f"",
            f"📞 Si tiene preguntas, contacte al hotel:",
            f"   • Email: {reservation.hotel.email}",
            f"   • Teléfono: {reservation.hotel.phone}",
            f"",
            f"⏰ Procesado el {reservation.updated_at.strftime('%d/%m/%Y a las %H:%M')}"
        ])
        
        return "\n".join(message_parts)
