from rest_framework import viewsets, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.db import IntegrityError
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
        "is_superuser": user.is_superuser,
    }
    
    # Obtener información del perfil y hoteles asignados
    try:
        profile = user.profile
        hotels = profile.hotels.all()
        
        response_data.update({
            "profile": {
                "id": profile.id,
                "phone": profile.phone or "",
                "position": profile.position or "",
                "is_active": profile.is_active,
            },
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
        })
    except UserProfile.DoesNotExist:
        # Si no tiene perfil (ej: superuser creado por shell)
        response_data.update({
            "profile": None,
            "hotels": [],
            "hotel_ids": [],
        })
    
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
        if is_active is not None:
            if is_active.lower() in ['true', '1']:
                qs = qs.filter(is_active=True)
            elif is_active.lower() in ['false', '0']:
                qs = qs.filter(is_active=False)
        else:
            # Por defecto, solo mostrar usuarios activos
            qs = qs.filter(is_active=True)
        
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
