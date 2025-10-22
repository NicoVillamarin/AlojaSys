from rest_framework import serializers
from django.contrib.auth.models import User
from .models import UserProfile


class UserProfileSerializer(serializers.ModelSerializer):
    """Serializer para el perfil de usuario con hoteles asignados"""
    
    # Campos del User relacionado
    username = serializers.CharField(source='user.username')
    email = serializers.EmailField(source='user.email', required=False, allow_blank=True)
    first_name = serializers.CharField(source='user.first_name', required=False, allow_blank=True)
    last_name = serializers.CharField(source='user.last_name', required=False, allow_blank=True)
    password = serializers.CharField(write_only=True, required=False, allow_blank=True)
    
    # Campos de solo lectura para mostrar info de hoteles y empresa
    hotel_names = serializers.SerializerMethodField()
    enterprise_name = serializers.SerializerMethodField()
    full_name = serializers.SerializerMethodField()
    
    class Meta:
        model = UserProfile
        fields = [
            'id',
            'username',
            'email',
            'first_name',
            'last_name',
            'password',
            'full_name',
            'phone',
            'position',
            'enterprise',
            'enterprise_name',
            'hotels',
            'hotel_names',
            'is_active',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'full_name', 'hotel_names', 'enterprise_name']
    
    def get_hotel_names(self, obj):
        """Retorna lista de nombres de hoteles asignados"""
        return [hotel.name for hotel in obj.hotels.all()]
    
    def get_enterprise_name(self, obj):
        """Retorna el nombre de la empresa asignada"""
        return obj.enterprise.name if obj.enterprise else None
    
    def get_full_name(self, obj):
        """Retorna el nombre completo del usuario"""
        full = obj.user.get_full_name()
        return full if full else obj.user.username
    
    def validate(self, data):
        """Validación personalizada para username y email únicos"""
        user_data = data.get('user', {})
        username = user_data.get('username')
        email = user_data.get('email', '')
        
        # Si estamos creando (no hay instance)
        if not self.instance:
            # Validar username único
            if username and User.objects.filter(username=username).exists():
                raise serializers.ValidationError({
                    'username': f'El nombre de usuario "{username}" ya está en uso. Por favor, elige otro.'
                })
            
            # Validar email único (si se proporciona)
            if email and User.objects.filter(email=email).exists():
                raise serializers.ValidationError({
                    'email': f'El email "{email}" ya está registrado.'
                })
        else:
            # Si estamos actualizando, excluir el usuario actual de la validación
            if username and User.objects.filter(username=username).exclude(id=self.instance.user.id).exists():
                raise serializers.ValidationError({
                    'username': f'El nombre de usuario "{username}" ya está en uso. Por favor, elige otro.'
                })
            
            if email and User.objects.filter(email=email).exclude(id=self.instance.user.id).exists():
                raise serializers.ValidationError({
                    'email': f'El email "{email}" ya está registrado.'
                })
        
        return data
    
    def create(self, validated_data):
        """Crea un nuevo usuario y su perfil con hoteles asignados"""
        user_data = validated_data.pop('user')
        password = user_data.pop('password', None)
        hotels_data = validated_data.pop('hotels', [])
        enterprise_data = validated_data.pop('enterprise', None)
        
        # IMPORTANTE: Si no hay contraseña, no se puede crear el usuario
        if not password:
            raise serializers.ValidationError({'password': 'La contraseña es requerida para crear un usuario.'})
        
        # Crear el usuario sin password primero
        user = User.objects.create_user(
            username=user_data.get('username'),
            email=user_data.get('email', ''),
            first_name=user_data.get('first_name', ''),
            last_name=user_data.get('last_name', ''),
        )
        
        # Establecer la contraseña de forma segura
        user.set_password(password)
        user.is_active = True
        user.save()
        
        # Crear el perfil solo con campos que pertenecen a UserProfile
        profile = UserProfile.objects.create(
            user=user,
            enterprise_id=enterprise_data,
            phone=validated_data.get('phone', ''),
            position=validated_data.get('position', ''),
            is_active=validated_data.get('is_active', True)
        )
        
        # Asignar hoteles
        if hotels_data:
            profile.hotels.set(hotels_data)
        
        return profile
    
    def update(self, instance, validated_data):
        """Actualiza el usuario y su perfil"""
        user_data = validated_data.pop('user', {})
        password = user_data.pop('password', None)
        hotels_data = validated_data.pop('hotels', None)
        enterprise_data = validated_data.pop('enterprise', None)
        
        # Actualizar campos del User
        user = instance.user
        user.username = user_data.get('username', user.username)
        user.email = user_data.get('email', user.email)
        user.first_name = user_data.get('first_name', user.first_name)
        user.last_name = user_data.get('last_name', user.last_name)
        
        if password:
            user.set_password(password)
        
        user.save()
        
        # Actualizar solo campos del perfil (phone, position, is_active, enterprise)
        if 'phone' in validated_data:
            instance.phone = validated_data['phone']
        if 'position' in validated_data:
            instance.position = validated_data['position']
        if 'is_active' in validated_data:
            instance.is_active = validated_data['is_active']
        if enterprise_data is not None:
            instance.enterprise_id = enterprise_data
        
        instance.save()
        
        # Actualizar hoteles si se proporcionaron
        if hotels_data is not None:
            instance.hotels.set(hotels_data)
        
        return instance

