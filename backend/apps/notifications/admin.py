from django.contrib import admin
from .models import Notification


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'type', 'title', 'user', 'is_read', 'created_at', 'hotel_id'
    ]
    list_filter = [
        'type', 'is_read', 'created_at', 'hotel_id'
    ]
    search_fields = [
        'title', 'message', 'user__username', 'user__email'
    ]
    readonly_fields = ['id', 'created_at']
    ordering = ['-created_at']
    
    fieldsets = (
        ('Información Básica', {
            'fields': ('id', 'type', 'title', 'message')
        }),
        ('Destinatario', {
            'fields': ('user', 'is_read')
        }),
        ('Contexto', {
            'fields': ('hotel_id', 'reservation_id', 'metadata')
        }),
        ('Timestamps', {
            'fields': ('created_at',)
        }),
    )
    
    actions = ['mark_as_read', 'mark_as_unread']
    
    def mark_as_read(self, request, queryset):
        updated = queryset.update(is_read=True)
        self.message_user(request, f'{updated} notificaciones marcadas como leídas.')
    mark_as_read.short_description = "Marcar como leídas"
    
    def mark_as_unread(self, request, queryset):
        updated = queryset.update(is_read=False)
        self.message_user(request, f'{updated} notificaciones marcadas como no leídas.')
    mark_as_unread.short_description = "Marcar como no leídas"
