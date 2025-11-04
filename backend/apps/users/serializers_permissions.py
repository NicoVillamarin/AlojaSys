"""
Serializers para gestión de permisos y grupos
"""
from rest_framework import serializers
from django.contrib.auth.models import Permission, Group
from django.contrib.contenttypes.models import ContentType


class ContentTypeSerializer(serializers.ModelSerializer):
    """Serializer para ContentType (muestra qué modelo pertenece cada permiso)"""
    
    class Meta:
        model = ContentType
        fields = ['id', 'app_label', 'model']
        read_only_fields = ['id', 'app_label', 'model']


class PermissionSerializer(serializers.ModelSerializer):
    """Serializer para permisos - formato completo con toda la información útil"""
    content_type = serializers.SerializerMethodField()
    permission = serializers.SerializerMethodField()
    
    class Meta:
        model = Permission
        fields = [
            'id',
            'name',  # Nombre descriptivo de Django (ej: "Can view stock")
            'codename',  # Solo el codename (ej: "view_stock")
            'content_type',  # Nombre del modelo (ej: "stock")
            'permission',  # Formato completo para hooks (ej: "stock.view_stock")
        ]
        read_only_fields = ['id', 'name', 'codename']
    
    def get_content_type(self, obj):
        """Retorna el nombre del modelo (content_type.model)"""
        return obj.content_type.model
    
    def get_permission(self, obj):
        """Retorna el formato app.codename completo para hooks"""
        return f"{obj.content_type.app_label}.{obj.codename}"


class PermissionDetailSerializer(serializers.ModelSerializer):
    """Serializer completo para cuando se necesita más información"""
    content_type = ContentTypeSerializer(read_only=True)
    app_label = serializers.CharField(source='content_type.app_label', read_only=True)
    model = serializers.CharField(source='content_type.model', read_only=True)
    name = serializers.SerializerMethodField()
    full_name = serializers.SerializerMethodField()
    
    class Meta:
        model = Permission
        fields = [
            'id',
            'name',  # Nombre descriptivo (ej: "Can change Vista de Calendario")
            'codename',
            'content_type',
            'app_label',
            'model',
            'full_name',  # app.codename
        ]
        read_only_fields = ['id', 'name', 'codename', 'content_type']
    
    def get_name(self, obj):
        """Retorna el formato app.codename"""
        return f"{obj.content_type.app_label}.{obj.codename}"
    
    def get_full_name(self, obj):
        """Retorna el formato app.codename (alias de name para compatibilidad)"""
        return f"{obj.content_type.app_label}.{obj.codename}"


class GroupSerializer(serializers.ModelSerializer):
    """Serializer para grupos de usuarios"""
    permissions = PermissionSerializer(many=True, read_only=True)
    permissions_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Group
        fields = ['id', 'name', 'permissions', 'permissions_count']
        read_only_fields = ['id']
    
    def get_permissions_count(self, obj):
        """Cuenta de permisos del grupo"""
        return obj.permissions.count()


class GroupCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer para crear/actualizar grupos con permisos"""
    permissions = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=Permission.objects.all(),
        required=False
    )
    
    class Meta:
        model = Group
        fields = ['id', 'name', 'permissions']
        read_only_fields = ['id']


class UserPermissionsSerializer(serializers.Serializer):
    """Serializer para gestionar permisos de usuarios"""
    permissions = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=Permission.objects.all(),
        required=False
    )
    groups = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=Group.objects.all(),
        required=False
    )

