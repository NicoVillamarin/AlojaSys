from rest_framework import serializers
from .models import Notification, NotificationType


class NotificationSerializer(serializers.ModelSerializer):
    type_display = serializers.CharField(source='get_type_display', read_only=True)
    user_name = serializers.CharField(source='user.username', read_only=True)
    created_at_formatted = serializers.DateTimeField(source='created_at', read_only=True)
    
    class Meta:
        model = Notification
        fields = [
            'id', 'type', 'type_display', 'title', 'message', 
            'user', 'user_name', 'is_read', 'created_at', 'created_at_formatted',
            'hotel_id', 'reservation_id', 'metadata'
        ]
        read_only_fields = ['id', 'created_at']


class NotificationCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = [
            'type', 'title', 'message', 'user', 'hotel_id', 
            'reservation_id', 'metadata'
        ]


class NotificationMarkReadSerializer(serializers.Serializer):
    is_read = serializers.BooleanField()


class NotificationStatsSerializer(serializers.Serializer):
    unread_count = serializers.IntegerField()
    total_count = serializers.IntegerField()
    by_type = serializers.DictField()
