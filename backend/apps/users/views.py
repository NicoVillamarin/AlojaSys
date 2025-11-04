from rest_framework import viewsets, status
from rest_framework.decorators import api_view, permission_classes, action
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.response import Response
from django.db import IntegrityError
from django.db import models
from django.contrib.auth.models import Permission, Group
from django.contrib.contenttypes.models import ContentType
from .models import UserProfile
from .serializers import UserProfileSerializer


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def me_view(request):
    """
    Vista para obtener información del usuario actual, incluyendo:
    - Datos básicos del usuario
    - Información del perfil (si existe)
    - Hoteles asignados
    - Permisos
    """
    user = request.user
    
    # Datos básicos del usuario
    response_data = {
        "user_id": user.id,
        "username": user.username,
        "email": user.email or "",
        "first_name": user.first_name or "",
        "last_name": user.last_name or "",
        "full_name": user.get_full_name() or user.username,
        "is_staff": user.is_staff,
        "is_superuser": user.is_superuser,  # Incluir en la respuesta para que el frontend pueda mostrar/editarlo
    }
    
    # DEBUG: Log información del usuario
    print(f"🔍 /api/me/ - Usuario: {user.username}")
    print(f"   - is_superuser: {user.is_superuser}")
    print(f"   - is_staff: {user.is_staff}")
    print(f"   - Grupos: {[g.name for g in user.groups.all()]}")
    
    # Obtener permisos del usuario (todos los que tiene, directos o por grupos)
    if user.is_superuser:
        # Si es superuser, devolver TODOS los permisos del sistema
        print(f"   ⚠️ Usuario es SUPERUSER - devolviendo TODOS los permisos")
        user_permissions = Permission.objects.select_related('content_type').all()
    else:
        # Obtener IDs de permisos directos
        direct_permission_ids = list(user.user_permissions.values_list('id', flat=True))
        print(f"   - Permisos directos: {len(direct_permission_ids)}")
        
        # Obtener IDs de permisos por grupos
        group_permission_ids = list(
            Permission.objects.filter(group__user=user).values_list('id', flat=True).distinct()
        )
        print(f"   - Permisos por grupos: {len(group_permission_ids)}")
        
        # Combinar IDs y obtener permisos
        all_permission_ids = list(set(direct_permission_ids + group_permission_ids))
        print(f"   - Total permisos únicos: {len(all_permission_ids)}")
        user_permissions = Permission.objects.filter(id__in=all_permission_ids).select_related('content_type')
        
        # Log algunos permisos de ejemplo
        if user_permissions.exists():
            ejemplo_permisos = [f"{p.content_type.app_label}.{p.codename}" for p in user_permissions[:5]]
            print(f"   - Ejemplo permisos: {ejemplo_permisos}")
    
    # Convertir permisos a formato simple: ["app.codename", ...]
    permissions_list = [f"{p.content_type.app_label}.{p.codename}" for p in user_permissions]
    print(f"   ✅ Total permisos devueltos: {len(permissions_list)}")
    
    # También incluir información de grupos
    groups = user.groups.all()
    groups_list = [{"id": g.id, "name": g.name} for g in groups]
    
    # Importar modelos necesarios
    from apps.core.models import Hotel
    from apps.enterprises.models import Enterprise
    
    # Obtener información del perfil y hoteles asignados
    try:
        profile = user.profile
        
        # Si es superusuario, devolver todos los hoteles activos
        if user.is_superuser:
            hotels = Hotel.objects.filter(is_active=True).select_related('city', 'city__state', 'city__state__country')
            enterprises = Enterprise.objects.filter(is_active=True)
        else:
            # Usuario normal: solo hoteles asignados
            hotels = profile.hotels.filter(is_active=True).select_related('city', 'city__state', 'city__state__country')
            enterprises = Enterprise.objects.filter(id=profile.enterprise.id, is_active=True) if profile.enterprise else Enterprise.objects.none()
        
        # Construir URL del avatar si existe
        avatar_image_url = None
        if profile.avatar_image:
            avatar_image_url = request.build_absolute_uri(profile.avatar_image.url)
        
        response_data.update({
            "profile": {
                "id": profile.id,
                "phone": profile.phone or "",
                "position": profile.position or "",
                "is_active": profile.is_active,
                "avatar_image_url": avatar_image_url,
            },
            "enterprise_ids": [enterprise.id for enterprise in enterprises],
            "enterprise": {
                "id": profile.enterprise.id,
                "name": profile.enterprise.name,
            } if profile.enterprise else None,
            "hotels": [
                {
                    "id": hotel.id,
                    "name": hotel.name,
                    "city": hotel.city.name if hotel.city else "",
                    "timezone": hotel.timezone,
                }
                for hotel in hotels
            ],
            "hotel_ids": [hotel.id for hotel in hotels],  # Para filtros rápidos
            "permissions": permissions_list,  # Lista de permisos del usuario
            "groups": groups_list,  # Grupos a los que pertenece
        })
    except UserProfile.DoesNotExist:
        # Si no tiene perfil (ej: superuser creado por shell)
        if user.is_superuser:
            # Superusuario sin perfil: devolver todos los hoteles y empresas
            from apps.core.models import Hotel
            from apps.enterprises.models import Enterprise
            hotels = Hotel.objects.filter(is_active=True).select_related('city', 'city__state', 'city__state__country')
            enterprises = Enterprise.objects.filter(is_active=True)
            response_data.update({
                "profile": None,
                "enterprise_ids": [enterprise.id for enterprise in enterprises],
                "enterprise": None,  # Superusuario sin perfil no tiene empresa específica
                "hotels": [
                    {
                        "id": hotel.id,
                        "name": hotel.name,
                        "city": hotel.city.name if hotel.city else "",
                        "timezone": hotel.timezone,
                    }
                    for hotel in hotels
                ],
                "hotel_ids": [hotel.id for hotel in hotels],
            })
        else:
            # Usuario normal sin perfil: no hoteles ni empresas
            response_data.update({
                "profile": None,
                "enterprise_ids": [],
                "enterprise": None,
                "hotels": [],
                "hotel_ids": [],
                "permissions": permissions_list,
                "groups": groups_list,
            })
    
    # Siempre agregar permisos y grupos al final
    if "permissions" not in response_data:
        response_data["permissions"] = permissions_list
    if "groups" not in response_data:
        response_data["groups"] = groups_list
    
    return Response(response_data)


class UserProfileViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gestionar usuarios y sus perfiles con asignación de hoteles.
    Permite crear, leer, actualizar y eliminar (soft delete) usuarios.
    """
    serializer_class = UserProfileSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """
        Filtra usuarios por búsqueda, hotel asignado y estado activo
        """
        qs = UserProfile.objects.select_related("user").prefetch_related("hotels").order_by("-created_at")
        
        # Filtro por búsqueda (username, email, nombre, apellido)
        search = self.request.query_params.get("search")
        if search:
            qs = qs.filter(
                user__username__icontains=search
            ) | qs.filter(
                user__email__icontains=search
            ) | qs.filter(
                user__first_name__icontains=search
            ) | qs.filter(
                user__last_name__icontains=search
            ) | qs.filter(
                position__icontains=search
            )
        
        # Filtro por hotel asignado
        hotel_id = self.request.query_params.get("hotel")
        if hotel_id:
            qs = qs.filter(hotels__id=hotel_id).distinct()
        
        # Filtro por estado activo
        is_active = self.request.query_params.get("is_active")
        if is_active is not None and is_active != "":
            if is_active.lower() in ['true', '1']:
                qs = qs.filter(is_active=True)
            elif is_active.lower() in ['false', '0']:
                qs = qs.filter(is_active=False)
        # Si no se especifica filtro, mostrar todos los usuarios (activos e inactivos)
        
        return qs

    def create(self, request, *args, **kwargs):
        """
        Crea un nuevo usuario, manejando errores de integridad.
        """
        try:
            return super().create(request, *args, **kwargs)
        except IntegrityError as e:
            error_message = str(e)
            if 'username' in error_message:
                return Response(
                    {'username': ['Este nombre de usuario ya está en uso.']},
                    status=status.HTTP_400_BAD_REQUEST
                )
            elif 'email' in error_message:
                return Response(
                    {'email': ['Este email ya está registrado.']},
                    status=status.HTTP_400_BAD_REQUEST
                )
            else:
                return Response(
                    {'detail': 'Error al crear el usuario. Por favor, verifica los datos.'},
                    status=status.HTTP_400_BAD_REQUEST
                )

    def update(self, request, *args, **kwargs):
        """
        Actualiza un usuario, manejando errores de integridad.
        """
        try:
            return super().update(request, *args, **kwargs)
        except IntegrityError as e:
            error_message = str(e)
            if 'username' in error_message:
                return Response(
                    {'username': ['Este nombre de usuario ya está en uso.']},
                    status=status.HTTP_400_BAD_REQUEST
                )
            elif 'email' in error_message:
                return Response(
                    {'email': ['Este email ya está registrado.']},
                    status=status.HTTP_400_BAD_REQUEST
                )
            else:
                return Response(
                    {'detail': 'Error al actualizar el usuario. Por favor, verifica los datos.'},
                    status=status.HTTP_400_BAD_REQUEST
                )

    def destroy(self, request, *args, **kwargs):
        """
        Eliminación suave: marcar el usuario como inactivo en lugar de eliminarlo.
        """
        profile = self.get_object()
        if not profile.is_active:
            return Response(status=status.HTTP_204_NO_CONTENT)
        
        profile.is_active = False
        profile.user.is_active = False
        profile.save(update_fields=["is_active", "updated_at"])
        profile.user.save(update_fields=["is_active"])
        
        return Response(status=status.HTTP_204_NO_CONTENT)


class PermissionViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet para listar y ver permisos disponibles en el sistema.
    Solo lectura - los permisos se crean automáticamente por Django.
    SIN PAGINACIÓN - devuelve todos los permisos para facilitar uso con hooks.
    """
    queryset = Permission.objects.select_related('content_type').order_by('content_type__app_label', 'content_type__model', 'codename')
    permission_classes = [IsAuthenticated]
    pagination_class = None  # Sin paginación - devuelve todos los permisos
    
    def get_serializer_class(self):
        from .serializers_permissions import PermissionSerializer, PermissionDetailSerializer
        
        # Para detalle individual, usar serializer completo
        if self.action == 'retrieve':
            return PermissionDetailSerializer
        # Para listado, usar serializer simple
        return PermissionSerializer
    
    def get_queryset(self):
        """Permite filtrar permisos por app o modelo"""
        qs = super().get_queryset()
        
        # Filtro por app
        app_label = self.request.query_params.get('app')
        if app_label:
            qs = qs.filter(content_type__app_label=app_label)
        
        # Filtro por modelo
        model = self.request.query_params.get('model')
        if model:
            qs = qs.filter(content_type__model=model)
        
        # Búsqueda
        search = self.request.query_params.get('search')
        if search:
            qs = qs.filter(
                models.Q(name__icontains=search) |
                models.Q(codename__icontains=search) |
                models.Q(content_type__app_label__icontains=search) |
                models.Q(content_type__model__icontains=search)
            )
        
        return qs
    
    @action(detail=False, methods=['get'])
    def by_app(self, request):
        """Agrupa permisos por aplicación - formato simplificado"""
        from collections import defaultdict
        
        permissions = self.get_queryset()
        grouped = defaultdict(list)
        
        for perm in permissions:
            app_label = perm.content_type.app_label
            grouped[app_label].append({
                'id': perm.id,
                'name': f"{app_label}.{perm.codename}",  # Formato simple para hooks
            })
        
        result = [
            {
                'app': app,
                'permissions': perms,
                'count': len(perms)
            }
            for app, perms in sorted(grouped.items())
        ]
        
        return Response(result)
    
    @action(detail=False, methods=['get'])
    def summary(self, request):
        """Resumen de permisos por app y modelo"""
        from collections import defaultdict
        
        permissions = self.get_queryset()
        summary = defaultdict(lambda: defaultdict(int))
        
        for perm in permissions:
            app_label = perm.content_type.app_label
            model = perm.content_type.model
            summary[app_label][model] += 1
        
        result = [
            {
                'app': app,
                'models': [
                    {'model': model, 'count': count}
                    for model, count in sorted(models.items())
                ],
                'total_permissions': sum(models.values())
            }
            for app, models in sorted(summary.items())
        ]
        
        return Response(result)


class GroupViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gestionar grupos de usuarios y sus permisos.
    Permite CRUD completo de grupos y asignación de permisos.
    """
    queryset = Group.objects.prefetch_related('permissions').all()
    permission_classes = [IsAuthenticated]
    
    def get_serializer_class(self):
        from .serializers_permissions import GroupSerializer, GroupCreateUpdateSerializer
        
        if self.action in ['create', 'update', 'partial_update']:
            return GroupCreateUpdateSerializer
        return GroupSerializer
    
    def get_queryset(self):
        """Permite filtrar grupos"""
        qs = super().get_queryset()
        
        search = self.request.query_params.get('search')
        if search:
            qs = qs.filter(name__icontains=search)
        
        return qs
    
    @action(detail=True, methods=['post', 'put'])
    def assign_permissions(self, request, pk=None):
        """Asigna permisos a un grupo"""
        group = self.get_object()
        permission_ids = request.data.get('permissions', [])
        
        if not permission_ids:
            return Response(
                {'detail': 'Se requiere al menos un permiso'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        permissions = Permission.objects.filter(id__in=permission_ids)
        group.permissions.set(permissions)
        
        serializer = self.get_serializer(group)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def add_permissions(self, request, pk=None):
        """Agrega permisos a un grupo (sin reemplazar los existentes)"""
        group = self.get_object()
        permission_ids = request.data.get('permissions', [])
        
        permissions = Permission.objects.filter(id__in=permission_ids)
        group.permissions.add(*permissions)
        
        serializer = self.get_serializer(group)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def remove_permissions(self, request, pk=None):
        """Elimina permisos de un grupo"""
        group = self.get_object()
        permission_ids = request.data.get('permissions', [])
        
        permissions = Permission.objects.filter(id__in=permission_ids)
        group.permissions.remove(*permissions)
        
        serializer = self.get_serializer(group)
        return Response(serializer.data)


class UserPermissionsViewSet(viewsets.ViewSet):
    """
    ViewSet para gestionar permisos de usuarios individuales.
    Permite asignar/remover permisos directos y grupos a usuarios.
    """
    permission_classes = [IsAuthenticated]
    
    def list(self, request):
        """Lista todos los usuarios con sus permisos (si se necesita)"""
        from django.contrib.auth import get_user_model
        User = get_user_model()
        
        users = User.objects.all()[:10]  # Limitar para no sobrecargar
        return Response({
            'message': 'Use detail actions para ver permisos de usuarios específicos',
            'endpoints': [
                '/api/user-permissions/{user_id}/permissions/',
                '/api/user-permissions/{user_id}/permissions/assign/',
                '/api/user-permissions/{user_id}/groups/assign/',
            ]
        })
    
    @action(detail=False, methods=['get'], url_path=r'users/(?P<user_id>[^/.]+)/permissions')
    def list_user_permissions(self, request, user_id=None):
        """Lista todos los permisos de un usuario (directos y por grupos)"""
        from django.contrib.auth import get_user_model
        
        User = get_user_model()
        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return Response(
                {'detail': 'Usuario no encontrado'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Permisos directos
        direct_permissions = user.user_permissions.all()
        
        # Permisos por grupos
        group_permissions = Permission.objects.filter(group__user=user).distinct()
        
        # Todos los permisos (sin duplicados)
        all_permissions = (direct_permissions | group_permissions).distinct()
        
        # Grupos del usuario
        groups = user.groups.all()
        
        from .serializers_permissions import PermissionSerializer, GroupSerializer
        
        return Response({
            'user_id': user.id,
            'username': user.username,
            'direct_permissions': PermissionSerializer(direct_permissions, many=True).data,
            'group_permissions': PermissionSerializer(group_permissions, many=True).data,
            'all_permissions': PermissionSerializer(all_permissions, many=True).data,
            'all_permissions_codenames': [
                f"{p.content_type.app_label}.{p.codename}" 
                for p in all_permissions
            ],  # Formato simple para hooks: ["calendar.view_calendarview", ...]
            'groups': GroupSerializer(groups, many=True).data,
        })
    
    @action(detail=False, methods=['post'], url_path=r'users/(?P<user_id>[^/.]+)/permissions/assign')
    def assign_permissions(self, request, user_id=None):
        """Asigna permisos directos a un usuario"""
        from django.contrib.auth import get_user_model
        
        User = get_user_model()
        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return Response(
                {'detail': 'Usuario no encontrado'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        permission_ids = request.data.get('permissions', [])
        if not permission_ids:
            return Response(
                {'detail': 'Se requiere al menos un permiso'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        permissions = Permission.objects.filter(id__in=permission_ids)
        user.user_permissions.set(permissions)
        
        from .serializers_permissions import PermissionSerializer
        return Response({
            'user_id': user.id,
            'permissions': PermissionSerializer(user.user_permissions.all(), many=True).data
        })
    
    @action(detail=False, methods=['post'], url_path=r'users/(?P<user_id>[^/.]+)/groups/assign')
    def assign_groups(self, request, user_id=None):
        """Asigna grupos a un usuario"""
        from django.contrib.auth import get_user_model
        
        User = get_user_model()
        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return Response(
                {'detail': 'Usuario no encontrado'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        group_ids = request.data.get('groups', [])
        if not group_ids:
            return Response(
                {'detail': 'Se requiere al menos un grupo'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        groups = Group.objects.filter(id__in=group_ids)
        user.groups.set(groups)
        
        from .serializers_permissions import GroupSerializer
        return Response({
            'user_id': user.id,
            'groups': GroupSerializer(user.groups.all(), many=True).data
        })
