from rest_framework.permissions import BasePermission, SAFE_METHODS

from .feature import is_housekeeping_enabled_for_hotel_id

class HousekeepingAccessPermission(BasePermission):
    """
    Permite acceso si:
    - es superusuario
    - tiene el permiso housekeeping.access_housekeeping
    - o su perfil tiene el flag is_housekeeping_staff
    """

    message = "Acceso restringido al módulo de housekeeping."

    def has_permission(self, request, view):
        user = request.user
        if not user or not user.is_authenticated:
            return False

        # El módulo puede estar deshabilitado por plan/licencia.
        # Permitimos bypass a superusuarios (admin del sistema).
        if not user.is_superuser:
            # Determinar hotel_id desde kwargs/query/data (según endpoint).
            hotel_id = (
                getattr(view, "kwargs", {}).get("hotel_id")
                or request.query_params.get("hotel")
                or request.data.get("hotel")
                or request.data.get("hotel_id")
            )
            try:
                hotel_id_int = int(hotel_id) if hotel_id is not None else None
            except (TypeError, ValueError):
                hotel_id_int = None

            if not is_housekeeping_enabled_for_hotel_id(hotel_id_int):
                self.message = "El módulo de housekeeping no está habilitado en su plan."
                return False

        if user.is_superuser:
            return True
        if user.has_perm("housekeeping.access_housekeeping"):
            return True
        profile = getattr(user, "profile", None)
        if profile and getattr(profile, "is_housekeeping_staff", False):
            return True
        return False

    def has_object_permission(self, request, view, obj):
        """
        Para endpoints detail (task/config/etc) donde no viene hotel por query,
        verificamos el hotel desde el objeto.
        """
        user = request.user
        if not user or not user.is_authenticated:
            return False
        if user.is_superuser:
            return True

        hotel_id = getattr(obj, "hotel_id", None)
        if not is_housekeeping_enabled_for_hotel_id(hotel_id):
            self.message = "El módulo de housekeeping no está habilitado en su plan."
            return False

        return self.has_permission(request, view)


class HousekeepingManageAllPermission(BasePermission):
    """
    Permite gestionar todo si:
    - es superusuario
    - o tiene el permiso housekeeping.manage_all_tasks
    """

    message = "No tiene permisos para gestionar todas las tareas."

    def has_permission(self, request, view):
        user = request.user
        if not user or not user.is_authenticated:
            return False
        if user.is_superuser or user.has_perm("housekeeping.manage_all_tasks"):
            return True
        return False

