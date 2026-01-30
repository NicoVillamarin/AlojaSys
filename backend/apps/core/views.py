from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from rest_framework.viewsets import ModelViewSet
from rest_framework.views import APIView
from rest_framework.filters import OrderingFilter, SearchFilter
from django.shortcuts import get_object_or_404
from datetime import datetime, date
from .models import Currency, Hotel
from .services.business_rules import get_business_rules
from .serializers import CurrencySerializer, HotelSerializer


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def validate_reservation_action(request):
    """
    Valida si se puede realizar una acción sobre una reserva
    """
    try:
        hotel_id = request.data.get('hotel_id')
        reservation_id = request.data.get('reservation_id')
        action = request.data.get('action')  # 'move', 'resize', 'cancel', 'check_in', 'check_out'
        
        if not all([hotel_id, reservation_id, action]):
            return Response({
                'error': 'Faltan parámetros requeridos: hotel_id, reservation_id, action'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        hotel = get_object_or_404(Hotel, id=hotel_id)
        business_rules = get_business_rules(hotel)
        
        # Importar aquí para evitar import circular
        from apps.reservations.models import Reservation
        reservation = get_object_or_404(Reservation, id=reservation_id, hotel=hotel)
        
        # Validar según la acción
        if action == 'move':
            can_do, reason = business_rules.can_move_reservation(reservation)
        elif action == 'resize':
            can_do, reason = business_rules.can_resize_reservation(reservation)
        elif action == 'cancel':
            can_do, reason = business_rules.can_cancel_reservation(reservation)
        elif action == 'check_in':
            can_do, reason = business_rules.can_check_in_reservation(reservation)
        elif action == 'check_out':
            can_do, reason = business_rules.can_check_out_reservation(reservation)
        else:
            return Response({
                'error': f'Acción no válida: {action}'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        return Response({
            'can_do': can_do,
            'reason': reason,
            'action': action,
            'reservation_id': reservation_id,
            'hotel_id': hotel_id
        })
        
    except Exception as e:
        return Response({
            'error': f'Error interno: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def validate_reservation_dates(request):
    """
    Valida fechas de reserva según reglas de negocio
    """
    try:
        hotel_id = request.data.get('hotel_id')
        check_in = request.data.get('check_in')
        check_out = request.data.get('check_out')
        room_id = request.data.get('room_id')
        
        if not all([hotel_id, check_in, check_out]):
            return Response({
                'error': 'Faltan parámetros requeridos: hotel_id, check_in, check_out'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Convertir strings a date
        try:
            check_in_date = datetime.strptime(check_in, '%Y-%m-%d').date()
            check_out_date = datetime.strptime(check_out, '%Y-%m-%d').date()
        except ValueError:
            return Response({
                'error': 'Formato de fecha inválido. Use YYYY-MM-DD'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        hotel = get_object_or_404(Hotel, id=hotel_id)
        business_rules = get_business_rules(hotel)
        
        is_valid, errors = business_rules.validate_reservation_dates(
            check_in_date, check_out_date, room_id
        )
        
        return Response({
            'is_valid': is_valid,
            'errors': errors,
            'check_in': check_in,
            'check_out': check_out,
            'room_id': room_id
        })
        
    except Exception as e:
        return Response({
            'error': f'Error interno: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_hotel_business_config(request, hotel_id):
    """
    Obtiene configuración de reglas de negocio del hotel
    """
    try:
        hotel = get_object_or_404(Hotel, id=hotel_id)
        business_rules = get_business_rules(hotel)
        
        config = business_rules.get_hotel_config()
        payment_policy = business_rules.get_payment_policy()
        
        return Response({
            'hotel_config': config,
            'payment_policy': {
                'id': payment_policy.id if payment_policy else None,
                'name': payment_policy.name if payment_policy else None,
                'allow_deposit': payment_policy.allow_deposit if payment_policy else False,
                'deposit_type': payment_policy.deposit_type if payment_policy else 'none',
                'deposit_value': float(payment_policy.deposit_value) if payment_policy else 0,
                'deposit_due': payment_policy.deposit_due if payment_policy else 'confirmation',
            } if payment_policy else None
        })
        
    except Exception as e:
        return Response({
            'error': f'Error interno: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class HotelViewSet(ModelViewSet):
    """
    ViewSet para gestionar hoteles
    """
    queryset = Hotel.objects.all()
    serializer_class = HotelSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        # Filtrar por usuario autenticado si es necesario
        return Hotel.objects.filter(is_active=True)


class CurrencyViewSet(ModelViewSet):
    """
    ViewSet para gestionar monedas (free-form).
    Por defecto lista solo activas; usar ?include_inactive=1 para ver todas.
    """

    queryset = Currency.objects.all()
    serializer_class = CurrencySerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [SearchFilter, OrderingFilter]
    search_fields = ["code", "name"]
    ordering_fields = ["code", "name", "updated_at"]
    ordering = ["code"]

    def get_queryset(self):
        qs = Currency.objects.all()
        include_inactive = self.request.query_params.get("include_inactive")
        if str(include_inactive).lower() not in ("1", "true", "yes"):
            qs = qs.filter(is_active=True)
        return qs


class StatusSummaryView(APIView):
    """
    Vista para obtener resumen de estados
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        try:
            # Importar aquí para evitar import circular
            from apps.reservations.models import Reservation
            from django.db.models import Count
            
            # Obtener estadísticas de reservas
            stats = Reservation.objects.values('status').annotate(
                count=Count('id')
            ).order_by('status')
            
            return Response({
                'reservation_statuses': list(stats),
                'total_reservations': sum(item['count'] for item in stats)
            })
            
        except Exception as e:
            return Response({
                'error': f'Error interno: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class GlobalSummaryView(APIView):
    """
    Vista para obtener resumen global del sistema
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        try:
            # Importar aquí para evitar import circular
            from apps.reservations.models import Reservation
            from apps.rooms.models import Room
            from django.db.models import Count, Sum
            
            # Estadísticas globales
            total_hotels = Hotel.objects.filter(is_active=True).count()
            total_rooms = Room.objects.count()
            total_reservations = Reservation.objects.count()
            
            # Reservas por estado
            reservation_stats = Reservation.objects.values('status').annotate(
                count=Count('id')
            ).order_by('status')
            
            return Response({
                'total_hotels': total_hotels,
                'total_rooms': total_rooms,
                'total_reservations': total_reservations,
                'reservation_statuses': list(reservation_stats)
            })
            
        except Exception as e:
            return Response({
                'error': f'Error interno: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)