from django.contrib import admin
from .models import CalendarEvent, RoomMaintenance, CalendarView


@admin.register(CalendarEvent)
class CalendarEventAdmin(admin.ModelAdmin):
    list_display = [
        'title', 'room', 'event_type', 'start_date', 'end_date', 
        'is_active', 'created_at'
    ]
    list_filter = [
        'event_type', 'is_active', 'hotel', 'room__room_type', 
        'start_date', 'created_at'
    ]
    search_fields = ['title', 'room__name', 'description']
    readonly_fields = ['created_at', 'updated_at']
    date_hierarchy = 'start_date'
    
    fieldsets = (
        ('Información Básica', {
            'fields': ('hotel', 'room', 'event_type', 'reservation')
        }),
        ('Fechas', {
            'fields': ('start_date', 'end_date', 'is_all_day')
        }),
        ('Detalles', {
            'fields': ('title', 'description', 'is_active')
        }),
        ('Metadatos', {
            'fields': ('created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(RoomMaintenance)
class RoomMaintenanceAdmin(admin.ModelAdmin):
    list_display = [
        'title', 'room', 'maintenance_type', 'priority', 'status', 
        'start_date', 'assigned_to'
    ]
    list_filter = [
        'maintenance_type', 'priority', 'status', 'hotel', 
        'room__room_type', 'start_date'
    ]
    search_fields = ['title', 'room__name', 'description']
    readonly_fields = ['created_at', 'updated_at']
    date_hierarchy = 'start_date'
    
    fieldsets = (
        ('Información Básica', {
            'fields': ('hotel', 'room', 'maintenance_type', 'title')
        }),
        ('Fechas', {
            'fields': ('start_date', 'end_date')
        }),
        ('Detalles', {
            'fields': ('description', 'priority', 'status')
        }),
        ('Asignación', {
            'fields': ('assigned_to',)
        }),
        ('Metadatos', {
            'fields': ('created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(CalendarView)
class CalendarViewAdmin(admin.ModelAdmin):
    list_display = [
        'user', 'hotel', 'default_view', 'show_maintenance', 
        'show_blocks', 'show_revenue'
    ]
    list_filter = [
        'default_view', 'show_maintenance', 'show_blocks', 
        'show_revenue', 'hotel'
    ]
    search_fields = ['user__username', 'hotel__name']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Usuario y Hotel', {
            'fields': ('user', 'hotel')
        }),
        ('Configuración de Vista', {
            'fields': ('default_view', 'show_maintenance', 'show_blocks', 'show_revenue')
        }),
        ('Filtros', {
            'fields': ('room_types', 'floors'),
            'classes': ('collapse',)
        }),
        ('Metadatos', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
