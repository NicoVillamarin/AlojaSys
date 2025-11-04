"""
Sistema de permisos personalizado para AlojaSys.

Django crea automáticamente permisos para cada modelo:
- add_{model_name} (ej: add_room)
- change_{model_name} (ej: change_room)
- delete_{model_name} (ej: delete_room)
- view_{model_name} (ej: view_room)

Este módulo proporciona clases de permisos personalizadas para DRF que:
1. Verifican permisos estándar de Django
2. Validan acceso a hoteles según el UserProfile
3. Permiten control granular por rol y hotel
"""

from rest_framework import permissions


class IsHotelStaff(permissions.BasePermission):
    """
    Permiso que verifica que el usuario tenga acceso al hotel especificado.
    
    Requiere que el objeto tenga un atributo 'hotel' o que se pueda obtener
    desde el request (query params o data).
    """
    
    def has_permission(self, request, view):
        """Verifica permisos a nivel de vista/endpoint"""
        # Si no está autenticado, denegar
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Superusuarios pueden todo
        if request.user.is_superuser:
            return True
        
        # Para list/create, verificar si hay hotel_id en query params o data
        if request.method in ['GET', 'POST']:
            hotel_id = None
            
            # Intentar obtener hotel_id de query params
            hotel_id = request.query_params.get('hotel') or request.query_params.get('hotel_id')
            
            # Si no está en query params, intentar del body (POST)
            if not hotel_id and hasattr(request, 'data'):
                hotel_id = request.data.get('hotel') or request.data.get('hotel_id')
            
            if hotel_id:
                return self._user_has_hotel_access(request.user, hotel_id)
        
        return True
    
    def has_object_permission(self, request, view, obj):
        """Verifica permisos a nivel de objeto específico"""
        # Superusuarios pueden todo
        if request.user.is_superuser:
            return True
        
        # Obtener hotel del objeto
        hotel = None
        if hasattr(obj, 'hotel'):
            hotel = obj.hotel
        elif hasattr(obj, 'reservation') and hasattr(obj.reservation, 'hotel'):
            hotel = obj.reservation.hotel
        elif hasattr(obj, 'room') and hasattr(obj.room, 'hotel'):
            hotel = obj.room.hotel
        
        if hotel:
            return self._user_has_hotel_access(request.user, hotel.id)
        
        # Si no hay hotel asociado, permitir (para objetos sin hotel)
        return True
    
    def _user_has_hotel_access(self, user, hotel_id):
        """Verifica si el usuario tiene acceso al hotel"""
        try:
            # Intentar obtener el perfil del usuario
            profile = getattr(user, 'profile', None)
            if not profile:
                return False
            
            # Verificar si el hotel está en los hoteles asignados
            return profile.hotels.filter(id=hotel_id).exists()
        except Exception:
            return False


class CanManageReservations(permissions.BasePermission):
    """
    Permiso para gestionar reservas.
    Requiere permisos 'add_reservation', 'change_reservation', etc.
    """
    
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        
        if request.user.is_superuser:
            return True
        
        # Verificar permisos según el método HTTP
        if request.method == 'GET':
            return request.user.has_perm('reservations.view_reservation')
        elif request.method == 'POST':
            return request.user.has_perm('reservations.add_reservation')
        elif request.method in ['PUT', 'PATCH']:
            return request.user.has_perm('reservations.change_reservation')
        elif request.method == 'DELETE':
            return request.user.has_perm('reservations.delete_reservation')
        
        return False
    
    def has_object_permission(self, request, view, obj):
        # Verificar acceso al hotel + permisos
        hotel_permission = IsHotelStaff()
        if not hotel_permission.has_object_permission(request, view, obj):
            return False
        
        # Verificar permisos específicos
        if request.method in ['GET']:
            return request.user.has_perm('reservations.view_reservation')
        elif request.method in ['PUT', 'PATCH']:
            return request.user.has_perm('reservations.change_reservation')
        elif request.method == 'DELETE':
            return request.user.has_perm('reservations.delete_reservation')
        
        return True


class CanManageRooms(permissions.BasePermission):
    """
    Permiso para gestionar habitaciones.
    Requiere permisos 'add_room', 'change_room', etc.
    """
    
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        
        if request.user.is_superuser:
            return True
        
        if request.method == 'GET':
            return request.user.has_perm('rooms.view_room')
        elif request.method == 'POST':
            return request.user.has_perm('rooms.add_room')
        elif request.method in ['PUT', 'PATCH']:
            return request.user.has_perm('rooms.change_room')
        elif request.method == 'DELETE':
            return request.user.has_perm('rooms.delete_room')
        
        return False
    
    def has_object_permission(self, request, view, obj):
        hotel_permission = IsHotelStaff()
        if not hotel_permission.has_object_permission(request, view, obj):
            return False
        
        if request.method in ['GET']:
            return request.user.has_perm('rooms.view_room')
        elif request.method in ['PUT', 'PATCH']:
            return request.user.has_perm('rooms.change_room')
        elif request.method == 'DELETE':
            return request.user.has_perm('rooms.delete_room')
        
        return True


class CanPerformCheckInOut(permissions.BasePermission):
    """
    Permiso específico para realizar check-in y check-out.
    Puede requerir permisos adicionales o estar basado en roles.
    """
    
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        
        if request.user.is_superuser:
            return True
        
        # Verificar que tenga permiso para cambiar reservas
        return request.user.has_perm('reservations.change_reservation')
    
    def has_object_permission(self, request, view, obj):
        hotel_permission = IsHotelStaff()
        if not hotel_permission.has_object_permission(request, view, obj):
            return False
        
        return request.user.has_perm('reservations.change_reservation')


class HasHotelAccessOrReadOnly(permissions.BasePermission):
    """
    Permiso que permite lectura a todos autenticados,
    pero escritura solo a usuarios con acceso al hotel.
    """
    
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Lectura permitida para todos autenticados
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # Superusuarios pueden escribir
        if request.user.is_superuser:
            return True
        
        # Para escritura, verificar acceso al hotel
        hotel_id = request.query_params.get('hotel') or request.query_params.get('hotel_id')
        if not hotel_id and hasattr(request, 'data'):
            hotel_id = request.data.get('hotel') or request.data.get('hotel_id')
        
        if hotel_id:
            hotel_permission = IsHotelStaff()
            return hotel_permission._user_has_hotel_access(request.user, hotel_id)
        
        return True
    
    def has_object_permission(self, request, view, obj):
        # Lectura permitida
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # Escritura requiere acceso al hotel
        hotel_permission = IsHotelStaff()
        return hotel_permission.has_object_permission(request, view, obj)

