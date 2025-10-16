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
    def process_refund(reservation: Reservation, cancellation_policy: CancellationPolicy = None) -> Dict[str, Any]:
        """
        Procesa la devolución automática de una reserva cancelada
        
        Args:
            reservation: Reserva a cancelar
            cancellation_policy: Política de cancelación aplicable (opcional, usa la aplicada a la reserva si no se proporciona)
            
        Returns:
            Dict con información del procesamiento de devolución
        """
        print(f"DEBUG RefundProcessor: Iniciando procesamiento para reserva {reservation.id}")
        try:
            with transaction.atomic():
                # 1. Usar la política aplicada a la reserva o la proporcionada
                if not cancellation_policy:
                    cancellation_policy = reservation.applied_cancellation_policy
                
                if not cancellation_policy:
                    print(f"DEBUG RefundProcessor: No hay política de cancelación para reserva {reservation.id}")
                    return {
                        'success': False,
                        'error': 'No hay política de cancelación aplicada a esta reserva',
                        'refund_amount': Decimal('0.00')
                    }
                
                # 2. Obtener política de devolución del hotel
                refund_policy = RefundPolicy.resolve_for_hotel(reservation.hotel)
                if not refund_policy:
                    print(f"DEBUG RefundProcessor: No hay política de devolución para hotel {reservation.hotel.id}")
                    return {
                        'success': False,
                        'error': 'No hay política de devolución configurada para este hotel',
                        'refund_amount': Decimal('0.00')
                    }
                
                # 3. Calcular reglas de cancelación y devolución
                cancellation_rules = cancellation_policy.get_cancellation_rules(reservation.check_in)
                refund_rules = refund_policy.get_refund_rules(reservation.check_in)
                
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
                        refund_rules
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
                print(f"DEBUG RefundProcessor: Procesamiento exitoso para reserva {reservation.id}, resultado: {result}")
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
        if cancellation_rules.get('type') == 'free':
            return Decimal('0.00')
        
        if cancellation_rules.get('type') == 'partial':
            penalty_percentage = cancellation_rules.get('penalty_percentage', 0)
            return (total_paid * Decimal(penalty_percentage)) / Decimal('100')
        
        # Para 'no_cancellation' o cualquier otro caso, penalidad completa
        return total_paid
    
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
        refund_rules: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """
        Procesa el pago de devolución según el método configurado
        """
        refund_method = refund_rules.get('refund_method', 'original_payment')
        
        # Obtener el pago original para el reembolso
        original_payment = RefundProcessor._get_original_payment(reservation)
        
        if not original_payment:
            return None
        
        # Crear registro de reembolso explícito
        refund = Refund.objects.create(
            reservation=reservation,
            payment=original_payment,
            amount=refund_amount,
            reason=RefundReason.CANCELLATION,
            refund_method=refund_method,
            processing_days=refund_rules.get('processing_days', 7),
            notes=f"Reembolso por cancelación - Método: {refund_method}"
        )
        
        # Procesar según el método
        if refund_method == 'original_payment':
            return RefundProcessor._refund_original_payment(reservation, refund_amount, refund)
        
        elif refund_method == 'bank_transfer':
            return RefundProcessor._create_pending_refund(reservation, refund_amount, 'bank_transfer', refund)
        
        elif refund_method == 'cash':
            return RefundProcessor._create_pending_refund(reservation, refund_amount, 'cash', refund)
        
        elif refund_method == 'voucher':
            return RefundProcessor._create_voucher_refund(reservation, refund_amount, refund)
        
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
                amount=last_card_payment.amount,
                defaults={'notes': f'Pago con tarjeta - ID: {last_card_payment.mp_payment_id}'}
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
        # Marcar como pendiente de procesamiento
        refund.mark_as_processing()
        refund.notes = "Voucher de crédito pendiente de generación"
        refund.save()
        
        return {
            'refund_id': refund.id,
            'method': 'voucher',
            'amount': float(refund_amount),
            'status': 'processing',
            'metadata': {
                'voucher_type': 'credit',
                'expiry_days': 365,
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
