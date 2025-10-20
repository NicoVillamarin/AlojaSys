"""
Servicio para calcular reglas de cancelación usando snapshot de políticas
Evita que cambios futuros en políticas afecten reservas hechas en el pasado
"""

from datetime import datetime, timedelta
from decimal import Decimal
from typing import Dict, Any, Optional
from django.db import models
from apps.reservations.models import Reservation


class SnapshotCancellationCalculator:
    """
    Calculadora que usa snapshot de políticas de cancelación para reservas históricas
    """
    
    @staticmethod
    def get_cancellation_rules_from_snapshot(reservation: Reservation) -> Optional[Dict[str, Any]]:
        """
        Obtiene las reglas de cancelación basadas en el snapshot de la reserva
        
        Args:
            reservation: Reserva con snapshot de política
            
        Returns:
            Dict con las reglas de cancelación calculadas o None si no hay snapshot
        """
        if not reservation.applied_cancellation_snapshot:
            return None
            
        snapshot = reservation.applied_cancellation_snapshot
        check_in_date = reservation.check_in
        
        # Calcular tiempo restante hasta check-in
        now = datetime.now().date()
        time_until_checkin = check_in_date - now
        hours_until_checkin = time_until_checkin.total_seconds() / 3600
        
        # Convertir tiempos del snapshot a horas
        free_cancellation_hours = SnapshotCancellationCalculator._convert_to_hours(
            snapshot.get('free_cancellation_time', 24),
            snapshot.get('free_cancellation_unit', 'hours')
        )
        
        partial_refund_hours = SnapshotCancellationCalculator._convert_to_hours(
            snapshot.get('partial_time', 72),
            snapshot.get('free_cancellation_unit', 'hours')  # Usar la misma unidad
        )
        
        no_refund_hours = SnapshotCancellationCalculator._convert_to_hours(
            snapshot.get('no_cancellation_time', 168),
            snapshot.get('no_cancellation_unit', 'hours')
        )
        
        # Determinar tipo de cancelación basado en tiempo restante
        if hours_until_checkin >= free_cancellation_hours:
            cancellation_type = 'free'
            refund_percentage = 100.0
            message = snapshot.get('free_cancellation_message', 
                f"Cancelación gratuita hasta {snapshot.get('free_cancellation_time', 24)} {snapshot.get('free_cancellation_unit', 'hours')} antes del check-in")
        elif hours_until_checkin >= partial_refund_hours:
            cancellation_type = 'partial'
            refund_percentage = float(snapshot.get('partial_percentage', 50.0))
            message = snapshot.get('partial_cancellation_message',
                f"Devolución parcial del {snapshot.get('partial_percentage', 50.0)}% hasta {snapshot.get('partial_time', 72)} {snapshot.get('free_cancellation_unit', 'hours')} antes del check-in")
        else:
            cancellation_type = 'no_refund'
            refund_percentage = 0.0
            message = snapshot.get('no_cancellation_message',
                f"Sin devolución después de {snapshot.get('no_cancellation_time', 168)} {snapshot.get('no_cancellation_unit', 'hours')} antes del check-in")
        
        # Calcular penalidad
        penalty_info = SnapshotCancellationCalculator._calculate_penalty_from_snapshot(
            snapshot, reservation
        )
        
        return {
            'cancellation_type': cancellation_type,
            'refund_percentage': refund_percentage,
            'message': message,
            'hours_until_checkin': hours_until_checkin,
            'free_cancellation_hours': free_cancellation_hours,
            'partial_refund_hours': partial_refund_hours,
            'no_refund_hours': no_refund_hours,
            'penalty': penalty_info,
            'policy_info': {
                'policy_id': snapshot.get('policy_id'),
                'policy_name': snapshot.get('name'),
                'snapshot_created_at': snapshot.get('snapshot_created_at'),
                'is_historical': True
            },
            'restrictions': {
                'allow_cancellation_after_checkin': snapshot.get('allow_cancellation_after_checkin', False),
                'allow_cancellation_after_checkout': snapshot.get('allow_cancellation_after_checkout', False),
                'allow_cancellation_no_show': snapshot.get('allow_cancellation_no_show', True),
                'allow_cancellation_early_checkout': snapshot.get('allow_cancellation_early_checkout', False),
            }
        }
    
    @staticmethod
    def _convert_to_hours(value: int, unit: str) -> float:
        """Convierte tiempo a horas"""
        if unit == 'hours':
            return float(value)
        elif unit == 'days':
            return float(value * 24)
        elif unit == 'weeks':
            return float(value * 24 * 7)
        else:
            return float(value)  # Default a horas
    
    @staticmethod
    def _calculate_penalty_from_snapshot(snapshot: Dict[str, Any], reservation: Reservation) -> Dict[str, Any]:
        """
        Calcula la penalidad basada en el snapshot de la política
        """
        fee_type = snapshot.get('fee_type', 'percentage')
        fee_value = float(snapshot.get('fee_value', 10.0))
        
        # Calcular monto total pagado
        total_paid = SnapshotCancellationCalculator._calculate_total_paid(reservation)
        
        if fee_type == 'none':
            penalty_amount = Decimal('0.00')
        elif fee_type == 'percentage':
            penalty_amount = total_paid * (Decimal(fee_value) / 100)
        elif fee_type == 'fixed':
            penalty_amount = Decimal(str(fee_value))
        elif fee_type == 'first_night':
            # Calcular precio de la primera noche
            if reservation.room and reservation.room.base_price:
                penalty_amount = reservation.room.base_price
            else:
                penalty_amount = total_paid * Decimal('0.1')  # 10% como fallback
        elif fee_type == 'nights_percentage':
            # Calcular porcentaje por noche
            nights = (reservation.check_out - reservation.check_in).days
            penalty_amount = total_paid * (Decimal(fee_value) / 100) * nights
        else:
            penalty_amount = Decimal('0.00')
        
        return {
            'fee_type': fee_type,
            'fee_value': fee_value,
            'penalty_amount': float(penalty_amount),
            'penalty_message': snapshot.get('cancellation_fee_message', 
                f"Penalidad de cancelación: {fee_value}{'%' if fee_type == 'percentage' else ' USD'}")
        }
    
    @staticmethod
    def _calculate_total_paid(reservation: Reservation) -> Decimal:
        """Calcula el total pagado de la reserva"""
        from apps.reservations.models import Payment
        
        total_paid = Payment.objects.filter(
            reservation=reservation
        ).aggregate(
            total=models.Sum('amount')
        )['total'] or Decimal('0.00')
        
        return total_paid
    
    @staticmethod
    def should_use_snapshot(reservation: Reservation) -> bool:
        """
        Determina si se debe usar el snapshot en lugar de la política actual
        
        Args:
            reservation: Reserva a evaluar
            
        Returns:
            True si se debe usar snapshot, False si usar política actual
        """
        # Usar snapshot si existe y la reserva está confirmada o en un estado posterior
        return (
            reservation.applied_cancellation_snapshot is not None and
            reservation.status in ['confirmed', 'check_in', 'check_out', 'cancelled']
        )
