from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from django.db.models import Q, Sum, Count, F
from django.utils import timezone
from datetime import date, timedelta
from decimal import Decimal

from .models import CalendarEvent, RoomMaintenance, CalendarView, CalendarEventType
from .serializers import (
    CalendarEventSerializer, RoomMaintenanceSerializer, CalendarViewSerializer,
    CalendarEventCreateSerializer, BulkActionSerializer, DragDropSerializer,
    CalendarStatsSerializer
)
from apps.reservations.models import Reservation, ReservationStatus
from apps.rooms.models import Room, RoomStatus
from apps.core.models import Hotel


class CalendarEventViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gestionar eventos del calendario
    """
    serializer_class = CalendarEventSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        qs = CalendarEvent.objects.select_related('hotel', 'room', 'reservation', 'created_by')
        
        # Filtrar por hotel
        hotel_id = self.request.query_params.get('hotel')
        if hotel_id:
            qs = qs.filter(hotel_id=hotel_id)
        
        # Filtrar por rango de fechas
        start_date = self.request.query_params.get('start_date')
        end_date = self.request.query_params.get('end_date')
        if start_date and end_date:
            qs = qs.filter(
                Q(start_date__lte=end_date) & Q(end_date__gte=start_date)
            )
        
        # Filtrar por tipo de evento
        event_type = self.request.query_params.get('event_type')
        if event_type:
            qs = qs.filter(event_type=event_type)
        
        # Filtrar por habitación
        room_id = self.request.query_params.get('room')
        if room_id:
            qs = qs.filter(room_id=room_id)
        
        # Solo eventos activos por defecto
        if self.request.query_params.get('include_inactive') != 'true':
            qs = qs.filter(is_active=True)
        
        return qs.order_by('start_date', 'room__name')
    
    def get_serializer_class(self):
        if self.action == 'create':
            return CalendarEventCreateSerializer
        return CalendarEventSerializer
    
    @action(detail=False, methods=['get'])
    def calendar_events(self, request):
        """
        Endpoint optimizado para obtener eventos del calendario
        Parámetros: hotel, start_date, end_date, view_type, include_maintenance, include_blocks
        """
        hotel_id = request.query_params.get('hotel')
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        view_type = request.query_params.get('view_type', 'month')
        include_maintenance = request.query_params.get('include_maintenance', 'true').lower() == 'true'
        include_blocks = request.query_params.get('include_blocks', 'true').lower() == 'true'
        
        if not all([hotel_id, start_date, end_date]):
            return Response(
                {"detail": "Parámetros requeridos: hotel, start_date, end_date"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            start_date = date.fromisoformat(start_date)
            end_date = date.fromisoformat(end_date)
        except ValueError:
            return Response(
                {"detail": "Formato de fecha inválido. Use YYYY-MM-DD"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Obtener eventos de reservas
        events = self.get_queryset().filter(
            hotel_id=hotel_id,
            event_type=CalendarEventType.RESERVATION,
            start_date__lte=end_date,
            end_date__gte=start_date
        )
        
        # Agregar eventos de mantenimiento si se solicitan
        if include_maintenance:
            maintenance_events = RoomMaintenance.objects.filter(
                hotel_id=hotel_id,
                start_date__lte=end_date,
                end_date__gte=start_date
            ).select_related('room', 'assigned_to', 'created_by')
            
            # Convertir mantenimientos a eventos de calendario
            for maintenance in maintenance_events:
                events = events.union(
                    CalendarEvent.objects.filter(id=-1)  # Query vacío para union
                )
        
        serializer = self.get_serializer(events, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def rooms_view(self, request):
        """
        Vista de habitaciones: filas = habitaciones, columnas = fechas
        """
        hotel_id = request.query_params.get('hotel')
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        
        if not all([hotel_id, start_date, end_date]):
            return Response(
                {"detail": "Parámetros requeridos: hotel, start_date, end_date"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            start_date = date.fromisoformat(start_date)
            end_date = date.fromisoformat(end_date)
        except ValueError:
            return Response(
                {"detail": "Formato de fecha inválido. Use YYYY-MM-DD"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Obtener habitaciones del hotel
        rooms = Room.objects.filter(
            hotel_id=hotel_id,
            is_active=True
        ).select_related('hotel').order_by('floor', 'name')
        
        # Obtener todas las reservas en el rango de fechas
        reservations = Reservation.objects.filter(
            hotel_id=hotel_id,
            check_in__lte=end_date,
            check_out__gt=start_date
        ).select_related('room').order_by('check_in')
        
        # Crear matriz de habitaciones x fechas
        result = []
        current_date = start_date
        
        while current_date <= end_date:
            day_data = {
                'date': current_date,
                'rooms': []
            }
            
            for room in rooms:
                # Buscar reserva para esta habitación en esta fecha
                room_reservation = None
                for reservation in reservations:
                    if (reservation.room_id == room.id and 
                        reservation.check_in <= current_date < reservation.check_out):
                        room_reservation = reservation
                        break
                
                room_data = {
                    'room_id': room.id,
                    'room_name': room.name,
                    'room_number': room.number,
                    'room_floor': room.floor,
                    'room_type': room.room_type,
                    'status': room.status,
                    'reservation': None
                }
                
                if room_reservation:
                    room_data['reservation'] = {
                        'id': room_reservation.id,
                        'guest_name': room_reservation.guest_name,
                        'status': room_reservation.status,
                        'check_in': room_reservation.check_in,
                        'check_out': room_reservation.check_out,
                        'guests': room_reservation.guests,
                        'total_price': room_reservation.total_price
                    }
                
                day_data['rooms'].append(room_data)
            
            result.append(day_data)
            current_date += timedelta(days=1)
        
        return Response({
            'hotel_id': int(hotel_id),
            'start_date': start_date,
            'end_date': end_date,
            'days': result
        })
    
    @action(detail=False, methods=['post'])
    def bulk_action(self, request):
        """
        Realizar acciones masivas en reservas
        """
        serializer = BulkActionSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        action_type = serializer.validated_data['action']
        reservation_ids = serializer.validated_data['reservation_ids']
        notes = serializer.validated_data.get('notes', '')
        
        # Obtener reservas
        reservations = Reservation.objects.filter(id__in=reservation_ids)
        
        if not reservations.exists():
            return Response(
                {"detail": "No se encontraron reservas con los IDs proporcionados"},
                status=status.HTTP_404_NOT_FOUND
            )
        
        results = []
        
        for reservation in reservations:
            try:
                if action_type == 'check_in':
                    if reservation.status in [ReservationStatus.CONFIRMED, ReservationStatus.CHECK_IN]:
                        reservation.status = ReservationStatus.CHECK_IN
                        reservation.room.status = RoomStatus.OCCUPIED
                        reservation.room.save()
                        reservation.save()
                        results.append({
                            'id': reservation.id,
                            'status': 'success',
                            'message': 'Check-in realizado'
                        })
                    else:
                        results.append({
                            'id': reservation.id,
                            'status': 'error',
                            'message': 'La reserva no puede hacer check-in'
                        })
                
                elif action_type == 'check_out':
                    if reservation.status == ReservationStatus.CHECK_IN:
                        reservation.status = ReservationStatus.CHECK_OUT
                        # Verificar si hay otra reserva activa
                        today = date.today()
                        overlapping = Reservation.objects.filter(
                            room=reservation.room,
                            status__in=[ReservationStatus.PENDING, ReservationStatus.CONFIRMED, ReservationStatus.CHECK_IN],
                            check_in__lt=today,
                            check_out__gt=today,
                        ).exclude(pk=reservation.pk).exists()
                        
                        if not overlapping:
                            reservation.room.status = RoomStatus.AVAILABLE
                            reservation.room.save()
                        
                        reservation.save()
                        results.append({
                            'id': reservation.id,
                            'status': 'success',
                            'message': 'Check-out realizado'
                        })
                    else:
                        results.append({
                            'id': reservation.id,
                            'status': 'error',
                            'message': 'La reserva no puede hacer check-out'
                        })
                
                elif action_type == 'cancel':
                    if reservation.status in [ReservationStatus.PENDING, ReservationStatus.CONFIRMED]:
                        reservation.status = ReservationStatus.CANCELLED
                        reservation.save()
                        results.append({
                            'id': reservation.id,
                            'status': 'success',
                            'message': 'Reserva cancelada'
                        })
                    else:
                        results.append({
                            'id': reservation.id,
                            'status': 'error',
                            'message': 'La reserva no puede ser cancelada'
                        })
                
                elif action_type == 'confirm':
                    if reservation.status == ReservationStatus.PENDING:
                        reservation.status = ReservationStatus.CONFIRMED
                        reservation.save()
                        results.append({
                            'id': reservation.id,
                            'status': 'success',
                            'message': 'Reserva confirmada'
                        })
                    else:
                        results.append({
                            'id': reservation.id,
                            'status': 'error',
                            'message': 'La reserva no puede ser confirmada'
                        })
                
            except Exception as e:
                results.append({
                    'id': reservation.id,
                    'status': 'error',
                    'message': str(e)
                })
        
        return Response({
            'action': action_type,
            'total_processed': len(reservation_ids),
            'results': results
        })
    
    @action(detail=False, methods=['post'])
    def drag_drop(self, request):
        """
        Mover reserva a nueva habitación y/o fechas (drag & drop)
        """
        serializer = DragDropSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        reservation_id = serializer.validated_data['reservation_id']
        new_room_id = serializer.validated_data.get('new_room_id')
        new_start_date = serializer.validated_data['new_start_date']
        new_end_date = serializer.validated_data['new_end_date']
        notes = serializer.validated_data.get('notes', '')
        
        try:
            reservation = Reservation.objects.get(id=reservation_id)
            
            # Validar que la nueva habitación esté disponible
            if new_room_id and new_room_id != reservation.room_id:
                new_room = Room.objects.get(id=new_room_id)
                
                # Verificar disponibilidad
                overlapping = Reservation.objects.filter(
                    room=new_room,
                    status__in=[ReservationStatus.PENDING, ReservationStatus.CONFIRMED, ReservationStatus.CHECK_IN],
                    check_in__lt=new_end_date,
                    check_out__gt=new_start_date,
                ).exclude(pk=reservation_id).exists()
                
                if overlapping:
                    return Response(
                        {"detail": "La habitación no está disponible en esas fechas"},
                        status=status.HTTP_400_BAD_REQUEST
                    )
                
                reservation.room = new_room
            
            # Actualizar fechas
            reservation.check_in = new_start_date
            reservation.check_out = new_end_date
            
            # Validar la reserva
            reservation.clean()
            reservation.save()
            
            return Response({
                'message': 'Reserva movida exitosamente',
                'reservation_id': reservation.id,
                'new_room': reservation.room.name,
                'new_dates': {
                    'check_in': reservation.check_in,
                    'check_out': reservation.check_out
                }
            })
            
        except Reservation.DoesNotExist:
            return Response(
                {"detail": "Reserva no encontrada"},
                status=status.HTTP_404_NOT_FOUND
            )
        except Room.DoesNotExist:
            return Response(
                {"detail": "Habitación no encontrada"},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {"detail": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=False, methods=['get'])
    def stats(self, request):
        """
        Obtener estadísticas del calendario
        """
        hotel_id = request.query_params.get('hotel')
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        
        if not all([hotel_id, start_date, end_date]):
            return Response(
                {"detail": "Parámetros requeridos: hotel, start_date, end_date"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            start_date = date.fromisoformat(start_date)
            end_date = date.fromisoformat(end_date)
        except ValueError:
            return Response(
                {"detail": "Formato de fecha inválido. Use YYYY-MM-DD"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Estadísticas de reservas
        reservations = Reservation.objects.filter(
            hotel_id=hotel_id,
            check_in__lte=end_date,
            check_out__gt=start_date
        )
        
        total_reservations = reservations.count()
        total_revenue = reservations.aggregate(
            total=Sum('total_price')
        )['total'] or Decimal('0.00')
        
        # Estadísticas de habitaciones
        total_rooms = Room.objects.filter(hotel_id=hotel_id, is_active=True).count()
        occupied_rooms = reservations.filter(
            status__in=[ReservationStatus.CHECK_IN]
        ).values('room').distinct().count()
        
        occupancy_rate = (occupied_rooms / total_rooms * 100) if total_rooms > 0 else 0
        
        # Estadísticas de mantenimiento
        maintenance_count = RoomMaintenance.objects.filter(
            hotel_id=hotel_id,
            start_date__lte=end_date,
            end_date__gte=start_date
        ).count()
        
        # Habitaciones bloqueadas
        blocked_rooms = Room.objects.filter(
            hotel_id=hotel_id,
            status=RoomStatus.OUT_OF_SERVICE
        ).count()
        
        available_rooms = total_rooms - occupied_rooms - blocked_rooms
        
        # Check-ins y check-outs de hoy
        today = date.today()
        check_ins_today = reservations.filter(check_in=today).count()
        check_outs_today = reservations.filter(check_out=today).count()
        
        stats_data = {
            'total_reservations': total_reservations,
            'total_revenue': float(total_revenue),
            'occupancy_rate': round(occupancy_rate, 2),
            'maintenance_count': maintenance_count,
            'blocked_rooms': blocked_rooms,
            'available_rooms': available_rooms,
            'check_ins_today': check_ins_today,
            'check_outs_today': check_outs_today,
        }
        
        serializer = CalendarStatsSerializer(stats_data)
        return Response(serializer.data)


class RoomMaintenanceViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gestionar mantenimiento de habitaciones
    """
    serializer_class = RoomMaintenanceSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        qs = RoomMaintenance.objects.select_related('hotel', 'room', 'assigned_to', 'created_by')
        
        hotel_id = self.request.query_params.get('hotel')
        if hotel_id:
            qs = qs.filter(hotel_id=hotel_id)
        
        status_filter = self.request.query_params.get('status')
        if status_filter:
            qs = qs.filter(status=status_filter)
        
        priority_filter = self.request.query_params.get('priority')
        if priority_filter:
            qs = qs.filter(priority=priority_filter)
        
        return qs.order_by('-start_date', 'priority')


class CalendarViewViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gestionar configuraciones de vista del calendario
    """
    serializer_class = CalendarViewSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return CalendarView.objects.filter(user=self.request.user)
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def availability_matrix(request):
    """
    Obtener matriz de disponibilidad de habitaciones
    """
    hotel_id = request.query_params.get('hotel')
    start_date = request.query_params.get('start_date')
    end_date = request.query_params.get('end_date')
    
    if not all([hotel_id, start_date, end_date]):
        return Response(
            {"detail": "Parámetros requeridos: hotel, start_date, end_date"},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        start_date = date.fromisoformat(start_date)
        end_date = date.fromisoformat(end_date)
    except ValueError:
        return Response(
            {"detail": "Formato de fecha inválido. Use YYYY-MM-DD"},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Obtener habitaciones
    rooms = Room.objects.filter(
        hotel_id=hotel_id,
        is_active=True
    ).order_by('floor', 'name')
    
    # Obtener reservas activas
    active_reservations = Reservation.objects.filter(
        hotel_id=hotel_id,
        status__in=[ReservationStatus.PENDING, ReservationStatus.CONFIRMED, ReservationStatus.CHECK_IN],
        check_in__lt=end_date,
        check_out__gt=start_date
    ).select_related('room')
    
    # Crear matriz de disponibilidad
    matrix = []
    current_date = start_date
    
    while current_date <= end_date:
        day_data = {
            'date': current_date,
            'rooms': []
        }
        
        for room in rooms:
            # Verificar si la habitación está ocupada en esta fecha
            is_occupied = any(
                res.room_id == room.id and res.check_in <= current_date < res.check_out
                for res in active_reservations
            )
            
            day_data['rooms'].append({
                'room_id': room.id,
                'room_name': room.name,
                'room_number': room.number,
                'room_floor': room.floor,
                'room_type': room.room_type,
                'is_available': not is_occupied,
                'status': room.status
            })
        
        matrix.append(day_data)
        current_date += timedelta(days=1)
    
    return Response({
        'hotel_id': int(hotel_id),
        'start_date': start_date,
        'end_date': end_date,
        'availability_matrix': matrix
    })
