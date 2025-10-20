from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Count, Q
from django.contrib.auth.models import User
from .models import Notification, NotificationType
from .serializers import (
    NotificationSerializer, 
    NotificationCreateSerializer,
    NotificationMarkReadSerializer,
    NotificationStatsSerializer
)


class NotificationViewSet(viewsets.ModelViewSet):
    serializer_class = NotificationSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """Filtrar notificaciones por usuario autenticado"""
        queryset = Notification.objects.filter(
            Q(user=self.request.user) | Q(user__isnull=True)
        ).order_by('-created_at')
        
        # Filtros opcionales
        notification_type = self.request.query_params.get('type')
        is_read = self.request.query_params.get('is_read')
        hotel_id = self.request.query_params.get('hotel_id')
        
        if notification_type:
            queryset = queryset.filter(type=notification_type)
        if is_read is not None:
            queryset = queryset.filter(is_read=is_read.lower() == 'true')
        if hotel_id:
            queryset = queryset.filter(hotel_id=hotel_id)
            
        return queryset
    
    def get_serializer_class(self):
        if self.action == 'create':
            return NotificationCreateSerializer
        return NotificationSerializer
    
    @action(detail=True, methods=['patch'])
    def mark_read(self, request, pk=None):
        """Marcar una notificación específica como leída"""
        notification = self.get_object()
        notification.mark_as_read()
        serializer = self.get_serializer(notification)
        return Response(serializer.data)
    
    @action(detail=False, methods=['post'])
    def mark_all_read(self, request):
        """Marcar todas las notificaciones del usuario como leídas"""
        count = Notification.mark_all_as_read(user=request.user)
        return Response({
            'message': f'{count} notificaciones marcadas como leídas',
            'count': count
        })
    
    @action(detail=False, methods=['get'])
    def unread_count(self, request):
        """Obtener el conteo de notificaciones no leídas"""
        count = Notification.get_unread_count(user=request.user)
        return Response({'unread_count': count})
    
    @action(detail=False, methods=['get'])
    def stats(self, request):
        """Obtener estadísticas de notificaciones"""
        user_notifications = Notification.objects.filter(
            Q(user=request.user) | Q(user__isnull=True)
        )
        
        unread_count = user_notifications.filter(is_read=False).count()
        total_count = user_notifications.count()
        
        # Estadísticas por tipo
        by_type = {}
        for notification_type, _ in NotificationType.choices:
            count = user_notifications.filter(type=notification_type).count()
            unread = user_notifications.filter(type=notification_type, is_read=False).count()
            by_type[notification_type] = {
                'total': count,
                'unread': unread
            }
        
        stats_data = {
            'unread_count': unread_count,
            'total_count': total_count,
            'by_type': by_type
        }
        
        serializer = NotificationStatsSerializer(stats_data)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def recent(self, request):
        """Obtener las últimas 5 notificaciones no leídas"""
        recent_notifications = self.get_queryset().filter(is_read=False)[:5]
        serializer = self.get_serializer(recent_notifications, many=True)
        return Response(serializer.data)
