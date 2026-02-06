from decimal import Decimal
from typing import Dict, Any, Optional
from django.db import transaction, models
from apps.reservations.models import Reservation
from apps.payments.models import CancellationPolicy, RefundPolicy, Refund, RefundStatus, RefundReason, PaymentIntent, PaymentIntentStatus
from apps.reservations.models import Payment
from datetime import datetime


class RefundProcessor:
    """
    Servicio para procesar devoluciones automáticas basadas en políticas de cancelación
    """
    
    @staticmethod
    def process_refund(reservation: Reservation, cancellation_policy: CancellationPolicy = None, cancellation_reason: str = None, refund_method: str = 'money') -> Dict[str, Any]:
        """
        Procesa la devolución automática de una reserva cancelada
        
        Args:
            reservation: Reserva a cancelar
            cancellation_policy: Política de cancelación aplicable (opcional, usa la aplicada a la reserva si no se proporciona)
            cancellation_reason: Motivo de cancelación (opcional)
            refund_method: Método de reembolso ('money' o 'voucher')
            
        Returns:
            Dict con información del procesamiento de devolución
        """
        try:
            with transaction.atomic():
                # 1. Usar la política aplicada a la reserva o la proporcionada
                if not cancellation_policy:
                    cancellation_policy = reservation.applied_cancellation_policy
                
                # 2. Obtener política de devolución del hotel
                refund_policy = RefundPolicy.resolve_for_hotel(reservation.hotel)
                
                # 3. Calcular reglas de cancelación y devolución
                # Usar snapshot si está disponible, sino usar política actual
                from apps.reservations.services.snapshot_cancellation_calculator import SnapshotCancellationCalculator
                
                if SnapshotCancellationCalculator.should_use_snapshot(reservation):
                    cancellation_rules = SnapshotCancellationCalculator.get_cancellation_rules_from_snapshot(reservation)
                    if not cancellation_rules and cancellation_policy:
                        # Fallback a política actual si no se puede calcular desde snapshot
                        cancellation_rules = cancellation_policy.get_cancellation_rules(reservation.check_in)
                else:
                    cancellation_rules = cancellation_policy.get_cancellation_rules(reservation.check_in) if cancellation_policy else None

                # Fallback seguro si no hay política configurada: permitir cancelar, pero NO devolver dinero automáticamente.
                if not cancellation_rules:
                    cancellation_rules = {
                        'cancellation_type': 'no_refund',
                        'type': 'no_refund',
                        'fee_type': 'percentage',
                        'fee_value': 100,
                        'penalty_percentage': 100,
                        'message': 'Sin política de cancelación configurada: se retiene lo pagado.'
                    }

                if refund_policy:
                    refund_rules = refund_policy.get_refund_rules(reservation.check_in)
                else:
                    refund_rules = {
                        'type': 'none',
                        'refund_percentage': 0,
                        'refund_method': 'original_payment',
                        'processing_days': 0,
                        'message': 'Sin política de devolución configurada: no se procesa devolución automática.'
                    }
                
                # 3. Calcular monto total pagado
                total_paid = RefundProcessor._calculate_total_paid(reservation)
                
                # 4. Calcular penalidad según política de cancelación
                penalty_amount = RefundProcessor._calculate_penalty(
                    reservation, 
                    cancellation_rules, 
                    total_paid
                )
                
                # 5. Calcular monto de devolución según política de devolución
                refund_amount = RefundProcessor._calculate_refund_amount(
                    total_paid, 
                    penalty_amount, 
                    refund_rules
                )
                
                # 6. Procesar devolución si aplica
                refund_result = None
                if refund_amount > 0:
                    refund_result = RefundProcessor._process_refund_payment(
                        reservation, 
                        refund_amount, 
                        refund_rules,
                        cancellation_reason,
                        refund_method
                    )
                
                # 7. Registrar log de cancelación con detalles financieros
                try:
                    RefundProcessor._log_cancellation_with_refund(
                        reservation, 
                        cancellation_rules, 
                        refund_rules, 
                        total_paid, 
                        penalty_amount, 
                        refund_amount,
                        refund_result
                    )
                except Exception as log_error:
                    print(f"Error registrando log de cancelación: {log_error}")
                    # Continuar sin fallar por el log
                
                result = {
                    'success': True,
                    'total_paid': float(total_paid),
                    'penalty_amount': float(penalty_amount),
                    'refund_amount': float(refund_amount),
                    'refund_processed': refund_result is not None,
                    'refund_result': refund_result,
                    'cancellation_rules': cancellation_rules,
                    'refund_rules': refund_rules
                }
                return result
                
        except Exception as e:
            return {
                'success': False,
                'error': f'Error procesando devolución: {str(e)}',
                'refund_amount': Decimal('0.00')
            }
    
    @staticmethod
    def _calculate_total_paid(reservation: Reservation) -> Decimal:
        """
        Calcula el total pagado de una reserva
        """
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
    def _calculate_penalty(
        reservation: Reservation, 
        cancellation_rules: Dict[str, Any], 
        total_paid: Decimal
    ) -> Decimal:
        """
        Calcula la penalidad según las reglas de cancelación
        """
        # Normalizar tipo: hoy convivieron `cancellation_type` y `type`
        cancellation_type = cancellation_rules.get('cancellation_type') or cancellation_rules.get('type') or 'no_refund'
        if cancellation_type == 'no_cancellation':
            cancellation_type = 'no_refund'

        if cancellation_type == 'free':
            return Decimal('0.00')

        # Soportar esquema nuevo (fee_type/fee_value) y viejo (penalty_percentage)
        fee_type = cancellation_rules.get('fee_type')
        fee_value = cancellation_rules.get('fee_value')

        # Snapshot incluye `penalty` con `fee_type/fee_value`
        if not fee_type and isinstance(cancellation_rules.get('penalty'), dict):
            fee_type = cancellation_rules['penalty'].get('fee_type')
            fee_value = cancellation_rules['penalty'].get('fee_value')

        # Si no tenemos fee_type, usar esquema viejo
        if not fee_type:
            if cancellation_type == 'partial':
                penalty_percentage = cancellation_rules.get('penalty_percentage', 0) or 0
                penalty_amount = (total_paid * Decimal(str(penalty_percentage))) / Decimal('100')
                return max(Decimal('0.00'), min(total_paid, penalty_amount))
            return total_paid

        fee_type = str(fee_type)
        try:
            fee_value_dec = Decimal(str(fee_value or 0))
        except Exception:
            fee_value_dec = Decimal('0')

        penalty_amount = Decimal('0.00')

        if fee_type == 'none':
            penalty_amount = Decimal('0.00')
        elif fee_type == 'percentage':
            penalty_amount = (total_paid * fee_value_dec) / Decimal('100')
        elif fee_type == 'fixed':
            penalty_amount = fee_value_dec
        elif fee_type == 'first_night':
            try:
                first_night = reservation.nights.order_by('date').values_list('total_night', flat=True).first()
                if first_night is not None:
                    penalty_amount = Decimal(str(first_night))
                elif getattr(reservation, 'room', None) and getattr(reservation.room, 'base_price', None) is not None:
                    penalty_amount = Decimal(str(reservation.room.base_price))
                else:
                    penalty_amount = total_paid
            except Exception:
                penalty_amount = total_paid
        elif fee_type == 'nights_percentage':
            try:
                nights = max(0, (reservation.check_out - reservation.check_in).days)
            except Exception:
                nights = 0
            penalty_amount = (total_paid * fee_value_dec) / Decimal('100') * Decimal(str(nights))
        else:
            # Fallback defensivo: retener lo pagado
            penalty_amount = total_paid

        # Nunca penalizar más de lo que el huésped pagó
        penalty_amount = max(Decimal('0.00'), min(total_paid, penalty_amount))
        return penalty_amount
    
    @staticmethod
    def _calculate_refund_amount(
        total_paid: Decimal, 
        penalty_amount: Decimal, 
        refund_rules: Dict[str, Any]
    ) -> Decimal:
        """
        Calcula el monto de devolución según las reglas de devolución
        """
        if refund_rules.get('type') == 'none':
            return Decimal('0.00')
        
        if refund_rules.get('type') == 'full':
            return total_paid - penalty_amount
        
        if refund_rules.get('type') == 'partial':
            refund_percentage = refund_rules.get('refund_percentage', 0)
            refund_amount = (total_paid * Decimal(refund_percentage)) / Decimal('100')
            return max(Decimal('0.00'), refund_amount - penalty_amount)
        
        return Decimal('0.00')
    
    @staticmethod
    def _process_refund_payment(
        reservation: Reservation, 
        refund_amount: Decimal, 
        refund_rules: Dict[str, Any],
        cancellation_reason: str = None,
        refund_method: str = 'money'
    ) -> Optional[Dict[str, Any]]:
        """
        Procesa el pago de devolución según el método configurado
        """
        # Usar el método pasado como parámetro, con fallback a la política
        if refund_method == 'money':
            refund_method = refund_rules.get('refund_method', 'original_payment')
        # Si es 'voucher', mantener 'voucher' independientemente de la política
        
        # Obtener el pago original para el reembolso
        original_payment = RefundProcessor._get_original_payment(reservation)
        
        if not original_payment:
            return None
        
        # Crear registro de reembolso explícito
        notes = f"Reembolso por cancelación - Método: {refund_method}"
        if cancellation_reason:
            notes += f" - Motivo: {cancellation_reason}"
        
        refund = Refund.objects.create(
            reservation=reservation,
            payment=original_payment,
            amount=refund_amount,
            reason=RefundReason.CANCELLATION,
            refund_method=refund_method,
            processing_days=refund_rules.get('processing_days', 7),
            notes=notes
        )
        
        # Notificar creación de reembolso (pendiente por defecto)
        try:
            from apps.notifications.services import NotificationService
            NotificationService.create_refund_auto_notification(
                reservation_code=f"RES-{reservation.id}",
                hotel_name=reservation.hotel.name,
                amount=str(refund_amount),
                status="pending",
                hotel_id=reservation.hotel.id,
                reservation_id=reservation.id
            )
        except Exception as e:
            print(f"⚠️ Error creando notificación de reembolso (pending) para reserva {reservation.id}: {e}")
        
        # Procesar según el método
        if refund_method == 'original_payment':
            result = RefundProcessor._refund_original_payment(reservation, refund_amount, refund)
            # Notificar que pasó a processing
            try:
                from apps.notifications.services import NotificationService
                NotificationService.create_refund_auto_notification(
                    reservation_code=f"RES-{reservation.id}",
                    hotel_name=reservation.hotel.name,
                    amount=str(refund_amount),
                    status=result.get('status', 'processing'),
                    hotel_id=reservation.hotel.id,
                    reservation_id=reservation.id
                )
            except Exception as e:
                print(f"⚠️ Error creando notificación de reembolso (processing) para reserva {reservation.id}: {e}")
            return result
        
        elif refund_method == 'bank_transfer':
            result = RefundProcessor._create_pending_refund(reservation, refund_amount, 'bank_transfer', refund)
            # Ya se notificó como pending arriba
            return result
        
        elif refund_method == 'cash':
            result = RefundProcessor._create_pending_refund(reservation, refund_amount, 'cash', refund)
            return result
        
        elif refund_method == 'voucher':
            result = RefundProcessor._create_voucher_refund(reservation, refund_amount, refund)
            # Notificar processing
            try:
                from apps.notifications.services import NotificationService
                NotificationService.create_refund_auto_notification(
                    reservation_code=f"RES-{reservation.id}",
                    hotel_name=reservation.hotel.name,
                    amount=str(refund_amount),
                    status=result.get('status', 'processing'),
                    hotel_id=reservation.hotel.id,
                    reservation_id=reservation.id
                )
            except Exception as e:
                print(f"⚠️ Error creando notificación de reembolso (processing voucher) para reserva {reservation.id}: {e}")
            return result
        
        return None
    
    @staticmethod
    def _get_original_payment(reservation: Reservation) -> Optional[Payment]:
        """
        Obtiene el pago original para el reembolso
        """
        # Buscar el último pago aprobado con tarjeta
        last_card_payment = PaymentIntent.objects.filter(
            reservation=reservation,
            status=PaymentIntentStatus.APPROVED
        ).order_by('-created_at').first()
        
        if last_card_payment:
            # Crear un registro de Payment para el pago con tarjeta
            payment, created = Payment.objects.get_or_create(
                reservation=reservation,
                date=last_card_payment.created_at.date(),
                method='credit_card',
                amount=last_card_payment.amount
            )
            return payment
        
        # Buscar pagos manuales
        manual_payment = reservation.payments.filter(
            method__in=['cash', 'transfer', 'pos']
        ).order_by('-date').first()
        
        return manual_payment
    
    @staticmethod
    def _refund_original_payment(reservation: Reservation, refund_amount: Decimal, refund: Refund) -> Dict[str, Any]:
        """
        Intenta devolver por el método de pago original
        """
        # Buscar el último pago aprobado con tarjeta
        last_payment = PaymentIntent.objects.filter(
            reservation=reservation,
            status=PaymentIntentStatus.APPROVED
        ).order_by('-created_at').first()
        
        if last_payment:
            # Aquí se integraría con la API de Mercado Pago para devolución
            # Por ahora, marcamos como pendiente de procesamiento
            refund.mark_as_processing()
            refund.external_reference = f"MP_REFUND_{last_payment.mp_payment_id}"
            refund.notes = f"Reembolso pendiente - Pago original: {last_payment.mp_payment_id}"
            refund.save()
            
            return {
                'refund_id': refund.id,
                'method': 'credit_card_refund',
                'amount': float(refund_amount),
                'status': 'processing',
                'external_reference': refund.external_reference,
                'requires_manual_processing': True
            }
        
        # Si no hay pagos con tarjeta, crear devolución manual
        refund.mark_as_processing()
        # Preservar las notas originales (que incluyen el motivo de cancelación)
        if not refund.notes or "Reembolso manual pendiente" in refund.notes:
            refund.notes = "Reembolso manual pendiente"
        refund.save()
        
        return {
            'refund_id': refund.id,
            'method': 'manual_refund',
            'amount': float(refund_amount),
            'status': 'processing',
            'requires_manual_processing': True
        }
    
    @staticmethod
    def _create_pending_refund(
        reservation: Reservation, 
        refund_amount: Decimal, 
        method: str,
        refund: Refund,
        metadata: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        Crea un registro de devolución pendiente
        """
        # Marcar como pendiente
        refund.status = RefundStatus.PENDING
        refund.notes = f"Devolución pendiente - Método: {method}"
        if metadata:
            refund.notes += f" - {metadata}"
        refund.save()
        
        return {
            'refund_id': refund.id,
            'method': method,
            'amount': float(refund_amount),
            'status': 'pending',
            'metadata': metadata or {}
        }
    
    @staticmethod
    def _create_voucher_refund(reservation: Reservation, refund_amount: Decimal, refund: Refund) -> Dict[str, Any]:
        """
        Crea un voucher de crédito para devolución
        """
        from apps.payments.models import RefundVoucher, RefundVoucherStatus
        from datetime import datetime, timedelta
        
        try:
            # Obtener política de devolución para configurar expiración
            refund_policy = RefundPolicy.resolve_for_hotel(reservation.hotel)
            voucher_expiry_days = 365  # Default
            if refund_policy:
                voucher_expiry_days = refund_policy.voucher_expiry_days
            
            # Calcular fecha de expiración
            expiry_date = datetime.now() + timedelta(days=voucher_expiry_days)
            
            # Crear voucher
            voucher = RefundVoucher.objects.create(
                amount=refund_amount,
                expiry_date=expiry_date,
                hotel=reservation.hotel,
                original_refund=refund,
                notes=f"Voucher generado por cancelación de reserva #{reservation.id}"
            )
            
            # Actualizar refund con referencia al voucher
            refund.generated_voucher = voucher
            refund.mark_as_completed()
            refund.external_reference = f"VOUCHER_{voucher.code}"
            refund.notes = f"Voucher de crédito generado: {voucher.code} - Válido hasta {expiry_date.strftime('%d/%m/%Y')}"
            refund.save()
            
            return {
                'refund_id': refund.id,
                'method': 'voucher',
                'amount': float(refund_amount),
                'status': 'completed',
                'voucher_code': voucher.code,
                'voucher_id': voucher.id,
                'expiry_date': expiry_date.isoformat(),
                'metadata': {
                    'voucher_type': 'credit',
                    'expiry_days': voucher_expiry_days,
                    'requires_manual_processing': False
                }
            }
            
        except Exception as e:
            # Si falla la creación del voucher, marcar como fallido
            refund.mark_as_failed(f"Error generando voucher: {str(e)}")
            return {
                'refund_id': refund.id,
                'method': 'voucher',
                'amount': float(refund_amount),
                'status': 'failed',
                'error': str(e),
                'metadata': {
                    'voucher_type': 'credit',
                    'requires_manual_processing': True
                }
            }
    
    @staticmethod
    def _log_cancellation_with_refund(
        reservation: Reservation,
        cancellation_rules: Dict[str, Any],
        refund_rules: Dict[str, Any],
        total_paid: Decimal,
        penalty_amount: Decimal,
        refund_amount: Decimal,
        refund_result: Optional[Dict[str, Any]]
    ):
        """
        Registra un log detallado de la cancelación con información financiera
        """
        from apps.reservations.models import ReservationChangeLog, ReservationChangeEvent
        
        # Crear mensaje detallado
        message_parts = [
            f"Cancelación procesada - Total pagado: ${total_paid}",
            f"Penalidad aplicada: ${penalty_amount}",
            f"Devolución calculada: ${refund_amount}"
        ]
        
        if refund_result:
            message_parts.append(f"Método de devolución: {refund_result.get('method', 'N/A')}")
            if refund_result.get('status') == 'pending':
                message_parts.append("Devolución pendiente de procesamiento")
        
        message = " | ".join(message_parts)
        
        # Registrar en el log de cambios
        ReservationChangeLog.objects.create(
            reservation=reservation,
            event_type=ReservationChangeEvent.CANCEL,
            changed_by=None,  # Sistema automático
            message=message,
            snapshot={
                'cancellation_rules': cancellation_rules,
                'refund_rules': refund_rules,
                'total_paid': float(total_paid),
                'penalty_amount': float(penalty_amount),
                'refund_amount': float(refund_amount),
                'refund_result': refund_result
            }
        )


# Integración con el nuevo servicio v2
from .refund_processor_v2 import refund_processor_v2


class RefundProcessorV2Integration:
    """
    Integración del RefundProcessor original con el nuevo servicio v2
    """
    
    @staticmethod
    def process_refund_with_gateway(refund: Refund) -> bool:
        """
        Procesa un reembolso usando el nuevo servicio v2 con adaptadores de pasarelas
        
        Args:
            refund: Instancia del reembolso a procesar
            
        Returns:
            bool: True si el reembolso se procesó exitosamente
        """
        return refund_processor_v2.process_refund(refund)
    
    @staticmethod
    def process_refund_with_retries(refund: Refund, max_retries: int = 3) -> bool:
        """
        Procesa un reembolso con reintentos usando el nuevo servicio v2
        
        Args:
            refund: Instancia del reembolso a procesar
            max_retries: Número máximo de reintentos
            
        Returns:
            bool: True si el reembolso se procesó exitosamente
        """
        return refund_processor_v2.process_refund(refund, max_retries)
