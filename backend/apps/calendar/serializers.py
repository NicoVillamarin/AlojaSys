from rest_framework import serializers
from .models import CalendarEvent, RoomMaintenance, CalendarView
from apps.reservations.models import Reservation
from apps.rooms.models import Room
from apps.core.models import Hotel


class CalendarEventSerializer(serializers.ModelSerializer):
    room_name = serializers.CharField(source='room.name', read_only=True)
    room_number = serializers.IntegerField(source='room.number', read_only=True)
    room_floor = serializers.IntegerField(source='room.floor', read_only=True)
    room_type = serializers.CharField(source='room.room_type', read_only=True)
    hotel_name = serializers.CharField(source='hotel.name', read_only=True)
    
    # Información de la reserva si aplica
    reservation_id = serializers.IntegerField(source='reservation.id', read_only=True)
    guest_name = serializers.CharField(source='reservation.guest_name', read_only=True)
    guests_count = serializers.IntegerField(source='reservation.guests', read_only=True)
    total_price = serializers.DecimalField(source='reservation.total_price', max_digits=10, decimal_places=2, read_only=True)
    
    # Información de color y estilo
    color = serializers.SerializerMethodField()
    text_color = serializers.SerializerMethodField()
    
    class Meta:
        model = CalendarEvent
        fields = [
            'id', 'hotel', 'hotel_name', 'room', 'room_name', 'room_number', 
            'room_floor', 'room_type', 'event_type', 'reservation', 'reservation_id',
            'start_date', 'end_date', 'title', 'description', 'is_active', 
            'is_all_day', 'created_at', 'updated_at', 'created_by',
            'guest_name', 'guests_count', 'total_price', 'color', 'text_color'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_color(self, obj):
        """Obtiene el color según el tipo de evento y estado"""
        if obj.event_type == CalendarEventType.RESERVATION and obj.reservation:
            # Colores según estado de la reserva
            colors = {
                'pending': '#F59E0B',      # Amarillo
                'confirmed': '#3B82F6',    # Azul
                'check_in': '#10B981',     # Verde
                'check_out': '#6B7280',    # Gris
                'cancelled': '#EF4444',    # Rojo
                'no_show': '#8B5CF6',      # Púrpura
            }
            return colors.get(obj.reservation.status, '#6B7280')
        elif obj.event_type == CalendarEventType.MAINTENANCE:
            return '#F97316'  # Naranja
        elif obj.event_type == CalendarEventType.BLOCK:
            return '#DC2626'  # Rojo oscuro
        elif obj.event_type == CalendarEventType.CLEANING:
            return '#059669'  # Verde oscuro
        elif obj.event_type == CalendarEventType.OUT_OF_SERVICE:
            return '#7C2D12'  # Marrón
        return '#6B7280'  # Gris por defecto
    
    def get_text_color(self, obj):
        """Obtiene el color del texto (siempre blanco para contraste)"""
        return '#FFFFFF'


class RoomMaintenanceSerializer(serializers.ModelSerializer):
    room_name = serializers.CharField(source='room.name', read_only=True)
    room_number = serializers.IntegerField(source='room.number', read_only=True)
    room_floor = serializers.IntegerField(source='room.floor', read_only=True)
    assigned_to_name = serializers.CharField(source='assigned_to.get_full_name', read_only=True)
    created_by_name = serializers.CharField(source='created_by.get_full_name', read_only=True)
    
    # Información de color según prioridad
    color = serializers.SerializerMethodField()
    
    class Meta:
        model = RoomMaintenance
        fields = [
            'id', 'hotel', 'room', 'room_name', 'room_number', 'room_floor',
            'start_date', 'end_date', 'maintenance_type', 'title', 'description',
            'priority', 'status', 'assigned_to', 'assigned_to_name', 'created_by',
            'created_by_name', 'created_at', 'updated_at', 'color'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_color(self, obj):
        """Obtiene el color según la prioridad"""
        colors = {
            'low': '#10B981',      # Verde
            'medium': '#F59E0B',   # Amarillo
            'high': '#F97316',     # Naranja
            'urgent': '#EF4444',   # Rojo
        }
        return colors.get(obj.priority, '#6B7280')


class CalendarViewSerializer(serializers.ModelSerializer):
    hotel_name = serializers.CharField(source='hotel.name', read_only=True)
    
    class Meta:
        model = CalendarView
        fields = [
            'id', 'user', 'hotel', 'hotel_name', 'default_view',
            'show_maintenance', 'show_blocks', 'show_revenue',
            'room_types', 'floors', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class CalendarEventCreateSerializer(serializers.ModelSerializer):
    """Serializer para crear eventos de calendario desde reservas existentes"""
    
    class Meta:
        model = CalendarEvent
        fields = [
            'hotel', 'room', 'event_type', 'reservation',
            'start_date', 'end_date', 'title', 'description',
            'is_active', 'is_all_day', 'created_by'
        ]
    
    def create(self, validated_data):
        # Si es una reserva, extraer información automáticamente
        if validated_data.get('reservation') and validated_data['event_type'] == CalendarEventType.RESERVATION:
            reservation = validated_data['reservation']
            validated_data['hotel'] = reservation.hotel
            validated_data['room'] = reservation.room
            validated_data['start_date'] = reservation.check_in
            validated_data['end_date'] = reservation.check_out
            validated_data['title'] = f"{reservation.room.name} - {reservation.guest_name}"
            validated_data['description'] = f"Reserva #{reservation.id} - {reservation.guests} huéspedes"
        
        return super().create(validated_data)


class BulkActionSerializer(serializers.Serializer):
    """Serializer para acciones masivas en el calendario"""
    action = serializers.ChoiceField(choices=[
        ('check_in', 'Check-in'),
        ('check_out', 'Check-out'),
        ('cancel', 'Cancelar'),
        ('confirm', 'Confirmar'),
        ('delete', 'Eliminar'),
    ])
    reservation_ids = serializers.ListField(
        child=serializers.IntegerField(),
        min_length=1
    )
    notes = serializers.CharField(required=False, allow_blank=True)


class DragDropSerializer(serializers.Serializer):
    """Serializer para operaciones de drag & drop"""
    reservation_id = serializers.IntegerField()
    new_room_id = serializers.IntegerField(required=False)
    new_start_date = serializers.DateField()
    new_end_date = serializers.DateField()
    notes = serializers.CharField(required=False, allow_blank=True)
    
    def validate(self, data):
        if data['new_start_date'] >= data['new_end_date']:
            raise serializers.ValidationError("La fecha de inicio debe ser anterior a la fecha de fin")
        return data


class CalendarStatsSerializer(serializers.Serializer):
    """Serializer para estadísticas del calendario"""
    total_reservations = serializers.IntegerField()
    total_revenue = serializers.DecimalField(max_digits=10, decimal_places=2)
    occupancy_rate = serializers.FloatField()
    maintenance_count = serializers.IntegerField()
    blocked_rooms = serializers.IntegerField()
    available_rooms = serializers.IntegerField()
    check_ins_today = serializers.IntegerField()
    check_outs_today = serializers.IntegerField()
