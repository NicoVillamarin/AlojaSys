from django.contrib import admin
from .models import DashboardMetrics

@admin.register(DashboardMetrics)
class DashboardMetricsAdmin(admin.ModelAdmin):
    list_display = [
        'hotel', 'date', 'total_rooms', 'occupied_rooms', 
        'occupancy_rate', 'total_revenue', 'total_guests'
    ]
    list_filter = ['hotel', 'date', 'created_at']
    search_fields = ['hotel__name']
    readonly_fields = ['created_at', 'updated_at']
    ordering = ['-date', 'hotel']
    
    fieldsets = (
        ('Información Básica', {
            'fields': ('hotel', 'date')
        }),
        ('Métricas de Habitaciones', {
            'fields': (
                'total_rooms', 'available_rooms', 'occupied_rooms',
                'maintenance_rooms', 'out_of_service_rooms', 'reserved_rooms'
            )
        }),
        ('Métricas de Reservas', {
            'fields': (
                'total_reservations', 'pending_reservations', 'confirmed_reservations',
                'cancelled_reservations', 'check_in_today', 'check_out_today', 'no_show_today'
            )
        }),
        ('Métricas de Huéspedes', {
            'fields': (
                'total_guests', 'guests_checked_in', 'guests_expected_today', 'guests_departing_today'
            )
        }),
        ('Métricas Financieras', {
            'fields': ('total_revenue', 'average_room_rate', 'occupancy_rate')
        }),
        ('Ocupación por Tipo de Habitación', {
            'fields': (
                'single_rooms_occupied', 'double_rooms_occupied',
                'triple_rooms_occupied', 'suite_rooms_occupied'
            )
        }),
        ('Metadatos', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
