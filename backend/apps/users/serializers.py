from rest_framework import serializers
from django.contrib.auth.models import User, Group
from .models import UserProfile


class UserProfileSerializer(serializers.ModelSerializer):
    """Serializer para el perfil de usuario con hoteles asignados"""
    
    # Campos del User relacionado
    username = serializers.CharField(source='user.username')
    email = serializers.EmailField(source='user.email', required=False, allow_blank=True)
    first_name = serializers.CharField(source='user.first_name', required=False, allow_blank=True)
    last_name = serializers.CharField(source='user.last_name', required=False, allow_blank=True)
    password = serializers.CharField(write_only=True, required=False, allow_blank=True, source='user.password')
    is_superuser = serializers.BooleanField(source='user.is_superuser', required=False, default=False)
    
    # Campos de solo lectura para mostrar info de hoteles y empresa
    hotel_names = serializers.SerializerMethodField()
    enterprise_name = serializers.SerializerMethodField()
    full_name = serializers.SerializerMethodField()
    avatar_image_url = serializers.SerializerMethodField()
    
    # Campos para recibir avatar como base64
    avatar_image_base64 = serializers.CharField(write_only=True, required=False)
    avatar_image_filename = serializers.CharField(write_only=True, required=False)
    
    # Campos de permisos (solo lectura)
    permissions = serializers.SerializerMethodField()
    groups = serializers.SerializerMethodField()
    permissions_codenames = serializers.SerializerMethodField()
    
    # Campo para recibir grupos (write_only, opcional)
    # Usamos ListField con IntegerField en lugar de PrimaryKeyRelatedField para evitar problemas con el modelo
    groups_ids = serializers.ListField(
        child=serializers.IntegerField(),
        required=False,
        write_only=True,
        allow_empty=True
    )
    
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
            'avatar_image',
            'avatar_image_url',
            'avatar_image_base64',
            'avatar_image_filename',
            'enterprise',
            'enterprise_name',
            'hotels',
            'hotel_names',
            'is_active',
            'is_superuser',  # Campo para crear/editar superuser
            'created_at',
            'updated_at',
            'permissions',
            'groups',
            'permissions_codenames',
            'groups_ids',  # Campo para asignar grupos
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'full_name', 'hotel_names', 'enterprise_name', 'avatar_image_url', 'permissions', 'groups', 'permissions_codenames']
    
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
    
    def get_avatar_image_url(self, obj):
        """Obtiene la URL completa del avatar"""
        if obj.avatar_image:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.avatar_image.url)
            return obj.avatar_image.url
        return None
    
    def get_permissions(self, obj):
        """Obtiene todos los permisos del usuario (directos y por grupos)"""
        from django.contrib.auth.models import Permission
        user = obj.user
        
        # Si es superuser, devolver TODOS los permisos del sistema
        if user.is_superuser:
            all_permissions = Permission.objects.select_related('content_type').all()
        else:
            # Obtener IDs de permisos directos
            direct_permission_ids = list(user.user_permissions.values_list('id', flat=True))
            
            # Obtener IDs de permisos por grupos
            group_permission_ids = list(
                Permission.objects.filter(group__user=user).values_list('id', flat=True).distinct()
            )
            
            # Combinar IDs y obtener permisos
            all_permission_ids = list(set(direct_permission_ids + group_permission_ids))
            all_permissions = Permission.objects.filter(id__in=all_permission_ids).select_related('content_type')
        
        return [
            {
                'id': p.id,
                'name': p.name,
                'codename': p.codename,
                'app_label': p.content_type.app_label,
                'model': p.content_type.model,
                'full_name': f"{p.content_type.app_label}.{p.codename}"
            }
            for p in all_permissions
        ]
    
    def get_permissions_codenames(self, obj):
        """Obtiene solo los codenames de permisos en formato app.codename (simple para hooks)"""
        from django.contrib.auth.models import Permission
        user = obj.user
        
        # Si es superuser, devolver TODOS los permisos del sistema
        if user.is_superuser:
            all_permissions = Permission.objects.select_related('content_type').all()
        else:
            # Obtener IDs de permisos directos
            direct_permission_ids = list(user.user_permissions.values_list('id', flat=True))
            
            # Obtener IDs de permisos por grupos
            group_permission_ids = list(
                Permission.objects.filter(group__user=user).values_list('id', flat=True).distinct()
            )
            
            # Combinar IDs y obtener permisos
            all_permission_ids = list(set(direct_permission_ids + group_permission_ids))
            all_permissions = Permission.objects.filter(id__in=all_permission_ids).select_related('content_type')
        
        # Retornar array simple: ["calendar.view_calendarview", "rooms.add_room", ...]
        return [f"{p.content_type.app_label}.{p.codename}" for p in all_permissions]
    
    def get_groups(self, obj):
        """Obtiene los grupos a los que pertenece el usuario"""
        user = obj.user
        groups = user.groups.all()
        
        return [
            {
                'id': g.id,
                'name': g.name,
                'permissions_count': g.permissions.count()
            }
            for g in groups
        ]
    
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
    
    def to_internal_value(self, data):
        """Transforma los datos del request a la estructura esperada por el serializer"""
        # DRF automáticamente anida campos con source='user.*' en {'user': {...}}
        # Pero is_superuser tiene source='user.is_superuser', así que también se anida
        # Guardar is_superuser si viene en el nivel superior
        is_superuser_value = data.get('is_superuser')
        
        # Llamar al método padre (esto procesa los campos con source='user.*')
        internal_data = super().to_internal_value(data)
        
        # Si is_superuser vino en el nivel superior, agregarlo a user_data
        if is_superuser_value is not None and 'user' in internal_data:
            internal_data['user']['is_superuser'] = is_superuser_value
        
        return internal_data
    
    def create(self, validated_data):
        """Crea un nuevo usuario y su perfil con hoteles asignados"""
        # Obtener user_data (DRF lo anida automáticamente por los campos con source='user.*')
        user_data = validated_data.pop('user', {})
        
        # Extraer la contraseña de user_data (ahora debería estar allí porque tiene source='user.password')
        password = user_data.pop('password', None)
        
        # Extraer is_superuser de user_data (puede estar allí si se agregó en to_internal_value)
        # Si no está en user_data, intentar obtenerlo de validated_data directamente
        is_superuser_requested = user_data.pop('is_superuser', None)
        if is_superuser_requested is None:
            is_superuser_requested = validated_data.pop('is_superuser', False)
        
        hotels_data = validated_data.pop('hotels', [])
        enterprise_data = validated_data.pop('enterprise', None)
        groups_ids = validated_data.pop('groups_ids', [])
        
        # Extraer campos de avatar para procesar
        avatar_image_base64 = validated_data.pop('avatar_image_base64', None)
        avatar_image_filename = validated_data.pop('avatar_image_filename', None)
        
        # Procesar enterprise: puede venir como objeto (con .id) o como ID directo
        enterprise_id = None
        if enterprise_data:
            if isinstance(enterprise_data, dict):
                enterprise_id = enterprise_data.get('id')
            elif hasattr(enterprise_data, 'id'):
                enterprise_id = enterprise_data.id
            else:
                enterprise_id = enterprise_data
        
        # IMPORTANTE: Si no hay contraseña, no se puede crear el usuario
        if not password:
            raise serializers.ValidationError({'password': 'La contraseña es requerida para crear un usuario.'})
        
        # Crear el usuario sin password primero
        # IMPORTANTE: Por defecto, los usuarios NO son superuser ni staff
        # Solo los administradores de AlojaSys deberían ser superusers
        print(f"🔐 CREANDO USUARIO: {user_data.get('username')}")
        print(f"   - is_superuser solicitado: {is_superuser_requested}")
        print(f"   - Antes de crear: is_superuser={is_superuser_requested}, is_staff={is_superuser_requested}")
        
        user = User.objects.create_user(
            username=user_data.get('username'),
            email=user_data.get('email', ''),
            first_name=user_data.get('first_name', ''),
            last_name=user_data.get('last_name', ''),
            is_staff=is_superuser_requested,  # Staff solo si es superuser
            is_superuser=is_superuser_requested,  # Superuser según lo solicitado
        )
        
        # VERIFICAR que se creó correctamente
        user.refresh_from_db()
        print(f"   - Después de create_user: is_superuser={user.is_superuser}, is_staff={user.is_staff}")
        
        # Validar que coincida con lo solicitado
        if user.is_superuser != is_superuser_requested:
            print(f"   ⚠️ ADVERTENCIA: is_superuser no coincide con lo solicitado!")
            user.is_superuser = is_superuser_requested
            user.is_staff = is_superuser_requested
            user.save()
            print(f"   ✅ Corregido: Ahora is_superuser={user.is_superuser}, is_staff={user.is_staff}")
        
        # Establecer la contraseña de forma segura
        user.set_password(password)
        user.is_active = True
        user.save()
        
        # VERIFICAR nuevamente después de guardar (por si hay signals que cambien algo)
        user.refresh_from_db()
        print(f"   - Después de save: is_superuser={user.is_superuser}, is_staff={user.is_staff}")
        if user.is_superuser != is_superuser_requested:
            print(f"   ⚠️ ADVERTENCIA: El usuario cambió después de guardar!")
            # Forzar al valor solicitado si por alguna razón cambió
            user.is_superuser = is_superuser_requested
            user.is_staff = is_superuser_requested
            user.save()
            print(f"   ✅ Corregido: Ahora is_superuser={user.is_superuser}, is_staff={user.is_staff}")
        
        # Asignar grupos si se proporcionaron (validar que existan)
        if groups_ids:
            groups = Group.objects.filter(id__in=groups_ids)
            user.groups.set(groups)
        
        # Crear el perfil solo con campos que pertenecen a UserProfile
        profile = UserProfile.objects.create(
            user=user,
            enterprise_id=enterprise_id,
            phone=validated_data.get('phone', ''),
            position=validated_data.get('position', ''),
            avatar_image=validated_data.get('avatar_image', None),
            is_active=validated_data.get('is_active', True)
        )
        
        # Procesar avatar desde base64 si se proporcionó
        if avatar_image_base64 and avatar_image_filename:
            self._save_avatar_from_base64(profile, avatar_image_base64, avatar_image_filename)
        
        # Asignar hoteles
        if hotels_data:
            profile.hotels.set(hotels_data)
        
        return profile
    
    def update(self, instance, validated_data):
        """Actualiza el usuario y su perfil"""
        user_data = validated_data.pop('user', {})
        # La contraseña debería estar en user_data porque tiene source='user.password'
        password = user_data.pop('password', None)
        hotels_data = validated_data.pop('hotels', None)
        enterprise_data = validated_data.pop('enterprise', None)
        groups_ids = validated_data.pop('groups_ids', None)
        
        # Extraer campos de avatar para procesar
        avatar_image_base64 = validated_data.pop('avatar_image_base64', None)
        avatar_image_filename = validated_data.pop('avatar_image_filename', None)
        
        # Procesar enterprise: puede venir como objeto (con .id) o como ID directo
        enterprise_id = None
        if enterprise_data is not None:
            if isinstance(enterprise_data, dict):
                enterprise_id = enterprise_data.get('id')
            elif hasattr(enterprise_data, 'id'):
                enterprise_id = enterprise_data.id
            else:
                enterprise_id = enterprise_data
        
        # Obtener is_superuser del payload (si viene desde el frontend)
        is_superuser_requested = validated_data.pop('is_superuser', None)
        
        # Actualizar campos del User
        user = instance.user
        user.username = user_data.get('username', user.username)
        user.email = user_data.get('email', user.email)
        user.first_name = user_data.get('first_name', user.first_name)
        user.last_name = user_data.get('last_name', user.last_name)
        
        # Actualizar is_superuser e is_staff si se proporcionó
        if is_superuser_requested is not None:
            print(f"🔄 ACTUALIZANDO USUARIO: {user.username}")
            print(f"   - is_superuser solicitado: {is_superuser_requested}")
            user.is_superuser = is_superuser_requested
            user.is_staff = is_superuser_requested  # Staff solo si es superuser
            print(f"   - Actualizado: is_superuser={user.is_superuser}, is_staff={user.is_staff}")
        
        if password:
            user.set_password(password)
        
        user.save()
        
        # Actualizar grupos si se proporcionaron (None significa que no se envió, [] significa que se quiere limpiar)
        if groups_ids is not None:
            # Validar que los grupos existan antes de asignarlos
            groups = Group.objects.filter(id__in=groups_ids)
            user.groups.set(groups)
        
        # Actualizar solo campos del perfil (phone, position, avatar_image, is_active, enterprise)
        if 'phone' in validated_data:
            instance.phone = validated_data['phone']
        if 'position' in validated_data:
            instance.position = validated_data['position']
        if 'avatar_image' in validated_data:
            instance.avatar_image = validated_data['avatar_image']
        if 'is_active' in validated_data:
            instance.is_active = validated_data['is_active']
        if enterprise_id is not None:
            instance.enterprise_id = enterprise_id
        
        instance.save()
        
        # Procesar avatar desde base64 si se proporcionó
        if avatar_image_base64 and avatar_image_filename:
            self._save_avatar_from_base64(instance, avatar_image_base64, avatar_image_filename)
        
        # Actualizar hoteles si se proporcionaron
        if hotels_data is not None:
            instance.hotels.set(hotels_data)
        
        return instance
    
    def _save_avatar_from_base64(self, profile, avatar_image_base64, avatar_image_filename):
        """Guarda el avatar desde base64"""
        try:
            import base64
            from django.core.files.base import ContentFile
            
            # Decodificar base64
            if ',' in avatar_image_base64:
                header, data = avatar_image_base64.split(',', 1)
            else:
                data = avatar_image_base64
            
            file_data = base64.b64decode(data)
            
            # Crear archivo
            file_obj = ContentFile(file_data, name=avatar_image_filename)
            
            # Guardar en el campo avatar_image
            profile.avatar_image.save(avatar_image_filename, file_obj, save=True)
            
        except Exception as e:
            print(f"Error guardando avatar desde base64: {e}")
            # No lanzar excepción para no romper el guardado del perfil

