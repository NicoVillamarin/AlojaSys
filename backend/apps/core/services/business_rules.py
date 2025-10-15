"""
Servicio centralizado para reglas de negocio del hotel
Consolida validaciones de diferentes módulos sin duplicar configuración
"""
from typing import Dict, List, Optional, Tuple
from datetime import date, datetime, time
from decimal import Decimal
from django.db import models
from apps.core.models import Hotel
from apps.reservations.models import Reservation, ReservationStatus
from apps.payments.models import PaymentPolicy
from apps.rates.models import RateRule


class BusinessRulesService:
    """Servicio centralizado para reglas de negocio"""
    
    def __init__(self, hotel: Hotel):
        self.hotel = hotel
    
    def can_move_reservation(self, reservation: Reservation) -> Tuple[bool, str]:
        """
        Valida si se puede mover una reserva según reglas de negocio
        
        Returns:
            Tuple[bool, str]: (puede_mover, razon)
        """
        # Estados que NO permiten movimiento
        non_movable_statuses = {
            ReservationStatus.CHECK_IN: "No se puede mover una reserva con huésped en el hotel",
            ReservationStatus.CHECK_OUT: "No se puede mover una reserva con huésped saliendo", 
            ReservationStatus.CANCELLED: "No se puede mover una reserva cancelada",
            ReservationStatus.NO_SHOW: "No se puede mover una reserva de no show"
        }
        
        if reservation.status in non_movable_statuses:
            return False, non_movable_statuses[reservation.status]
        
        # Estados que SÍ permiten movimiento
        movable_statuses = {
            ReservationStatus.PENDING: "Reserva pendiente - movimiento permitido",
            ReservationStatus.CONFIRMED: "Reserva confirmada - movimiento permitido"
        }
        
        if reservation.status in movable_statuses:
            return True, movable_statuses[reservation.status]
        
        # Estado no reconocido - por seguridad, no permitir
        return False, "Estado de reserva no válido para movimiento"
    
    def can_resize_reservation(self, reservation: Reservation) -> Tuple[bool, str]:
        """
        Valida si se puede redimensionar una reserva
        Misma lógica que can_move_reservation
        """
        return self.can_move_reservation(reservation)
    
    def can_cancel_reservation(self, reservation: Reservation) -> Tuple[bool, str]:
        """
        Valida si se puede cancelar una reserva
        """
        # No se puede cancelar reservas ya finalizadas
        final_statuses = {
            ReservationStatus.CHECK_OUT: "No se puede cancelar una reserva ya finalizada",
            ReservationStatus.CANCELLED: "La reserva ya está cancelada",
            ReservationStatus.NO_SHOW: "No se puede cancelar un no-show"
        }
        
        if reservation.status in final_statuses:
            return False, final_statuses[reservation.status]
        
        return True, "Cancelación permitida"
    
    def can_check_in_reservation(self, reservation: Reservation) -> Tuple[bool, str]:
        """
        Valida si se puede hacer check-in de una reserva
        """
        if reservation.status != ReservationStatus.CONFIRMED:
            return False, "Solo se puede hacer check-in de reservas confirmadas"
        
        # Verificar si es la fecha correcta
        today = date.today()
        if reservation.check_in > today:
            return False, f"El check-in no puede ser antes del {reservation.check_in}"
        
        return True, "Check-in permitido"
    
    def can_check_out_reservation(self, reservation: Reservation) -> Tuple[bool, str]:
        """
        Valida si se puede hacer check-out de una reserva
        """
        if reservation.status != ReservationStatus.CHECK_IN:
            return False, "Solo se puede hacer check-out de reservas con check-in realizado"
        
        return True, "Check-out permitido"
    
    def get_payment_policy(self) -> Optional[PaymentPolicy]:
        """
        Obtiene la política de pago activa para el hotel
        """
        return PaymentPolicy.resolve_for_hotel(self.hotel)
    
    def get_reservation_restrictions(self, check_in: date, check_out: date, room_id: int = None) -> Dict:
        """
        Obtiene restricciones para una reserva en fechas específicas
        """
        restrictions = {
            'min_stay': 1,
            'max_stay': None,
            'closed': False,
            'closed_to_arrival': False,
            'closed_to_departure': False,
            'available_rooms': []
        }
        
        # Buscar reglas aplicables
        rules = RateRule.objects.filter(
            plan__hotel=self.hotel,
            start_date__lte=check_in,
            end_date__gte=check_out
        )
        
        if room_id:
            rules = rules.filter(
                models.Q(target_room_id=room_id) | 
                models.Q(target_room__isnull=True)
            )
        
        # Aplicar restricciones de la regla con mayor prioridad
        for rule in rules.order_by('-priority'):
            if rule.min_stay:
                restrictions['min_stay'] = max(restrictions['min_stay'], rule.min_stay)
            
            if rule.max_stay:
                restrictions['max_stay'] = rule.max_stay if not restrictions['max_stay'] else min(restrictions['max_stay'], rule.max_stay)
            
            if rule.closed:
                restrictions['closed'] = True
            
            if rule.closed_to_arrival:
                restrictions['closed_to_arrival'] = True
            
            if rule.closed_to_departure:
                restrictions['closed_to_departure'] = True
        
        return restrictions
    
    def validate_reservation_dates(self, check_in: date, check_out: date, room_id: int = None) -> Tuple[bool, List[str]]:
        """
        Valida fechas de reserva según reglas de negocio
        """
        errors = []
        
        # Validación básica
        if check_in >= check_out:
            errors.append("La fecha de check-in debe ser anterior al check-out")
        
        if check_in < date.today():
            errors.append("No se pueden crear reservas en fechas pasadas")
        
        # Obtener restricciones
        restrictions = self.get_reservation_restrictions(check_in, check_out, room_id)
        
        # Validar estancia mínima
        nights = (check_out - check_in).days
        if nights < restrictions['min_stay']:
            errors.append(f"La estancia mínima es de {restrictions['min_stay']} noches")
        
        # Validar estancia máxima
        if restrictions['max_stay'] and nights > restrictions['max_stay']:
            errors.append(f"La estancia máxima es de {restrictions['max_stay']} noches")
        
        # Validar restricciones de cierre
        if restrictions['closed']:
            errors.append("No se pueden hacer reservas en estas fechas")
        
        if restrictions['closed_to_arrival'] and check_in == date.today():
            errors.append("No se permiten llegadas en esta fecha")
        
        if restrictions['closed_to_departure'] and check_out == date.today():
            errors.append("No se permiten salidas en esta fecha")
        
        return len(errors) == 0, errors
    
    def get_hotel_config(self) -> Dict:
        """
        Obtiene configuración del hotel para reglas de negocio
        """
        return {
            'check_in_time': self.hotel.check_in_time,
            'check_out_time': self.hotel.check_out_time,
            'auto_check_in_enabled': self.hotel.auto_check_in_enabled,
            'timezone': self.hotel.timezone,
            'is_active': self.hotel.is_active
        }


# Función de conveniencia para usar el servicio
def get_business_rules(hotel: Hotel) -> BusinessRulesService:
    """Obtiene el servicio de reglas de negocio para un hotel"""
    return BusinessRulesService(hotel)
