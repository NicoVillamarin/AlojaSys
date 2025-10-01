from rest_framework import serializers
from .models import DashboardMetrics
from apps.core.serializers import HotelSerializer
from apps.rooms.serializers import RoomSerializer
from apps.reservations.serializers import ReservationSerializer

class DashboardMetricsSerializer(serializers.ModelSerializer):
    hotel = HotelSerializer(read_only=True)
    
    class Meta:
        model = DashboardMetrics
        fields = [
            'id',
            'hotel',
            'date',
            'total_rooms',
            'available_rooms',
            'occupied_rooms',
            'maintenance_rooms',
            'out_of_service_rooms',
            'reserved_rooms',
            'total_reservations',
            'pending_reservations',
            'confirmed_reservations',
            'cancelled_reservations',
            'check_in_today',
            'check_out_today',
            'no_show_today',
            'total_guests',
            'guests_checked_in',
            'guests_expected_today',
            'guests_departing_today',
            'total_revenue',
            'average_room_rate',
            'occupancy_rate',
            'single_rooms_occupied',
            'double_rooms_occupied',
            'triple_rooms_occupied',
            'suite_rooms_occupied',
            'created_at',
            'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

class DashboardSummarySerializer(serializers.Serializer):
    """Serializer para resumen de métricas del dashboard"""
    hotel_id = serializers.IntegerField()
    hotel_name = serializers.CharField()
    date = serializers.DateField()
    
    # Resumen de habitaciones
    total_rooms = serializers.IntegerField()
    available_rooms = serializers.IntegerField()
    occupied_rooms = serializers.IntegerField()
    occupancy_rate = serializers.DecimalField(max_digits=5, decimal_places=2)
    
    # Resumen de reservas
    total_reservations = serializers.IntegerField()
    check_in_today = serializers.IntegerField()
    check_out_today = serializers.IntegerField()
    
    # Resumen de huéspedes
    total_guests = serializers.IntegerField()
    guests_checked_in = serializers.IntegerField()
    guests_expected_today = serializers.IntegerField()
    guests_departing_today = serializers.IntegerField()
    
    # Resumen financiero
    total_revenue = serializers.DecimalField(max_digits=10, decimal_places=2)
    average_room_rate = serializers.DecimalField(max_digits=10, decimal_places=2)
    # Extensiones de pricing
    revenue_night = serializers.DecimalField(max_digits=10, decimal_places=2, required=False)
    nights_sold = serializers.IntegerField(required=False)
    adr_night = serializers.DecimalField(max_digits=10, decimal_places=2, required=False)
    commissions_checkin = serializers.DecimalField(max_digits=10, decimal_places=2, required=False)
    revenue_net_checkin = serializers.DecimalField(max_digits=10, decimal_places=2, required=False)

class DashboardTrendsSerializer(serializers.Serializer):
    """Serializer para tendencias y comparaciones de métricas"""
    date = serializers.DateField()
    occupancy_rate = serializers.DecimalField(max_digits=5, decimal_places=2)
    total_revenue = serializers.DecimalField(max_digits=10, decimal_places=2)
    average_room_rate = serializers.DecimalField(max_digits=10, decimal_places=2)
    total_guests = serializers.IntegerField()
    check_in_today = serializers.IntegerField()
    check_out_today = serializers.IntegerField()
    # Extensiones: métricas financieras detalladas
    net_revenue = serializers.DecimalField(max_digits=10, decimal_places=2, required=False)
    commissions = serializers.DecimalField(max_digits=10, decimal_places=2, required=False)
    nights_sold = serializers.IntegerField(required=False)
    adr_night = serializers.DecimalField(max_digits=10, decimal_places=2, required=False)
