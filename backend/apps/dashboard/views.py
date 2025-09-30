from rest_framework import generics, status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.db.models import Sum, Avg, Count, Q
from django.utils import timezone
from datetime import date, timedelta
from decimal import Decimal

from .models import DashboardMetrics
from .serializers import (
    DashboardMetricsSerializer, 
    DashboardSummarySerializer, 
    DashboardTrendsSerializer
)
from apps.core.models import Hotel
from apps.rooms.models import Room
from apps.reservations.models import Reservation, ReservationStatus
def _compute_revenue_for_day(hotels_qs, target_date):
    """Calcula ingresos diarios prorrateados para un conjunto de hoteles en una fecha."""
    reservations = Reservation.objects.filter(
        hotel__in=hotels_qs,
        check_in__lte=target_date,
        check_out__gt=target_date,
        status__in=[
            ReservationStatus.CONFIRMED,
            ReservationStatus.CHECK_IN,
            ReservationStatus.CHECK_OUT,
        ],
    ).only('check_in', 'check_out', 'total_price')

    total = Decimal('0.00')
    for r in reservations:
        nights = (r.check_out - r.check_in).days
        if nights > 0:
            total += (r.total_price or Decimal('0.00')) / Decimal(nights)
        else:
            total += (r.total_price or Decimal('0.00'))
    return total.quantize(Decimal('0.01'))


class DashboardMetricsListCreateView(generics.ListCreateAPIView):
    """Vista para listar y crear métricas del dashboard"""
    serializer_class = DashboardMetricsSerializer
    
    def get_queryset(self):
        hotel_id = self.request.query_params.get('hotel_id')
        start_date = self.request.query_params.get('start_date')
        end_date = self.request.query_params.get('end_date')
        
        queryset = DashboardMetrics.objects.all()
        
        if hotel_id:
            queryset = queryset.filter(hotel_id=hotel_id)
        
        if start_date:
            queryset = queryset.filter(date__gte=start_date)
        
        if end_date:
            queryset = queryset.filter(date__lte=end_date)
        
        return queryset.order_by('-date')

class DashboardMetricsDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Vista para obtener, actualizar o eliminar métricas específicas"""
    queryset = DashboardMetrics.objects.all()
    serializer_class = DashboardMetricsSerializer

@api_view(['GET'])
def dashboard_summary(request):
    """Obtiene un resumen de métricas para un hotel específico o global"""
    hotel_id = request.query_params.get('hotel_id')
    target_date = request.query_params.get('date', date.today().isoformat())
    
    # Si no hay hotel_id, calcular métricas globales
    if not hotel_id:
        try:
            target_date = date.fromisoformat(target_date)
        except ValueError:
            return Response(
                {'error': 'Formato de fecha inválido'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Obtener todos los hoteles activos
        hotels = Hotel.objects.filter(is_active=True)
        if not hotels.exists():
            return Response(
                {'error': 'No hay hoteles disponibles'}, 
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Calcular métricas globales sumando todos los hoteles
        total_rooms = 0
        available_rooms = 0
        occupied_rooms = 0
        maintenance_rooms = 0
        out_of_service_rooms = 0
        reserved_rooms = 0
        total_reservations = 0
        pending_reservations = 0
        confirmed_reservations = 0
        cancelled_reservations = 0
        check_in_today = 0
        check_out_today = 0
        no_show_today = 0
        total_guests = 0
        guests_checked_in = 0
        guests_expected_today = 0
        guests_departing_today = 0
        total_revenue = Decimal('0.00')
        
        for hotel in hotels:
            metrics = DashboardMetrics.objects.filter(hotel=hotel, date=target_date).first()
            if not metrics:
                metrics = DashboardMetrics.calculate_metrics(hotel, target_date)
            total_rooms += metrics.total_rooms
            available_rooms += metrics.available_rooms
            occupied_rooms += metrics.occupied_rooms
            maintenance_rooms += metrics.maintenance_rooms
            out_of_service_rooms += metrics.out_of_service_rooms
            reserved_rooms += metrics.reserved_rooms
            total_reservations += metrics.total_reservations
            pending_reservations += metrics.pending_reservations
            confirmed_reservations += metrics.confirmed_reservations
            cancelled_reservations += metrics.cancelled_reservations
            check_in_today += metrics.check_in_today
            check_out_today += metrics.check_out_today
            no_show_today += metrics.no_show_today
            total_guests += metrics.total_guests
            guests_checked_in += metrics.guests_checked_in
            guests_expected_today += metrics.guests_expected_today
            guests_departing_today += metrics.guests_departing_today
            total_revenue += metrics.total_revenue
        
        # Calcular promedios
        average_room_rate = (total_revenue / Decimal(occupied_rooms)).quantize(Decimal('0.01')) if occupied_rooms > 0 else Decimal('0.00')
        occupancy_rate = (Decimal(occupied_rooms) / Decimal(total_rooms) * Decimal('100')).quantize(Decimal('0.01')) if total_rooms > 0 else Decimal('0.00')
        
        # Crear resumen global
        summary_data = {
            'hotel_id': None,
            'hotel_name': 'Todos los Hoteles',
            'date': target_date,
            'total_rooms': total_rooms,
            'available_rooms': available_rooms,
            'occupied_rooms': occupied_rooms,
            'maintenance_rooms': maintenance_rooms,
            'out_of_service_rooms': out_of_service_rooms,
            'reserved_rooms': reserved_rooms,
            'total_reservations': total_reservations,
            'pending_reservations': pending_reservations,
            'confirmed_reservations': confirmed_reservations,
            'cancelled_reservations': cancelled_reservations,
            'check_in_today': check_in_today,
            'check_out_today': check_out_today,
            'no_show_today': no_show_today,
            'total_guests': total_guests,
            'guests_checked_in': guests_checked_in,
            'guests_expected_today': guests_expected_today,
            'guests_departing_today': guests_departing_today,
            'total_revenue': total_revenue,
            'average_room_rate': average_room_rate,
            'occupancy_rate': occupancy_rate,
        }
        
        serializer = DashboardSummarySerializer(summary_data)
        return Response(serializer.data)
    
    try:
        hotel = Hotel.objects.get(id=hotel_id)
        target_date = date.fromisoformat(target_date)
    except Hotel.DoesNotExist:
        return Response(
            {'error': 'Hotel no encontrado'}, 
            status=status.HTTP_404_NOT_FOUND
        )
    except ValueError:
        return Response(
            {'error': 'Formato de fecha inválido'}, 
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Calcular/obtener métricas para la fecha especificada
    metrics = DashboardMetrics.objects.filter(hotel=hotel, date=target_date).first()
    if not metrics:
        metrics = DashboardMetrics.calculate_metrics(hotel, target_date)
    
    # Crear resumen
    summary_data = {
        'hotel_id': hotel.id,
        'hotel_name': hotel.name,
        'date': target_date,
        'total_rooms': metrics.total_rooms,
        'available_rooms': metrics.available_rooms,
        'occupied_rooms': metrics.occupied_rooms,
        'occupancy_rate': metrics.occupancy_rate,
        'total_reservations': metrics.total_reservations,
        'check_in_today': metrics.check_in_today,
        'check_out_today': metrics.check_out_today,
        'total_guests': metrics.total_guests,
        'guests_checked_in': metrics.guests_checked_in,
        'guests_expected_today': metrics.guests_expected_today,
        'guests_departing_today': metrics.guests_departing_today,
        'total_revenue': metrics.total_revenue,
        'average_room_rate': metrics.average_room_rate,
    }
    
    serializer = DashboardSummarySerializer(summary_data)
    return Response(serializer.data)

@api_view(['GET'])
def dashboard_trends(request):
    """Obtiene tendencias de métricas para un rango de fechas"""
    hotel_id = request.query_params.get('hotel_id')
    start_date = request.query_params.get('start_date')
    end_date = request.query_params.get('end_date')
    days = int(request.query_params.get('days', 30))
    
    # Si no hay hotel_id, calcular tendencias globales
    if not hotel_id:
        # Determinar rango de fechas
        if start_date and end_date:
            start_date = date.fromisoformat(start_date)
            end_date = date.fromisoformat(end_date)
        else:
            end_date = date.today()
            start_date = end_date - timedelta(days=days-1)
        
        # Obtener todos los hoteles activos
        hotels = Hotel.objects.filter(is_active=True)
        if not hotels.exists():
            return Response(
                {'error': 'No hay hoteles disponibles'}, 
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Calcular tendencias globales
        trends_data = []
        current_date = start_date
        
        while current_date <= end_date:
            # Sumar métricas de todos los hoteles para esta fecha
            daily_total_rooms = 0
            daily_occupied_rooms = 0
            daily_total_revenue = Decimal('0.00')
            daily_total_guests = 0
            daily_check_in = 0
            daily_check_out = 0

        daily_metrics = DashboardMetrics.objects.filter(hotel__in=hotels, date=current_date)
        if not daily_metrics.exists():
            # En lugar de calcular todas las métricas completas, calcular revenue diario directo para evitar plano
            daily_total_revenue = _compute_revenue_for_day(hotels, current_date)
        else:
            for metric in daily_metrics:
                daily_total_rooms += metric.total_rooms
                daily_occupied_rooms += metric.occupied_rooms
                daily_total_revenue += metric.total_revenue
                daily_total_guests += metric.total_guests
                daily_check_in += metric.check_in_today
                daily_check_out += metric.check_out_today

            # Calcular promedios
            daily_average_room_rate = (daily_total_revenue / Decimal(daily_occupied_rooms)).quantize(Decimal('0.01')) if daily_occupied_rooms > 0 else Decimal('0.00')
            daily_occupancy_rate = (Decimal(daily_occupied_rooms) / Decimal(daily_total_rooms) * Decimal('100')).quantize(Decimal('0.01')) if daily_total_rooms > 0 else Decimal('0.00')

            trends_data.append({
                'date': current_date,
                'occupancy_rate': daily_occupancy_rate,
                'total_revenue': daily_total_revenue,
                'average_room_rate': daily_average_room_rate,
                'total_guests': daily_total_guests,
                'check_in_today': daily_check_in,
                'check_out_today': daily_check_out,
            })

            current_date += timedelta(days=1)
        
        serializer = DashboardTrendsSerializer(trends_data, many=True)
        return Response(serializer.data)
    
    try:
        hotel = Hotel.objects.get(id=hotel_id)
    except Hotel.DoesNotExist:
        return Response(
            {'error': 'Hotel no encontrado'}, 
            status=status.HTTP_404_NOT_FOUND
        )
    
    # Determinar rango de fechas
    if start_date and end_date:
        start_date = date.fromisoformat(start_date)
        end_date = date.fromisoformat(end_date)
    else:
        end_date = date.today()
        start_date = end_date - timedelta(days=days-1)
    
    # Obtener métricas para el rango de fechas
    metrics = DashboardMetrics.objects.filter(
        hotel=hotel,
        date__range=[start_date, end_date]
    ).order_by('date')
    
    # Si no hay métricas, calcularlas
    if not metrics.exists():
        current_date = start_date
        while current_date <= end_date:
            DashboardMetrics.calculate_metrics(hotel, current_date)
            current_date += timedelta(days=1)
        
        metrics = DashboardMetrics.objects.filter(
            hotel=hotel,
            date__range=[start_date, end_date]
        ).order_by('date')
    
    # Serializar tendencias
    trends_data = []
    for metric in metrics:
        trends_data.append({
            'date': metric.date,
            'occupancy_rate': metric.occupancy_rate,
            'total_revenue': metric.total_revenue,
            'average_room_rate': metric.average_room_rate,
            'total_guests': metric.total_guests,
            'check_in_today': metric.check_in_today,
            'check_out_today': metric.check_out_today,
        })
    
    serializer = DashboardTrendsSerializer(trends_data, many=True)
    return Response(serializer.data)

@api_view(['GET'])
def dashboard_occupancy_by_room_type(request):
    """Obtiene ocupación por tipo de habitación"""
    hotel_id = request.query_params.get('hotel_id')
    target_date = request.query_params.get('date', date.today().isoformat())
    
    # Si no hay hotel_id, calcular ocupación global por tipo
    if not hotel_id:
        try:
            target_date = date.fromisoformat(target_date)
        except ValueError:
            return Response(
                {'error': 'Formato de fecha inválido'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Obtener todos los hoteles activos
        hotels = Hotel.objects.filter(is_active=True)
        if not hotels.exists():
            return Response(
                {'error': 'No hay hoteles disponibles'}, 
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Calcular ocupación global por tipo respetando la fecha
        occupancy_by_type = {
            'single': {'total': 0, 'occupied': 0, 'available': 0},
            'double': {'total': 0, 'occupied': 0, 'available': 0},
            'triple': {'total': 0, 'occupied': 0, 'available': 0},
            'suite': {'total': 0, 'occupied': 0, 'available': 0}
        }

        # Totales por tipo (inventario actual)
        occupancy_by_type['single']['total'] = Room.objects.filter(room_type='single', is_active=True).count()
        occupancy_by_type['double']['total'] = Room.objects.filter(room_type='double', is_active=True).count()
        occupancy_by_type['triple']['total'] = Room.objects.filter(room_type='triple', is_active=True).count()
        occupancy_by_type['suite']['total'] = Room.objects.filter(room_type='suite', is_active=True).count()

        daily_metrics = DashboardMetrics.objects.filter(hotel__in=hotels, date=target_date)
        if not daily_metrics.exists():
            for hotel in hotels:
                DashboardMetrics.calculate_metrics(hotel, target_date)
            daily_metrics = DashboardMetrics.objects.filter(hotel__in=hotels, date=target_date)

        for metric in daily_metrics:
            occupancy_by_type['single']['occupied'] += metric.single_rooms_occupied
            occupancy_by_type['double']['occupied'] += metric.double_rooms_occupied
            occupancy_by_type['triple']['occupied'] += metric.triple_rooms_occupied
            occupancy_by_type['suite']['occupied'] += metric.suite_rooms_occupied

        for key in list(occupancy_by_type.keys()):
            total = occupancy_by_type[key]['total']
            occupied = occupancy_by_type[key]['occupied']
            occupancy_by_type[key]['available'] = max(total - occupied, 0)

        return Response(occupancy_by_type)
    
    try:
        hotel = Hotel.objects.get(id=hotel_id)
        target_date = date.fromisoformat(target_date)
    except Hotel.DoesNotExist:
        return Response(
            {'error': 'Hotel no encontrado'}, 
            status=status.HTTP_404_NOT_FOUND
        )
    except ValueError:
        return Response(
            {'error': 'Formato de fecha inválido'}, 
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Calcular métricas para la fecha especificada
    metrics = DashboardMetrics.calculate_metrics(hotel, target_date)
    
    # Obtener ocupación por tipo de habitación
    occupancy_by_type = {
        'single': {
            'total': Room.objects.filter(hotel=hotel, room_type='single', is_active=True).count(),
            'occupied': metrics.single_rooms_occupied,
            'available': Room.objects.filter(
                hotel=hotel, 
                room_type='single', 
                is_active=True,
                status='available'
            ).count()
        },
        'double': {
            'total': Room.objects.filter(hotel=hotel, room_type='double', is_active=True).count(),
            'occupied': metrics.double_rooms_occupied,
            'available': Room.objects.filter(
                hotel=hotel, 
                room_type='double', 
                is_active=True,
                status='available'
            ).count()
        },
        'triple': {
            'total': Room.objects.filter(hotel=hotel, room_type='triple', is_active=True).count(),
            'occupied': metrics.triple_rooms_occupied,
            'available': Room.objects.filter(
                hotel=hotel, 
                room_type='triple', 
                is_active=True,
                status='available'
            ).count()
        },
        'suite': {
            'total': Room.objects.filter(hotel=hotel, room_type='suite', is_active=True).count(),
            'occupied': metrics.suite_rooms_occupied,
            'available': Room.objects.filter(
                hotel=hotel, 
                room_type='suite', 
                is_active=True,
                status='available'
            ).count()
        }
    }
    
    return Response(occupancy_by_type)

@api_view(['GET'])
def dashboard_revenue_analysis(request):
    """Análisis de ingresos por rango de fechas"""
    hotel_id = request.query_params.get('hotel_id')
    start_date = request.query_params.get('start_date')
    end_date = request.query_params.get('end_date')
    days = int(request.query_params.get('days', 30))
    
    # Determinar rango de fechas
    if start_date and end_date:
        start_date = date.fromisoformat(start_date)
        end_date = date.fromisoformat(end_date)
    else:
        end_date = date.today()
        start_date = end_date - timedelta(days=days-1)

    # Modo GLOBAL (sin hotel_id): sumar por todos los hoteles
    if not hotel_id:
        hotels = Hotel.objects.filter(is_active=True)
        if not hotels.exists():
            return Response({'error': 'No hay hoteles disponibles'}, status=status.HTTP_404_NOT_FOUND)

        # Traer métricas del rango (todos los hoteles)
        metrics = DashboardMetrics.objects.filter(
            hotel__in=hotels,
            date__range=[start_date, end_date]
        ).order_by('date')

        # Backfill si no hay ninguna métrica
        if not metrics.exists():
            current_date = start_date
            while current_date <= end_date:
                for h in hotels:
                    DashboardMetrics.calculate_metrics(h, current_date)
                current_date += timedelta(days=1)
            metrics = DashboardMetrics.objects.filter(
                hotel__in=hotels,
                date__range=[start_date, end_date]
            ).order_by('date')

        # Agregados globales
        total_revenue = sum(m.total_revenue for m in metrics)
        total_occupied = sum(m.occupied_rooms for m in metrics)
        days_count = (end_date - start_date).days + 1
        average_daily_revenue = (total_revenue / Decimal(days_count)) if days_count > 0 else Decimal('0.00')
        average_room_rate = (total_revenue / Decimal(total_occupied)).quantize(Decimal('0.01')) if total_occupied > 0 else Decimal('0.00')

        # Ingresos por tipo (global) a partir de reservas confirmadas/check-in/out
        revenue_by_type = {}
        for room_type in ['single', 'double', 'triple', 'suite']:
            reservations = Reservation.objects.filter(
                hotel__in=hotels,
                room__room_type=room_type,
                status__in=[ReservationStatus.CHECK_IN, ReservationStatus.CHECK_OUT],
                check_in__lte=end_date,
                check_out__gte=start_date
            )
            revenue_by_type[room_type] = reservations.aggregate(total=Sum('total_price'))['total'] or Decimal('0.00')

        # Serie diaria (sumando todos los hoteles por fecha) usando revenue diario ya prorrateado en métricas
        daily_map = {}
        for m in metrics:
            if m.date not in daily_map:
                daily_map[m.date] = {'revenue': Decimal('0.00'), 'occupied': 0, 'total_rooms': 0}
            daily_map[m.date]['revenue'] += m.total_revenue
            daily_map[m.date]['occupied'] += m.occupied_rooms
            daily_map[m.date]['total_rooms'] += m.total_rooms

        daily_revenue = []
        for d, vals in sorted(daily_map.items()):
            revenue = vals['revenue']
            if vals['total_rooms'] == 0:
                # Si no hay métricas persistidas, calculamos revenue directo para ese día
                revenue = _compute_revenue_for_day(hotels, d)
            occ = (Decimal(vals['occupied']) / Decimal(vals['total_rooms']) * Decimal('100')).quantize(Decimal('0.01')) if vals['total_rooms'] > 0 else Decimal('0.00')
            daily_revenue.append({'date': d, 'revenue': revenue, 'occupancy_rate': occ})

        analysis_data = {
            'period': {
                'start_date': start_date,
                'end_date': end_date,
                'days': days_count
            },
            'revenue': {
                'total': total_revenue,
                'average_daily': average_daily_revenue,
                'average_room_rate': average_room_rate
            },
            'revenue_by_room_type': revenue_by_type,
            'daily_revenue': daily_revenue,
        }
        return Response(analysis_data)

    # Modo HOTEL específico
    try:
        hotel = Hotel.objects.get(id=hotel_id)
    except Hotel.DoesNotExist:
        return Response({'error': 'Hotel no encontrado'}, status=status.HTTP_404_NOT_FOUND)

    metrics = DashboardMetrics.objects.filter(
        hotel=hotel,
        date__range=[start_date, end_date]
    ).order_by('date')

    if not metrics.exists():
        current_date = start_date
        while current_date <= end_date:
            DashboardMetrics.calculate_metrics(hotel, current_date)
            current_date += timedelta(days=1)
        metrics = DashboardMetrics.objects.filter(
            hotel=hotel,
            date__range=[start_date, end_date]
        ).order_by('date')

    total_revenue = sum(metric.total_revenue for metric in metrics)
    average_daily_revenue = (total_revenue / Decimal(len(metrics))).quantize(Decimal('0.01')) if metrics else Decimal('0.00')
    # Calcular tarifa promedio global del período ponderada por ocupación
    total_occupied = sum(metric.occupied_rooms for metric in metrics)
    average_room_rate = (total_revenue / Decimal(total_occupied)).quantize(Decimal('0.01')) if total_occupied > 0 else Decimal('0.00')

    revenue_by_type = {}
    for room_type in ['single', 'double', 'triple', 'suite']:
        reservations = Reservation.objects.filter(
            hotel=hotel,
            room__room_type=room_type,
            status__in=[ReservationStatus.CHECK_IN, ReservationStatus.CHECK_OUT],
            check_in__lte=end_date,
            check_out__gte=start_date
        )
        revenue_by_type[room_type] = reservations.aggregate(total=Sum('total_price'))['total'] or Decimal('0.00')

    analysis_data = {
        'period': {
            'start_date': start_date,
            'end_date': end_date,
            'days': len(metrics)
        },
        'revenue': {
            'total': total_revenue,
            'average_daily': average_daily_revenue,
            'average_room_rate': average_room_rate
        },
        'revenue_by_room_type': revenue_by_type,
        'daily_revenue': [
            {
                'date': metric.date,
                'revenue': metric.total_revenue,
                'occupancy_rate': metric.occupancy_rate
            }
            for metric in metrics
        ]
    }

    return Response(analysis_data)

@api_view(['POST'])
def refresh_dashboard_metrics(request):
    """Refresca las métricas del dashboard para un hotel específico"""
    hotel_id = request.data.get('hotel_id')
    target_date = request.data.get('date', date.today().isoformat())
    
    if not hotel_id:
        return Response(
            {'error': 'hotel_id es requerido'}, 
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        hotel = Hotel.objects.get(id=hotel_id)
        target_date = date.fromisoformat(target_date)
    except Hotel.DoesNotExist:
        return Response(
            {'error': 'Hotel no encontrado'}, 
            status=status.HTTP_404_NOT_FOUND
        )
    except ValueError:
        return Response(
            {'error': 'Formato de fecha inválido'}, 
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Calcular métricas
    metrics = DashboardMetrics.calculate_metrics(hotel, target_date)
    
    serializer = DashboardMetricsSerializer(metrics)
    return Response(serializer.data, status=status.HTTP_200_OK)
